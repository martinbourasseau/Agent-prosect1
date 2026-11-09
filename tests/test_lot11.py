"""Lot 11 — garanties de la campagne de découverte du 09/11.

Ces tests ne figent pas les compteurs du portefeuille : ils vérifient les
invariants qui doivent rester vrais quand un lot s'ajoute (aucun écrasement,
trois axes indépendants et justifiés, brouillons conditionnés, aucun envoi).
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from prospecto.config import SUPPRESSION_PATH
from prospecto.crm import CRM
from prospecto.models import EVIDENCE_KINDS, Evidence, SIGNAL_LEVELS
from prospecto.messaging import check_email_v4, compose_email
from prospecto.models import Prospect
from prospecto.queue import ValidationQueue
from prospecto.scoring import AXES
from prospecto.sender import Sender
from prospecto.sources import ExplorationLedger

ROOT = Path(__file__).resolve().parents[1]
LOT = "2026-11-09-lot11"
CAMPAIGN = "2026-11-09-lot11"
RECHERCHES = ROOT / "data/history/lot11-recherches-2026-11-09.json"
IMPORT = ROOT / "data/history/lot11-import-2026-11-09.json"
BROUILLONS = ROOT / "data/history/lot11-brouillons-2026-11-09.json"


class RechercheLot11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = RECHERCHES.read_text(encoding="utf-8")
        cls.d = json.loads(cls.raw)
        cls.examined = cls.d["examined"]

    def test_la_recherche_a_reellement_ete_executee(self):
        """L'objectif annoncé était 60 à 80 structures examinées."""
        self.assertGreaterEqual(len(self.examined), 60)
        for entry in self.examined:
            self.assertTrue(entry["company"])
            self.assertTrue(entry["url"].startswith("http"), entry["company"])
            self.assertTrue(entry["note"], entry["company"])
            self.assertIn(entry["decision"],
                          ("retenue", "approfondir", "écartée", "annuaire_seul"))

    def test_chaque_structure_examinee_est_unique(self):
        names = [e["company"] for e in self.examined]
        self.assertEqual(len(names), len(set(names)))

    def test_la_couverture_est_multi_departements(self):
        deps = {e["department"] for e in self.examined if e["department"]}
        self.assertGreaterEqual(len(deps), 20)

    def test_les_annuaires_seuls_ne_sont_jamais_retenus(self):
        for entry in self.examined:
            if entry["decision"] == "retenue":
                self.assertNotEqual(entry["source_type"], "annuaire_seul")
            if entry["decision"] == "annuaire_seul":
                self.assertNotEqual(entry["decision"], "retenue")

    def test_les_constats_errones_ont_ete_corriges_et_traces(self):
        by = {e["company"]: e for e in self.examined}
        # MPO avait été crédité à tort d'une absence de formulaire.
        self.assertIn("CONSTAT CORRIGÉ", by["M.P.O. Mécanique Précision de l'Ouest"]["note"])
        self.assertEqual(by["M.P.O. Mécanique Précision de l'Ouest"]["decision"], "approfondir")
        self.assertIn("CONSTAT CORRIGÉ", by["La Conserverie des Producteurs"]["note"])
        self.assertIn("CONSTAT CORRIGÉ", by["Bureau Bois Concept"]["note"])

    def test_aucun_caractere_parasite(self):
        self.assertEqual(re.findall(r"[\u3000-\u9fff]", self.raw), [])

    def test_le_bloc_securite_ne_revendique_aucune_action_interdite(self):
        self.assertTrue(self.d["securite"])
        for key, value in self.d["securite"].items():
            self.assertIs(value, False, key)


