"""Phase 10 bis — verrous sur les découvertes et les invariants de la passe."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from prospecto import config
from prospecto.crm import CRM
from prospecto.messaging import check_email_v4
from prospecto.models import Evidence, GeneratedEmail, Prospect
from prospecto.sources import ExplorationLedger

DATA = config.DATA_DIR


def _prospect(rec):
    evs = [Evidence(**{k: v for k, v in e.items() if k in Evidence.__dataclass_fields__})
           for e in rec.get("evidence", [])]
    p = Prospect(company=rec["company"], domain=rec.get("domain", ""),
                 contact_email=rec.get("email", ""), sector=rec.get("sector", ""),
                 needs=rec.get("needs") or [], evidences=evs,
                 website=rec.get("website", ""),
                 email_verification=rec.get("email_verification", "public_unverified"))
    p.email_dns_status = rec.get("email_dns_status", "not_checked")
    p.recommended_service = rec.get("recommended_service", "")
    return p


class EnvoisHorsAgentTests(unittest.TestCase):
    """Les 8 envois du 09/11 doivent rester réconciliés, jamais recontactés."""

    @classmethod
    def setUpClass(cls):
        cls.crm = {r["company"]: r for r in CRM().records}
        cls.audit = json.loads(
            (DATA / "history" / "audit-gmail-phase10bis-2026-11-07.json")
            .read_text(encoding="utf-8"))

    def test_les_huit_envois_sont_reconcilies(self):
        self.assertEqual(len(self.audit["envois_hors_agent"]), 8)
        self.assertEqual(self.audit["introuvables"], [])

    def test_les_huit_fiches_sont_contactees_dont_plus_jamais(self):
        for u in self.audit["envois_hors_agent"]:
            rec = self.crm[u["company"]]
            self.assertEqual(rec["status"], "contacté", u["company"])
            self.assertTrue(rec.get("gmail_sent_message_id"), u["company"])
            actions = [h.get("action") for h in rec.get("history", [])]
            self.assertIn("envoi_hors_agent_reconcilie", actions, u["company"])

    def test_le_journal_de_production_na_pas_bouge(self):
        log = json.loads((DATA / "history" / "send-log.json").read_text(encoding="utf-8"))
        entries = log if isinstance(log, list) else log.get("entries", [])
        self.assertEqual(len(entries), 60,
                         "les envois hors agent vont au journal des rapprochements")

    def test_le_journal_des_rapprochements_a_ete_etendu_sans_ecrasement(self):
        j = json.loads((DATA / "history" / "reconciliations.json").read_text(encoding="utf-8"))
        self.assertEqual(len(j["reconciliations"]), 5)
        self.assertEqual(j["count"], 5)
        last = j["reconciliations"][-1]
        self.assertEqual(last["matched"], 8)
        self.assertEqual(last["origin"], "phase10bis-audit-gmail")
        # les 4 entrées antérieures sont toujours là
        self.assertEqual(j["reconciliations"][0]["matched"], 15)

    def test_label_8_est_bien_le_libelle_du_lot_10(self):
        v = self.audit["label_verification"]
        self.assertIn("Prospection/2026-11-07-lot10", v["reponse"])
        self.assertIn("OUI", v["reponse"])

    def test_deux_brouillons_restant_seulement(self):
        self.assertEqual(len(self.audit["brouillons_restants"]), 2)
        labels = {b["label"] for b in self.audit["brouillons_restants"]}
        self.assertEqual(labels, {"Label_7", "Label_6"})

    def test_le_piege_des_requetes_filtrees_est_documente(self):
        self.assertIn("complete:true", self.audit["piege_requete"])
        self.assertIn("in:anywhere", self.audit["piege_requete"])


class ContenuBrouillonsTests(unittest.TestCase):
    def test_les_cinq_messages_du_lot_10_restant_conformes(self):
        crm = CRM().records
        arch = json.loads((DATA / "messages" / "brouillons-2026-11-07-lot10.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(len(arch["messages"]), 5)
        for m in arch["messages"]:
            rec = next(r for r in crm if (r.get("email") or "") == m["to"])
            ge = GeneratedEmail(to=m["to"], subject=m["subject"], body=m["body"],
                                company=rec["company"], need=rec.get("need", "refonte"),
                                message_version="v4")
            self.assertEqual(check_email_v4(ge, _prospect(rec)), [], m["company"])
            self.assertIn("Martin BOURASSEAU", m["body"])
            self.assertIn("ne pas me relancer", m["body"])

    def test_larchive_garde_lhistorique_du_depot(self):
        arch = json.loads((DATA / "messages" / "brouillons-2026-11-07-lot10.json")
                          .read_text(encoding="utf-8"))
        self.assertTrue(arch["deposited_to_gmail"])
        self.assertTrue(arch["statut_2026_11_07_audit"]["sent_observed"])
        for m in arch["messages"]:
            self.assertTrue(m["gmail_draft_id"], "identifiant de brouillon conservé")


class RecherchesPhase10BisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((DATA / "history" / "phase10bis-recherches-2026-11-07.json")
                           .read_text(encoding="utf-8"))
        cls.crm = {r["company"]: r for r in CRM().records}

    def test_le_perimetre_de_recherche_est_atteint(self):
        b1 = self.d["B1_perimetre_recherche"]
        self.assertTrue(b1["objectif_atteint"])
        self.assertGreaterEqual(b1["examinees_cette_passe"], b1["objectif_restant"])
        self.assertEqual(b1["examinees_cette_passe"], len(b1["entries"]))

    def test_les_deja_outillees_sont_ecartees_meme_si_le_site_est_beau(self):
        entries = {e["company"]: e for e in self.d["B1_perimetre_recherche"]["entries"]}
        for name in ("Lanoy Couverture", "LOC'B", "Hublo", "Easypro", "Blanc Comme Neige"):
            self.assertEqual(entries[name]["decision"], "écartée", name)
            self.assertNotIn(name, self.crm, name)

    def test_une_adresse_vue_seulement_en_extrait_nentre_pas_au_crm(self):
        for name in ("DBS Location Benne", "AZ Menuiseries Escaliers",
                     "La Châtaigneraie de Bel Air", "Scierie des Combrailles",
                     "Bennes & Co", "PSL Blanchisserie", "Pressing Perce Neige"):
            self.assertNotIn(name, self.crm,
                             "%s : adresse non lue directement, ne doit pas être importée" % name)

    def test_les_cinq_importees_ont_une_adresse_lue_et_routable(self):
        self.assertEqual(len(self.d["imported"]), 5)
        for i in self.d["imported"]:
            rec = self.crm[i["company"]]
            self.assertEqual(rec["email_verification"], "verified")
            self.assertEqual(rec["email_provenance"], "publiee")
            self.assertIn("lue directement", rec["email_verification_basis"])
            self.assertEqual(rec["status"], "nouveau", "aucun envoi sur les nouvelles fiches")

    def test_les_corrections_de_departement_sont_tracees(self):
        corr = {c["company"]: c for c in self.d["corrections_departement"]}
        self.assertEqual(corr["Menuiserie Mirolo"]["avant"], "68")
        self.assertEqual(corr["Menuiserie Mirolo"]["apres"], "02")
        self.assertEqual(corr["AZ Menuiseries Escaliers"]["apres"], "60")
        self.assertEqual(self.crm["Menuiserie Mirolo"]["department"], "02")

    def test_les_deux_opportunites_prioritaires_ont_une_decision_motivée(self):
        opps = {o["company"]: o for o in self.d["C_opportunites_prioritaires"]}
        self.assertEqual(len(opps), 2)
        for name, o in opps.items():
            self.assertTrue(o["identity"], name)
            self.assertGreaterEqual(len(o["pages_read"]), 2, name)
            self.assertTrue(o["signal_parcours"], name)
            self.assertTrue(o["why_not_draft"], name)
            self.assertTrue(o["next_step"], name)

    def test_lavis_non_date_ne_prouve_pas_un_probleme_actuel(self):
        o = next(o for o in self.d["C_opportunites_prioritaires"]
                 if o["company"] == "La Châtaigneraie de Bel Air")
        self.assertIn("aucune date", o["signal_review"])
        self.assertTrue(o["decision"].startswith("approfondir"))

    def test_erm27_est_conservee_sans_brouillon(self):
        o = next(o for o in self.d["C_opportunites_prioritaires"]
                 if o["company"] == "ERM 27")
        self.assertIn("pas de brouillon", o["decision"])
        self.assertTrue(self.crm["ERM 27"]["revue_humaine_requise"])


class ContreSignauxTests(unittest.TestCase):
    def test_le_defaut_est_documente_et_mesure_sans_modifier_les_scores(self):
        d = json.loads((DATA / "history" / "simulation-contre-signaux-2026-11-07.json")
                       .read_text(encoding="utf-8"))
        self.assertTrue(d["aucun_score_modifie"])
        self.assertGreater(d["fiches_avec_contre_signal_explicite"], 0)
        self.assertGreater(d["ecart_maximal_simule"], 0)
        self.assertTrue(d["protocole_requis_pour_corriger"])

    def test_les_fiches_a_contre_signaux_dominants_sont_marquees(self):
        crm = {r["company"]: r for r in CRM().records}
        for name in ("Delahautemaison", "ERM 27"):
            self.assertTrue(crm[name].get("revue_humaine_requise"), name)
            self.assertTrue(crm[name].get("revue_motif"), name)

    def test_les_axes_restant_en_v8_et_la_priorite_en_v9(self):
        for rec in CRM().records:
            self.assertEqual(rec["scores"]["engine_version"], "v8", rec["company"])
            self.assertEqual(rec["priority_engine_version"], "v9-priority", rec["company"])


class SecuritePhase10BisTests(unittest.TestCase):
    def test_les_envois_restant_bloques(self):
        st = json.loads((DATA / "campaigns" / "v4-settings.json").read_text(encoding="utf-8"))
        self.assertFalse(st["enabled"])
        self.assertTrue(st["dry_run"])

    def test_le_pref_vol_bloque_sur_un_domaine_gratuit(self):
        import shutil
        import tempfile
        from prospecto.sender import Sender
        target = Path(tempfile.mkdtemp()) / "s.json"
        shutil.copy(DATA / "campaigns" / "v4-settings.json", target)
        ok, reasons = Sender(settings_path=target).preflight()[:2]
        self.assertFalse(ok)
        self.assertTrue(any("gratuit" in r for r in reasons),
                        "le blocage de fond est le domaine d'envoi gratuit")
        self.assertTrue(any("DKIM" in r for r in reasons))

    def test_opposition_et_suppression_intactes(self):
        sup = json.loads((DATA / "suppression.json").read_text(encoding="utf-8"))
        mails = {e["email"] for e in sup["entries"]}
        self.assertIn("celarenarde@gmail.com", mails)
        self.assertEqual(sup["count"], 2)
        crm = {r["company"]: r for r in CRM().records}
        renarde = [r for r in crm.values() if r.get("status") == "opposition"]
        self.assertEqual(len(renarde), 1)

    def test_registre_et_portefeuille_restant_distincts(self):
        led = ExplorationLedger().entries
        crm = CRM().records
        self.assertGreater(len(led), len(crm),
                           "le registre contient les écartées, pas le portefeuille")
        self.assertTrue(any(e["decision"] == "écartée" for e in led))
        self.assertFalse(any(r.get("status") == "écartée" for r in crm))


if __name__ == "__main__":
    unittest.main()
