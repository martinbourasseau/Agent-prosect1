"""Tests du lot 6 : réconciliation des envois hors agent, redirections d'accusés
automatiques, personnalisation des démonstrations et rotation des CTA.

Aucun accès réseau : tous les rapprochements se font sur des données en mémoire.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from prospecto.inbox_audit import (
    classify_inbound,
    extract_redirect_address,
    INTENT_AUTO_REPLY,
    INTENT_OPT_OUT,
    INTENT_HUMAN,
)
from prospecto.messaging import (
    CTA_DEMO_VARIANTS,
    check_email_v4,
    compose_email,
    select_cta_demo,
)
from prospecto.models import (
    Prospect,
    EVIDENCE_PROCESS_MANUAL,
    NEED_AUTOMATISATION,
)
from prospecto.reconcile import reconcile_sent, OBSERVED_SOURCE


class FakeQueueItem:
    def __init__(self, qid, to, subject, status="pending", campaign="lot-test"):
        self.id = qid
        self.to = to
        self.subject = subject
        self.status = status
        self.campaign = campaign
        self.updated_at = ""
        self.history = []
        self.gmail_message_id = ""


class FakeQueue:
    def __init__(self, items):
        self.items = items
        self.saved = False

    def save(self):
        self.saved = True


class FakeCRM:
    def __init__(self, records):
        self.records = records
        self.saved = False

    def save(self):
        self.saved = True


class FakeSendLog:
    def __init__(self):
        self.entries = []
        self.saved = False

    def record(self, **kwargs):
        self.entries.append(kwargs)

    def save(self):
        self.saved = True


def _prospect(company="Atelier Test", **kwargs):
    base = dict(
        company=company,
        sector="Artisanat",
        city="Nantes",
        department="44",
        website="https://exemple.fr/",
        domain="exemple.fr",
        custom_hook="Votre page contact ne propose qu'un e-mail libre pour demander un devis.",
        contact_email="contact@exemple.fr",
        needs=[NEED_AUTOMATISATION],
        evidences=[{"kind": EVIDENCE_PROCESS_MANUAL,
                    "source_url": "https://exemple.fr/contact",
                    "quote": "Les devis se font par e-mail.",
                    "observed_at": "2026-11-06"}],
    )
    base.update(kwargs)
    return Prospect.from_dict(base)


class RedirectAddressTests(unittest.TestCase):
    def test_adresse_de_remplacement_francaise(self):
        text = ("Cette adresse va bientot disparaitre. Pour toute demande, merci désormais "
                "d'utiliser l'adresse suivante:\nb3r@gallia28.fr\nBien cordialement,")
        self.assertEqual(extract_redirect_address(text, "contact@ancien.fr"), "b3r@gallia28.fr")

    def test_nouvelle_adresse_explicite(self):
        self.assertEqual(extract_redirect_address("Notre nouvelle adresse : siege@groupe.fr"),
                         "siege@groupe.fr")

    def test_formulation_anglaise(self):
        self.assertEqual(extract_redirect_address("Please now use hello@newdomain.com"),
                         "hello@newdomain.com")

    def test_pas_de_redirection(self):
        self.assertEqual(extract_redirect_address("Votre demande a bien été prise en compte."), "")

    def test_ne_renvoie_pas_l_expediteur(self):
        self.assertEqual(
            extract_redirect_address("adresse suivante : contact@ancien.fr", "contact@ancien.fr"), "")

    def test_ignore_les_adresses_generiques_de_role(self):
        self.assertEqual(extract_redirect_address("adresse suivante : no-reply@exemple.fr"), "")

    def test_accuse_avec_redirection_reste_un_accuse(self):
        verdict = classify_inbound(
            from_email="contact@blanchisseriedes3regions.fr",
            subject="Réponse automatique : votre site",
            text="Cette adresse va bientot disparaitre, merci désormais d'utiliser l'adresse "
                 "suivante: b3r@gallia28.fr",
        )
        self.assertEqual(verdict["intent"], INTENT_AUTO_REPLY)


class OptOutTests(unittest.TestCase):
    def test_ne_pas_me_relancer_est_une_opposition(self):
        verdict = classify_inbound(
            from_email="celarenarde@gmail.com",
            subject="Re: automatiser les inscriptions ?",
            text="Ne pas me relancer\n\nSmets Nicolas\nCentre Equestre de la Renarde",
        )
        self.assertEqual(verdict["intent"], INTENT_OPT_OUT)

    def test_une_vraie_question_reste_une_reponse_humaine(self):
        verdict = classify_inbound(
            from_email="client@exemple.fr",
            subject="Re: votre message",
            text="Bonjour, quels sont vos délais pour mettre cela en place ? Merci.",
        )
        self.assertEqual(verdict["intent"], INTENT_HUMAN)


class ReconcileSentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.path = Path(self.tmp.name) / "reconciliations.json"
        self.addCleanup(self.tmp.cleanup)
        self.item = FakeQueueItem("lot-001", "Contact@Exemple.fr", "Objet exact")
        self.queue = FakeQueue([self.item])
        self.record = {"company": "Exemple", "email": "contact@exemple.fr",
                       "status": "brouillon_créé", "email_status": "brouillon_créé",
                       "next_action": "Créer le brouillon Gmail"}
        self.crm = FakeCRM([self.record])
        self.log = FakeSendLog()
        self.obs = [{"to": "contact@exemple.fr", "subject": "Objet exact",
                     "gmail_message_id": "msg-1", "gmail_thread_id": "thr-1",
                     "sent_at": "2026-11-05T14:34:00+01:00"}]

    def _run(self, observed=None):
        import prospecto.reconcile as rec
        original = rec.RECONCILE_PATH
        rec.RECONCILE_PATH = self.path
        try:
            return reconcile_sent(observed if observed is not None else self.obs,
                                  self.crm, self.queue, self.log)
        finally:
            rec.RECONCILE_PATH = original

    def test_brouillon_passe_a_envoye(self):
        result = self._run()
        self.assertEqual(result.matched, 1)
        self.assertEqual(self.item.status, "sent")
        self.assertEqual(self.record["status"], "contacté")
        self.assertEqual(self.record["email_status"], "envoyé")
        self.assertEqual(self.record["send_source"], OBSERVED_SOURCE)

    def test_preuve_conservee(self):
        self._run()
        self.assertEqual(self.item.gmail_message_id, "msg-1")
        self.assertEqual(self.item.gmail_thread_id, "thr-1")
        self.assertEqual(self.record["sent_at"], "2026-11-05T14:34:00+01:00")
        self.assertTrue(any(h["action"] == "reconciled_sent" for h in self.item.history))

    def test_historique_jamais_ecrase(self):
        self.item.history.append({"action": "created"})
        self._run()
        self.assertEqual(len(self.item.history), 2)

    def test_idempotent(self):
        self._run()
        again = self._run()
        self.assertEqual(again.matched, 0)
        self.assertEqual(again.already_sent, 1)
        self.assertEqual(len(self.log.entries), 1)

    def test_statut_avance_jamais_retrograde(self):
        for advanced in ("opposition", "rebond", "refus", "demande_rdv"):
            self.item.status = "pending"
            self.record["status"] = advanced
            self._run()
            self.assertEqual(self.record["status"], advanced)

    def test_destinataire_inconnu_signale(self):
        result = self._run([{"to": "inconnu@autre.fr", "subject": "X"}])
        self.assertEqual(result.matched, 0)
        self.assertEqual(len(result.unmatched), 1)

    def test_rapprochement_insensible_a_la_casse(self):
        self.obs[0]["to"] = "CONTACT@EXEMPLE.FR"
        self.assertEqual(self._run().matched, 1)

    def test_objet_different_ne_rapproche_pas(self):
        self.obs[0]["subject"] = "Autre objet"
        self.obs[0]["gmail_message_id"] = ""
        self.assertEqual(self._run().matched, 0)

    def test_sauvegardes_declenchees(self):
        self._run()
        self.assertTrue(self.queue.saved and self.crm.saved and self.log.saved)

    def test_journal_horodate(self):
        self._run()
        self.assertEqual(self.log.entries[0]["source"], OBSERVED_SOURCE)
        self.assertEqual(self.log.entries[0]["status"], "sent")


class DemoPhraseTests(unittest.TestCase):
    def test_detail_personnalise_utilise_meme_pour_l_automatisation(self):
        p = _prospect(demo_detail="démo du formulaire buffet avec délai de 72 h")
        body = compose_email(p, "automation_ia").body
        self.assertIn("démo du formulaire buffet avec délai de 72 h", body)

    def test_repli_generique_sans_detail(self):
        body = compose_email(_prospect(demo_detail=""), "automation_ia").body
        self.assertIn("sans engagement", body)
        self.assertTrue("démonstration" in body or "maquette" in body)

    def test_message_reste_conforme_avec_detail(self):
        p = _prospect(demo_detail="démo d'une demande de location avec dates")
        self.assertEqual(check_email_v4(compose_email(p, "synatrap_ia"), p), [])


class CtaRotationTests(unittest.TestCase):
    def test_cta_stable_pour_une_meme_entreprise(self):
        p = _prospect("Entreprise Stable")
        self.assertEqual(select_cta_demo(p), select_cta_demo(p))

    def test_cta_toujours_dans_le_jeu_autorise(self):
        for name in ("A", "B", "C", "Celtuce Traiteur", "SAS Maire", "Joly Location"):
            self.assertIn(select_cta_demo(_prospect(name)), CTA_DEMO_VARIANTS)

    def test_au_moins_deux_cta_sur_un_lot(self):
        names = ["Celtuce Traiteur", "Mamie Cuisine Traiteur", "Baptiste Break",
                 "SARL Joly Location", "SARL Uzès Location", "Techniques Piscine"]
        self.assertGreaterEqual(len({select_cta_demo(_prospect(n)) for n in names}), 2)

    def test_au_moins_trois_formulations_disponibles(self):
        # v5 (lot 7) : le jeu est passé de 3 à 7 appels à l'action distincts.
        self.assertGreaterEqual(len(CTA_DEMO_VARIANTS), 3)
        self.assertEqual(len(set(CTA_DEMO_VARIANTS)), len(CTA_DEMO_VARIANTS))

    def test_cta_present_dans_le_corps(self):
        p = _prospect("Entreprise CTA")
        self.assertIn(select_cta_demo(p), compose_email(p, "automation_ia").body)


class SignatureTests(unittest.TestCase):
    def test_identite_exacte_dans_chaque_variante(self):
        for variant in ("automation_ia", "refonte", "synatrap_ia", "with_example",
                        "demo_site", "short_hook"):
            body = compose_email(_prospect(), variant).body
            self.assertIn("Martin BOURASSEAU", body)
            self.assertNotIn("boisseau", body.lower())
            self.assertIn("https://prospecto.website", body)
            self.assertIn("ne pas me relancer", body)


if __name__ == "__main__":
    unittest.main()


class MergeInboundTests(unittest.TestCase):
    """Le bloc « replies » doit refléter l'audit de boîte, sans double compte."""

    def test_audit_seul_compte_les_oppositions(self):
        from prospecto.metrics import merge_inbound
        merged = merge_inbound([], [{"message_id": "m1", "intent": "opposition"}])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["intent"], "opposition")

    def test_pas_de_double_compte_sur_le_meme_message(self):
        from prospecto.metrics import merge_inbound
        replies = [{"message_id": "m1", "intent": "opposition"}]
        audit = [{"message_id": "m1", "intent": "opposition"}]
        self.assertEqual(len(merge_inbound(replies, audit)), 1)

    def test_repli_sur_expediteur_et_objet(self):
        from prospecto.metrics import merge_inbound
        a = [{"from": "x@y.fr", "subject": "Re: bonjour", "intent": "opposition"}]
        b = [{"from_email": "X@Y.fr", "subject": "Re: bonjour", "intent": "opposition"}]
        self.assertEqual(len(merge_inbound(a, b)), 1)

    def test_messages_distincts_tous_conserves(self):
        from prospecto.metrics import merge_inbound
        audit = [{"message_id": "m1", "intent": "auto_reply"},
                 {"message_id": "m2", "intent": "rebond"},
                 {"message_id": "m3", "intent": "opposition"}]
        self.assertEqual(len(merge_inbound([], audit)), 3)

    def test_listes_vides(self):
        from prospecto.metrics import merge_inbound
        self.assertEqual(merge_inbound([], []), [])
