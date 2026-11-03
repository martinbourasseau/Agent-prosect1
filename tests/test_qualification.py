"""Tests de qualification : barème, preuves obligatoires, dédoublonnage."""
import unittest

from prospecto.models import (
    Prospect, Evidence, NEED_REFONTE, NEED_SITE_WEB,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
)
from prospecto.qualification import (
    qualify, qualify_batch, load_contacted_emails,
    QUALIFIED, NOT_QUALIFIED, EXCLUDED, REVIEW,
)


def base_prospect(**kw):
    base = dict(
        company="Nouvelle Entreprise",
        domain="nouvelle-entreprise.fr",
        contact_email="contact@nouvelle-entreprise.fr",
        sector="services",
        needs=[NEED_REFONTE],
        evidences=[Evidence(
            EVIDENCE_WEBSITE_GAP, "http://nouvelle-entreprise.fr",
            "pas de HTTPS", "2026-11-03", "Le site ne s'affichait pas en HTTPS.",
        )],
    )
    base.update(kw)
    return Prospect(**base)


class TestQualification(unittest.TestCase):
    def test_public_need_qualifies(self):
        p = base_prospect(
            needs=[NEED_SITE_WEB],
            evidences=[Evidence(
                EVIDENCE_PUBLIC_NEED, "https://facebook.com/post/9",
                "cherche à créer son site", "2026-11-01",
                "vous cherchiez à créer votre site (Facebook, 1er novembre)",
            )],
        )
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, QUALIFIED)
        self.assertGreaterEqual(res.score, 50)

    def test_two_gaps_plus_sector_qualifies(self):
        p = base_prospect(evidences=[
            Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "https", "2026-11-03", "pas de HTTPS"),
            Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "form", "2026-11-03", "pas de formulaire"),
        ])
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, QUALIFIED)  # 40 (2 lacunes) + 10 secteur = 50
        self.assertGreaterEqual(res.score, 50)

    def test_no_evidence_not_qualified(self):
        p = base_prospect(evidences=[])
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, NOT_QUALIFIED)

    def test_invalid_email_not_qualified(self):
        p = base_prospect(contact_email="invalide")
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, NOT_QUALIFIED)

    def test_already_contacted_excluded(self):
        p = base_prospect(contact_email="contact@superchi.fr", domain="superchi.fr")
        res = qualify(p)  # historique réel du dépôt
        self.assertEqual(res.status, EXCLUDED)

    def test_history_loaded_from_repo(self):
        contacted = load_contacted_emails()
        self.assertIn("contact@superchi.fr", contacted)
        self.assertIn("multitech.assistance@gmail.com", contacted)
        self.assertEqual(len(contacted), 8)

    def test_batch_dedup(self):
        p1 = base_prospect()
        p2 = base_prospect(company="Copie Conforme")
        results = qualify_batch([p1, p2])
        self.assertEqual(results[1].status, EXCLUDED)

    def test_weak_signal_review(self):
        p = base_prospect(
            sector="secteur-inconnu",
            evidences=[
                Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "https", "2026-11-03", "pas de HTTPS"),
                Evidence(EVIDENCE_SECTOR_OPPORTUNITY, "https://x.fr", "devis par e-mail", "2026-11-03", "devis traités à la main"),
            ],
        )
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, REVIEW)  # 20 + 10 = 30, à revoir


if __name__ == "__main__":
    unittest.main()
