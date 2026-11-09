"""Lot 13 — pilote de détection de besoins réels.

Ces tests vérifient des INVARIANTS, jamais des compteurs cumulatifs propres à
ce lot. Aucun test ne dit « le CRM contient 121 fiches » : un tel test casserait
au lot suivant et n'exprimerait aucune règle. On teste des propriétés : une
hypothèse n'est pas importable, un signal expiré est rejeté même explicite, les
trois axes restent indépendants, une fiche n'est créée que sur coordonnées
publiées, etc.
"""
from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Les scripts de chaque lot nomment leurs modules `journal` et `fiches`. Un simple
# sys.path.insert renverrait ceux du Lot 12, deja charges par test_lot12 : les
# tests passeraient sur les mauvaises donnees. On charge donc ceux du Lot 13 sous
# des noms uniques, sans polluer sys.modules pour les autres tests.
import importlib.util  # noqa: E402


def _load(alias: str, filename: str):
    path = ROOT / "scripts/lot13" / filename
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


_classification = _load("lot13_classification", "classification.py")
CATEGORY_A = _classification.CATEGORY_A
CATEGORY_B = _classification.CATEGORY_B
CATEGORY_C = _classification.CATEGORY_C
CATEGORY_D = _classification.CATEGORY_D
DISQUALIFIERS = _classification.DISQUALIFIERS
LABELS = _classification.LABELS
Signal = _classification.Signal
classify = _classification.classify
importable = _classification.importable

# `journal.py` fait `from classification import ...` : on expose le module du
# Lot 13 sous ce nom le temps du chargement, puis on retire l'entree.
sys.modules["classification"] = _classification
journal = _load("lot13_journal", "journal.py")
fiches_mod = _load("lot13_fiches", "fiches.py")
sys.modules.pop("classification", None)
FICHES, TODAY, build = fiches_mod.FICHES, fiches_mod.TODAY, fiches_mod.build
from prospecto.counter_signals import PENALTY_CAP, collect  # noqa: E402
from prospecto.models import Evidence  # noqa: E402
from prospecto.priority import ENGINE_VERSION  # noqa: E402
from prospecto.scoring import AXES, KIND_BASE_IA  # noqa: E402


class TestClassification(unittest.TestCase):
    """La catégorie répond à la nature de la preuve, pas à l'envie de contacter."""

    def test_besoin_explicite_lu_et_pertinent_donne_A(self):
        cat, _ = classify(Signal("X", expressed=True, identity_established=True,
                                 page_read=True))
        self.assertEqual(cat, CATEGORY_A)

    def test_processus_observe_sans_demande_donne_B(self):
        cat, _ = classify(Signal("X", identity_established=True, page_read=True,
                                 observed=True))
        self.assertEqual(cat, CATEGORY_B)

    def test_identite_masquee_ne_donne_jamais_A(self):
        """Le cas des projets Codeur : besoin réel, client derrière un abonnement."""
        cat, _ = classify(Signal("X", expressed=True, page_read=True,
                                 identity_established=False))
        self.assertEqual(cat, CATEGORY_C)

    def test_rattachement_non_etabli_reste_une_hypothese(self):
        """Le cas Adastra : activité concordante mais contact cité absent."""
        cat, raisons = classify(Signal("X", expressed=True, page_read=True,
                                       identity_established=True,
                                       attachment_established=False))
        self.assertEqual(cat, CATEGORY_C)
        self.assertTrue(any("rattachement" in r for r in raisons))

    def test_page_non_lue_reste_une_hypothese(self):
        cat, _ = classify(Signal("X", identity_established=True, page_read=False))
        self.assertEqual(cat, CATEGORY_C)

    def test_signal_expire_est_rejete_meme_explicite(self):
        """Un AO expiré ne se rattrape pas par la force de sa preuve."""
        cat, _ = classify(Signal("X", expressed=True, identity_established=True,
                                 page_read=True, still_relevant=False))
        self.assertEqual(cat, CATEGORY_D)

    def test_contre_signal_disqualifiant_primaute_sur_le_besoin(self):
        for motif in DISQUALIFIERS:
            with self.subTest(motif=motif):
                cat, _ = classify(Signal("X", expressed=True, observed=True,
                                         identity_established=True, page_read=True,
                                         disqualifiers=[motif]))
                self.assertEqual(cat, CATEGORY_D)

    def test_vendeur_de_solution_est_rejete(self):
        cat, _ = classify(Signal("Agence", identity_established=True, page_read=True,
                                 observed=True, disqualifiers=["vendeur_de_solution"]))
        self.assertEqual(cat, CATEGORY_D)

    def test_seules_A_et_B_sont_importables(self):
        self.assertTrue(importable(CATEGORY_A))
        self.assertTrue(importable(CATEGORY_B))
        self.assertFalse(importable(CATEGORY_C))
        self.assertFalse(importable(CATEGORY_D))

    def test_validation_refuse_un_besoin_explicite_non_lu(self):
        errs = Signal("X", expressed=True, identity_established=True).validate()
        self.assertTrue(any("doit être lu" in e for e in errs))

    def test_validation_refuse_un_motif_inconnu(self):
        errs = Signal("X", disqualifiers=["motif_invente"]).validate()
        self.assertTrue(any("inconnu" in e for e in errs))

    def test_chaque_categorie_a_un_libelle(self):
        for cat in (CATEGORY_A, CATEGORY_B, CATEGORY_C, CATEGORY_D):
            self.assertIn(cat, LABELS)
            self.assertTrue(LABELS[cat].strip())

    def test_classify_ne_leve_jamais_sur_signal_valide(self):
        s = Signal("X", identity_established=True, page_read=True)
        self.assertEqual(s.validate(), [])
        cat, raisons = classify(s)
        self.assertIn(cat, LABELS)
        self.assertTrue(raisons)


