"""Phase 10 — hiérarchie des signaux, non-double-paiement, contactabilité.

Chaque test verrouille un défaut établi par l'audit du portefeuille
(docs/audit-phase10-portefeuille.md) ou mesuré pendant le développement de v8.
Les tests de régression sur Cordes et Âme, Caléo, Canfora et Froger portent sur
les données RÉELLES du CRM.
"""
from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from prospecto.models import (
    Evidence, Prospect, EVIDENCE_PUBLIC_NEED, EVIDENCE_PROCESS_MANUAL,
    EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY, EVIDENCE_MATURITY,
    SIGNAL_EXPRESSED, SIGNAL_OBSERVED, SIGNAL_INDIRECT, SIGNAL_HYPOTHETICAL,
    SIGNAL_LEVELS, KIND_DEFAULT_LEVEL,
)
from prospecto.opportunity import (
    AUTOMATION_SIGNALS, detect_signals, detect_maturity, match_form,
)
from prospecto.scoring import (
    score_prospect, scores_from_record, contactability, strongest_per_evidence,
    expressed_axes, LEVEL_FACTOR, AXIS_IA, AXIS_SITE_WEB, AXIS_REFONTE,
)

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 7)


def ev(kind, quote, url="https://exemple.fr/page", **kw):
    base = dict(kind=kind, quote=quote, source_url=url, observed_at="2026-11-07",
                source_type="site_officiel", reliability="haute",
                verified_at="2026-11-07", observed=True)
    base.update(kw)
    return Evidence(**base)


def prospect(evidences, **kw):
    base = dict(company="Exemple", domain="exemple.fr", sector="services",
                contact_email="contact@exemple.fr", website="https://exemple.fr",
                needs=["automatisation"], evidences=evidences)
    base.update(kw)
    return Prospect(**base)


def crm_records():
    return json.loads((ROOT / "data" / "crm" / "prospects.json")
                      .read_text(encoding="utf-8"))["prospects"]


# ---------------------------------------------------------------------------
# 1. Les quatre niveaux de signal
# ---------------------------------------------------------------------------
class SignalLevelTests(unittest.TestCase):
    def test_les_quatre_niveaux_existent_et_sont_ordonnes(self):
        self.assertEqual(len(SIGNAL_LEVELS), 4)
        self.assertGreater(LEVEL_FACTOR[SIGNAL_EXPRESSED], LEVEL_FACTOR[SIGNAL_OBSERVED])
        self.assertGreater(LEVEL_FACTOR[SIGNAL_OBSERVED], LEVEL_FACTOR[SIGNAL_INDIRECT])
        self.assertGreater(LEVEL_FACTOR[SIGNAL_INDIRECT], LEVEL_FACTOR[SIGNAL_HYPOTHETICAL])

    def test_niveau_deduit_du_type_de_preuve(self):
        self.assertEqual(KIND_DEFAULT_LEVEL[EVIDENCE_PUBLIC_NEED], SIGNAL_EXPRESSED)
        self.assertEqual(KIND_DEFAULT_LEVEL[EVIDENCE_PROCESS_MANUAL], SIGNAL_OBSERVED)
        self.assertEqual(KIND_DEFAULT_LEVEL[EVIDENCE_SECTOR_OPPORTUNITY], SIGNAL_INDIRECT)

    def test_une_non_observation_ne_peut_rester_un_fait(self):
        e = ev(EVIDENCE_PUBLIC_NEED, "Nous cherchons une solution.", observed=False)
        self.assertEqual(e.signal_level, SIGNAL_HYPOTHETICAL)
        self.assertEqual(e.validate(), [])

    def test_le_niveau_explicite_est_respecte(self):
        e = ev(EVIDENCE_WEBSITE_GAP, "Indice repéré.", signal_level=SIGNAL_INDIRECT)
        self.assertEqual(e.signal_level, SIGNAL_INDIRECT)

    def test_niveau_inconnu_refuse(self):
        e = ev(EVIDENCE_WEBSITE_GAP, "x", signal_level="inventé")
        self.assertTrue(any("niveau de signal" in m for m in e.validate()))

    def test_a_processus_egal_un_signal_exprime_pese_plus(self):
        """Le cœur de la section C : une demande publiée vaut plus qu'un indice."""
        quote = "Nous recevons les demandes de devis par e-mail et y répondons à la main."
        observed = score_prospect(prospect([ev(EVIDENCE_PROCESS_MANUAL, quote)]), today=TODAY)
        indirect = score_prospect(
            prospect([ev(EVIDENCE_PROCESS_MANUAL, quote, signal_level=SIGNAL_INDIRECT)]),
            today=TODAY)
        hypothetical = score_prospect(
            prospect([ev(EVIDENCE_PROCESS_MANUAL, quote, observed=False)]), today=TODAY)
        self.assertGreater(observed[AXIS_IA]["score"], indirect[AXIS_IA]["score"])
        self.assertGreater(indirect[AXIS_IA]["score"], hypothetical[AXIS_IA]["score"])

    def test_fiabilite_et_niveau_sont_independants(self):
        """Une presse fiable peut porter un signal indirect : les deux pèsent."""
        quote = "Venez nous rencontrer en magasin pour établir un devis personnalisé."
        fiable_indirect = score_prospect(prospect([
            ev(EVIDENCE_PROCESS_MANUAL, quote, source_type="presse_locale",
               reliability="haute", signal_level=SIGNAL_INDIRECT)]), today=TODAY)
        officiel_observe = score_prospect(prospect([
            ev(EVIDENCE_PROCESS_MANUAL, quote)]), today=TODAY)
        self.assertGreater(officiel_observe[AXIS_IA]["score"],
                           fiable_indirect[AXIS_IA]["score"])