class ImportLot11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = CRM().records
        cls.lot = [r for r in cls.records if r.get("lot") == LOT]
        cls.report = json.loads(IMPORT.read_text(encoding="utf-8"))

    def test_les_fiches_retenues_sont_importees(self):
        self.assertEqual(len(self.lot), 16)
        self.assertEqual(self.report["fiches_creees"], 16)
        self.assertEqual(self.report["collisions"], [])

    def test_les_trois_axes_sont_independants_et_justifies(self):
        for rec in self.lot:
            self.assertEqual(rec["scoring_version"], "v8")
            self.assertEqual(rec["scores"]["engine_version"], "v8")
            for axis in AXES:
                block = rec["scores"][axis]
                self.assertIn("score", block, rec["company"])
                self.assertTrue(0 <= block["score"] <= 100)
                self.assertTrue(block["reasons"], (rec["company"], axis))
            # Indépendance : un site en ligne ne doit pas donner un score de création.
            self.assertLessEqual(rec["scores"]["site_web"]["score"], 20, rec["company"])

    def test_chaque_preuve_est_valide_citee_et_datee(self):
        for rec in self.lot:
            self.assertTrue(rec["evidence"], rec["company"])
            for raw in rec["evidence"]:
                e = Evidence(**{k: v for k, v in raw.items()
                                if k in Evidence.__dataclass_fields__})
                self.assertEqual(e.validate(), [], (rec["company"], e.kind))
                self.assertIn(e.kind, EVIDENCE_KINDS)
                self.assertIn(e.signal_level, SIGNAL_LEVELS)
                self.assertTrue(e.source_url.startswith("http"))
                self.assertTrue(e.quote)
                self.assertEqual(e.verified_at, "2026-11-09")

    def test_les_entreprises_multi_domaines_ne_creent_qu_une_fiche(self):
        domains = [r["domain"] for r in self.lot]
        self.assertEqual(len(domains), len(set(domains)))
        self.assertNotIn("multi-pneus.fr", domains)
        self.assertNotIn("multi-pneus-36.fr", domains)
        self.assertNotIn("cs-depannages-reims.com", domains)

    def test_les_preuves_portent_les_domaines_alternatifs(self):
        rec = next(r for r in self.lot if r["company"] == "Multi Pneus 36")
        urls = " ".join(e["source_url"] for e in rec["evidence"])
        self.assertIn("multi-pneus.fr", urls)

    def test_une_adresse_publiee_est_toujours_controlee_en_dns(self):
        for rec in self.lot:
            if rec["email"]:
                self.assertEqual(rec["email_verification"], "verified")
                self.assertEqual(rec["email_dns_status"], "mx_ok")
                self.assertEqual(rec["email_dns_checked_at"], "2026-11-09")
                self.assertEqual(rec["email_provenance"], "publiee")
                self.assertIn("le MX ne prouve pas", rec["email_verification_basis"])
            else:
                self.assertEqual(rec["email_verification"], "none")
                self.assertIn("aucune adresse", rec["email_verification_basis"])

    def test_aucune_fiche_du_lot_n_est_marquee_contactee(self):
        brouillons = {b["company"] for b in
                      json.loads(BROUILLONS.read_text(encoding="utf-8"))["brouillons"]}
        for rec in self.lot:
            attendu = "brouillon_créé" if rec["company"] in brouillons else "nouveau"
            self.assertEqual(rec["status"], attendu, rec["company"])
            self.assertEqual(rec["email_status"], "non_contacté")
            self.assertFalse(rec.get("gmail_sent_message_id"))

    def test_chaque_fiche_du_lot_porte_son_historique_de_creation(self):
        for rec in self.lot:
            actions = [h.get("action") for h in rec.get("history", [])]
            self.assertIn("fiche_creee_lot11", actions, rec["company"])
            self.assertTrue(all(h.get("at") for h in rec["history"]))

    def test_la_priorite_est_transversale_et_versionnee(self):
        for rec in self.lot:
            self.assertEqual(rec["priority_engine_version"], "v10-priority")
            self.assertEqual(rec["commercial"]["value"], rec["commercial_value"])
            self.assertEqual(rec["commercial"]["tier"], rec["commercial_priority"])
            self.assertTrue(rec["commercial"]["reasons"])

    def test_les_contre_signaux_reduisent_la_priorite_sans_toucher_aux_axes(self):
        rec = next(r for r in self.lot if r["company"] == "Transports Bonnevialle")
        block = rec["commercial"]
        # EDI déjà en place : contre-signal fort, pénalité de 24 points.
        self.assertEqual(block["counter_signal_penalty"], 24)
        self.assertEqual(rec["commercial_priority"], "basse")
        self.assertEqual(rec["scores"]["refonte"]["score"], 81)
        self.assertTrue(any(d["strength"] == "fort"
                            for d in block["counter_signal_details"]))

    def test_un_besoin_exprime_verifie_reste_prioritaire(self):
        rec = next(r for r in self.lot if r["company"] == "Miditraçage Esvia")
        self.assertEqual(rec["commercial"]["signal_class"], "exprime_verifie")
        self.assertEqual(rec["commercial_priority"], "haute")
        # Le site est récent : l'axe refonte ne doit pas être gonflé.
        self.assertLess(rec["scores"]["refonte"]["score"],
                        rec["scores"]["ia_automatisation"]["score"])

    def test_une_offre_d_emploi_n_est_pas_une_intention_d_achat(self):
        from prospecto.discovery import analyse_page

        report = analyse_page(
            "Saisie et envoie des devis demandés. Suivi des relances factures clients. "
            "Classement et archivage. Contrat à pourvoir.",
            url="https://www.miditracage-esvia.com/actualites/2026/04/29/assistant-e-administratif-et-commercial-avignon/")
        # Un problème opérationnel n'est jamais une intention d'achat déclarée.
        for problem in report["problems"]:
            self.assertFalse(problem["proves_purchase_intent"], problem["kind"])

    def test_le_registre_a_absorbe_toutes_les_structures_examinees(self):
        ledger = ExplorationLedger()
        entries = [e for e in ledger.entries if e.get("lot") == LOT]
        researched = json.loads(RECHERCHES.read_text(encoding="utf-8"))["examined"]
        self.assertEqual(len(entries), len(researched))
        # Le registre est CUMULATIF : les lots suivants y ajoutent leurs
        # propres entrées. On vérifie que le lot 11 y est bien en entier et
        # que le total n'a pas régressé, jamais qu'il est resté figé à 213.
        self.assertGreaterEqual(len(ledger.entries), self.report["registre_apres"])
        noms_lot = {e.get("company") for e in entries}
        self.assertTrue({r["company"] for r in researched} <= noms_lot)


