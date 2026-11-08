"""Sections H, K, L — contrôles de la phase 10 sur les données réelles.

Ces tests ne rejouent aucune recherche : ils vérifient que ce qui a été décidé
et écrit reste cohérent, que les garde-fous tiennent, et que les journaux de
production ne sont pas pollués par les fixtures.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from prospecto import config
from prospecto.crm import CRM
from prospecto.dossier import audit_portfolio, build_dossier
from prospecto.metrics import compute_metrics
from prospecto.planner import NEED_QUERIES, NEED_QUERY_EXCLUSIONS, SearchHistory
from prospecto.scoring import scores_from_record
from prospecto.sender import Sender
from prospecto.sources import ExplorationLedger
from prospecto.email_verify import BLOCKING_STATUSES

DATA = config.DATA_DIR

ROOT = Path(__file__).resolve().parent.parent
LOT10 = "2026-11-07-lot10"
RECOVERIES = "2026-11-07-approfondissement"


def records():
    return CRM().records


class PlannerNeedQueryTests(unittest.TestCase):
    """Le défaut observé : les requêtes de besoin ne ramenaient que des agences."""

    def test_les_requetes_de_besoin_excluent_les_vendeurs(self):
        for token in ("-agence", "-freelance", "-prestataire"):
            self.assertIn(token, NEED_QUERY_EXCLUSIONS)

    def test_aucune_requete_ne_vante_la_prestation(self):
        # « recherche prestataire site internet » est la formulation que les
        # agences optimisent : elle doit avoir disparu des motifs.
        for template in NEED_QUERIES:
            self.assertNotIn("création site web {city}", template)
            self.assertNotIn('"recherche prestataire" site internet', template)

    def test_les_motifs_restants_sont_formules_du_cote_client(self):
        joined = " ".join(NEED_QUERIES).lower()
        self.assertIn("notre site", joined)
        self.assertIn("nous", joined)

    def test_les_requetes_sont_syntaxiquement_valides(self):
        # Régression : une apostrophe non échappée avait cassé tout le module.
        for template in NEED_QUERIES:
            rendered = template.format(city="Ajaccio") + " " + NEED_QUERY_EXCLUSIONS
            self.assertIn("Ajaccio", rendered)
            self.assertEqual(rendered.count('"') % 2, 0, rendered)


class Lot10IntegrityTests(unittest.TestCase):
    def test_le_lot10_est_trace_avec_son_objectif_non_atteint(self):
        path = config.DATA_DIR / "history" / "lot10-exploration-2026-11-07.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["lot"], LOT10)
        self.assertEqual(raw["examined"], len(raw["entries"]))
        # L'honnêteté du chiffre est le contrôle : pas de gonflement.
        self.assertFalse(raw["objective_reached"])
        self.assertTrue(raw["gap_reason"])

    def test_chaque_decision_du_lot10_porte_un_motif_et_une_source(self):
        path = config.DATA_DIR / "history" / "lot10-exploration-2026-11-07.json"
        for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]:
            self.assertTrue(entry["reason"], entry["company"])
            self.assertTrue(entry["source_url"], entry["company"])
            self.assertIn(entry["decision"],
                          ("retenue", "approfondir", "écartée", "annuaire_seul"))

    def test_les_agences_web_ne_sont_pas_devenues_des_fiches(self):
        names = {r["company"].lower() for r in records()}
        for agency in ("ms france concept", "bonu", "l'agence corse"):
            self.assertNotIn(agency, names)

    def test_les_entreprises_belges_sont_ecartees(self):
        doms = {(r.get("domain") or "").lower() for r in records()}
        self.assertNotIn("atelier-constantberger.be", doms)

    def test_le_lot10_n_empiete_pas_sur_les_autres_lots(self):
        recs = records()
        lot10 = {r["domain"] for r in recs if r.get("lot") == LOT10}
        others = {(r.get("domain") or "").lower() for r in recs if r.get("lot") != LOT10}
        self.assertTrue(lot10)
        self.assertEqual(lot10 & others, set())


class RecoveryIntegrityTests(unittest.TestCase):
    def test_les_quatre_recuperations_sont_qualifiables(self):
        recs = records()
        got = [r for r in recs if r.get("lot") == RECOVERIES]
        self.assertEqual(len(got), 4)
        for rec in got:
            dossier = build_dossier(rec)
            self.assertTrue(dossier.qualified, (rec["company"], dossier.blockers))

    def test_les_recuperations_ont_une_adresse_publiee_et_une_preuve_datee(self):
        for rec in records():
            if rec.get("lot") != RECOVERIES:
                continue
            self.assertEqual(rec.get("email_provenance"), "publiee", rec["company"])
            self.assertEqual(rec.get("email_verification"), "verified", rec["company"])
            self.assertEqual(rec.get("email_dns_status"), "mx_ok", rec["company"])
            dated = [e for e in rec["evidence"]
                     if e.get("verified_at") and e.get("source_url")]
            self.assertTrue(dated, rec["company"])

    def test_les_decisions_non_reexaminees_sont_dites_comme_telles(self):
        path = config.DATA_DIR / "history" / "approfondissement-lot9-2026-11-07.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        untouched = [e for e in raw["entries"] if e["decision"] == "non réexaminé"]
        self.assertTrue(untouched)
        for entry in untouched:
            self.assertIn("Non réexaminé", entry["reason"])
            self.assertIn("n'est PAS revalidé", entry["reason"])
        self.assertEqual(raw["reviewed"], raw["total"] - len(untouched))

    def test_le_registre_conserve_les_decisions_antérieures(self):
        # Le journal est append-only : une entreprise dont le rejet est levé
        # doit porter les deux décisions, pas la seconde à la place de la première.
        entries = ExplorationLedger().entries
        for name in ("Zicplace", "O Lames Déchues"):
            decisions = [e["decision"] for e in entries if e["company"] == name]
            self.assertIn("écartée", decisions, name)
            self.assertIn("retenue", decisions, name)


class DashboardMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = compute_metrics()

    def test_le_tableau_de_bord_expose_les_trois_nouveaux_blocs(self):
        for key in ("qualification", "recherche", "revue_portefeuille"):
            self.assertIn(key, self.m)

    def test_la_qualification_compte_reellement_les_coordonnees(self):
        q = self.m["qualification"]
        self.assertEqual(q["examined"], len(records()))
        self.assertGreater(q["email_verified"], 0)
        self.assertGreater(q["phone_verified"], 0)
        self.assertEqual(q["email_provenance"]["decodee_non_confirmee"], 0)

    def test_le_taux_de_qualification_est_calculable(self):
        q = self.m["qualification"]
        self.assertLessEqual(q["qualified"], q["examined"])
        self.assertGreater(q["qualified"], 0)

    def test_la_couverture_couvre_les_treize_regions(self):
        cov = self.m["recherche"]["coverage"]
        self.assertEqual(cov["region_count"], cov["regions_total"])
        self.assertGreaterEqual(cov["department_count"], 45)

    def test_le_rendement_des_sources_est_lisse(self):
        for perf in self.m["recherche"]["source_performance"]:
            self.assertGreaterEqual(perf["yield_score"], 0.0)
            self.assertLessEqual(perf["yield_score"], 1.0)
            if perf["examined"] == 0:
                # Une source neuve ne doit pas être traitée comme mauvaise.
                self.assertGreater(perf["yield_score"], 0.10)

    def test_la_source_la_plus_rentable_est_le_site_officiel(self):
        perfs = [p for p in self.m["recherche"]["source_performance"] if p["examined"]]
        best = max(perfs, key=lambda p: p["yield_score"])
        self.assertEqual(best["source_type"], "site_officiel")

    def test_la_partition_du_portefeuille_reste_exclusive(self):
        self.assertTrue(self.m["portefeuille"]["controle_exclusif"])
        self.assertEqual(self.m["portefeuille"]["total"], len(records()))

    def test_le_lot10_est_visible_avec_son_ecart_a_l_objectif(self):
        lot10 = self.m["revue_portefeuille"]["lot10"]
        self.assertFalse(lot10["objectif_atteint"])
        self.assertLess(lot10["examinees"], lot10["objectif"])

    def test_l_audit_gmail_est_expose_sans_confondre_envoi_et_delivrance(self):
        gmail = self.m["revue_portefeuille"]["gmail_phase10"]
        self.assertEqual(gmail["nouveau_depuis_dernier_audit"], 0)
        self.assertEqual(gmail["challenge"], 1)
        self.assertEqual(gmail["opposition"], 1)


class SafetyTests(unittest.TestCase):
    def test_les_envois_restant_bloques(self):
        settings = json.loads(config.CAMPAIGN_SETTINGS_PATH.read_text(encoding="utf-8"))
        self.assertFalse(settings["enabled"])

    def test_le_pré_vol_echoue_sur_une_copie_sans_toucher_la_production(self):
        import shutil
        import tempfile
        before = config.CAMPAIGN_SETTINGS_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "settings.json"
            shutil.copyfile(config.CAMPAIGN_SETTINGS_PATH, copy)
            ok, reasons = Sender(settings_path=copy).preflight()
        self.assertFalse(ok)
        self.assertGreaterEqual(len(reasons), 3)
        self.assertEqual(config.CAMPAIGN_SETTINGS_PATH.read_bytes(), before)

    def test_les_oppositions_et_suspensions_ne_qualifient_jamais(self):
        blocked = {"opposition", "suspendu", "rebond", "non_delivrable", "contacté"}
        for rec in records():
            if rec.get("status") in blocked:
                self.assertFalse(build_dossier(rec).qualified, rec["company"])

    def test_la_liste_de_suppression_contient_l_opposition_connue(self):
        raw = (config.DATA_DIR / "suppression.json").read_text(encoding="utf-8").lower()
        self.assertIn("celarenarde@gmail.com", raw)

    def test_aucune_adresse_decodee_non_confirmee(self):
        audit = audit_portfolio(records())
        self.assertEqual(audit["email_provenance"]["decodee_non_confirmee"], 0)

    def test_les_scores_du_crm_sont_reproductibles(self):
        for rec in records():
            fresh = scores_from_record(rec)
            stored = rec.get("scores") or {}
            for axis in ("site_web", "refonte", "ia_automatisation"):
                self.assertEqual(fresh[axis]["score"], stored[axis]["score"],
                                 (rec["company"], axis))

    def test_les_journaux_de_production_ne_contiennent_pas_de_fixtures(self):
        raw = json.loads((config.DATA_DIR / "history" / "reconciliations.json")
                         .read_text(encoding="utf-8"))
        items = raw.get("reconciliations", [])
        self.assertLessEqual(len(items), 10)
        # On contrôle les ENTRÉES, pas la note : celle-ci documente précisément
        # la mise en quarantaine des fixtures et doit pouvoir dire le mot.
        payload = json.dumps(items, ensure_ascii=False).lower()
        for marker in ("fixture", "example.com", "test@", "unittest"):
            self.assertNotIn(marker, payload)
        for item in items:
            self.assertTrue(item.get("at"))
            self.assertIn("matched", item)


if __name__ == "__main__":
    unittest.main()


class SecondePassePhase10Tests(unittest.TestCase):
    """Contrôles de la seconde passe : pistes F, lot 10 suite, audit E."""

    @classmethod
    def setUpClass(cls):
        cls.crm = CRM().records
        cls.by_name = {r["company"]: r for r in cls.crm}

    def test_les_quatre_nouvelles_fiches_ont_une_adresse_publiee_et_verifiee(self):
        for name in ("Fermetures Leichnam", "Forages Berenguer", "Ouest Affûtage",
                     "Sellerie Industrielle de l'Est"):
            rec = self.by_name[name]
            self.assertEqual(rec["email_verification"], "verified", name)
            self.assertEqual(rec["email_provenance"], "publiee", name)
            self.assertNotIn(rec["email_dns_status"], BLOCKING_STATUSES, name)
            self.assertTrue(rec.get("department"), name)

    def test_chaque_nouvelle_preuve_est_officielle_datee_et_citee(self):
        for name in ("Fermetures Leichnam", "Forages Berenguer", "Ouest Affûtage",
                     "Sellerie Industrielle de l'Est"):
            for e in self.by_name[name]["evidence"]:
                self.assertEqual(e["source_type"], "site_officiel", name)
                self.assertEqual(e["reliability"], "haute", name)
                self.assertTrue(e["observed"], name)
                self.assertTrue(e["source_url"].startswith("http"), name)
                self.assertTrue(e["quote"].strip(), name)
                self.assertEqual(e["observed_at"], "2026-11-07", name)

    def test_les_huit_pistes_ne_sont_pas_huit_prospects(self):
        p = DATA / "history" / "approfondissement-8-pistes-2026-11-07.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["examined"], 8)
        self.assertEqual(d["qualified"], 2, "seules 2 des 8 pistes qualifient")
        self.assertEqual(len(d["imported"]), 2)
        self.assertGreater(d["rejected"], 0)
        for dec in d["decisions"]:
            self.assertTrue(dec["step_done"], dec["company"])
            self.assertTrue(dec["source"].startswith("http"), dec["company"])

    def test_une_adresse_vue_seulement_en_extrait_nest_pas_retenue(self):
        d = json.loads((DATA / "history" / "approfondissement-8-pistes-2026-11-07.json")
                       .read_text(encoding="utf-8"))
        rh = next(x for x in d["decisions"] if x["company"].startswith("Rhonalpe"))
        self.assertEqual(rh["decision"], "approfondir")
        self.assertNotIn("Rhonalpe Étanchéité", self.by_name,
                         "adresse vue sur annuaire tiers : ne doit pas entrer au CRM")

    def test_le_lot10_suite_declare_son_objectif_non_atteint(self):
        d = json.loads((DATA / "history" / "lot10-suite-exploration-2026-11-07.json")
                       .read_text(encoding="utf-8"))
        self.assertFalse(d["objective_reached"])
        self.assertEqual(d["examined"], len(d["entries"]))
        self.assertLess(d["examined"], d["objective"])
        self.assertTrue(d["gap_reason"])
        self.assertTrue(d["structural_finding"])

    def test_une_structure_deja_outillee_est_ecartee(self):
        d = json.loads((DATA / "history" / "lot10-suite-exploration-2026-11-07.json")
                       .read_text(encoding="utf-8"))
        for name in ("L'Atelier du Marin", "AtelierD", "Valcreuse", "Totem Bau"):
            e = next(x for x in d["entries"] if x["company"] == name)
            self.assertEqual(e["decision"], "écartée", name)
            self.assertNotIn(name, self.by_name, name)

    def test_audit_E_clarifie_que_ce_ne_sont_pas_des_fiches_CRM(self):
        d = json.loads((DATA / "history" / "audit-38-fiches-2026-11-07.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(d["count"], 38)
        self.assertEqual(d["in_crm"], 0)
        self.assertTrue(d["clarification"])
        self.assertEqual(d["promues_au_crm_depuis"], 0)
        self.assertGreater(d["closables"], 0)
        for r in d["entries"]:
            self.assertTrue(r["categorie_rejet"], r["company"])
            self.assertTrue(r["next_step"], r["company"])

    def test_les_anciens_brouillons_et_les_journaux_sont_intacts(self):
        d = json.loads((DATA / "messages" / "brouillons-2026-11-07-lot10.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(len(d["messages"]), 5)
        self.assertTrue(d["deposited_to_gmail"])
        for legacy in ("1a1b672541671292", "1a1b1b991300c965", "1a1b1b98459979b3",
                       "1a1b1b9735345222", "1a1b16dee5899e57"):
            self.assertNotIn(legacy, json.dumps(d["messages"]))

    def test_aucun_envoi_supplementaire(self):
        log = json.loads((DATA / "history" / "send-log.json").read_text(encoding="utf-8"))
        entries = log if isinstance(log, list) else log.get("entries", [])
        self.assertEqual(len(entries), 60, "aucun nouvel envoi en seconde passe")
        for name in ("Fermetures Leichnam", "Forages Berenguer", "Ouest Affûtage",
                     "Sellerie Industrielle de l'Est"):
            self.assertEqual(self.by_name[name]["status"], "nouveau", name)

    def test_le_pref_vol_bloque_toujours(self):
        import shutil, tempfile
        tmp = tempfile.mkdtemp()
        target = Path(tmp) / "s.json"
        shutil.copy(DATA / "campaigns" / "v4-settings.json", target)
        ok, reasons = Sender(settings_path=target).preflight()[:2]
        self.assertFalse(ok)
        self.assertTrue(reasons)