# ---------------------------------------------------------------------------
# 2. Le besoin exprimé porte sur l'axe qu'il désigne
# ---------------------------------------------------------------------------
class ExpressedNeedTests(unittest.TestCase):
    def test_besoin_exprime_automatisation_porte_sur_l_axe_ia(self):
        e = ev(EVIDENCE_PUBLIC_NEED,
               "Je souhaite automatiser les relances de prospects, sans intervention "
               "manuelle de ma part.")
        s = score_prospect(prospect([e], needs=["automatisation"]), today=TODAY)
        self.assertGreaterEqual(s[AXIS_IA]["score"], 30)
        self.assertTrue(any("besoin exprimé" in r for r in s[AXIS_IA]["reasons"]))

    def test_besoin_exprime_creation_porte_sur_l_axe_creation(self):
        e = ev(EVIDENCE_PUBLIC_NEED,
               "Nous recherchons quelqu'un pour créer un site internet vitrine.")
        s = score_prospect(prospect([e], needs=["site_web"]), today=TODAY)
        self.assertGreaterEqual(s[AXIS_SITE_WEB]["score"], 30)

    def test_un_besoin_peut_designer_deux_axes_independants(self):
        e = ev(EVIDENCE_PUBLIC_NEED,
               "Nous ouvrons un restaurant et avons besoin d'un site internet avec "
               "un module de réservation intégré.")
        axes = expressed_axes([e])
        self.assertIn(e, axes[AXIS_SITE_WEB])
        self.assertIn(e, axes[AXIS_IA])

    def test_repeter_la_meme_demande_n_augmente_pas_le_score(self):
        e = ev(EVIDENCE_PUBLIC_NEED, "Nous cherchons à automatiser nos devis.")
        one = score_prospect(prospect([e]), today=TODAY)[AXIS_IA]["score"]
        twice = score_prospect(prospect([e, e]), today=TODAY)[AXIS_IA]["score"]
        self.assertEqual(one, twice)

    def test_une_deduction_sectorielle_ne_devient_pas_un_besoin_exprime(self):
        e = ev(EVIDENCE_SECTOR_OPPORTUNITY, "Ont créé la société, spécialisée en décoration.")
        self.assertEqual(expressed_axes([e])[AXIS_IA], [])
        s = score_prospect(prospect([e]), today=TODAY)
        self.assertLessEqual(s[AXIS_IA]["score"], 15)


