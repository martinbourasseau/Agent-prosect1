"""Tests générateur v3 : conformité, garde-fous, anti-invention, whitelist exemples."""
import json
import tempfile
import unittest
from pathlib import Path

from prospecto import config
from prospecto.models import (
    Prospect, Evidence,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
)
from prospecto.generator import generate_email, check_email, GenerationError


def prospect_refonte():
    return Prospect(
        company="Menuiserie Martin", domain="menuiserie-martin.fr",
        contact_email="contact@menuiserie-martin.fr", sector="batiment",
        needs=[NEED_REFONTE],
        evidences=[Evidence(
            EVIDENCE_WEBSITE_GAP, "http://menuiserie-martin.fr", "pas de formulaire", "2026-11-03",
            "je n'ai trouvé aucun formulaire de contact ou de demande de devis sur les pages ouvertes.",
        )],
    )


def prospect_public_need():
    return Prospect(
        company="Cabinet Leroy", domain="cabinet-leroy.fr",
        contact_email="bonjour@cabinet-leroy.fr", sector="architecture", contact_name="Sophie",
        needs=[NEED_SITE_WEB],
        evidences=[Evidence(
            EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/leroy",
            "nous cherchons à créer notre site vitrine", "2026-10-30",
            "vous cherchez à créer votre site vitrine (Codeur.com, 30 octobre)",
        )],
    )


class TestGeneration(unittest.TestCase):
    def test_all_needs_conforming(self):
        for need in (NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION):
            p = prospect_public_need()
            p.needs = [need]
            p.process_hint = "vos demandes de devis"
            email = generate_email(p)
            self.assertEqual(check_email(email, p), [])
            self.assertEqual(email.need, need)

    def test_demo_central_and_limited(self):
        email = generate_email(prospect_refonte())
        self.assertIn("démonstration personnalisée", email.body)
        self.assertIn("gratuitement", email.body)
        self.assertIn("sans engagement", email.body)
        self.assertIn("direction graphique", email.body)

    def test_public_need_referenced(self):
        email = generate_email(prospect_public_need())
        self.assertIn("votre site vitrine", email.body)
        self.assertIn("Bonjour Sophie,", email.body)

    def test_greeting_without_name(self):
        self.assertTrue(generate_email(prospect_refonte()).body.startswith("Bonjour,"))

    def test_signature_portfolio(self):
        email = generate_email(prospect_refonte())
        self.assertIn("Martin BOURASSEAU", email.body)
        self.assertIn("https://prospecto.website", email.body)

    def test_opt_out(self):
        self.assertIn("ne pas me relancer", generate_email(prospect_refonte()).body)

    def test_short_plain_text(self):
        email = generate_email(prospect_refonte())
        words = len(email.body.split())
        self.assertLessEqual(words, config.MAX_BODY_WORDS)
        self.assertGreaterEqual(words, config.MIN_BODY_WORDS)
        self.assertNotIn("**", email.body)

    def test_single_offer(self):
        p = prospect_public_need()
        p.needs = [NEED_AGENT_IA, NEED_AUTOMATISATION]
        email = generate_email(p)
        self.assertEqual(email.need, NEED_AGENT_IA)
        self.assertIn("agents IA", email.body)

    def test_invalid_prospect_rejected(self):
        p = prospect_refonte(); p.contact_email = "pas-un-email"
        with self.assertRaises(GenerationError):
            generate_email(p)

    def test_no_evidence_rejected(self):
        p = prospect_refonte(); p.evidences = []
        with self.assertRaises(GenerationError):
            generate_email(p)

    def test_demo_detail_personalizes(self):
        p = prospect_refonte()
        p.demo_detail = "un aperçu visuel de votre page d'accueil repensée"
        email = generate_email(p)
        self.assertIn("votre page d'accueil repensée", email.body)
        self.assertEqual(check_email(email, p), [])

    def test_demo_detail_cannot_promise_full(self):
        p = prospect_refonte(); p.demo_detail = "une refonte complète gratuite de votre site"
        with self.assertRaises(GenerationError):
            generate_email(p)


class TestExampleWhitelist(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig = config.REALISATIONS_PATH
        config.REALISATIONS_PATH = Path(self.tmp.name) / "realisations.json"

    def tearDown(self):
        config.REALISATIONS_PATH = self.orig
        self.tmp.cleanup()

    def _write_whitelist(self, urls):
        config.REALISATIONS_PATH.write_text(json.dumps(
            {"realisations": [{"url": u} for u in urls]}), encoding="utf-8")

    def test_non_whitelisted_example_rejected(self):
        self._write_whitelist([])
        p = prospect_refonte(); p.example_urls = ["https://exemple-invente.fr"]
        with self.assertRaises(GenerationError):
            generate_email(p)

    def test_whitelisted_example_included(self):
        self._write_whitelist(["https://realisation-validée.fr"])
        p = prospect_refonte(); p.example_urls = ["https://realisation-validée.fr"]
        email = generate_email(p)
        self.assertIn("https://realisation-validée.fr", email.body)
        self.assertEqual(check_email(email, p), [])

    def test_no_example_by_default(self):
        p = prospect_refonte()
        email = generate_email(p)
        self.assertNotIn("Un exemple de ce que je réalise", email.body)


class TestGuardrails(unittest.TestCase):
    def test_missing_demo_detected(self):
        email = generate_email(prospect_refonte())
        email.body = email.body.replace("démonstration", "présentation")
        self.assertTrue(any("démonstration" in x for x in check_email(email)))

    def test_missing_opt_out_detected(self):
        email = generate_email(prospect_refonte())
        email.body = email.body.replace("ne pas me relancer", "stop")
        self.assertTrue(any("opt-out" in x for x in check_email(email)))

    def test_hook_annonce_without_evidence_detected(self):
        p = prospect_refonte()
        email = generate_email(p)
        email.body = email.body.replace("En parcourant", "J'ai lu votre annonce. En parcourant")
        self.assertTrue(any("annonce" in x for x in check_email(email, p)))


if __name__ == "__main__":
    unittest.main()
