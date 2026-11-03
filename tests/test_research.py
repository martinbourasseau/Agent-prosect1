"""Tests de l'audit de site : constats factuels, bornés aux pages consultées."""
import unittest

from prospecto.research import audit_html


class TestAudit(unittest.TestCase):
    def test_https_form_cta_ok_no_gaps(self):
        html = '''
        <html><body>
        <a href="tel:+33200000000">Appelez-nous</a>
        <form action="/contact"><input name="email"></form>
        <a href="/devis">Demander un devis</a>
        </body></html>
        '''
        audit = audit_html(html, "https://exemple.fr")
        self.assertTrue(audit.https_ok)
        self.assertTrue(audit.has_contact_form)
        self.assertTrue(audit.has_visible_cta)
        self.assertEqual(audit.gaps, [])

    def test_http_flagged(self):
        audit = audit_html("<html></html>", "http://exemple.fr")
        self.assertFalse(audit.https_ok)
        self.assertTrue(any("HTTPS" in g for g in audit.gaps))

    def test_missing_form_and_cta_flagged(self):
        html = "<html><body><p>Bienvenue</p><a href='/page'>En savoir plus</a></body></html>"
        audit = audit_html(html, "https://exemple.fr")
        self.assertFalse(audit.has_contact_form)
        self.assertFalse(audit.has_visible_cta)
        self.assertEqual(len(audit.gaps), 2)
        self.assertTrue(all("pages" in g for g in audit.gaps))  # constats bornés

    def test_mailto_counts_as_contact(self):
        html = '<html><a href="mailto:contact@exemple.fr">Écrivez-nous</a></html>'
        audit = audit_html(html, "https://exemple.fr")
        self.assertTrue(audit.has_mailto)
        self.assertTrue(audit.has_visible_cta)
        self.assertFalse(any("formulaire" in g for g in audit.gaps))

    def test_evidences_generated(self):
        audit = audit_html("<html></html>", "http://exemple.fr")
        evidences = audit.to_evidences(observed_at="2026-11-03")
        self.assertGreaterEqual(len(evidences), 1)
        self.assertEqual(evidences[0].kind, "website_gap")
        self.assertEqual(evidences[0].source_url, "http://exemple.fr")
        self.assertEqual(evidences[0].observed_at, "2026-11-03")


if __name__ == "__main__":
    unittest.main()