# ---------------------------------------------------------------------------
# 3. Une preuve ne paie qu'une fois
# ---------------------------------------------------------------------------
class NoDoubleRewardTests(unittest.TestCase):
    def test_deux_signaux_sur_une_preuve_ne_comptent_qu_une_fois(self):
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "Venez nous rencontrer en magasin pour établir un devis personnalisé !")
        dets = detect_signals([e], "ia_automatisation")
        self.assertEqual(len(dets), 1)
        self.assertEqual(len(strongest_per_evidence(dets)), 1)

    def test_deux_preuves_distinctes_comptent_deux_fois(self):
        a = ev(EVIDENCE_PROCESS_MANUAL,
               "Venez nous rencontrer en magasin pour établir un devis personnalisé !",
               "https://exemple.fr/a")
        b = ev(EVIDENCE_PROCESS_MANUAL,
               "N'hésitez pas à venir nous présenter votre demande en magasin.",
               "https://exemple.fr/b")
        dets = detect_signals([a, b], "ia_automatisation")
        self.assertEqual(len({d.evidence_index for d in dets}), 2)

    def test_le_signal_le_plus_fort_est_garde(self):
        e = ev(EVIDENCE_PROCESS_MANUAL,
               "Commande uniquement par téléphone, devis personnalisé sur place.")
        dets = detect_signals([e], "ia_automatisation")
        self.assertEqual(len(dets), 1)
        self.assertEqual(dets[0].signal.id, "commande_telephone_seulement")


# ---------------------------------------------------------------------------
# 4. Deux bugs de fond corrigés pendant la phase
# ---------------------------------------------------------------------------
class DetectionBugsTests(unittest.TestCase):
    def test_une_recommandation_n_est_pas_un_equipement_existant(self):
        """Dance Center : le détail conseillait un paiement en ligne.

        Le moteur en concluait que le paiement en ligne existait et retirait
        des points. Seul l'extrait verbatim fait preuve.
        """
        e = ev(EVIDENCE_WEBSITE_GAP,
               "Les 3 chèques correspondant aux 3 trimestres sont à remettre.",
               detail="Un parcours d'inscription et de paiement en ligne "
                      "simplifierait la rentrée.")
        self.assertEqual(detect_maturity([e]), [],
                         "une suggestion ne doit pas devenir un contre-signal")
        self.assertTrue(detect_signals([e], "ia_automatisation"))

    def test_le_detail_ne_cree_pas_un_fait_absent_de_la_citation(self):
        """Charme de l'Hêtre : « aucun site trouvé » n'était que dans le détail."""
        e = ev(EVIDENCE_SECTOR_OPPORTUNITY,
               "Depuis le 1er juillet, Chloé Poupinet a créé sa société.",
               detail="Aucun site web trouvé dans les recherches.")
        self.assertEqual(detect_signals([e], "site_web"), [])

    def test_adverbe_insere_ne_fait_plus_perdre_le_signal(self):
        e = ev(EVIDENCE_WEBSITE_GAP, "Commande uniquement par téléphone !")
        self.assertEqual({d.signal.id for d in detect_signals([e], "ia_automatisation")},
                         {"commande_telephone_seulement"})

    def test_motif_generique_ne_declenche_pas_de_faux_positif(self):
        """« par téléphone » seul ne signifie pas « commande exclusive »."""
        e = ev(EVIDENCE_WEBSITE_GAP, "Vous pouvez aussi nous joindre par téléphone.")
        self.assertNotIn("commande_telephone_seulement",
                         {d.signal.id for d in detect_signals([e], "ia_automatisation")})

    def test_forme_souple_retire_les_adverbes_restrictifs(self):
        self.assertEqual(match_form("Commande uniquement par téléphone"),
                         match_form("Commande par téléphone"))


