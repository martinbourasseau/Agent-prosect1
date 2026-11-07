"""Lot 9 — diversification des sources, scores fondés sur les preuves, garde-fous.

Chaque test verrouille un défaut réellement rencontré pendant la mission du
6 novembre 2026 (lot 9), pour qu'il ne revienne pas au lot suivant. Les
premier et dernier groupes sont des tests d'intégrité sur les données livrées.
"""
from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from prospecto.messaging import compose_email, check_email_v4
from prospecto.metrics import portfolio_categories
from prospecto.models import (
    Evidence, Prospect, EVIDENCE_KINDS, EVIDENCE_MATURITY, EVIDENCE_TRUST,
    EVIDENCE_PROCESS_MANUAL, EVIDENCE_JOURNEY_GAP, SOURCE_TYPES, RELIABILITY_LEVELS,
)
from prospecto.opportunity import (
    AUTOMATION_SIGNALS, MATURITY_SIGNALS, NON_GAP_KINDS, analyze, detect_signals,
    detect_maturity, normalize,
)
from prospecto.queue import ValidationQueue
from prospecto.references import (
    load_references, reference_by_id, reference_is_relevant, select_reference,
)
from prospecto.scoring import score_prospect, AXIS_IA, AXIS_SITE_WEB, AXIS_REFONTE
from prospecto.sender import Sender
from prospecto.sources import (
    SOURCE_CATALOGUE, SECTOR_POOL, TERRITORY_POOL, ExplorationLedger,
    coverage, plan_queries,
)
from prospecto.suppression import SuppressionList

ROOT = Path(__file__).resolve().parents[1]
LOT = "2026-11-06-lot9"
LOT_PATH = ROOT / "data" / "prospects" / ("campagne-%s.json" % LOT)
CAMPAIGN_PATH = ROOT / "data" / "campaigns" / ("campagne-%s.json" % LOT)
MESSAGES_PATH = ROOT / "data" / "messages" / ("messages-%s.json" % LOT)
TODAY = date(2026, 11, 6)


def lot9() -> list[dict]:
    return json.loads(LOT_PATH.read_text(encoding="utf-8"))


def ev(kind: str, quote: str, url: str = "https://exemple.fr/page", **kw) -> Evidence:
    base = dict(kind=kind, quote=quote, source_url=url, observed_at="2026-11-06",
                source_type="site_officiel", reliability="haute",
                verified_at="2026-11-06", observed=True)
    base.update(kw)
    return Evidence(**base)


def prospect(evidences: list[Evidence], **kw) -> Prospect:
    base = dict(company="Exemple", domain="exemple.fr", sector="services",
                contact_email="contact@exemple.fr", website="https://exemple.fr",
                needs=["automatisation"], evidences=evidences)
    base.update(kw)
    return Prospect(**base)


# ---------------------------------------------------------------------------
# 1. Catalogue de sources et planification
# ---------------------------------------------------------------------------
class SourceCatalogueTests(unittest.TestCase):
    def test_types_du_catalogue_sont_ceux_du_modele(self):
        for src in SOURCE_CATALOGUE:
            self.assertIn(src.type, SOURCE_TYPES)
            self.assertIn(src.reliability, RELIABILITY_LEVELS)

    def test_sept_familles_de_sources_distinctes(self):
        types = {s.type for s in SOURCE_CATALOGUE}
        self.assertGreaterEqual(len(types), 7)
        self.assertIn("registre_public", types)
        self.assertIn("presse_locale", types)
        self.assertIn("appel_projet", types)

    def test_chaque_source_documente_ses_conditions_d_acces(self):
        """Aucune source ne doit être utilisée sans savoir ce qu'elle autorise."""
        for src in SOURCE_CATALOGUE:
            self.assertTrue(src.access_note.strip(), src.type)
        joined = " ".join(s.access_note.lower() for s in SOURCE_CATALOGUE)
        self.assertIn("captcha", joined)
        self.assertIn("robots", joined)

    def test_pools_de_secteurs_et_territoires_non_vides(self):
        self.assertGreaterEqual(len(SECTOR_POOL), 40)
        self.assertGreaterEqual(len(TERRITORY_POOL), 40)
        self.assertEqual(len(SECTOR_POOL), len(set(SECTOR_POOL)))

    def test_plan_queries_evite_les_departements_deja_couverts(self):
        records = [{"department": "75", "sector": "traiteur", "domain": "a.fr"},
                   {"department": "69", "sector": "formation", "domain": "b.fr"}]
        cov = coverage(records)
        self.assertIn("75", cov.departments)
        specs = plan_queries(records, count=12)
        self.assertTrue(specs)
        for spec in specs:
            self.assertNotIn(spec.department, {"75", "69"})

    def test_plan_queries_fait_tourner_les_types_de_sources(self):
        specs = plan_queries([], count=14)
        self.assertGreaterEqual(len({s.source_type for s in specs}), 5)


