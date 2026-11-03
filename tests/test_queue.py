"""Tests de la file de validation et de l'export Gmail (brouillons only)."""
import json
import tempfile
import unittest
from pathlib import Path

from prospecto.models import GeneratedEmail
from prospecto.queue import ValidationQueue, PENDING, APPROVED, REJECTED, SENT
from prospecto.gmail_export import export_for_gmail, export_eml


def make_email(to="contact@exemple.fr"):
    return GeneratedEmail(
        to=to,
        subject="Une idée pour Exemple ?",
        body="Bonjour,\n\nUne démonstration personnalisée, gratuitement et sans engagement.\n",
        company="Exemple",
        need="refonte",
        evidence_sources=["https://exemple.fr"],
    )


class TestQueue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "queue.json"
        self.queue = ValidationQueue(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_starts_pending(self):
        item = self.queue.add(make_email(), "campagne-test")
        self.assertEqual(item.status, PENDING)
        self.assertEqual(item.id, "campagne-test-001")
        self.assertTrue(self.path.exists())

    def test_persistence(self):
        self.queue.add(make_email(), "campagne-test")
        reloaded = ValidationQueue(self.path)
        self.assertEqual(len(reloaded.items), 1)
        self.assertEqual(reloaded.items[0].company, "Exemple")

    def test_duplicate_same_campaign_rejected(self):
        self.queue.add(make_email(), "campagne-test")
        with self.assertRaises(ValueError):
            self.queue.add(make_email(), "campagne-test")

    def test_approve_then_mark_sent(self):
        item = self.queue.add(make_email(), "c")
        self.queue.approve(item.id)
        self.assertEqual(self.queue.get(item.id).status, APPROVED)
        self.queue.mark_sent(item.id, "msg-123")
        sent = self.queue.get(item.id)
        self.assertEqual(sent.status, SENT)
        self.assertEqual(sent.gmail_message_id, "msg-123")

    def test_cannot_send_without_approval(self):
        item = self.queue.add(make_email(), "c")
        with self.assertRaises(ValueError):
            self.queue.mark_sent(item.id)

    def test_cannot_reject_sent(self):
        item = self.queue.add(make_email(), "c")
        self.queue.approve(item.id)
        self.queue.mark_sent(item.id)
        with self.assertRaises(ValueError):
            self.queue.reject(item.id)

    def test_reject_with_reason(self):
        item = self.queue.add(make_email(), "c")
        self.queue.reject(item.id, "doublon secteur")
        self.assertEqual(self.queue.get(item.id).status, REJECTED)
        self.assertEqual(self.queue.get(item.id).decision_reason, "doublon secteur")

    def test_attach_draft(self):
        item = self.queue.add(make_email(), "c")
        self.queue.attach_draft(item.id, "r-42")
        self.assertEqual(self.queue.get(item.id).gmail_draft_id, "r-42")

    def test_history_traced(self):
        item = self.queue.add(make_email(), "c")
        self.queue.approve(item.id)
        actions = [h["action"] for h in self.queue.get(item.id).history]
        self.assertEqual(actions, ["created", APPROVED])

    def test_counts(self):
        self.queue.add(make_email("a@x.fr"), "c")
        item = self.queue.add(make_email("b@x.fr"), "c")
        self.queue.approve(item.id)
        counts = self.queue.counts()
        self.assertEqual(counts[PENDING], 1)
        self.assertEqual(counts[APPROVED], 1)


class TestGmailExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "queue.json"
        self.queue = ValidationQueue(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_export_only_approved_by_default(self):
        self.queue.add(make_email("pending@x.fr"), "c")
        item = self.queue.add(make_email("ok@x.fr"), "c")
        self.queue.approve(item.id)
        out = export_for_gmail(self.queue, Path(self.tmp.name) / "export.json")
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["drafts"][0]["to"], ["ok@x.fr"])
        self.assertIn("BROUILLONS", payload["purpose"])

    def test_eml_export(self):
        item = self.queue.add(make_email(), "c")
        self.queue.approve(item.id)
        paths = export_eml(self.queue, Path(self.tmp.name) / "eml")
        self.assertEqual(len(paths), 1)
        from email import message_from_bytes, policy
        msg = message_from_bytes(paths[0].read_bytes(), policy=policy.default)
        self.assertEqual(msg["Subject"], "Une idée pour Exemple ?")
        self.assertEqual(msg["To"], "contact@exemple.fr")
        self.assertIn("démonstration", msg.get_content())


if __name__ == "__main__":
    unittest.main()