# ---------------------------------------------------------------------------
# 5. Les signaux faibles demandés en section C
# ---------------------------------------------------------------------------
class WeakSignalTests(unittest.TestCase):
    IDS = {s.id for s in AUTOMATION_SIGNALS}

    def test_inscriptions_manuelles(self):
        self.assertIn("inscription_manuelle", self.IDS)
        e = ev(EVIDENCE_WEBSITE_GAP, "Les inscriptions ont lieu au secrétariat de l'école.")
        self.assertIn("inscription_manuelle",
                      {d.signal.id for d in detect_signals([e], "ia_automatisation")})

    def test_encaissement_sans_parcours_en_ligne(self):
        self.assertIn("paiement_manuel", self.IDS)
        e = ev(EVIDENCE_WEBSITE_GAP, "Règlement par chèque à l'ordre de l'association.")
        self.assertIn("paiement_manuel",
                      {d.signal.id for d in detect_signals([e], "ia_automatisation")})

    def test_demande_a_adresser_directement(self):
        self.assertIn("contact_direct_manuel", self.IDS)
        e = ev(EVIDENCE_WEBSITE_GAP,
               "Veuillez nous contacter directement par email pour les groupes.")
        self.assertIn("contact_direct_manuel",
                      {d.signal.id for d in detect_signals([e], "ia_automatisation")})


# ---------------------------------------------------------------------------
# 6. Contactabilité : distincte de la force du signal
# ---------------------------------------------------------------------------
class ContactabilityTests(unittest.TestCase):
    def test_signal_fort_sans_adresse_garde_son_score(self):
        e = ev(EVIDENCE_PUBLIC_NEED, "Nous cherchons à automatiser nos relances.")
        with_addr = score_prospect(prospect([e]), today=TODAY)
        without = score_prospect(prospect([e], contact_email="",
                                          email_verification="none"), today=TODAY)
        self.assertEqual(with_addr[AXIS_IA]["score"], without[AXIS_IA]["score"])
        self.assertTrue(without["contactability"]["blockers"])
        self.assertFalse(without["contactability"]["contactable"])
        self.assertTrue(with_addr["contactability"]["contactable"])

    def test_adresse_decodee_reste_non_confirmee(self):
        p = prospect([], notes="Adresse décodée d'un lien mailto mal formé.")
        c = contactability(p)
        self.assertTrue(c["decoded_address_unconfirmed"])
        self.assertFalse(c["contactable"])
        self.assertTrue(any("décodée" in b for b in c["blockers"]))

    def test_domaine_non_routable_est_un_blocage(self):
        p = prospect([], email_dns_status="nxdomain")
        self.assertFalse(contactability(p)["contactable"])

    def test_chaque_score_porte_sa_date_d_evaluation(self):
        s = score_prospect(prospect([]), today=TODAY)
        self.assertEqual(s["evaluated_at"], "2026-11-07")
        for axis in (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA):
            self.assertEqual(s[axis]["evaluated_at"], "2026-11-07")


# ---------------------------------------------------------------------------
# 7. Régressions demandées sur les quatre fiches du lot 9 (données réelles)
# ---------------------------------------------------------------------------
class Lot9RegressionTests(unittest.TestCase):
    """Ces quatre entreprises ne doivent plus jamais perdre leur besoin."""

    def _record(self, name):
        return next(r for r in crm_records() if r["company"] == name)

    def _signals(self, name):
        s = scores_from_record(self._record(name))
        return s, {x for x in s[AXIS_IA]["observed_signals"]}

    def test_cordes_et_ame_garde_la_difficulte_enoncee(self):
        s, obs = self._signals("Cordes et Âme")
        self.assertGreaterEqual(s[AXIS_IA]["score"], 30)
        self.assertIn("Difficulté à répondre énoncée par l'entreprise", obs)
        # La boutique en ligne reste un contre-signal : elle est citée.
        self.assertTrue(s[AXIS_IA]["counter_signals"])

    def test_caleo_garde_le_depot_via_messagerie(self):
        s, obs = self._signals("Caléo Tests & Services")
        self.assertGreaterEqual(s[AXIS_IA]["score"], 50)
        self.assertIn("Le formulaire se termine dans la messagerie du client", obs)

    def test_canfora_garde_le_deplacement_obligatoire(self):
        s, obs = self._signals("Cordonnerie Canfora David")
        self.assertGreaterEqual(s[AXIS_IA]["score"], 40)
        self.assertIn("Un déplacement est nécessaire pour être chiffré", obs)
        self.assertEqual(s[AXIS_IA]["confidence"], "haute")

    def test_froger_garde_les_echeances_recurrentes(self):
        s, obs = self._signals("Froger Étanchéité")
        self.assertGreaterEqual(s[AXIS_IA]["score"], 40)
        self.assertTrue(obs)
        self.assertGreaterEqual(s[AXIS_REFONTE]["score"], 35)

    def test_les_quatre_ont_des_preuves_et_une_confiance(self):
        for name in ("Cordes et Âme", "Caléo Tests & Services",
                     "Cordonnerie Canfora David", "Froger Étanchéité"):
            s = scores_from_record(self._record(name))
            for axis in (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA):
                self.assertTrue(0 <= s[axis]["score"] <= 100, name)
                self.assertIn(s[axis]["confidence"], ("haute", "moyenne", "faible"))
                self.assertTrue(s[axis]["reasons"], name)
            self.assertTrue(s[AXIS_IA]["evidence"], name)