# ---------------------------------------------------------------------------
# 2. Registre d'exploration : une structure écartée n'est pas réexaminée
# ---------------------------------------------------------------------------
class ExplorationLedgerTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ledger.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_recharge_ce_qui_a_ete_ecarté(self):
        led = ExplorationLedger(self.path)
        led.record("Déjà Vue", "dejavue.fr", "35", "affutage", "écartée",
                   "réservation en ligne déjà en place")
        led.save()
        again = ExplorationLedger(self.path)
        self.assertTrue(again.seen("dejavue.fr"))
        self.assertTrue(again.seen("Déjà Vue"))
        self.assertFalse(again.seen("jamais-vue.fr"))
        self.assertEqual(again.stats()["by_decision"]["écartée"], 1)

    def test_motif_d_exclusion_obligatoire_pour_etre_utile(self):
        led = ExplorationLedger(self.path)
        entry = led.record("Sans Motif", "sansmotif.fr", decision="écartée",
                           reason="déjà outillé : paiement en ligne")
        self.assertTrue(entry["reason"])
        self.assertTrue(entry["examined_at"])

    def test_secteurs_examinés_ressortent_pour_ne_pas_repetter(self):
        led = ExplorationLedger(self.path)
        led.record("A", "a.fr", sector="etalonnage_metrologie")
        led.record("B", "b.fr", sector="cordonnerie_bourrellerie")
        terms = led.examined_sector_terms()
        self.assertIn("etalonnage", terms)
        self.assertIn("cordonnerie", terms)


