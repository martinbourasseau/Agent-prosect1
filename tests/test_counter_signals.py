"""Section C — contre-signaux explicites : force, portée, bornage, traçabilité."""
from __future__ import annotations

import json
import unittest
from datetime import date

from prospecto import config, counter_signals as cs
from prospecto.crm import CRM
from prospecto.models import Evidence, EVIDENCE_MATURITY, EVIDENCE_TRUST
from prospecto.priority import ENGINE_VERSION, assess
from prospecto.scoring import scores_from_record

TODAY = date(2026, 11, 7)


def ev(detail, quote="", observed="2026-11-07", kind=EVIDENCE_MATURITY,
       source_type="site_officiel", reliability="haute"):
    return Evidence(kind=kind, detail=detail, quote=quote,
                    source_url="https://exemple.fr/page", observed_at=observed,
                    source_type=source_type, reliability=reliability,
                    signal_level="observe")


class ClassificationTests(unittest.TestCase):
    def test_negation_absolue_est_forte(self):
        sig = cs.classify(ev("CONTRE-SIGNAL : aucun besoin identifiable, prestataire en place"), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_STRONG)
        self.assertTrue(sig.negates_need)
        self.assertEqual(sig.penalty, 24)

    def test_negation_partielle_est_seulement_moderee(self):
        """« le besoin n'est pas la création d'un parcours de devis » ne nie pas
        la refonte poursuivie : elle en réduit le périmètre."""
        sig = cs.classify(ev("Le formulaire qualifie déjà le type de projet. "
                             "Le besoin n'est pas la création d'un parcours de devis."), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_MODERATE)
        self.assertFalse(sig.negates_need)

    def test_delimitation_du_besoin_est_faible(self):
        sig = cs.classify(ev("La structure de collecte existe. Le manque est la persistence."), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertEqual(sig.penalty, 0, "délimiter ne doit pas déplacer la priorité")

    def test_contre_signal_visant_un_autre_besoin_est_faible(self):
        sig = cs.classify(ev("Encaissement CB sur place : contre-signal à un besoin "
                             "de paiement en ligne."), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertEqual(sig.penalty, 0)

    def test_equipement_sans_marqueur_explicite_reste_prudent(self):
        sig = cs.classify(ev("L'entreprise possède un site internet."), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertIn("prudence", sig.reason)

    def test_contre_signal_ancien_perd_sa_force(self):
        sig = cs.classify(ev("CONTRE-SIGNAL MAJEUR : aucun besoin", observed="2025-01-01"), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertFalse(sig.fresh)
        self.assertIn("ancien", sig.reason)

    def test_contre_signal_non_date_perd_sa_force(self):
        sig = cs.classify(ev("CONTRE-SIGNAL MAJEUR : aucun besoin", observed=""), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertFalse(sig.fresh)

    def test_source_non_officielle_perd_sa_force(self):
        sig = cs.classify(ev("CONTRE-SIGNAL MAJEUR : aucun besoin",
                             source_type="annuaire_pro"), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_WEAK)
        self.assertFalse(sig.reliable_source)

    def test_entreprise_fermee_est_un_contre_signal_fort(self):
        sig = cs.classify(ev("Entreprise fermée définitivement en 2026."), TODAY)
        self.assertEqual(sig.strength, cs.STRENGTH_STRONG)
        self.assertTrue(sig.negates_need)

    def test_les_signaux_de_confiance_ne_sont_pas_des_contre_signaux(self):
        """`signal_confiance` est une preuve POSITIVE : la compter comme
        contre-signal pénaliserait les fiches les mieux documentées."""
        signals = cs.collect([ev("COFRAC 2-5035, laboratoire depuis 2007",
                                 kind=EVIDENCE_TRUST)], TODAY)
        self.assertEqual(signals, [])


class BornageTests(unittest.TestCase):
    def test_aucun_contre_signal_aucune_penalite(self):
        self.assertEqual(cs.total_penalty([]), 0)

    def test_trois_faibles_ne_valent_pas_un_fort(self):
        weak = [cs.classify(ev("Le manque est la persistence."), TODAY) for _ in range(3)]
        self.assertEqual(cs.total_penalty(weak), 0)

    def test_empilement_est_plafonne(self):
        strong = cs.classify(ev("aucun besoin identifiable"), TODAY)
        moderate = cs.classify(ev("boutique en ligne avec panier"), TODAY)
        # 24 + 3 × 11 × 0,4 = 37,2 : le plafond doit s'appliquer.
        total = cs.total_penalty([strong, moderate, moderate, moderate])
        self.assertEqual(total, cs.PENALTY_CAP)
        self.assertEqual(total, 32)

    def test_empilement_reduit_au_dela_du_plus_fort(self):
        strong = cs.classify(ev("aucun besoin identifiable"), TODAY)
        moderate = cs.classify(ev("boutique en ligne avec panier"), TODAY)
        # 24 + 11 × 0,4 = 28,4 → 28, sous le plafond.
        self.assertEqual(cs.total_penalty([strong, moderate]), 28)

    def test_le_plus_fort_compte_plein_les_autres_a_taux_reduit(self):
        strong = cs.classify(ev("aucun besoin identifiable"), TODAY)
        moderate = cs.classify(ev("boutique en ligne avec panier"), TODAY)
        self.assertEqual(cs.total_penalty([moderate, strong]),
                         cs.total_penalty([strong, moderate]))


class PortefeuilleReelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crm = {r["company"]: r for r in CRM().records}
        cls.sim = json.loads((config.DATA_DIR / "history" /
                              "simulation-priorite-v10-2026-11-07.json").read_text(encoding="utf-8"))
        cls.applied = json.loads((config.DATA_DIR / "history" /
                                  "priorite-commerciale-v9-vers-v10.json").read_text(encoding="utf-8"))

    def test_la_simulation_a_porte_sur_tout_le_portefeuille(self):
        self.assertEqual(self.sim["fiches_analysees"], 92)
        self.assertTrue(self.sim["simulation_acceptee"])
        self.assertEqual(self.sim["axes_v8_modifies"], 0)

    def test_les_seize_fiches_signalees_portent_un_contre_signal(self):
        self.assertEqual(self.sim["fiches_avec_contre_signal"], 16)
        forces = self.sim["contre_signaux_par_force"]
        self.assertEqual(forces, {"faible": 7, "modere": 8, "fort": 2})

    def test_le_champ_counter_signals_n_est_plus_vide(self):
        """C'était le défaut d'origine : les preuves existaient, le champ restait vide."""
        for name in ("ERM 27", "Delahautemaison", "Scierie Labrue", "Caléo Tests & Services"):
            rec = self.crm[name]
            self.assertTrue(rec["commercial"]["counter_signals"], name)
            self.assertTrue(rec["commercial"]["counter_signal_details"], name)

    def test_erm27_n_est_plus_en_priorite_haute(self):
        rec = self.crm["ERM 27"]
        self.assertEqual(rec["commercial_priority"], "moyenne")
        self.assertEqual(rec["commercial_value"], 47)
        self.assertEqual(rec["commercial"]["counter_signal_penalty"], 24)

    def test_delahautemaison_descend_en_basse(self):
        rec = self.crm["Delahautemaison"]
        self.assertEqual(rec["commercial_priority"], "basse")
        self.assertEqual(rec["commercial"]["counter_signal_penalty"], 28)

    def test_le_cas_limite_o_lames_dechues_garde_sa_priorite(self):
        """71 avec un contre-signal hors sujet : aucune pénalité, pas de
        rétrogradation mécanique au franchissement du seuil."""
        rec = self.crm["O Lames Déchues"]
        self.assertEqual(rec["commercial_priority"], "haute")
        self.assertEqual(rec["commercial_value"], 71)
        self.assertEqual(rec["commercial"]["counter_signal_penalty"], 0)

    def test_les_axes_v8_sont_identiques_avant_apres(self):
        for row in self.applied["crm_before"]:
            rec = self.crm[row["company"]]
            for axis, value in row["axes_v8"].items():
                self.assertEqual(rec["scores"][axis]["score"], value,
                                 f"{row['company']} / {axis}")
        self.assertEqual(self.applied["axes_v8_modifies"], 0)

    def test_les_anciennes_valeurs_sont_archivees(self):
        self.assertEqual(len(self.applied["crm_before"]), 92)
        for row in self.applied["crm_before"]:
            self.assertIn("commercial_priority", row)
            self.assertEqual(row["priority_engine_version"], "v9-priority")

    def test_chaque_fiche_modifiee_garde_une_trace(self):
        # Seules les fiches MIGRÉES de v9 vers v10 portent un bloc de calibration.
        # Une fiche créée directement sous v10 n'a jamais eu d'avant/après : lui
        # réclamer ce bloc ferait échouer tout ajout de portefeuille ultérieur.
        for row in self.applied["crm_before"]:
            rec = self.crm[row["company"]]
            block = rec.get("calibration_priorite_commerciale_v10")
            self.assertIsNotNone(block, rec["company"])
            self.assertIn("avant", block)
            self.assertIn("penalite_contre_signaux", block)
            actions = [h.get("action") for h in rec.get("history", [])]
            self.assertIn("calibration_priorite_v10", actions, rec["company"])

    def test_aucun_besoin_exprime_verifie_n_a_ete_degrade(self):
        self.assertEqual(self.sim["controles"]["besoins_exprimes_degrades"], [])
        self.assertEqual(self.sim["controles"]["besoins_exprimes_verifies"], 17)

    def test_aucune_fiche_sans_contre_signal_n_a_bouge_en_valeur(self):
        self.assertEqual(self.sim["controles"]["fiches_sans_contre_signal_ayant_bouge"], [])
        self.assertEqual(self.sim["controles"]["fiches_faibles_ayant_change_de_palier"], [])

    def test_recalculer_une_fiche_donne_le_resultat_enregistre(self):
        """Idempotence : le moteur appliqué doit redonner la valeur stockée."""
        from tests.test_phase10bis import _prospect
        for name in ("ERM 27", "O Lames Déchues", "Scierie Labrue", "Caléo Tests & Services"):
            rec = self.crm[name]
            got = assess(_prospect(rec), scores_from_record(rec), TODAY)
            self.assertEqual(got.value, rec["commercial_value"], name)
            self.assertEqual(got.tier, rec["commercial_priority"], name)
            self.assertEqual(got.engine_version, ENGINE_VERSION)


if __name__ == "__main__":
    unittest.main()
