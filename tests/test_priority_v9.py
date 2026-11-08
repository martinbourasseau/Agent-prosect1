"""Calibration v9 — priorité commerciale transversale.

Le comportement attendu est formulé comme des invariants, pas comme des
valeurs figées : c'est ce qui permet de recalibrer plus tard sans réécrire
les tests.
"""
from __future__ import annotations

import json
import unittest
from datetime import date

from prospecto import config
from prospecto.crm import CRM
from prospecto.models import (
    Evidence, Prospect, EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP,
    SIGNAL_EXPRESSED, SIGNAL_OBSERVED, SIGNAL_INDIRECT, SIGNAL_HYPOTHETICAL,
)
from prospecto.priority import (
    assess, offer_relevance, BASE_BY_CLASS, MAGNITUDE_CAP, MAGNITUDE_RATE,
    THRESHOLD_HAUTE, AXES, RELEVANCE_PROPOSE, RELEVANCE_HORS_OFFRE,
    RELEVANCE_INCERTAINE, ENGINE_VERSION,
)
from prospecto.scoring import scores_from_record

TODAY = date(2026, 11, 7)


def ev(kind=EVIDENCE_WEBSITE_GAP, quote="Le site n'est pas adapté au mobile.",
       level=SIGNAL_OBSERVED, verified="2026-11-07", source_type="site_officiel",
       reliability="haute", observed=True):
    return Evidence(kind=kind, quote=quote, detail="", source_url="https://exemple.fr/",
                    source_type=source_type, observed_at="2026-11-07",
                    verified_at=verified, reliability=reliability,
                    observed=observed, signal_level=level)


def prospect(evidences, email="contact@exemple.fr", verification="verified", dns="mx_ok"):
    p = Prospect(company="Test", domain="exemple.fr", contact_email=email,
                 sector="Artisanat", needs=["refonte"], evidences=evidences,
                 website="https://exemple.fr/", email_verification=verification)
    p.email_dns_status = dns
    return p


def scores_for(best=50, blockers=None):
    s = {a: {"score": 0, "counter_signals": []} for a in AXES}
    s["refonte"]["score"] = best
    s["contactability"] = {"blockers": blockers or []}
    return s


class HierarchyTests(unittest.TestCase):
    """Le défaut que la calibration doit corriger."""

    def test_a_magnitude_egale_l_exprime_verifie_devant_l_observe(self):
        expr = assess(prospect([ev(EVIDENCE_PUBLIC_NEED,
                                   "Nous souhaitons refondre notre site internet.",
                                   SIGNAL_EXPRESSED)]), scores_for(50), TODAY)
        obs = assess(prospect([ev()]), scores_for(50), TODAY)
        self.assertGreater(expr.value, obs.value)
        self.assertEqual(expr.value - obs.value,
                         BASE_BY_CLASS["exprime_verifie"] - BASE_BY_CLASS[SIGNAL_OBSERVED])

    def test_l_ecart_est_constant_quelle_que_soit_la_magnitude(self):
        gaps = set()
        for v in range(0, 101):
            mag = min(MAGNITUDE_CAP, int(round(v * MAGNITUDE_RATE)))
            gaps.add((BASE_BY_CLASS["exprime_verifie"] + mag)
                     - (BASE_BY_CLASS[SIGNAL_OBSERVED] + mag))
        self.assertEqual(len(gaps), 1)
        self.assertGreater(gaps.pop(), 0)

    def test_un_site_techniquement_correct_ne_penalise_pas_un_besoin_exprime(self):
        # C'est exactement le cas que la v8 pénalisait : site impeccable, mais
        # l'entreprise demande explicitement de l'automatisation.
        p = prospect([ev(EVIDENCE_PUBLIC_NEED,
                         "Nous souhaitons automatiser nos devis et nos relances.",
                         SIGNAL_EXPRESSED)])
        s = scores_for(34)
        s["site_web"]["score"] = 5
        a = assess(p, s, TODAY)
        self.assertGreaterEqual(a.value, THRESHOLD_HAUTE)
        self.assertEqual(a.tier, "haute")

    def test_le_plancher_ne_depends_pas_de_la_magnitude(self):
        p = prospect([ev(EVIDENCE_PUBLIC_NEED, "Nous cherchons un nouveau site vitrine.",
                         SIGNAL_EXPRESSED)])
        a = assess(p, scores_for(0), TODAY)
        self.assertEqual(a.value, THRESHOLD_HAUTE)
        self.assertTrue(a.floor_applied)
        self.assertEqual(a.tier, "haute")

    def test_un_probleme_observe_massif_peut_rester_haute(self):
        # Régression de la première calibration rejetée : un plafond de
        # magnitude interdisait mécaniquement « haute » à toute la classe.
        a = assess(prospect([ev()]), scores_for(98), TODAY)
        self.assertEqual(a.tier, "haute")

    def test_ordre_des_quatre_classes(self):
        cases = [
            (EVIDENCE_PUBLIC_NEED, SIGNAL_EXPRESSED, "2026-11-07"),
            (EVIDENCE_WEBSITE_GAP, SIGNAL_OBSERVED, "2026-11-07"),
            (EVIDENCE_WEBSITE_GAP, SIGNAL_INDIRECT, "2026-11-07"),
            (EVIDENCE_WEBSITE_GAP, SIGNAL_HYPOTHETICAL, "2026-11-07"),
        ]
        values = [assess(prospect([ev(k, level=l, verified=v)]), scores_for(50), TODAY).value
                  for k, l, v in cases]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(len(set(values)), 4)


