"""Tests CRM : fusion sans écrasement, dédoublonnage, preuves, stats."""
import tempfile
import unittest
from pathlib import Path

from prospecto.crm import CRM
from prospecto.models import Prospect, Evidence, NEED_REFONTE, EVIDENCE_PUBLIC_NEED


def prospect():
    return Prospect(
        company="Atelier CRM", domain="atelier-crm.fr",
        contact_email="contact@atelier-crm.fr", sector="batiment",
        needs=[NEED_REFONTE], city="Nantes", department="44",
        source="Codeur.com",
        evidences=[Evidence(EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/1",
                            "besoin refonte", "2026-11-03", "vous cherchez une refonte")],
    )


class TestCRM(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.crm = CRM(Path(self.tmp.name) / "crm.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_creates(self):
        rec, created = self.crm.import_prospect(prospect())
        self.assertTrue(created)
        self.assertEqual(rec["company"], "Atelier CRM")
        self.assertEqual(rec["tier"], "haute")
        self.assertEqual(rec["department"], "44")

    def test_merge_does_not_overwrite(self):
        self.crm.import_prospect(prospect())
        p2 = prospect()
        p2.city = "Paris"  # ne doit pas écraser Nantes
        p2.phone = "0102030405"  # champ vide → comblé
        rec, created = self.crm.import_prospect(p2)
        self.assertFalse(created)
        self.assertEqual(rec["city"], "Nantes")
        self.assertEqual(rec["phone"], "0102030405")

    def test_evidence_dedup_and_append(self):
        self.crm.import_prospect(prospect())
        p2 = prospect()
        p2.evidences = [
            Evidence(EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/1", "besoin refonte", "2026-11-03", "doublon"),
            Evidence(EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/2", "nouveau besoin", "2026-11-04", "nouvelle preuve"),
        ]
        rec, _ = self.crm.import_prospect(p2)
        self.assertEqual(len(rec["evidence"]), 2)

    def test_persistence(self):
        self.crm.import_prospect(prospect())
        self.crm.save()
        reloaded = CRM(self.crm.path)
        self.assertEqual(len(reloaded.records), 1)

    def test_dedup_by_domain(self):
        self.crm.import_prospect(prospect())
        p2 = prospect(); p2.company = "Autre Nom"; p2.contact_email = "autre@atelier-crm.fr"
        _, created = self.crm.import_prospect(p2)
        self.assertFalse(created)  # même domaine → fusion
        self.assertEqual(len(self.crm.records), 1)

    def test_stats(self):
        self.crm.import_prospect(prospect())
        stats = self.crm.stats()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["with_email"], 1)
        self.assertEqual(stats["expressed_needs"], 1)
        self.assertEqual(stats["by_tier"]["haute"], 1)


if __name__ == "__main__":
    unittest.main()
