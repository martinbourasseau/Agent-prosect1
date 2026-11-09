"""Phase 10 finale — consolidation des messages sortis (dashboard à 68).

Couvre explicitement les cas demandés : les 8 rapprochements, les messages
présents dans les deux journaux, les doublons d'identifiants, les messages sans
identité exploitable, les anciens lots et les rapprochements répétés.
"""
from __future__ import annotations

import hashlib
import json
import unittest

from prospecto import config
from prospecto.crm import CRM
from prospecto.metrics import compute_metrics, pipeline_categories
from prospecto.outbound import (
    ORIGIN_PRODUCTION,
    ORIGIN_RECONCILIATION,
    consolidate_outbound,
    load_outbound,
)


def entry(mid, to="a@exemple.fr", subject="Objet", **kw):
    return {"status": "sent", "gmail_message_id": mid, "to": to,
            "subject": subject, "at": "2026-11-04T10:00:00+00:00", **kw}


def recon(companies=(), sent_messages=(), at="2026-11-07"):
    return {"at": at, "updated_companies": list(companies),
            "sent_messages": list(sent_messages), "matched": len(companies)}


class ConsolidationSyntheticTests(unittest.TestCase):
    def test_un_rapprochement_neuf_ajoute_un_message(self):
        out = consolidate_outbound(
            [entry("prod-1")],
            [recon(sent_messages=[{"company": "B", "gmail_message_id": "sent-2"}])],
            [{"company": "B", "email": "b@exemple.fr"}])
        self.assertEqual(out.total, 2)
        self.assertEqual(out.from_production, 1)
        self.assertEqual(out.from_reconciliation, 1)

    def test_message_present_dans_les_deux_journaux_compte_une_fois(self):
        out = consolidate_outbound(
            [entry("meme-id")],
            [recon(sent_messages=[{"company": "A", "gmail_message_id": "meme-id"}])], [])
        self.assertEqual(out.total, 1)
        self.assertEqual(len(out.duplicates), 1)
        self.assertIn("deja compte", out.duplicates[0].reason)

    def test_doublon_d_identifiant_dans_le_journal_de_production(self):
        out = consolidate_outbound([entry("dup"), entry("dup")], [], [])
        self.assertEqual(out.total, 1)
        self.assertEqual(len(out.duplicates), 1)

    def test_rapprochements_repetes_ne_cumulent_pas(self):
        r = recon(sent_messages=[{"company": "B", "gmail_message_id": "s1"}])
        out = consolidate_outbound([entry("p1")], [r, r, r],
                                   [{"company": "B", "email": "b@exemple.fr"}])
        self.assertEqual(out.total, 2, "trois rapprochements du même message = un message")
        self.assertEqual(len(out.duplicates), 2)

    def test_deux_messages_d_identifiants_distincts_a_la_meme_adresse(self):
        """Deux lots peuvent écrire deux fois à la même adresse : ce sont deux
        messages réels. Dédoublonner sur l'adresse effacerait un envoi."""
        out = consolidate_outbound([
            entry("id-1", to="same@exemple.fr", campaign="lot1"),
            entry("id-2", to="same@exemple.fr", campaign="lot2"),
        ], [], [])
        self.assertEqual(out.total, 2)
        self.assertEqual(len({m.gmail_message_id for m in out.messages}), 2)

    def test_brouillon_et_message_envoye_partageant_le_fil(self):
        """Gmail attribue un nouvel identifiant au message envoyé mais garde le
        fil : sans cette règle le même envoi serait compté deux fois."""
        out = consolidate_outbound(
            [entry("draft-msg", gmail_thread_id="fil-1")],
            [recon(sent_messages=[{"company": "A", "gmail_message_id": "sent-msg",
                                   "gmail_thread_id": "fil-1"}])], [])
        self.assertEqual(out.total, 1)

    def test_ancien_rapprochement_sans_identifiant_ne_cree_pas_d_envoi(self):
        """Un rapprochement qui ne nomme qu'une entreprise déjà journalisée
        désigne un message existant : il ne doit rien ajouter."""
        out = consolidate_outbound(
            [entry("p1", to="a@exemple.fr")],
            [recon(companies=["A"])],
            [{"company": "A", "email": "a@exemple.fr"}])
        self.assertEqual(out.total, 1)
        self.assertEqual(len(out.duplicates), 1)
        self.assertIn("deja presente", out.duplicates[0].reason)

    def test_entreprise_sans_identifiant_ni_trace_reste_non_attribuable(self):
        out = consolidate_outbound([], [recon(companies=["Inconnue"])], [])
        self.assertEqual(out.total, 0, "ajouter serait inventer un envoi")
        self.assertEqual(len(out.unattributed), 1)

    def test_repli_sur_reference_de_file_pour_les_anciens_lots(self):
        out = consolidate_outbound(
            [{"status": "sent", "queue_id": "2026-11-03-v2-001", "to": "x@exemple.fr"}],
            [], [])
        self.assertEqual(out.total, 1)
        self.assertEqual(out.messages[0].identity_basis, "queue_id")

    def test_repli_sur_adresse_et_objet(self):
        out = consolidate_outbound(
            [{"status": "sent", "to": "x@exemple.fr", "subject": "Bonjour"}], [], [])
        self.assertEqual(out.messages[0].identity_basis, "adresse_objet")

    def test_message_sans_aucune_identite_est_conserve_et_signale(self):
        out = consolidate_outbound([{"status": "sent"}, {"status": "sent"}], [], [])
        self.assertEqual(out.total, 2, "sans preuve de doublon, ne pas fusionner")
        self.assertTrue(all(m.weak_identity for m in out.messages))
        self.assertEqual(out.summary()["identites_faibles"], 2)

    def test_les_statuts_non_sortants_sont_ignores(self):
        out = consolidate_outbound(
            [entry("p1"), {"status": "dry_run", "gmail_message_id": "dry"},
             {"status": "failed", "gmail_message_id": "ko"}], [], [])
        self.assertEqual(out.total, 1)

    def test_acceptation_n_est_pas_remise(self):
        out = consolidate_outbound([entry("p1"), {"status": "sent", "queue_id": "q2"}], [], [])
        self.assertEqual(out.total, 2)
        self.assertEqual(out.accepted_by_provider, 1,
                         "seul un identifiant fournisseur prouve l'acceptation")

    def test_entree_vide(self):
        out = consolidate_outbound([], [], [])
        self.assertEqual(out.total, 0)
        self.assertEqual(out.summary()["doublons_ecartes"], 0)


class ConsolidationRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = CRM().records
        cls.out = load_outbound(cls.records)

    def test_total_reel_est_68(self):
        self.assertEqual(self.out.total, 68)
        self.assertEqual(self.out.from_production, 60)
        self.assertEqual(self.out.from_reconciliation, 8)

    def test_les_37_rapprochements_anciens_sont_des_doublons(self):
        """15 + 8 + 14 entreprises déjà journalisées : les additionner aurait
        donné 97 messages au lieu de 68."""
        self.assertEqual(len(self.out.duplicates), 37)
        self.assertEqual(self.out.unattributed, [])

    def test_les_huit_identifiants_reconcilies_sont_presents(self):
        audit = json.loads((config.DATA_DIR / "history" /
                            "audit-gmail-phase10bis-2026-11-07.json").read_text(encoding="utf-8"))
        ids = {m.gmail_message_id for m in self.out.messages
               if m.origin == ORIGIN_RECONCILIATION}
        self.assertEqual(ids, {e["sent_message_id"] for e in audit["envois_hors_agent"]})

    def test_les_deux_messages_de_meme_adresse_sont_preserves(self):
        for mail in ("contact@renovationpremium.com", "secteur72fr@gmail.com"):
            got = [m for m in self.out.messages if m.to == mail]
            self.assertEqual(len(got), 2, mail)
            self.assertEqual(len({m.gmail_message_id for m in got}), 2, mail)

    def test_tous_les_messages_ont_une_identite_forte(self):
        self.assertEqual(self.out.summary()["identites_faibles"], 0)
        self.assertTrue(all(m.identity_basis == "gmail_message_id" for m in self.out.messages))

    def test_la_consolidation_n_ecrit_aucun_journal(self):
        paths = [config.SEND_LOG_PATH,
                 config.DATA_DIR / "history" / "reconciliations.json"]
        before = {p: hashlib.md5(p.read_bytes()).hexdigest() for p in paths}
        load_outbound(self.records)
        consolidate_outbound([], [], [])
        after = {p: hashlib.md5(p.read_bytes()).hexdigest() for p in paths}
        self.assertEqual(before, after, "la consolidation est en lecture seule")


class DashboardCoherenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = compute_metrics()

    def test_le_dashboard_annonce_68_messages_sortis(self):
        self.assertEqual(self.m["pipeline"]["envoyes"], 68)
        self.assertEqual(self.m["deliverability"]["sent"], 68)

    def test_la_provenance_est_exposee(self):
        ob = self.m["outbound"]
        self.assertEqual(ob["total"], 68)
        self.assertEqual(ob["journal_production"], 60)
        self.assertEqual(ob["rapproches"], 8)
        self.assertEqual(ob["doublons_ecartes"], 37)

    def test_les_onze_categories_demandees_sont_presentes(self):
        p = self.m["pipeline"]
        for key in ("messages_prepares", "brouillons", "envoyes",
                    "acceptes_par_fournisseur", "delivres_confirmes",
                    "delivrance_non_confirmee", "rebonds", "challenges_delivrance",
                    "reponses_humaines", "reponses_automatiques", "oppositions"):
            self.assertIn(key, p)

    def test_les_categories_de_delivrance_se_somment_au_total(self):
        p = self.m["pipeline"]
        self.assertTrue(p["controle_exclusif"])
        self.assertEqual(p["delivres_confirmes"] + p["delivrance_non_confirmee"]
                         + p["rebonds"] + p["challenges_delivrance"], p["envoyes"])

    def test_les_deux_vues_partagent_la_meme_definition_du_non_confirme(self):
        """Elles affichaient 56 et 55 pour la même réalité."""
        self.assertEqual(self.m["deliverability"]["delivery_unconfirmed"],
                         self.m["pipeline"]["delivrance_non_confirmee"])
        self.assertEqual(self.m["pipeline"]["delivrance_non_confirmee"], 63)

    def test_un_message_envoye_n_est_jamais_compte_comme_delivre(self):
        p = self.m["pipeline"]
        self.assertEqual(p["delivres_confirmes"], 3)
        self.assertLess(p["delivres_confirmes"], p["envoyes"])
        self.assertEqual(p["acceptes_par_fournisseur"], 68,
                         "acceptation ≠ remise : les 68 sont acceptés, 3 prouvés remis")

    def test_il_reste_deux_brouillons_apres_synchronisation_de_la_file(self):
        p = self.m["pipeline"]
        self.assertEqual(p["brouillons"], 2)
        self.assertEqual(p["en_attente"], 1)

    def test_la_file_garde_l_historique_des_huit_envois_externes(self):
        from prospecto.queue import ValidationQueue
        items = ValidationQueue().items
        found = [i for i in items
                 if any(h.get("action") == "external_send_reconciled" for h in i.history)]
        self.assertEqual(len(found), 8)
        for i in found:
            self.assertEqual(i.status, "sent")
            h = next(h for h in i.history if h["action"] == "external_send_reconciled")
            self.assertTrue(h["gmail_sent_message_id"])
            self.assertIn(h["status_before"], ("draft", "pending"))

    def test_pipeline_sur_donnees_synthétiques_sans_consolidation(self):
        d = {"sent": 10, "delivery_confirmed": 2, "hard_bounces": 1, "soft_bounces": 0,
             "delivery_challenges": 1, "human_replies": 1, "auto_replies": 0, "opt_outs": 0}
        p = pipeline_categories({"deliverability": d}, [])
        self.assertEqual(p["envoyes"], 10)
        self.assertEqual(p["delivrance_non_confirmee"], 6)
        self.assertTrue(p["controle_exclusif"])


if __name__ == "__main__":
    unittest.main()