# ---------------------------------------------------------------------------
# 3. v7.1 — les quatre trous de détection trouvés sur les pages du lot 9
# ---------------------------------------------------------------------------
class NewSignalTests(unittest.TestCase):
    """Chacun de ces cas donnait un score IA nul ou trop bas avant le lot 9."""

    IDS = {s.id for s in AUTOMATION_SIGNALS}

    def test_difficulte_enoncee_par_l_entreprise_est_detectee(self):
        """Cordes et Âme : la difficulté est publiée, ce n'est pas une déduction."""
        self.assertIn("capacite_reponse_limitee", self.IDS)
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "il peut être compliqué de répondre aux appels. "
               "Nous relevons les messages une fois par jour.")
        found = {d.signal.id for d in detect_signals([e], "ia_automatisation")}
        self.assertIn("capacite_reponse_limitee", found)

    def test_formulaire_qui_finit_dans_la_messagerie_est_detecte(self):
        """Caléo : le formulaire est bon, c'est le dépôt qui manque."""
        self.assertIn("depot_via_messagerie", self.IDS)
        e = ev(EVIDENCE_JOURNEY_GAP,
               "Le bouton ci-dessous ouvre votre messagerie avec la demande pré-remplie.")
        found = {d.signal.id for d in detect_signals([e], "ia_automatisation")}
        self.assertIn("depot_via_messagerie", found)

    def test_deplacement_obligatoire_pour_un_devis_est_detecte(self):
        """Canfora : deux pages distinctes imposent le passage en boutique.

        v8 : une preuve ne paie qu'une fois. Sur UNE seule page contenant deux
        formulations, un seul signal est récompensé ; sur DEUX pages qui
        établissent des constats distincts, les deux comptent. C'est le cas
        réel de Canfora (bourrellerie + sellerie).
        """
        self.assertIn("deplacement_obligatoire", self.IDS)
        one = ev(EVIDENCE_PROCESS_MANUAL,
                 "Venez nous rencontrer en magasin pour établir un devis personnalisé !",
                 "https://exemple.fr/bourrellerie")
        found_one = {d.signal.id for d in detect_signals([one], "ia_automatisation")}
        self.assertEqual(len(found_one), 1, "une preuve ne doit payer qu'une fois")

        two = ev(EVIDENCE_PROCESS_MANUAL,
                 "Pour vos travaux de sellerie, n'hésitez pas à venir nous "
                 "présenter votre demande en magasin et établir un devis personnalisé.",
                 "https://exemple.fr/sellerie")
        found_two = {d.signal.id for d in detect_signals([one, two], "ia_automatisation")}
        self.assertIn("deplacement_obligatoire", found_two)
        self.assertIn("devis_manuel", found_two)

    def test_echeances_recurrentes_sont_detectees(self):
        """Froger : contrats annuels avec compte-rendu."""
        self.assertIn("echeances_recurrentes", self.IDS)
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "Nous proposons des contrats annuels comprenant le nettoyage et "
               "un compte-rendu détaillé.", observed=False)
        dets = [d for d in detect_signals([e], "ia_automatisation")
                if d.signal.id == "echeances_recurrentes"]
        self.assertEqual(len(dets), 1)
        self.assertTrue(dets[0].hypothetical)

    def test_qualification_avant_chiffrage_est_detectee(self):
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "En cas d'instrument inhabituel, nous vous recontactons pour "
               "confirmer la faisabilité avant de chiffrer.")
        found = {d.signal.id for d in detect_signals([e], "ia_automatisation")}
        self.assertIn("tri_manuel", found)


# ---------------------------------------------------------------------------
# 4. Une preuve de maturité ou de confiance n'est pas un manque
# ---------------------------------------------------------------------------
class NonGapEvidenceTests(unittest.TestCase):
    def test_deux_nouveaux_types_de_preuve_sont_valides(self):
        self.assertIn(EVIDENCE_MATURITY, EVIDENCE_KINDS)
        self.assertIn(EVIDENCE_TRUST, EVIDENCE_KINDS)
        self.assertEqual(ev(EVIDENCE_MATURITY, "Réservation en ligne.").validate(), [])
        self.assertEqual(ev(EVIDENCE_TRUST, "SIREN 482141652.").validate(), [])

    def test_une_preuve_de_maturite_ne_cree_jamais_un_besoin(self):
        """Le texte d'un contre-signal peut contenir « demande de devis »."""
        self.assertEqual(NON_GAP_KINDS, {"maturite_existante", "signal_confiance"})
        e = ev(EVIDENCE_MATURITY,
               "Une demande de devis par téléphone est déjà possible, avec "
               "paiement en ligne et réservation en ligne.")
        self.assertEqual(detect_signals([e], "ia_automatisation"), [])

    def test_une_preuve_de_confiance_ne_cree_jamais_un_besoin(self):
        e = ev(EVIDENCE_TRUST,
               "Entreprise établie : devis personnalisé sur demande depuis 1958.")
        self.assertEqual(detect_signals([e], "ia_automatisation"), [])

    def test_la_maturite_reste_un_contre_signal_actif(self):
        e = ev(EVIDENCE_MATURITY, "Boutique en ligne avec panier.")
        self.assertEqual({d.signal.id for d in detect_maturity([e])},
                         {"paiement_en_ligne"})

    def test_process_hint_sert_meme_si_la_premiere_preuve_est_une_maturite(self):
        """Le texte libre ne doit pas être perdu à cause de l'ordre des preuves."""
        maturite = ev(EVIDENCE_MATURITY, "Boutique en ligne.")
        process = ev(EVIDENCE_PROCESS_MANUAL, "Nous contacter pour toute demande.")
        found = detect_signals([maturite, process], "ia_automatisation",
                              extra_text="devis par téléphone")
        self.assertIn("devis_manuel", {d.signal.id for d in found})

    def test_un_signal_de_maturite_n_est_pas_compte_deux_fois(self):
        """Bug v7 corrigé : paiement en ligne compté besoin ET contre-signal."""
        e = ev(EVIDENCE_PROCESS_MANUAL, "Paiement en ligne disponible.")
        self.assertEqual(detect_signals([e], "ia_automatisation"), [])
        self.assertTrue(detect_maturity([e]))