class BrouillonsLot11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(BROUILLONS.read_text(encoding="utf-8"))
        cls.drafts = cls.d["brouillons"]
        cls.lot = [r for r in CRM().records if r.get("lot") == LOT]

    def test_quatre_brouillons_et_pas_un_de_plus(self):
        self.assertEqual(len(self.drafts), 4)
        autorises = [r for r in self.lot if r.get("brouillon_autorise_lot11")]
        self.assertEqual({r["company"] for r in autorises},
                         {b["company"] for b in self.drafts})

    def test_la_regle_de_brouillon_est_appliquee_uniformement(self):
        for rec in self.lot:
            driving = rec["commercial"]["best_axis"]
            conf = rec["scores"][driving]["confidence"]
            attendu = bool(rec["commercial"]["contactable"]
                           and rec["commercial_priority"] == "haute"
                           and conf != "faible")
            self.assertEqual(rec["brouillon_autorise_lot11"], attendu, rec["company"])
            self.assertTrue(rec["brouillon_motif"], rec["company"])

    def test_les_sans_adresse_n_ont_aucun_brouillon(self):
        sans = [r for r in self.lot if not r["email"]]
        self.assertEqual(len(sans), 3)
        for rec in sans:
            self.assertFalse(rec["brouillon_autorise_lot11"])
            self.assertNotIn(rec["company"], {b["company"] for b in self.drafts})

    def test_une_confiance_faible_bloque_le_brouillon(self):
        for name in ("FMESURE", "Plast e-Concept", "SAS Adrien Fernandes D&S"):
            rec = next(r for r in self.lot if r["company"] == name)
            self.assertEqual(rec["commercial_priority"], "haute")
            self.assertFalse(rec["brouillon_autorise_lot11"], name)
            self.assertIn("confiance", rec["brouillon_motif"])

    def test_chaque_brouillon_est_conforme_au_controle_v4(self):
        for b in self.drafts:
            rec = next(r for r in self.lot if r["company"] == b["company"])
            evs = [Evidence(**{k: v for k, v in e.items()
                               if k in Evidence.__dataclass_fields__})
                   for e in rec["evidence"]]
            p = Prospect(company=rec["company"], domain=rec["domain"],
                         contact_email=rec["email"], sector=rec["sector"],
                         needs=rec["needs"], evidences=evs, website=rec["website"],
                         process_hint=rec["process_hint"], demo_detail=rec["demo_detail"],
                         custom_hook=rec["custom_hook"],
                         custom_subject=rec["custom_subject"],
                         observation=rec.get("observation", ""),
                         recommended_service=rec["recommended_service"],
                         email_verification=rec["email_verification"],
                         email_dns_status=rec["email_dns_status"])
            email = compose_email(p)
            self.assertEqual(check_email_v4(email, p), [], b["company"])
            self.assertEqual(email.body.strip(), b["body"].strip())
            self.assertEqual(email.subject, b["subject"])

    def test_les_limites_de_longueur_sont_respectees(self):
        for b in self.drafts:
            self.assertLessEqual(len(b["body"].split()), 167, b["company"])
            self.assertGreaterEqual(len(b["body"].split()), 40)
            self.assertLessEqual(len(b["subject"]), 70)
            self.assertNotEqual(b["subject"], "Une idée pour votre entreprise ?")

    def test_l_identite_et_la_signature_sont_exactes(self):
        for b in self.drafts:
            self.assertIn("Martin BOURASSEAU", b["body"])
            self.assertIn("Création de sites web · Refonte · Agents IA · Automatisation",
                          b["body"])
            self.assertIn("https://prospecto.website", b["body"])
            self.assertIn("ne pas me relancer", b["body"])

    def test_les_brouillons_sont_en_file_sans_etre_envoyes(self):
        items = ValidationQueue().items
        for b in self.drafts:
            item = next(i for i in items if i.id == b["queue_id"])
            self.assertEqual(item.campaign, CAMPAIGN)
            self.assertEqual(item.status, "pending")
            self.assertEqual(item.to, b["to"])
            self.assertEqual(item.gmail_draft_id, b["draft_id"])
            self.assertEqual(item.gmail_message_id, b["message_id"])
        self.assertFalse(self.d["envoi_autorise"])

    def test_aucun_destinataire_du_lot_n_est_dans_la_suppression(self):
        sup = json.loads(SUPPRESSION_PATH.read_text(encoding="utf-8"))
        interdits = {e["email"].lower() for e in sup["entries"]}
        for b in self.drafts:
            self.assertNotIn(b["to"].lower(), interdits)