class TestJournal(unittest.TestCase):
    """Le journal doit refléter la recherche réellement faite, sans quota artificiel."""

    def test_chaque_entite_a_une_categorie_calculee(self):
        for e in journal.E:
            with self.subTest(nom=e["nom"]):
                self.assertIn(e["categorie"], LABELS)
                self.assertTrue(e["raisons_moteur"])

    def test_decision_decoule_de_la_categorie(self):
        for e in journal.E:
            with self.subTest(nom=e["nom"]):
                if importable(e["categorie"]):
                    self.assertEqual(e["decision"], "importee")
                elif e["categorie"] == CATEGORY_C:
                    self.assertEqual(e["decision"], "approfondir")
                else:
                    self.assertEqual(e["decision"], "écartée")

    def test_pererimetre_de_recherche_atteint(self):
        """40 à 60 entreprises demandées. On vérifie un plancher, pas un total figé."""
        self.assertGreaterEqual(len(journal.E), 40)

    def test_aucune_fiche_pour_une_identite_non_etablie(self):
        for e in journal.E:
            if not e["signal"]["identite_etablie"]:
                self.assertNotEqual(e["decision"], "importee", e["nom"])

    def test_aucune_fiche_pour_une_page_non_lue(self):
        for e in journal.E:
            if not e["signal"]["page_lue"]:
                self.assertNotEqual(e["decision"], "importee", e["nom"])

    def test_requetes_orientees_besoin_pas_annuaire(self):
        """La stratégie demandée : événements, offres, AO, processus — pas « métier + ville »."""
        axes = {r[0] for r in journal.REQUETES}
        self.assertIn("marche_public", axes)
        self.assertIn("processus", axes)
        self.assertIn("besoin_exprime", axes)
        for _, libelle, _ in journal.REQUETES:
            self.assertNotIn("métier + ville", libelle)

    def test_pieges_de_recherche_documentes(self):
        """Les requêtes qui ne ramènent que des vendeurs doivent être tracées."""
        rendements = " ".join(r[2].lower() for r in journal.REQUETES)
        self.assertIn("vendeur", rendements)
        self.assertIn("intérim", rendements)

    def test_intermediaires_jamais_importes(self):
        noms = {n for n, _, _ in journal.INTERMEDIAIRES}
        for e in journal.E:
            if e["nom"] in noms:
                self.assertNotEqual(e["decision"], "importee")

    def test_stats_coherentes_avec_les_entites(self):
        st = journal.stats()
        self.assertEqual(sum(st["categories"].values()), len(journal.E))
        self.assertEqual(sum(st["decisions"].values()), len(journal.E))
        self.assertEqual(st["importables"],
                         sum(1 for e in journal.E if importable(e["categorie"])))

    def test_stats_distinguent_appels_et_pages(self):
        st = journal.stats()
        self.assertGreaterEqual(st["appels_lecture"], st["pages_distinctes_lues"])
        self.assertEqual(st["appels_reussis"] + st["appels_echoues"], st["appels_lecture"])

    def test_pas_de_caractere_parasite_dans_le_journal(self):
        blob = json.dumps(journal.E + [list(r) for r in journal.REQUETES], ensure_ascii=False)
        self.assertNotRegex(blob, r"[\u3000-\u9fff\uff00-\uffef]")

    def test_archivage_produit_un_json_lisible(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "j.json"
            journal.archiver(p)
            data = json.loads(p.read_text(encoding="utf-8"))
        self.assertFalse(data["securite"]["envoi_autorise"])
        self.assertTrue(data["securite"]["dry_run"])
        self.assertTrue(data["securite"]["acces_payant_non_contourne"])
        self.assertEqual(len(data["entites"]), len(journal.E))


class TestFiches(unittest.TestCase):
    """Les fiches importées respectent les règles de preuve du dépôt."""

    def test_toute_fiche_importee_est_A_ou_B(self):
        for f in FICHES:
            self.assertTrue(importable(f["qualification_category"]), f["company"])

    def test_toute_preuve_est_valide(self):
        for f in FICHES:
            for raw in build(f)["prospect"].evidences:
                self.assertEqual(raw.validate(), [], f["company"])

    def test_toute_preuve_a_url_citation_et_date(self):
        for f in FICHES:
            for e in build(f)["prospect"].evidences:
                self.assertTrue(e.source_url.startswith("http"), e.kind)
                self.assertTrue(e.quote.strip(), e.kind)
                self.assertTrue(e.observed_at, e.kind)

    def test_les_trois_axes_restant_independants(self):
        for f in FICHES:
            s = build(f)["scores"]
            for axe in AXES:
                self.assertIn(axe, s)
            self.assertEqual(s["engine_version"], "v8")

    def test_un_site_en_ligne_ne_cree_pas_un_besoin_de_creation(self):
        """Styl'Home a un site moderne : la création ne doit pas être le meilleur axe."""
        for f in FICHES:
            r = build(f)
            if not f["website"]:
                continue
            s = r["scores"]
            self.assertLess(s["site_web"]["score"], s["refonte"]["score"], f["company"])
            self.assertNotEqual(r["assessment"].best_axis, "site_web")

    def test_axe_IA_plafonne_sans_processus_publie(self):
        """Aucun processus interne n'a été lu : l'axe IA reste au plafond du type."""
        for f in FICHES:
            if f["process_hint"]:
                continue
            s = build(f)["scores"]
            self.assertLessEqual(s["ia_automatisation"]["score"], KIND_BASE_IA, f["company"])

    def test_contre_signaux_reellement_lus_par_le_moteur(self):
        for f in FICHES:
            if not f.get("contre_signaux"):
                continue
            p = build(f)["prospect"]
            signals = collect(p.evidences, today=TODAY)
            self.assertTrue(signals, f["company"])

    def test_penalite_de_contre_signaux_bornee(self):
        for f in FICHES:
            a = build(f)["assessment"]
            self.assertLessEqual(a.counter_signal_penalty, PENALTY_CAP)
            self.assertGreaterEqual(a.counter_signal_penalty, 0)

    def test_email_publie_et_mx_verifie(self):
        for f in FICHES:
            if not f["email"]:
                continue
            p = build(f)["prospect"]
            self.assertEqual(p.email_verification, "verified")
            self.assertEqual(p.email_dns_status, "mx_ok")

    def test_aucune_coordinee_inventee(self):
        """Un champ vide reste vide : ni téléphone deviné, ni titulaire supposé."""
        for f in FICHES:
            if not f["phone"]:
                self.assertEqual(build(f)["prospect"].phone, "")
            if not f["contact_name"]:
                self.assertEqual(build(f)["prospect"].contact_name, "")

    def test_moteur_de_priorite_du_depot(self):
        for f in FICHES:
            self.assertEqual(build(f)["assessment"].engine_version, ENGINE_VERSION)

    def test_categorie_qualitative_distincte_du_palier(self):
        """Une fiche A peut être haute priorité : les deux ne sont pas le même champ."""
        for f in FICHES:
            r = build(f)
            self.assertIn(f["qualification_category"], LABELS)
            self.assertIn(r["assessment"].tier,
                          ("haute", "moyenne", "basse", "a_approfondir"))


class TestArchives(unittest.TestCase):
    """Les archives du lot doivent être cohérentes et sans engagement d'envoi."""

    def setUp(self):
        self.hist = ROOT / "data/history"

    def test_archive_recherche_presente_et_coherente(self):
        p = self.hist / "lot13-recherches-2026-11-03.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(len(data["entites"]), len(journal.E))
        self.assertFalse(data["securite"]["envoi_autorise"])

    def test_archive_import_sans_brouillon(self):
        p = self.hist / "lot13-import-2026-11-03.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data["brouillons_autorises"], [])
        self.assertFalse(data["envoi_autorise"])
        for f in data["fiches"]:
            self.assertFalse(f["brouillon"])
            self.assertTrue(importable(f["categorie"]))

    def test_archive_import_crm_croit_du_nombre_cree(self):
        data = json.loads((self.hist / "lot13-import-2026-11-03.json").read_text(encoding="utf-8"))
        self.assertEqual(data["crm_apres"] - data["crm_avant"], data["fiches_creees"])
        self.assertEqual(data["registre_apres"] - data["registre_avant"], data["registre_ajouts"])

    def test_pref_vol_reste_bloque_et_documente(self):
        data = json.loads((self.hist / "lot13-preflight-2026-11-03.json").read_text(encoding="utf-8"))
        self.assertFalse(data["resultat"])
        self.assertEqual(len(data["motifs"]), 3)
        self.assertTrue(data["config_reelle_inchangee"])
        self.assertTrue(data["dns_non_modifie"])
        self.assertTrue(data["aucun_achat"])
        self.assertTrue(data["actions_requises"])

    def test_note_de_dates_documente_sans_corriger(self):
        data = json.loads((self.hist / "suivi-dates-lots-1-a-11-2026-11-03.json").read_text(encoding="utf-8"))
        self.assertIn("aucune correction", data["statut"].lower())
        self.assertTrue(data["champs_porteurs_de_dates"])
        self.assertTrue(data["methode_de_correction_proposee_NON_APPLIQUEE"])
        self.assertTrue(data["sources_de_dates_reelles"])
        self.assertTrue(data["actions_requises_de_l_utilisateur"])

    def test_note_de_dates_s_appuie_sur_une_source_independante(self):
        data = json.loads((self.hist / "suivi-dates-lots-1-a-11-2026-11-03.json").read_text(encoding="utf-8"))
        indep = [s for s in data["sources_de_dates_reelles"] if s["independante"]]
        self.assertTrue(indep)
        self.assertTrue(any("Gmail" in s["source"] for s in indep))


class TestProtections(unittest.TestCase):
    """Le pilote ne doit avoir produit aucun engagement d'envoi."""

    def test_campagne_reste_desactivee_et_en_dry_run(self):
        cfg = json.loads((ROOT / "data/campaigns/v4-settings.json").read_text(encoding="utf-8"))
        self.assertFalse(cfg["enabled"])
        self.assertTrue(cfg["dry_run"])

    def test_fiches_du_lot_sans_brouillon_autorise(self):
        crm = json.loads((ROOT / "data/crm/prospects.json").read_text(encoding="utf-8"))
        lot = [r for r in crm["prospects"] if r.get("lot") == "2026-11-03-lot13"]
        self.assertTrue(lot, "aucune fiche du lot : importer d'abord")
        for r in lot:
            self.assertFalse(r.get("brouillon_autorise_lot13"))
            self.assertFalse(r.get("gmail_draft_id"))
            self.assertEqual(r.get("email_status"), "non_contacté")

    def test_fiches_du_lot_portent_la_categorie(self):
        crm = json.loads((ROOT / "data/crm/prospects.json").read_text(encoding="utf-8"))
        for r in crm["prospects"]:
            if r.get("lot") != "2026-11-03-lot13":
                continue
            self.assertTrue(importable(r["qualification_category"]))
            self.assertEqual(r["qualification_label"], LABELS[r["qualification_category"]])
            self.assertTrue(r["qualification_basis"])

    def test_preuves_serialisees_completes(self):
        """CRM.import_prospect ne garde que 5 clés : upsert doit tout conserver."""
        crm = json.loads((ROOT / "data/crm/prospects.json").read_text(encoding="utf-8"))
        for r in crm["prospects"]:
            if r.get("lot") != "2026-11-03-lot13":
                continue
            for e in r["evidence"]:
                self.assertIn("source_type", e)
                self.assertIn("signal_level", e)
                self.assertIn("detail", e)

    def test_quatre_brouillons_lot11_toujours_en_place(self):
        """La revue est en lecture seule : les identifiants doivent subsister."""
        p = ROOT / "data/history/lot11-brouillons-2026-11-09.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        blob = json.dumps(data, ensure_ascii=False)
        for ident in ("r4042321371979229617", "r2207186572977723131",
                      "r8619847980088428557", "r-2619464416091008266"):
            self.assertIn(ident, blob)




class TestCoherenceTableauDeBord(unittest.TestCase):
    """Invariants de comptage : les compteurs ne doivent jamais se contredire.

    Aucune valeur absolue n'est assertée : ces règles doivent rester vraies au
    lot suivant, quel que soit le nombre de fiches ou de messages.
    """

    @classmethod
    def setUpClass(cls):
        from prospecto.metrics import compute_metrics
        cls.m = compute_metrics()

    def test_partition_du_portefeuille_exclusive(self):
        f = self.m["portefeuille"]
        self.assertTrue(f["controle_exclusif"])
        etapes = ("oppositions", "suspendus", "rebonds", "contactes",
                  "brouillons_en_attente", "a_investiguer", "decouverts")
        total = sum(f[k] for k in etapes) + sum(f.get("autres_details", {}).values())
        self.assertEqual(total, f["total"])

    def test_pipeline_exclusif(self):
        self.assertTrue(self.m["pipeline"]["controle_exclusif"])

    def test_envoyes_egale_production_plus_rapprochements(self):
        """Envois de l'agent et envois manuels restent distingués puis sommés."""
        p, ob = self.m["pipeline"], self.m["outbound"]
        self.assertEqual(p["envoyes"], ob["journal_production"] + ob["rapproches"])

    def test_delivrance_partition_sans_double_compte(self):
        p = self.m["pipeline"]
        self.assertEqual(
            p["delivres_confirmes"] + p["delivrance_non_confirmee"]
            + p["rebonds"] + p["challenges_delivrance"], p["envoyes"])

    def test_delivres_jamais_superieur_aux_envoyes(self):
        p = self.m["pipeline"]
        self.assertLessEqual(p["delivres_confirmes"], p["envoyes"])

    def test_acceptation_fournisseur_distincte_de_la_remise(self):
        """Accepté par le fournisseur ne veut pas dire délivré."""
        p = self.m["pipeline"]
        self.assertLessEqual(p["delivres_confirmes"], p["acceptes_par_fournisseur"])
        self.assertIn("acceptes_par_fournisseur", p["definitions"])
        self.assertIn("delivres_confirmes", p["definitions"])

    def test_crm_et_portefeuille_memes_totaux(self):
        self.assertEqual(self.m["crm"]["total"], self.m["portefeuille"]["total"])

    def test_brouillons_gmail_inferieur_aux_fiches_au_statut_brouillon(self):
        """Une fiche peut porter un statut brouillon sans brouillon Gmail existant."""
        self.assertLessEqual(self.m["pipeline"]["brouillons"],
                             self.m["portefeuille"]["brouillons_en_attente"])

    def test_registre_au_moins_aussi_grand_que_le_crm(self):
        self.assertGreaterEqual(self.m["exploration"]["examined"], self.m["crm"]["total"])

    def test_delivrabilite_ne_presume_pas_la_remise(self):
        d = self.m["deliverability"]
        self.assertIn("ne prouve pas la remise", d["note"])
        self.assertEqual(d["sent"], d["delivery_confirmed"] + d["delivery_unconfirmed"]
                         + d["hard_bounces"] + d["delivery_challenges"])


if __name__ == "__main__":
    unittest.main()