# ---------------------------------------------------------------------------
# 5. Scores : preuves, confiance, indépendance vis-à-vis du métier
# ---------------------------------------------------------------------------
class ScoringEvidenceTests(unittest.TestCase):
    def test_deux_pages_decrivant_le_meme_processus_donnent_confiance_haute(self):
        """Canfora : bourrellerie ET sellerie disent la même chose."""
        evs = [ev(EVIDENCE_PROCESS_MANUAL,
                  "Venez nous rencontrer en magasin pour établir un devis personnalisé !",
                  "https://exemple.fr/bourrellerie"),
               ev(EVIDENCE_PROCESS_MANUAL,
                  "Venir nous présenter votre demande en magasin et établir un devis personnalisé.",
                  "https://exemple.fr/sellerie")]
        ia = score_prospect(prospect(evs), today=TODAY)[AXIS_IA]
        self.assertEqual(ia["confidence"], "haute")
        self.assertNotIn("processus observé sur une seule page : confirmer sur une seconde source",
                         ia["missing_information"])

    def test_une_hypothese_pese_moins_qu_un_fait_observe(self):
        quote = "Venez nous rencontrer en magasin pour établir un devis personnalisé !"
        seen = score_prospect(prospect([ev(EVIDENCE_PROCESS_MANUAL, quote)]), today=TODAY)
        guessed = score_prospect(
            prospect([ev(EVIDENCE_PROCESS_MANUAL, quote, observed=False)]), today=TODAY)
        self.assertGreater(seen[AXIS_IA]["score"], guessed[AXIS_IA]["score"])
        self.assertTrue(guessed[AXIS_IA]["hypothetical_signals"])

    def test_une_source_peu_fiable_pese_moins(self):
        quote = "Venez nous rencontrer en magasin pour établir un devis personnalisé !"
        high = score_prospect(prospect([ev(EVIDENCE_PROCESS_MANUAL, quote)]), today=TODAY)
        low = score_prospect(
            prospect([ev(EVIDENCE_PROCESS_MANUAL, quote,
                         source_type="annuaire_pro", reliability="faible")]), today=TODAY)
        self.assertGreater(high[AXIS_IA]["score"], low[AXIS_IA]["score"])

    def test_le_metier_n_influence_pas_le_score_ia(self):
        """Deux entreprises du même secteur, processus différents, scores différents."""
        quote = "Venez nous rencontrer en magasin pour établir un devis personnalisé !"
        manuel = prospect([ev(EVIDENCE_PROCESS_MANUAL, quote)], sector="paysagiste")
        outille = prospect([ev(EVIDENCE_PROCESS_MANUAL, quote),
                            ev(EVIDENCE_MATURITY,
                               "Réservation en ligne et paiement en ligne disponibles.")],
                           sector="paysagiste")
        a = score_prospect(manuel, today=TODAY)[AXIS_IA]["score"]
        b = score_prospect(outille, today=TODAY)[AXIS_IA]["score"]
        self.assertGreater(a, b)
        # Et changer seulement le secteur ne change rien.
        autre = prospect([ev(EVIDENCE_PROCESS_MANUAL, quote)], sector="luthier")
        self.assertEqual(a, score_prospect(autre, today=TODAY)[AXIS_IA]["score"])

    def test_chaque_motif_cite_un_extrait_reel_et_une_source(self):
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "Venez nous rencontrer en magasin pour établir un devis personnalisé !",
               "https://exemple.fr/contact")
        ia = score_prospect(prospect([e]), today=TODAY)[AXIS_IA]
        cited = " ".join(ia["reasons"])
        self.assertIn("https://exemple.fr/contact", cited)
        self.assertIn("Venez nous rencontrer", cited)

    def test_sans_preuve_le_score_reste_prudent_et_les_manques_sont_listes(self):
        ia = score_prospect(prospect([]), today=TODAY)[AXIS_IA]
        self.assertLessEqual(ia["score"], 15)
        self.assertTrue(ia["missing_information"])

    def test_un_site_existant_n_affiche_plus_un_manque_contradictoire(self):
        site = score_prospect(prospect([]), today=TODAY)[AXIS_SITE_WEB]
        self.assertIn("un site existe déjà : la création n'est pas le bon service",
                      site["missing_information"])
        self.assertNotIn("aucune observation directe sur la présence en ligne",
                         site["missing_information"])

    def test_les_trois_axes_sont_independants_et_bornes(self):
        s = score_prospect(prospect([ev(EVIDENCE_PROCESS_MANUAL,
                                       "Devis par téléphone uniquement.")]), today=TODAY)
        for axis in (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA):
            self.assertIn(axis, s)
            self.assertTrue(0 <= s[axis]["score"] <= 100)
            self.assertIn(s[axis]["confidence"], RELIABILITY_LEVELS)
        self.assertEqual(s["engine_version"], "v8")


