"""Tests du générateur : conformité v2 et garde-fous anti-dérive."""
import unittest

from prospecto.models import (
    Prospect, Evidence, GeneratedEmail,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
)
from prospecto.generator import generate_email, check_email, GenerationError
from prospecto import config


def prospect_refonte():
    return Prospect(
        company="Menuiserie Martin",
        domain="menuiserie-martin.fr",
        contact_email="contact@menuiserie-martin.fr",
        sector="batiment",
        needs=[NEED_REFONTE],
        evidences=[Evidence(
            EVIDENCE_WEBSITE_GAP, "http://menuiserie-martin.fr",
            "pas de formulaire", "2026-11-03",
            "Je n'ai trouvé aucun formulaire de contact ou de demande de devis sur les pages que j'ai ouvertes.",
        )],
    )


def prospect_public_need():
    return Prospect(
        company="Cabinet Leroy",
        domain="cabinet-leroy.fr",
        contact_email="bonjour@cabinet-leroy.fr",
        sector="architecture",
        contact_name="Sophie",
        needs=[NEED_SITE_WEB],
        evidences=[Evidence(
            EVIDENCE_PUBLIC_NEED, "https://linkedin.com/posts/leroy",
            "nous cherchons à créer notre site vitrine", "2026-10-30",
            "vous cherchiez à créer votre site vitrine (post LinkedIn du 30 octobre)",
        )],
    )


class TestGeneration(unittest.TestCase):
    def test_all_needs_generate_conforming_emails(self):
        for need in (NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION):
            p = prospect_public_need()
            p.needs = [need]
            p.process_hint = "vos demandes de devis"
            email = generate_email(p)
            self.assertEqual(check_email(email, p), [])
            self.assertEqual(email.need, need)

    def test_demo_is_central_and_limited(self):
        email = generate_email(prospect_refonte())
        self.assertIn("démonstration personnalisée", email.body)
        self.assertIn("gratuitement et sans engagement", email.body)
        self.assertIn("aperçu visuel", email.body)  # démo refonte, pas refonte complète

    def test_public_need_referenced_with_source(self):
        email = generate_email(prospect_public_need())
        self.assertIn("post LinkedIn du 30 octobre", email.body)
        self.assertIn("Bonjour Sophie,", email.body)

    def test_greeting_without_name(self):
        email = generate_email(prospect_refonte())
        self.assertTrue(email.body.startswith("Bonjour,"))

    def test_signature_v2_with_portfolio(self):
        email = generate_email(prospect_refonte())
        self.assertIn("Martin BOURASSEAU", email.body)
        self.assertIn("Création web · Agents IA · Automatisation", email.body)
        self.assertIn("https://prospecto.website", email.body)

    def test_opt_out_present(self):
        email = generate_email(prospect_refonte())
        self.assertIn("ne pas me relancer", email.body)

    def test_short_and_plain_text(self):
        email = generate_email(prospect_refonte())
        words = len(email.body.split())
        self.assertLessEqual(words, config.MAX_BODY_WORDS)
        self.assertGreaterEqual(words, config.MIN_BODY_WORDS)
        self.assertNotIn("**", email.body)

    def test_one_main_offer_only(self):
        p = prospect_public_need()
        p.needs = [NEED_AGENT_IA, NEED_AUTOMATISATION]
        email = generate_email(p)
        self.assertEqual(email.need, NEED_AGENT_IA)
        self.assertIn("agents IA", email.body)

    def test_demo_detail_personalizes_limited_offer(self):
        p = prospect_refonte()
        p.demo_detail = "un aperçu visuel d'amélioration de votre page d'accueil"
        email = generate_email(p)
        self.assertIn("votre page d'accueil", email.body)
        self.assertIn("gratuitement et sans engagement", email.body)
        self.assertEqual(check_email(email, p), [])

    def test_demo_detail_cannot_promise_full_build(self):
        p = prospect_refonte()
        p.demo_detail = "une refonte complète gratuite de votre site"
        with self.assertRaises(GenerationError):
            generate_email(p)

    def test_invalid_prospect_rejected(self):
        p = prospect_refonte()
        p.contact_email = "pas-un-email"
        with self.assertRaises(GenerationError):
            generate_email(p)

    def test_no_evidence_rejected(self):
        p = prospect_refonte()
        p.evidences = []
        with self.assertRaises(GenerationError):
            generate_email(p)


class TestGuardrails(unittest.TestCase):
    def test_forbidden_full_free_promise_detected(self):
        email = generate_email(prospect_refonte())
        email.body = email.body.replace(
            "un aperçu visuel d'amélioration d'une page clé de votre site",
            "une refonte complète gratuite de votre site",
        )
        problems = check_email(email)
        self.assertTrue(any("promesse interdite" in p for p in problems))

    def test_missing_demo_detected(self):
        email = generate_email(prospect_refonte())
        email.body = email.body.replace("démonstration", "présentation")
        self.assertTrue(any("démonstration" in p for p in check_email(email)))

    def test_missing_opt_out_detected(self):
        email = generate_email(prospect_refonte())
        email.body = email.body.replace("ne pas me relancer", "stop")
        self.assertTrue(any("opt-out" in p for p in check_email(email)))

    def test_claims_without_evidence_detected(self):
        p = prospect_refonte()
        email = generate_email(p)
        p.evidences = [Evidence(
            EVIDENCE_SECTOR_OPPORTUNITY, "https://x.fr", "secteur", "2026-11-03", "opportunité",
        )]
        self.assertTrue(any("sans preuve" in pr for pr in check_email(email, p)))


if __name__ == "__main__":
    unittest.main()