class SecuriteLot11Tests(unittest.TestCase):
    """Le pré-vol doit rester bloqué, et le tester ne doit rien modifier."""

    def test_le_pre_vol_reste_bloque_sur_les_trois_motifs(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "v4-settings.json"
            shutil.copy(ROOT / "data/campaigns/v4-settings.json", tmp)
            before = tmp.read_bytes()
            ok, issues = Sender(settings_path=tmp).preflight()
            self.assertFalse(ok)
            self.assertEqual(len(issues), 3)
            joined = " ".join(issues)
            self.assertIn("enabled=false", joined)
            self.assertIn("DKIM", joined)
            self.assertIn("gratuit", joined)
            # Le contrôle persiste l'état DNS : il ne doit viser que la copie.
            self.assertNotEqual(tmp.read_bytes(), before)
        real = json.loads((ROOT / "data/campaigns/v4-settings.json").read_text(encoding="utf-8"))
        self.assertIs(real["enabled"], False)
        self.assertIs(real["dry_run"], True)

    def test_le_journal_d_envois_n_a_pas_bouge(self):
        from prospecto.outbound import load_outbound

        self.assertEqual(load_outbound().from_production, 60)

    def test_la_suppression_est_inchangee(self):
        sup = json.loads(SUPPRESSION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(sup["count"], 2)

    def test_les_fiches_anterieures_ont_garde_leurs_scores(self):
        report = json.loads(IMPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["fiches_anterieures_inchangees"], 92)
        # « Antérieures au lot 11 » est un instantané, pas « tout sauf le lot
        # 11 » : cette dernière formulation grossit à chaque nouveau lot et
        # figeait le portefeuille à 92.
        # L'invariant réel est une RÈGLE, pas un effectif : aucune fiche du
        # portefeuille ne doit changer de version d'axes. Le rapport d'import
        # garde la trace figée des 92 fiches vérifiées à cet instant ; le CRM,
        # lui, continue de croître à chaque lot.
        for rec in CRM().records:
            self.assertEqual(rec["scores"]["engine_version"], "v8", rec.get("company"))


if __name__ == "__main__":
    unittest.main()
