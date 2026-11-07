"""Section E — planificateur : mémoire, rendement des sources, couverture."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from prospecto.planner import (
    SearchHistory, SearchPlanner, SourcePerformance, source_performance,
    territorial_coverage, region_of, fingerprint, REGIONS, DEPT_TO_REGION,
)
from prospecto.sources import ExplorationLedger, TERRITORY_POOL, SECTOR_POOL


def ledger_with(entries):
    tmp = tempfile.TemporaryDirectory()
    led = ExplorationLedger(Path(tmp.name) / "ledger.json")
    for e in entries:
        led.record(**e)
    return tmp, led


def history_empty():
    tmp = tempfile.TemporaryDirectory()
    return tmp, SearchHistory(Path(tmp.name) / "search.json")


class RegionTests(unittest.TestCase):
    def test_chaque_du_pool_a_une_region(self):
        for dept, _ in TERRITORY_POOL:
            self.assertIn(dept, DEPT_TO_REGION, f"{dept} sans région")

    def test_les_regions_couvrent_la_metropole(self):
        self.assertEqual(len(REGIONS), 13)
        self.assertEqual(region_of("75"), "Île-de-France")
        self.assertEqual(region_of("2A"), "Corse")
        self.assertEqual(region_of("971"), "hors métropole")

    def test_pas_de_departement_dans_deux_regions(self):
        seen = set()
        for depts in REGIONS.values():
            for d in depts:
                self.assertNotIn(d, seen, f"{d} en double")
                seen.add(d)


class SearchHistoryTests(unittest.TestCase):
    def test_une_requete_executee_est_reconnue(self):
        tmp, h = history_empty()
        self.addCleanup(tmp.cleanup)
        self.assertFalse(h.already_run("pisciniste Aurillac"))
        h.record("pisciniste Aurillac", department="15")
        self.assertTrue(h.already_run("pisciniste Aurillac"))

    def test_la_reconnaissance_ignore_casse_et_espaces(self):
        tmp, h = history_empty()
        self.addCleanup(tmp.cleanup)
        h.record("Pisciniste   Aurillac")
        self.assertTrue(h.already_run("  pisciniste aurillac "))

    def test_persistence_sur_disque(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "h.json"
            h = SearchHistory(path)
            h.record("requête A", department="03", source_type="site_officiel",
                     examined=5, retained=1, qualified=1, lot="lot10")
            h.save()
            again = SearchHistory(path)
            self.assertEqual(len(again.entries), 1)
            self.assertTrue(again.already_run("requête A"))
            self.assertEqual(again.entries[0]["qualified"], 1)

    def test_statistiques_par_source_et_region(self):
        tmp, h = history_empty()
        self.addCleanup(tmp.cleanup)
        h.record("q1", department="03", source_type="site_officiel",
                 examined=4, retained=1, qualified=1)
        h.record("q2", department="75", source_type="site_officiel", examined=2)
        s = h.stats()
        self.assertEqual(s["queries"], 2)
        self.assertEqual(s["by_source"]["site_officiel"]["examined"], 6)
        self.assertIn("Auvergne-Rhône-Alpes", s["regions"])
        self.assertIn("Île-de-France", s["regions"])

    def test_fingerprint_stable(self):
        self.assertEqual(fingerprint("  A  B "), fingerprint("a b"))


class SourcePerformanceTests(unittest.TestCase):
    def test_une_source_productive_passe_devant(self):
        tmp, led = ledger_with([
            dict(company="A", domain="a.fr", decision="retenue", source_type="site_officiel"),
            dict(company="B", domain="b.fr", decision="retenue", source_type="site_officiel"),
            dict(company="C", domain="c.fr", decision="écartée", source_type="annuaire_pro"),
            dict(company="D", domain="d.fr", decision="annuaire_seul", source_type="annuaire_pro"),
        ])
        self.addCleanup(tmp.cleanup)
        records = [
            {"company": "A", "domain": "a.fr", "email": "a@a.fr", "email_verification": "mx_ok"},
            {"company": "B", "domain": "b.fr", "email": "b@b.fr", "email_verification": "mx_ok"},
        ]
        perf = source_performance(led, records)
        self.assertEqual(perf[0].source_type, "site_officiel")
        self.assertEqual(perf[0].qualified, 2)
        by = {p.source_type: p for p in perf}
        self.assertGreater(by["site_officiel"].yield_score, by["annuaire_pro"].yield_score)

    def test_retenue_sans_coordonnees_n_est_pas_qualifiee(self):
        tmp, led = ledger_with([
            dict(company="A", domain="a.fr", decision="retenue", source_type="site_officiel"),
        ])
        self.addCleanup(tmp.cleanup)
        perf = {p.source_type: p for p in source_performance(
            led, [{"company": "A", "domain": "a.fr", "email": ""}])}
        self.assertEqual(perf["site_officiel"].retained, 1)
        self.assertEqual(perf["site_officiel"].qualified, 0)

    def test_le_lissage_evite_de_sur_reagir_a_un_coup_de_chance(self):
        lucky = SourcePerformance("chance", examined=1, retained=1, qualified=1)
        proven = SourcePerformance("prouvée", examined=40, retained=12, qualified=12)
        self.assertGreater(proven.yield_score, lucky.yield_score)

    def test_une_source_jamais_utilisee_garde_un_prior_neutre(self):
        p = SourcePerformance("neuve")
        self.assertAlmostEqual(p.yield_score, 0.15)   # le prior, ni plus ni moins
        self.assertEqual(p.qualification_rate, 0.0)


class CoverageTests(unittest.TestCase):
    def test_la_couverture_compte_les_regions_pas_seulement_les_departements(self):
        records = [{"department": "75"}, {"department": "92"}, {"department": "93"}]
        cov = territorial_coverage(records)
        self.assertEqual(cov["department_count"], 3)
        self.assertEqual(cov["region_count"], 1)
        self.assertEqual(cov["regions"], ["Île-de-France"])

    def test_le_registre_complete_la_couverture_du_crm(self):
        tmp, led = ledger_with([dict(company="X", department="2A", decision="écartée")])
        self.addCleanup(tmp.cleanup)
        cov = territorial_coverage([{"department": "75"}], led)
        self.assertEqual(cov["department_count"], 2)
        self.assertIn("Corse", cov["regions"])

    def test_les_regions_vierges_sont_identifiees(self):
        cov = territorial_coverage([{"department": "75"}])
        self.assertIn("Bretagne", cov["unexplored_regions"])
        self.assertNotIn("Île-de-France", cov["unexplored_regions"])


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.t1, self.led = ledger_with([])
        self.t2, self.hist = history_empty()
        self.addCleanup(self.t1.cleanup)
        self.addCleanup(self.t2.cleanup)
        self.records = [{"company": "Déjà vu", "domain": "dejavu.fr",
                         "sector": "traiteur", "department": "44"}]

    def _planner(self):
        return SearchPlanner(self.records, self.led, self.hist)

    def test_le_plan_ne_repete_une_requete_deja_executee(self):
        p = self._planner()
        first = p.plan(8)
        self.assertEqual(len(first), 8)
        for q in first:
            self.hist.record(q.query, department=q.department,
                             source_type=q.source_type)
        second = self._planner().plan(8)
        self.assertFalse({q.query for q in first} & {q.query for q in second})

    def test_le_plan_varie_les_departements(self):
        plan = self._planner().plan(14)
        self.assertGreaterEqual(len({q.department for q in plan}), 6)
        self.assertGreaterEqual(len({q.region for q in plan}), 4)

    def test_les_territoires_jamais_explores_passent_devant(self):
        self.records[0]["department"] = "44"
        ranked = self._planner().ranked_territories()
        self.assertNotEqual(ranked[0][0], "44")

    def test_une_part_du_plan_cherche_des_besoins_publies(self):
        plan = self._planner().plan(10, expressed_share=0.4)
        needs = [q for q in plan if q.track == "besoin_exprime"]
        self.assertEqual(len(needs), 4)
        self.assertTrue(all(q.priority > 1.5 for q in needs))

    def test_les_besoins_publies_passent_avant_l_exploration(self):
        plan = self._planner().plan(10)
        tracks = [q.track for q in plan]
        self.assertEqual(tracks, sorted(tracks, key=lambda t: t != "besoin_exprime"))

    def test_les_secteurs_deja_travailles_sont_evites(self):
        self.records[0]["sector"] = "pisciniste — entretien et rénovation de bassins"
        labels = {label for label, _ in self._planner().fresh_sectors()}
        self.assertNotIn("pisciniste — entretien et rénovation de bassins", labels)

    def test_un_secteur_du_registre_est_aussi_evite(self):
        self.led.record(company="Y", sector="taxidermiste_naturaliste", decision="écartée")
        labels = " ".join(label for label, _ in self._planner().fresh_sectors()).lower()
        self.assertNotIn("taxidermiste", labels)

    def test_chaque_piste_est_justifiee(self):
        for q in self._planner().plan(6):
            self.assertTrue(q.rationale)
            self.assertTrue(q.region)
            self.assertGreater(q.priority, 0)

    def test_plan_reproductible_a_etat_egal(self):
        a = [q.query for q in self._planner().plan(6)]
        b = [q.query for q in self._planner().plan(6)]
        self.assertEqual(a, b)

    def test_la_vue_d_ensemble_expose_le_rendement_reel(self):
        ov = self._planner().overview()
        self.assertIn("source_performance", ov)
        self.assertIn("coverage", ov)
        self.assertIn("search_history", ov)
        self.assertEqual(ov["coverage"]["regions_total"], 13)

    def test_le_pool_n_est_pas_une_liste_fige_de_metiers(self):
        self.assertGreaterEqual(len(SECTOR_POOL), 40)
        self.assertGreaterEqual(len(TERRITORY_POOL), 50)


if __name__ == "__main__":
    unittest.main()