# ---------------------------------------------------------------------------
# 6. Références : seulement si pertinentes, formulation neutre
# ---------------------------------------------------------------------------
class ReferenceRelevanceTests(unittest.TestCase):
    def test_une_reference_hors_sujet_est_ecartee(self):
        refs = load_references()
        site = reference_by_id("groupe-bourasseau", refs)
        self.assertIsNotNone(site)
        p = prospect([], solution_type="automatisation_admin")
        self.assertFalse(reference_is_relevant(site, p))

    def test_une_reference_pertinente_est_conservee(self):
        refs = load_references()
        site = reference_by_id("groupe-bourasseau", refs)
        p = prospect([], solution_type="refonte_site")
        self.assertTrue(reference_is_relevant(site, p))

    def test_select_reference_ne_propose_rien_pour_un_besoin_administratif(self):
        p = prospect([ev(EVIDENCE_PROCESS_MANUAL, "Devis par téléphone.")],
                     solution_type="automatisation_admin", needs=["automatisation"])
        self.assertIsNone(select_reference(p, load_references()))

    def test_formulations_restees_neutres(self):
        refs = load_references()
        for ref in refs:
            text = (getattr(ref, "pitch", "") or "") + " " + (getattr(ref, "label", "") or "")
            low = text.lower()
            for forbidden in ("j'ai réalisé", "nous avons réalisé", "mon client",
                              "notre client", "j'ai créé"):
                self.assertNotIn(forbidden, low, "%s : %s" % (ref.id, forbidden))