# ---------------------------------------------------------------------------
# 8. Régressions sur les faux négatifs et sur-évaluations de l'audit
# ---------------------------------------------------------------------------
class PortfolioRegressionTests(unittest.TestCase):
    def _score(self, name):
        r = next(x for x in crm_records() if x["company"] == name)
        return scores_from_record(r)

    def test_brasserie_vdl_commande_telephone_n_est_plus_un_zero(self):
        self.assertGreaterEqual(self._score("Brasserie VDL")[AXIS_IA]["score"], 35)

    def test_dance_center_inscriptions_et_cheques_comptent(self):
        s = self._score("Dance Center")
        self.assertGreaterEqual(s[AXIS_IA]["score"], 30)
        self.assertNotIn("Paiement en ligne en place", s[AXIS_IA]["counter_signals"])

    def test_charme_de_l_hetre_n_est_plus_sur_evalue(self):
        """40/100 en création sur un simple article de presse, c'était trop."""
        self.assertLessEqual(self._score("Charme de l'Hêtre")[AXIS_SITE_WEB]["score"], 20)

    def test_une_entreprise_deja_equipee_reste_basse(self):
        """Un équipement cité noir sur blanc reste un contre-signal.

        Uzès Location n'est PAS déjà équipée (formulaire à champ libre, aucune
        réservation en ligne) : son score d'IA est légitime. Le principe se
        vérifie sur une entreprise qui publie réellement son équipement.
        """
        equipped = ev(EVIDENCE_MATURITY,
                      "Réservez et payez en ligne : réservation en ligne, paiement "
                      "en ligne sécurisé, confirmation immédiate.")
        s = score_prospect(prospect([equipped]), today=TODAY)
        self.assertLessEqual(s[AXIS_IA]["score"], 15)
        self.assertTrue(s[AXIS_IA]["counter_signals"])

    def test_une_negation_ne_devient_jamais_un_equipement(self):
        """« Il n'y a pas de paiement en ligne » affirmait l'inverse."""
        e = ev(EVIDENCE_WEBSITE_GAP,
               "Il n'y a pas de paiement en ligne, le règlement se fait par chèque.")
        self.assertEqual(detect_maturity([e]), [])
        self.assertGreater(
            score_prospect(prospect([e]), today=TODAY)[AXIS_IA]["score"], 0)

    def test_le_constat_du_chercheur_est_cite_comme_tel(self):
        """Un signal issu du process_hint ne doit pas citer l'entreprise."""
        e = ev(EVIDENCE_WEBSITE_GAP, "Nom & prénom * / E-mail * / Votre Message *")
        dets = detect_signals([e], "ia_automatisation",
                             "demandes de devis via formulaire à champ libre")
        hint = [d for d in dets if d.evidence_index == -1]
        self.assertTrue(hint)
        self.assertTrue(hint[0].quote.startswith("Constat du chercheur"))
        self.assertEqual(hint[0].source_url, "")


if __name__ == "__main__":
    unittest.main()
