"""Tests de la stratégie v2 : personnalisation et démonstration gratuite."""
import unittest

from prospecto.models import (
    Prospect, Evidence,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP,
)
from prospecto.strategy import (
    DEMO_OFFERS, build_subject, build_opening, realisation_example,
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
            detail="Le site ne s'affichait pas en connexion sécurisée (HTTPS) lors de mon passage.",
        )],
    )
    base.update(kw)
    return Prospect(**base)


class TestDemoOffers(unittest.TestCase):
    def test_demo_offer_per_need(self):
        self.assertIn("maquette", DEMO_OFFERS[NEED_SITE_WEB])
        self.assertIn("aperçu visuel", DEMO_OFFERS[NEED_REFONTE])
        self.assertIn("exemple concret", DEMO_OFFERS[NEED_AGENT_IA])
        self.assertIn("illustration du processus", DEMO_OFFERS[NEED_AUTOMATISATION])

    def test_demo_never_promises_full_build(self):
        for offer in DEMO_OFFERS.values():
            self.assertNotIn("complet", offer.lower())
            self.assertNotIn("entièrement", offer.lower())


class TestSubjects(unittest.TestCase):
    def test_subject_reference_and_short(self):
        for need in (NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION):
            p = make_prospect(needs=[need], process_hint="vos demandes de devis")
            subject = build_subject(p)
            self.assertIn("idée", subject.lower())
            self.assertLessEqual(len(subject), 70)

    def test_subject_contains_company(self):
        p = make_prospect(needs=[NEED_REFONTE])
        self.assertIn("Atelier Dupont", build_subject(p))

    def test_subject_elision(self):
        p = make_prospect(company="Akla Architectes", needs=[NEED_REFONTE])
        self.assertIn("le site d'Akla Architectes", build_subject(p))
        p = make_prospect(company="Quattro Architectes", needs=[NEED_REFONTE])
        self.assertIn("le site de Quattro Architectes", build_subject(p))

    def test_long_company_falls_back_to_short_subject(self):
        p = make_prospect(
            company="Entreprise Avec Un Nom Vraiment Très Long Pour Tester Les Limites",
            needs=[NEED_AUTOMATISATION],
            process_hint="les demandes de devis entrantes par e-mail",
        )
        self.assertLessEqual(len(build_subject(p)), 70)


class TestOpening(unittest.TestCase):
    def test_public_need_has_priority_and_is_cited(self):
        p = make_prospect(
            needs=[NEED_SITE_WEB],
            evidences=[
                Evidence(EVIDENCE_WEBSITE_GAP, "http://x.fr", "gap", "2026-11-03", "un constat"),
                Evidence(
                    EVIDENCE_PUBLIC_NEED,
                    "https://facebook.com/post/123",
                    "cherche quelqu'un pour créer notre site",
                    "2026-10-28",
                    "vous cherchiez quelqu'un pour créer votre site (post Facebook du 28 octobre)",
                ),
            ],
        )
        opening = build_opening(p)
        self.assertIn("post Facebook du 28 octobre", opening)
        self.assertNotIn("relevé", opening)

    def test_website_gaps_are_factual_and_bounded(self):
        p = make_prospect()
        opening = build_opening(p)
        self.assertIn("voici ce que j'y ai relevé", opening)
        self.assertIn("HTTPS", opening)
        self.assertIn("atelier-dupont.fr", opening)

    def test_no_invented_problem_without_evidence(self):
        p = make_prospect(
            needs=[NEED_AGENT_IA],
            evidences=[Evidence(
                EVIDENCE_PUBLIC_NEED, "https://linkedin.com/post/1",
                "nous croulons sous les e-mails", "2026-11-01",
                "vous indiquiez sur LinkedIn (1er novembre) être débordé par les e-mails entrants",
            )],
            process_hint="",
        )
        opening = build_opening(p)
        self.assertIn("LinkedIn", opening)

    def test_neutral_opening_when_no_specific_signal(self):
        p = make_prospect(
            needs=[NEED_AGENT_IA],
            evidences=[Evidence(
                EVIDENCE_PUBLIC_NEED, "https://example.com", "x", "2026-11-03", "",
            )],
            process_hint="",
        )
        # Sans detail, la citation brute est utilisée — jamais de problème inventé.
        opening = build_opening(p)
        self.assertTrue(opening.startswith("J'ai vu que"))


class TestRealisations(unittest.TestCase):
    def test_sector_adapted_example(self):
        self.assertIn("devis", realisation_example("batiment", NEED_REFONTE))
        self.assertIn("rendez-vous", realisation_example("automobile", NEED_AUTOMATISATION))

    def test_unknown_sector_falls_back(self):
        self.assertTrue(realisation_example("secteur-inconnu", NEED_SITE_WEB))


if __name__ == "__main__":
    unittest.main()