# ---------------------------------------------------------------------------
# 7. Garde-fous d'envoi : rien ne part, jamais
# ---------------------------------------------------------------------------
class SendSafetyTests(unittest.TestCase):
    def test_preflight_reste_bloquant(self):
        """preflight() persiste son résultat DNS : on isole le fichier de réglages.

        Sans cela, chaque exécution des tests réécrivait last_checked_at dans
        data/campaigns/v4-settings.json — le fichier de production.
        """
        import shutil
        import tempfile
        from prospecto.sender import SETTINGS_PATH

        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "v4-settings.json"
            shutil.copyfile(SETTINGS_PATH, isolated)
            ok, issues = Sender(settings_path=isolated).preflight()
            self.assertFalse(ok)
            self.assertGreaterEqual(len(issues), 1)
            # Le blocage doit rester explicite, pas seulement « un problème ».
            joined = " ".join(issues).lower()
            self.assertIn("enabled=false", joined)

    def test_les_tests_ne_reecrivent_pas_les_reglages_de_production(self):
        import shutil
        import tempfile
        from prospecto.sender import SETTINGS_PATH

        before = SETTINGS_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "v4-settings.json"
            shutil.copyfile(SETTINGS_PATH, isolated)
            Sender(settings_path=isolated).preflight()
        self.assertEqual(before, SETTINGS_PATH.read_bytes(),
                         "les réglages de production ont été modifiés par un test")

    def test_adresse_absente_bloque_quel_que_soit_le_score(self):
        s = Sender()
        self.assertTrue(s._is_blocked({"email": "", "scores": {"priority": 100}}))
        self.assertTrue(s._is_blocked({"email": "   "}))

    def test_contacte_suspendu_oppose_ne_recoivent_jamais_rien(self):
        s = Sender()
        for status in ("contacté", "suspendu", "opposition", "rebond", "auto_reply"):
            self.assertTrue(s._is_blocked({"email": "a@b.fr", "status": status}), status)
        self.assertTrue(s._is_blocked({"email": "a@b.fr", "suspended_at": "2026-11-06"}))

    def test_une_opposition_de_la_liste_est_respectee(self):
        sup = SuppressionList()
        entries = sup.entries if hasattr(sup, "entries") else []
        for entry in entries:
            addr = (entry.get("email") if isinstance(entry, dict) else str(entry)) or ""
            if addr:
                self.assertTrue(sup.is_suppressed(addr), addr)

    def test_aucune_entree_lot9_dans_le_journal_d_envoi(self):
        log = json.loads((ROOT / "data" / "history" / "send-log.json").read_text(encoding="utf-8"))
        entries = log.get("entries", [])
        self.assertEqual([e for e in entries if LOT in json.dumps(e)], [])