class OfferRelevanceTests(unittest.TestCase):
    """Une demande exprimée n'est pas automatiquement une priorité."""

    def test_une_demande_hors_offre_est_retrogradee(self):
        p = prospect([ev(EVIDENCE_PUBLIC_NEED,
                         "Nous recherchons quelqu'un pour créer notre logo et notre charte graphique.",
                         SIGNAL_EXPRESSED)])
        a = assess(p, scores_for(90), TODAY)
        self.assertEqual(a.relevance, RELEVANCE_HORS_OFFRE)
        self.assertEqual(a.tier, "basse")
        self.assertEqual(a.magnitude, 0)

    def test_externalisation_commerciale_hors_offre(self):
        p = prospect([ev(EVIDENCE_PUBLIC_NEED,
                         "Prendre des rendez-vous qualifiés entre notre dirigeant et des décideurs d'entreprise.",
                         SIGNAL_EXPRESSED)])
        a = assess(p, scores_for(60), TODAY)
        self.assertEqual(a.relevance, RELEVANCE_HORS_OFFRE)
        self.assertNotEqual(a.tier, "haute")

    def test_module_de_reservation_reste_dans_l_offre(self):
        # Ne pas confondre « prendre des RDV qualifiés » (_force de vente) et
        # « module de prise de rendez-vous » (système que nous construisons).
        p = prospect([ev(EVIDENCE_PUBLIC_NEED,
                         "Nous voulons un module de réservation en ligne pour nos inscriptions.",
                         SIGNAL_EXPRESSED)])
        rel, _, matched, _ = offer_relevance(p.evidences)
        self.assertEqual(rel, RELEVANCE_PROPOSE)
        self.assertIn("ia_automatisation", matched)

    def test_demande_mixte_garde_la_partie_pertinente(self):
        p = prospect([ev(EVIDENCE_PUBLIC_NEED,
                         "Nous cherchons un logo et un site internet pour notre atelier.",
                         SIGNAL_EXPRESSED)])
        rel, _, matched, out = offer_relevance(p.evidences)
        self.assertEqual(rel, RELEVANCE_PROPOSE)
        self.assertIn("site_web", matched)
        self.assertIn("logo", out)

    def test_une_demande_vue_sur_une_page_tierce_reste_non_verifiee(self):
        # `verified_at` ne peut pas servir de critère : le modèle le remplit
        # automatiquement avec `observed_at`. C'est l'autorité de la source
        # qui distingue une annonce publiée par l'entreprise d'une annonce
        # rapportée par un tiers.
        p = prospect([ev(EVIDENCE_PUBLIC_NEED, "Nous souhaitons refondre notre site.",
                         SIGNAL_EXPRESSED, source_type="page_professionnelle")])
        a = assess(p, scores_for(34), TODAY)
        self.assertEqual(a.signal_class, "exprime_non_verifie")
        self.assertFalse(a.verified)
        self.assertEqual(a.tier, "moyenne")
        self.assertFalse(a.floor_applied)

    def test_une_date_seule_ne_prouve_pas_la_verification(self):
        from prospecto.priority import _is_verified
        # Le modèle remplit verified_at automatiquement : ce test garde la
        # régression visible si quelqu'un revient à un test de date.
        e = ev(EVIDENCE_PUBLIC_NEED, "Nous voulons un site.", SIGNAL_EXPRESSED,
               source_type="annuaire_pro")
        self.assertTrue(e.verified_at)
        self.assertFalse(_is_verified(e))

    def test_sans_besoin_exprime_la_pertinence_est_proposee_par_construction(self):
        rel, factor, _, _ = offer_relevance([ev()])
        self.assertEqual(rel, RELEVANCE_PROPOSE)
        self.assertEqual(factor, 1.0)


