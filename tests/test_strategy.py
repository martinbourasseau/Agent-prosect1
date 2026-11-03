"""Tests stratégie v3 : hooks, objets, démo gratuite, prestation unique."""
import unittest

from prospecto.models import (
    Prospect, Evidence,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP,
)
from prospecto.strategy import (
    DEMO_OFFERS, build_subject, build_hook, realisation_example, de_company,
)


def make_prospect(**kw):
    base = dict(
        company="Atelier Dupont",
        domain="atelier-dupont.fr",
        contact_email="contact@atelier-dupont.fr",
        sector="batiment",
        needs=[NEED_REFONTE],
        evidences=[Evidence(
            kind=EVIDENCE_WEBSITE_GAP,
            source_url="http://atelier-dupont.fr",
            quote="pas de HTTPS",
            observed_at="2026-11-03",
            detail="le site ne s'affichait pas en connexion sécurisée (HTTPS) lors de mon passage.",
        )],
    )
    base.update(kw)
    return Prospect(**base)


class TestDemoOffers(unittest.TestCase):
    def test_demo_offer_per_need(self):
        self.assertIn("maquette", DEMO_OFFERS[NEED_SITE_WEB])
        self.assertIn("direction graphique", DEMO_OFFERS[NEED_REFONTE])
        self.assertIn("cas d'usage", DEMO_OFFERS[NEED_AGENT_IA])
        self.assertIn("processus automatisé", DEMO_OFFERS[NEED_AUTOMATISATION])

    def test_demo_never_promises_full_build(self):
        for offer in DEMO_OFFERS.values():
            self.assertNotIn("complet", offer.lower())
            self.assertNotIn("entièrement", offer.lower())


class TestSubjects(unittest.TestCase):
    def test_subject_short_for_all_needs(self):
        for need in (NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION):
            p = make_prospect(needs=[need], process_hint="vos devis")
            s = build_subject(p)
            self.assertTrue(s.strip())
            self.assertLessEqual(len(s), 70)

    def test_custom_subject_override(self):
        p = make_prospect(custom_subject="Votre annonce m'a interpellé")
        self.assertEqual(build_subject(p), "Votre annonce m'a interpellé")

    def test_long_company_falls_back_short(self):
        p = make_prospect(
            company="Entreprise Avec Un Nom Vraiment Très Long Pour Tester Les Limites",
            needs=[NEED_AUTOMATISATION], process_hint="les demandes de devis entrantes par e-mail",
        )
        self.assertLessEqual(len(build_subject(p)), 70)

    def test_elision(self):
        self.assertEqual(de_company("Akla Architectes"), "d'Akla Architectes")
        self.assertEqual(de_company("Quattro Architectes"), "de Quattro Architectes")


class TestHooks(unittest.TestCase):
    def test_public_need_hook_cites_detail(self):
        p = make_prospect(needs=[NEED_SITE_WEB], evidences=[Evidence(
            EVIDENCE_PUBLIC_NEED, "https://codeur.com/p/1",
            "nous cherchons à créer notre site", "2026-11-01",
            "vous cherchez à créer votre site vitrine (Codeur.com, 1er novembre)",
        )])
        hook = build_hook(p)
        self.assertIn("votre site vitrine", hook)
        self.assertIn("annonce", hook)

    def test_custom_hook_override(self):
        p = make_prospect(custom_hook="Votre projet de terrasse m'a donné une idée.")
        self.assertEqual(build_hook(p), "Votre projet de terrasse m'a donné une idée.")

    def test_website_gap_hook_factual(self):
        p = make_prospect()
        hook = build_hook(p)
        self.assertIn("relevé un point concret", hook)
        self.assertIn("HTTPS", hook)

    def test_process_hook(self):
        p = make_prospect(needs=[NEED_AUTOMATISATION], process_hint="vos demandes de devis arrivent par e-mail",
                          evidences=[Evidence(EVIDENCE_PUBLIC_NEED, "https://x.fr", "x", "2026-11-03", "détail")])
        # public need prime ; on teste le fallback processus sans public_need
        p.evidences = [Evidence("sector_opportunity", "https://x.fr", "devis", "2026-11-03", "devis par e-mail")]
        hook = build_hook(p)
        self.assertIn("piste concrète", hook)

    def test_neutral_hook_no_invention(self):
        p = make_prospect(needs=[NEED_AGENT_IA], process_hint="",
                          evidences=[Evidence("sector_opportunity", "https://x.fr", "x", "2026-11-03", "")])
        hook = build_hook(p)
        self.assertIn("possibilité intéressante", hook)


class TestRealisations(unittest.TestCase):
    def test_sector_adapted(self):
        self.assertIn("devis", realisation_example("batiment", NEED_REFONTE))
        self.assertIn("rendez-vous", realisation_example("automobile", NEED_AUTOMATISATION))

    def test_unknown_sector_fallback(self):
        self.assertTrue(realisation_example("inconnu", NEED_SITE_WEB))


if __name__ == "__main__":
    unittest.main()
