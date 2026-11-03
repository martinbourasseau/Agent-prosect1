"""Tests qualification v3 : barème, niveaux de priorité, dédoublonnage."""
import unittest

from prospecto.models import (
    Prospect, Evidence, NEED_REFONTE, NEED_SITE_WEB,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
)
from prospecto.qualification import (
    qualify, qualify_batch, load_contacted_emails,
    QUALIFIED, NOT_QUALIFIED, EXCLUDED, REVIEW,
)
from prospecto.config import TIER_HAUTE, TIER_MOYENNE, TIER_A_APPROFONDIR


def base_prospect(**kw):
    base = dict(
        company="Nouvelle Entreprise", domain="nouvelle-entreprise.fr",
        contact_email="contact@nouvelle-entreprise.fr", sector="services",
        needs=[NEED_REFONTE],
        evidences=[Evidence(
            EVIDENCE_WEBSITE_GAP, "http://nouvelle-entreprise.fr",
            "pas de HTTPS", "2026-11-03", "Le site ne s'affichait pas en HTTPS.",
        )],
    )
    base.update(kw)
    return Prospect(**base)


class TestQualification(unittest.TestCase):
    def test_public_need_haute(self):
        p = base_prospect(needs=[NEED_SITE_WEB], evidences=[Evidence(
            EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/9",
            "cherche à créer son site", "2026-11-01", "vous cherchez à créer votre site",
        )])
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.tier, TIER_HAUTE)
        self.assertEqual(res.status, QUALIFIED)
        self.assertGreaterEqual(res.score, 50)

    def test_two_gaps_moyenne(self):
        p = base_prospect(evidences=[
            Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "https", "2026-11-03", "pas de HTTPS"),
            Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "form", "2026-11-03", "pas de formulaire"),
        ])
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.tier, TIER_MOYENNE)
        self.assertEqual(res.status, REVIEW)
        self.assertGreaterEqual(res.score, 50)

    def test_no_evidence_not_qualified(self):
        p = base_prospect(evidences=[])
        res = qualify(p, contacted_emails=set(), contacted_domains=set())
        self.assertEqual(res.status, NOT_QUALIFIED)
        self.assertEqual(res.tier, TIER_A_APPROFONDIR)

    def test_invalid_email(self):
        p = base_prospect(contact_email="invalide")
        self.assertEqual(qualify(p, set(), set()).status, NOT_QUALIFIED)

    def test_already_contacted_excluded(self):
        p = base_prospect(contact_email="contact@superchi.fr", domain="superchi.fr")
        self.assertEqual(qualify(p).status, EXCLUDED)

    def test_history_loaded(self):
        contacted = load_contacted_emails()
        self.assertIn("contact@superchi.fr", contacted)
        self.assertEqual(len(contacted), 8)

    def test_batch_dedup(self):
        results = qualify_batch([base_prospect(), base_prospect(company="Copie Conforme")])
        self.assertEqual(results[1].status, EXCLUDED)

    def test_weak_signal_moyenne_not_rejected(self):
        p = base_prospect(sector="inconnu", evidences=[
            Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "https", "2026-11-03", "pas de HTTPS"),
            Evidence(EVIDENCE_SECTOR_OPPORTUNITY, "https://x.fr", "devis", "2026-11-03", "devis à la main"),
        ])
        res = qualify(p, set(), set())
        self.assertEqual(res.tier, TIER_MOYENNE)  # conservée, pas rejetée
        self.assertEqual(res.status, REVIEW)

    def test_public_need_without_email_a_approfondir(self):
        p = base_prospect(contact_email="", evidences=[Evidence(
            EVIDENCE_PUBLIC_NEED, "https://x.fr", "besoin", "2026-11-03", "besoin exprimé",
        )])
        res = qualify(p, set(), set())
        self.assertEqual(res.tier, TIER_A_APPROFONDIR)


if __name__ == "__main__":
    unittest.main()
