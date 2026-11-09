"""Section D — pilote marchés publics : règles de classement et données réelles."""
from __future__ import annotations

import json
import unittest
from datetime import date

from prospecto import config
from prospecto.public_tenders import (
    AUTHOR_BUYER, AUTHOR_VENDOR, CATEGORY_A, CATEGORY_B, CATEGORY_C,
    TenderNotice, assess_tender, load_pilot,
)

TODAY = date(2026, 11, 9)


def notice(**kw):
    base = dict(ref="REF-1", title="Refonte du site internet", buyer="Commune X",
                source="BOAMP", official_url="https://boamp.fr/avis",
                deadline="2026-11-30", procedure="procédure adaptée",
                estimated_value_eur=20000.0, value_verified=True,
                scope_summary="conception et refonte du site internet")
    base.update(kw)
    return TenderNotice(**base)


class ReglesDeClassementTests(unittest.TestCase):
    def test_avis_ouvert_accessible_et_complet_classe_A(self):
        a = assess_tender(notice(), TODAY)
        self.assertEqual(a.category, CATEGORY_A)
        self.assertTrue(a.in_scope)
        self.assertEqual(a.days_left, 21)

    def test_une_annonce_de_prestataire_n_est_jamais_une_demande_d_acheteur(self):
        a = assess_tender(notice(author=AUTHOR_VENDOR), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertIn("prestataire", a.reasons[0])

    def test_un_agregateur_seul_ne_prouve_pas_une_demande(self):
        self.assertEqual(assess_tender(notice(author="agregateur"), TODAY).category, CATEGORY_C)

    def test_avis_expire_classe_C(self):
        a = assess_tender(notice(deadline="2026-10-01"), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertTrue(a.expired)
        self.assertLess(a.days_left, 0)

    def test_avis_attribue_classe_C(self):
        a = assess_tender(notice(notice_type="attribution"), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertIn("pas ouvert", a.reasons[0])

    def test_montant_hors_de_portee_classe_C(self):
        a = assess_tender(notice(estimated_value_eur=210000.0), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertIn("hors de portée", a.reasons[0])

    def test_hors_perimetre_classe_C(self):
        a = assess_tender(notice(title="Conception impression du magazine municipal",
                                 scope_summary="impression et livraison"), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertFalse(a.in_scope)

    def test_le_code_cpv_ne_suffit_pas_a_rendre_un_marche_pertinent(self):
        """Cas réel : INRS, événementiel, portant le CPV « conception de sites »."""
        a = assess_tender(notice(title="Organisation de congrès et colloques",
                                 scope_summary="journées techniques hybrides, événements",
                                 cpv=("72413000",)), TODAY)
        self.assertEqual(a.category, CATEGORY_C)

    def test_echeance_trop_proche_classe_B(self):
        a = assess_tender(notice(deadline="2026-11-12"), TODAY)
        self.assertEqual(a.category, CATEGORY_B)
        self.assertTrue(any("délai de réponse court" in r for r in a.reasons))

    def test_element_non_verifie_classe_B(self):
        a = assess_tender(notice(unverified=("RC non lu",)), TODAY)
        self.assertEqual(a.category, CATEGORY_B)
        self.assertIn("RC non lu", a.reasons)

    def test_montant_inconnu_classe_B(self):
        a = assess_tender(notice(estimated_value_eur=None, value_verified=False), TODAY)
        self.assertEqual(a.category, CATEGORY_B)
        self.assertTrue(any("montant non publié" in r for r in a.reasons))

    def test_procedure_formalisee_classe_B(self):
        a = assess_tender(notice(procedure="procédure formalisée"), TODAY)
        self.assertEqual(a.category, CATEGORY_B)

    def test_avis_ancien_sans_echeance_ne_peut_etre_presume_ouvert(self):
        a = assess_tender(notice(deadline="", published_at="2025-06-10"), TODAY)
        self.assertEqual(a.category, CATEGORY_C)
        self.assertIn("ouverture non établie", a.reasons[0])

    def test_avis_recent_sans_echeance_reste_a_verifier(self):
        a = assess_tender(notice(deadline="", published_at="2026-11-01"), TODAY)
        self.assertEqual(a.category, CATEGORY_B)

    def test_automatisation_et_ia_sont_dans_le_perimetre(self):
        for title in ("Déploiement d'un agent conversationnel",
                      "Automatisation des processus administratifs",
                      "Accompagnement du programme IA"):
            a = assess_tender(notice(title=title, scope_summary=title.lower()), TODAY)
            self.assertTrue(a.in_scope, title)


class PiloteReelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot, cls.raw = load_pilot()
        cls.summary = cls.pilot.summary()
        cls.by_ref = {n.ref: n for n in cls.pilot.notices}

    def test_objectif_d_examen_atteint(self):
        """20 consultations étaient un objectif d'examen, pas un quota
        d'opportunités : 30 ont été examinées."""
        self.assertGreaterEqual(self.summary["consultations_examinees"], 20)
        self.assertEqual(self.summary["consultations_examinees"], 30)

    def test_diversite_des_acheteurs_et_secteurs(self):
        self.assertGreaterEqual(len(self.summary["secteurs"]), 10)
        buyers = {n.buyer for n in self.pilot.notices}
        self.assertEqual(len(buyers), 29, "30 avis, Météo-France deux fois")

    def test_les_trois_categories_sont_renseignees(self):
        self.assertEqual(set(self.summary["categories"]), {"A", "B", "C"})
        self.assertEqual(sum(self.summary["categories"].values()), 30)

    def test_aucune_opportunite_A_sans_verification_complete(self):
        """Résultat honnête : aucune consultation n'est directement exploitable
        tant que les pièces de candidature ne sont pas réunies."""
        self.assertEqual(self.summary["categories"]["A"], 0)
        self.assertEqual(self.summary["categories"]["B"], 10)
        self.assertEqual(self.summary["categories"]["C"], 20)

    def test_les_annonces_de_prestataires_ne_sont_pas_comptees_comme_avis(self):
        rejected = self.raw["annonces_non_acheteurs_ecartees"]
        self.assertEqual(len(rejected), 3)
        self.assertEqual(self.summary["annonces_non_acheteurs_ecartees"], 3)
        refs = {n.ref for n in self.pilot.notices}
        for r in rejected:
            self.assertNotIn(r["source_url"], refs)
            self.assertTrue(r["motif_rejet"])

    def test_tous_les_avis_ont_un_lien_officiel_ou_de_profil(self):
        for n in self.pilot.notices:
            self.assertTrue(n.official_url.startswith("http"), n.ref)
            self.assertTrue(n.buyer, n.ref)
            self.assertTrue(n.source, n.ref)

    def test_toutes_les_pistes_A_ou_B_ont_une_raison_explicite(self):
        for a in self.pilot.assessments():
            if a.category in (CATEGORY_A, CATEGORY_B):
                self.assertGreaterEqual(len(a.reasons), 2, a.ref)
                self.assertTrue(self.by_ref[a.ref].scope_summary, a.ref)

    def test_mieussy_est_la_piste_la_mieux_instruite(self):
        m = self.by_ref["BOAMP 26-97266"]
        self.assertTrue(m.value_verified)
        self.assertEqual(m.estimated_value_eur, 20000)
        self.assertIn("RÈGLEMENT DE CONSULTATION LU", m.requirements)
        self.assertIn("3 dernières années", m.requirements)
        self.assertEqual(len(m.pages_read), 3)
        self.assertIn("2026-11-20", m.deadline)
        a = assess_tender(m, TODAY)
        self.assertEqual(a.category, CATEGORY_B)
        self.assertEqual(a.days_left, 11)

    def test_le_commentaire_d_un_tiers_n_a_pas_cree_une_exigence(self):
        """Un site d'agence affirmait que le marché était exigeant en
        références. L'exigence n'est retenue que depuis le RC de l'acheteur."""
        rejected = next(r for r in self.raw["annonces_non_acheteurs_ecartees"]
                        if "lafabriquedunet" in r["source_url"])
        self.assertIn("n'a PAS été retenue", rejected["motif_rejet"])
        self.assertIn("RÈGLEMENT DE CONSULTATION LU",
                      self.by_ref["BOAMP 26-97266"].requirements)

    def test_les_avis_d_attribution_ne_sont_pas_comptes_comme_ouverts(self):
        attributed = [n for n in self.pilot.notices if n.notice_type == "attribution"]
        self.assertEqual(len(attributed), 4)
        for n in attributed:
            self.assertEqual(assess_tender(n, TODAY).category, CATEGORY_C, n.ref)

    def test_les_gros_marches_sont_ecartes_par_le_montant_publie(self):
        for ref, value in (("CNRS 26.14.027", 1500000),
                           ("METEO-FRANCE2637F0267", 300000),
                           ("BOAMP 26-98846 / TED 708553-2026", 210000)):
            n = self.by_ref[ref]
            self.assertEqual(n.estimated_value_eur, value)
            self.assertTrue(n.value_verified)
            self.assertEqual(assess_tender(n, TODAY).category, CATEGORY_C, ref)

    def test_le_constat_ia_est_documente(self):
        self.assertIn("Aucune consultation ouverte", self.raw["constats"]["ia_et_automatisation"])

    def test_aucune_candidature_ni_contact_ni_depense(self):
        self.assertTrue(self.raw["aucune_candidature_deposee"])
        self.assertTrue(self.raw["aucun_acheteur_contacte"])
        self.assertTrue(self.raw["aucune_depense"])

    def test_la_date_de_reference_est_justifiee(self):
        self.assertEqual(self.raw["date_reference"], "2026-11-09")
        self.assertIn("recoupement", self.raw["note_date"])

    def test_les_pistes_B_sont_triees_par_echeance_dans_le_resume(self):
        rows = self.summary["exploitables"]
        self.assertEqual(len(rows), 10)
        days = [r["jours_restants"] for r in rows if r["jours_restants"] is not None]
        self.assertTrue(all(d >= 0 for d in days), "aucune piste B expirée")
        self.assertEqual(min(days), 4)


if __name__ == "__main__":
    unittest.main()