# ---------------------------------------------------------------------------
# 8. Tableau de bord : catégories réelles, sans double comptage
# ---------------------------------------------------------------------------
class DashboardCategoryTests(unittest.TestCase):
    def test_la_partition_du_portefeuille_est_exclusive(self):
        records = [
            {"status": "nouveau"}, {"status": "nouveau"},
            {"status": "contacté"}, {"status": "auto_reply"},
            {"status": "opposition"}, {"status": "suspendu"},
            {"status": "rebond"}, {"status": "brouillon_en_attente"},
            {"status": "a_approfondir"},
        ]
        f = portfolio_categories(records)
        self.assertTrue(f["controle_exclusif"])
        self.assertEqual(f["total"], 9)
        self.assertEqual(f["contactes"], 2)
        self.assertEqual(f["decouverts"], 2)
        self.assertEqual(f["oppositions"], 1)
        self.assertEqual(f["suspendus"], 1)

    def test_une_opposition_n_est_pas_comptee_aussi_comme_contacte(self):
        f = portfolio_categories([{"status": "opposition"}])
        self.assertEqual(f["oppositions"], 1)
        self.assertEqual(f["contactes"], 0)

    def test_qualifies_est_transversal_et_ne_s_ajoute_pas(self):
        f = portfolio_categories([{"status": "contacté", "commercial_priority": "haute"}])
        self.assertEqual(f["qualifies"], 1)
        self.assertEqual(f["contactes"], 1)
        self.assertIn("ne s'ajoute pas", f["definitions"]["qualifies"])

    def test_un_statut_inconnu_reste_visible(self):
        f = portfolio_categories([{"status": "mystère"}])
        self.assertEqual(f["autres_details"], {"mystère": 1})
        self.assertTrue(f["controle_exclusif"])

    def test_queue_counts_inclut_les_brouillons_et_la_file_obsolete(self):
        """Les 4 brouillons du lot 9 étaient invisibles dans l'ancien compteur."""
        counts = ValidationQueue().counts()
        self.assertIn("draft", counts)
        self.assertIn("obsolete", counts)
        self.assertEqual(counts["total"], sum(
            v for k, v in counts.items() if k not in ("total", "ouverts")))
        self.assertEqual(counts["ouverts"],
                         counts.get("pending", 0) + counts.get("approved", 0)
                         + counts.get("draft", 0))

    def test_le_dashboard_affiche_les_lignes_de_categories(self):
        html = (ROOT / "prospecto" / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn("funnel", html)
        self.assertIn("METRICS.portefeuille", html)
        self.assertIn("METRICS.exploration", html)


# ---------------------------------------------------------------------------
# 9. Intégrité des données livrées pour le lot 9
# ---------------------------------------------------------------------------
class Lot9IntegrityTests(unittest.TestCase):
    def test_quatre_fiches_avec_coordonnees_sourcees(self):
        recs = lot9()
        self.assertEqual(len(recs), 4)
        for r in recs:
            self.assertTrue(r["contact_email"], r["company"])
            self.assertTrue(r["phone"], r["company"])
            self.assertTrue(r["website"].startswith("https://"), r["company"])
            self.assertTrue(r["notes"], r["company"])
            self.assertEqual(Prospect.from_dict(r).validate(), [], r["company"])

    def test_chaque_preuve_porte_source_fiabilite_et_date(self):
        for r in lot9():
            for e in r["evidences"]:
                self.assertIn(e["source_type"], SOURCE_TYPES)
                self.assertIn(e["reliability"], RELIABILITY_LEVELS)
                self.assertEqual(e["verified_at"], "2026-11-06")
                self.assertTrue(e["source_url"].startswith("https://"))
                self.assertTrue(e["quote"].strip())
                self.assertIsInstance(e["observed"], bool)

    def test_les_faits_observes_sont_distingues_des_hypotheses(self):
        for r in lot9():
            inferred = [e for e in r["evidences"] if not e["observed"]]
            for e in inferred:
                self.assertIn("Hypothèse", e["detail"], r["company"])

    def test_aucune_adresse_n_est_deduite_d_un_nom_de_domaine(self):
        """Chaque adresse doit être justifiée par une page dans les notes."""
        for r in lot9():
            self.assertIn(r["contact_email"], r["notes"], r["company"])

    def test_quatre_brouillons_et_aucun_envoi(self):
        camp = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
        self.assertFalse(camp["enabled"])
        self.assertFalse(camp["send_allowed"])
        self.assertEqual(camp["sent_manually_count"], 0)
        self.assertEqual(camp["gmail_label"], "Prospection/" + LOT)
        self.assertEqual(len(camp["drafts"]), 4)
        for d in camp["drafts"]:
            self.assertEqual(d["status"], "draft")
            self.assertTrue(d["gmail_draft_id"])
            self.assertTrue(d["gmail_message_id"])
            self.assertEqual(d["violations"], [])

    def test_les_messages_livres_passent_les_controles_v4(self):
        """On contrôle le corps RÉELLEMENT livré, pas une recomposition approximate.

        Les amorces dépendent de la composition du lot (LotRotation) : sans elle,
        une variante plus longue peut dépasser le plafond alors que le message
        stocké est conforme. On vérifie donc les deux : le texte livré, et sa
        reproductibilité dans les conditions de production.
        """
        from prospecto.models import GeneratedEmail
        from prospecto.personalization import LotRotation

        raw = {r["company"]: r for r in lot9()}
        msgs = json.loads(MESSAGES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(msgs), 4)
        rotation = LotRotation(list(raw))
        for m in msgs:
            p = Prospect.from_dict(raw[m["company"]])
            delivered = GeneratedEmail(
                to=m["to"], subject=m["subject"], body=m["body"],
                company=m["company"], need=p.primary_need or "automatisation",
                variant=m["variant"], message_version=m["message_version"])
            self.assertEqual(check_email_v4(delivered, p), [], m["company"])
            rebuilt = compose_email(p, variant=m["variant"], rotation=rotation)
            self.assertEqual(rebuilt.body.strip(), m["body"].strip(), m["company"])
            self.assertIn("ne pas me relancer", m["body"])
            self.assertIn("Martin BOURASSEAU", m["body"])
            self.assertIn("https://prospecto.website", m["body"])

    def test_les_quatre_variantes_sont_differentes(self):
        msgs = json.loads(MESSAGES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len({m["variant"] for m in msgs}), 4)

    def test_aucune_reference_forcee_hors_sujet(self):
        """Aucune des quatre fiches ne relève de la création/refonte de site vitrine."""
        msgs = json.loads(MESSAGES_PATH.read_text(encoding="utf-8"))
        for m in msgs:
            self.assertFalse(m["reference_id"], m["company"])

    def test_anti_doublon_sur_tout_le_crm(self):
        crm = json.loads((ROOT / "data" / "crm" / "prospects.json").read_text(encoding="utf-8"))
        records = crm.get("prospects", crm if isinstance(crm, list) else [])
        domains = [r.get("domain", "").lower() for r in records if r.get("domain")]
        self.assertEqual(len(domains), len(set(domains)))
        emails = [r.get("email", "").lower() for r in records if r.get("email")]
        self.assertEqual(len(emails), len(set(emails)))
        lot9_domains = {r["domain"] for r in lot9()}
        others = {r.get("domain", "").lower() for r in records if r.get("lot") != LOT}
        self.assertEqual(lot9_domains & others, set())

    def test_le_journal_d_exploration_couvre_plus_que_les_fiches(self):
        stats = ExplorationLedger().stats()
        self.assertGreaterEqual(stats["examined"], 50)
        self.assertEqual(stats["by_decision"]["retenue"], 4)
        self.assertGreaterEqual(len(stats["departments"]), 20)
        self.assertGreaterEqual(len(stats["by_source_type"]), 3)

    def test_les_fiches_ecartees_ne_sont_pas_devenues_des_fiches(self):
        led = ExplorationLedger()
        rejected = {e["domain"] for e in led.entries
                    if e["decision"] != "retenue" and e.get("domain")}
        self.assertTrue(rejected)
        self.assertEqual(rejected & {r["domain"] for r in lot9()}, set())

    def test_les_tests_ne_polluent_pas_le_journal_de_reconciliation(self):
        """Fuite réelle : 189 entrées de fixture sur 193 dans le vrai journal.

        reconcile_sent() écrivait TOUOURS son historique dans le fichier de
        production, même quand l'appelant passait un CRM, une file et un journal
        en mémoire. Chaque exécution de la suite ajoutait des faux rapprochements.
        """
        import tempfile
        from prospecto.reconcile import reconcile_sent, RECONCILE_PATH

        class _CRM:
            def __init__(self): self.records = []
            def save(self): pass

        class _Queue:
            def __init__(self): self.items = []
            def save(self): pass

        before = RECONCILE_PATH.read_bytes() if RECONCILE_PATH.exists() else b""
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "reconciliations.json"
            reconcile_sent([{"to": "fixture@exemple.fr", "subject": "Test"}],
                           _CRM(), _Queue(), None, history_path=hist)
            self.assertTrue(hist.exists())
            self.assertIn("fixture@exemple.fr", hist.read_text(encoding="utf-8"))
        after = RECONCILE_PATH.read_bytes() if RECONCILE_PATH.exists() else b""
        self.assertEqual(before, after, "le journal de production a été modifié par un test")

    def test_le_journal_reel_ne_contient_plus_de_fixtures(self):
        path = ROOT / "data" / "history" / "reconciliations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(data, ensure_ascii=False)
        for marker in ("deja@exemple.fr", "Déjà Contacté", "personne@autre.fr"):
            self.assertNotIn(marker, blob)
        self.assertEqual(data["count"], len(data["reconciliations"]))
        # La quarantaine conserve tout : rien n'a été détruit.
        q = json.loads((ROOT / "data" / "history" /
                        "reconciliations-pollution-tests-2026-11-06.json").read_text(encoding="utf-8"))
        self.assertGreater(q["count"], 0)
        self.assertEqual(q["count"], len(q["entries"]))

    def test_historique_des_scores_preserve(self):
        for name in ("scores-v6-vers-v7.json", "scores-v7-vers-v71.json"):
            path = ROOT / "data" / "history" / name
            self.assertTrue(path.exists(), name)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data.get("changes") is not None, name)


if __name__ == "__main__":
    unittest.main()