class ContactabilityTests(unittest.TestCase):
    def test_sans_adresse_la_priorite_est_plafonnee_mais_la_valeur_conservee(self):
        p = prospect([ev(EVIDENCE_PUBLIC_NEED, "Nous voulons automatiser nos devis.",
                         SIGNAL_EXPRESSED)], email="")
        a = assess(p, scores_for(60), TODAY)
        self.assertEqual(a.tier, "a_approfondir")
        self.assertTrue(a.capped_by_contactability)
        self.assertGreaterEqual(a.value, THRESHOLD_HAUTE)

    def test_domaine_non_routable_plafonne(self):
        p = prospect([ev()], dns="nxdomain")
        a = assess(p, scores_for(90), TODAY)
        self.assertEqual(a.tier, "a_approfondir")
        self.assertFalse(a.contactable)

    def test_un_blocage_de_contactabilite_plafonne(self):
        a = assess(prospect([ev()]), scores_for(90, blockers=["adresse décodée"]), TODAY)
        self.assertEqual(a.tier, "a_approfondir")


class IndependenceTests(unittest.TestCase):
    """Les trois scores ne doivent pas être affectés."""

    def test_les_axes_ne_sont_pas_recalcules(self):
        recs = CRM().records
        for rec in recs:
            fresh = scores_from_record(rec)
            for axis in AXES:
                self.assertEqual(int(fresh[axis]["score"]), int(rec["scores"][axis]["score"]),
                                 (rec["company"], axis))

    def test_la_priorite_v8_est_conservee_dans_scores(self):
        archive = json.loads((config.DATA_DIR / "history"
                              / "priorite-commerciale-v8-vers-v9.json").read_text(encoding="utf-8"))
        for entry in archive["entries"]:
            rec = next(r for r in CRM().records if r["company"] == entry["company"])
            self.assertEqual(rec["scores"].get("priority"),
                             entry["before"]["v8_priority_in_scores"], rec["company"])

    def test_la_valeur_transversale_n_est_pas_le_max_des_axes(self):
        # Deux fiches de même meilleur axe peuvent avoir des valeurs différentes.
        expr = assess(prospect([ev(EVIDENCE_PUBLIC_NEED, "Nous voulons un site vitrine.",
                                   SIGNAL_EXPRESSED)]), scores_for(50), TODAY)
        obs = assess(prospect([ev()]), scores_for(50), TODAY)
        self.assertEqual(expr.best_axis_score, obs.best_axis_score)
        self.assertNotEqual(expr.value, obs.value)


class TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((config.DATA_DIR / "history"
                                  / "priorite-commerciale-v8-vers-v9.json")
                                 .read_text(encoding="utf-8"))

    def test_le_crm_d_avant_migration_est_archive(self):
        self.assertEqual(len(self.archive["crm_before_migration"]), 83)
        self.assertEqual(self.archive["axes_modified"], 0)

    def test_chaque_fiche_porte_le_bloc_commercial_et_son_historique(self):
        for rec in CRM().records:
            self.assertIn("commercial", rec, rec["company"])
            self.assertEqual(rec["commercial"]["engine_version"], ENGINE_VERSION)
            self.assertEqual(rec["priority_engine_version"], ENGINE_VERSION)
            actions = [h.get("action") for h in rec.get("history", [])]
            self.assertIn("calibration_priorite_commerciale_v9", actions, rec["company"])

    def test_le_changement_est_trace_avant_apres(self):
        for entry in self.archive["entries"]:
            self.assertIn("commercial_priority", entry["before"])
            self.assertIn("commercial_priority", entry["after"])
            self.assertEqual(entry["before"]["axes"], entry["after"]["axes"])

    def test_la_evaluation_est_datee_et_expliquee(self):
        for rec in CRM().records:
            c = rec["commercial"]
            self.assertEqual(c["evaluated_at"], TODAY.isoformat())
            self.assertTrue(c["reasons"])
            self.assertIn(c["confidence"], ("haute", "moyenne", "faible"))
            self.assertIn(c["signal_class"], BASE_BY_CLASS)

    def test_une_preuve_n_est_pas_comptee_deux_fois(self):
        for rec in CRM().records:
            for axis in AXES:
                cited = [(e.get("source_url", ""), (e.get("quote") or "")[:60])
                         for e in (rec["scores"][axis].get("evidence") or [])]
                self.assertEqual(len(cited), len(set(cited)), (rec["company"], axis))

    def test_les_oppositions_ne_deviennent_pas_actionnables(self):
        from prospecto.dossier import build_dossier
        for rec in CRM().records:
            if rec.get("status") in ("opposition", "suspendu", "rebond"):
                self.assertFalse(build_dossier(rec).qualified, rec["company"])


if __name__ == "__main__":
    unittest.main()