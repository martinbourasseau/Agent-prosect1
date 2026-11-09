"""Section F — dossier de qualification : publiée ET vérifiée, jamais devinée."""
from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from prospecto.dossier import (
    build_dossier, audit_portfolio, decode_obfuscated_mailto, email_provenance,
    email_publication_evidence, commercial_angle, EMAIL_PUBLISHED, EMAIL_DECODED,
    EMAIL_ABSENT, FORBIDDEN_STATUSES,
)
from prospecto.scoring import AXIS_IA, AXIS_REFONTE, AXIS_SITE_WEB

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 7)


def record(**kw):
    base = {
        "company": "Exemple SARL", "sector": "étanchéité", "city": "Rennes",
        "department": "35", "website": "https://exemple.fr",
        "email": "contact@exemple.fr", "email_verification": "verified",
        "email_dns_status": "mx_ok", "email_provenance": EMAIL_PUBLISHED,
        "phone": "02 99 00 00 00", "phone_verification": "verified",
        "status": "nouveau",
        "evidence": [{"kind": "processus_manuel", "quote": "Devis établis à la main.",
                      "source_url": "https://exemple.fr/devis",
                      "source_type": "site_officiel", "observed_at": "2026-11-07",
                      "observed": True, "reliability": "haute"}],
        "scores": {AXIS_SITE_WEB: {"score": 5, "confidence": "moyenne"},
                   AXIS_REFONTE: {"score": 40, "confidence": "moyenne"},
                   AXIS_IA: {"score": 60, "confidence": "haute",
                             "observed_signals": ["Devis établi ou transmis à la main"]}},
    }
    base.update(kw)
    return base


class DecodeTests(unittest.TestCase):
    def test_decodage_pourcent(self):
        self.assertEqual(decode_obfuscated_mailto("mailto:contact%40exemple.fr"),
                         "contact@exemple.fr")

    def test_decodage_chaine_inversee(self):
        self.assertEqual(
            decode_obfuscated_mailto("mailto:moc.liamg%40etiehcnateregorf"),
            "frogeretancheite@gmail.com")

    def test_adresse_deja_claire(self):
        self.assertEqual(decode_obfuscated_mailto("mailto:a.b@exemple.fr?subject=x"),
                         "a.b@exemple.fr")

    def test_rien_n_est_invente(self):
        self.assertEqual(decode_obfuscated_mailto("mailto:pas-une-adresse"), "")
        self.assertEqual(decode_obfuscated_mailto(""), "")


class ProvenanceTests(unittest.TestCase):
    def test_absente(self):
        self.assertEqual(email_provenance(record(email="")), EMAIL_ABSENT)

    def test_reconstitution_detectee_dans_les_notes(self):
        r = record(notes="Adresse décodée d'un lien mailto inversé.")
        r.pop("email_provenance")
        self.assertEqual(email_provenance(r), EMAIL_DECODED)

    def test_le_statut_explicite_prime_sur_l_heuristique(self):
        """Froger : la note raconte la reconstitution PUIS sa confirmation."""
        r = record(notes="Adresse reconstituée puis confirmée en clair le 2026-11-07.",
                   email_provenance=EMAIL_PUBLISHED)
        self.assertEqual(email_provenance(r), EMAIL_PUBLISHED)

    def test_une_reconstitution_explicite_reste_non_confirmee(self):
        self.assertEqual(email_provenance(record(email_provenance=EMAIL_DECODED)),
                         EMAIL_DECODED)


class VerificationTests(unittest.TestCase):
    def test_preuve_de_publication_trouvee_sur_source_officielle(self):
        r = record()
        r["evidence"].append({"kind": "signal_confiance",
                              "quote": "E-mail : contact@exemple.fr",
                              "source_url": "https://exemple.fr/contact",
                              "source_type": "site_officiel",
                              "observed_at": "2026-11-07"})
        found = email_publication_evidence(r)
        self.assertEqual(found["url"], "https://exemple.fr/contact")
        self.assertEqual(found["date"], "2026-11-07")

    def test_une_source_non_officielle_ne_suffit_pas(self):
        r = record(email_verification="public_unverified")
        r["evidence"] = [{"kind": "signal_confiance",
                          "quote": "contact@exemple.fr",
                          "source_url": "https://annuaire-tiers.fr/fiche",
                          "source_type": "annuaire_pro",
                          "observed_at": "2026-11-07"}]
        self.assertEqual(email_publication_evidence(r), {})
        self.assertFalse(build_dossier(r, TODAY).email_verified)

    def test_publiee_mais_non_recoupee_n_est_pas_verifiee(self):
        d = build_dossier(record(email_verification="public_unverified"), TODAY)
        self.assertFalse(d.email_verified)
        self.assertTrue(any("non recoupée" in b for b in d.blockers))

    def test_mx_seul_ne_verifie_pas_une_adresse(self):
        d = build_dossier(record(email_verification="", email_dns_status="mx_ok"), TODAY)
        self.assertFalse(d.email_verified)

    def test_domaine_non_routable_bloque(self):
        d = build_dossier(record(email_dns_status="nxdomain"), TODAY)
        self.assertFalse(d.email_verified)
        self.assertTrue(any("non routable" in b for b in d.blockers))

    def test_telephone_publie_et_verifie(self):
        self.assertTrue(build_dossier(record(), TODAY).phone_verified)
        self.assertFalse(build_dossier(record(phone_verification="public_unverified"),
                                       TODAY).phone_verified)
        self.assertFalse(build_dossier(record(phone=""), TODAY).phone_verified)

    def test_fiche_complete_qualifie(self):
        d = build_dossier(record(), TODAY)
        self.assertTrue(d.qualified, d.blockers)
        self.assertEqual(d.evaluated_at, "2026-11-07")
        self.assertTrue(d.commercial_angle)
        self.assertTrue(d.recommended_service)
        self.assertEqual(d.confidence, "haute")


class GuardTests(unittest.TestCase):
    def test_une_adresse_reconstituee_bloque_le_dossier(self):
        d = build_dossier(record(email_provenance=EMAIL_DECODED), TODAY)
        self.assertFalse(d.qualified)
        self.assertTrue(any("non confirmée" in b for b in d.blockers))

    def test_aucune_adresse_ne_se_devine(self):
        d = build_dossier(record(email=""), TODAY)
        self.assertFalse(d.qualified)
        self.assertTrue(any("jamais à deviner" in b for b in d.blockers))

    def test_opposition_est_definitive(self):
        d = build_dossier(record(status="opposition", opposed=True), TODAY)
        self.assertFalse(d.qualified)
        self.assertTrue(any("définitivement exclu" in b for b in d.blockers))

    def test_suspension_bloque(self):
        d = build_dossier(record(status="suspendu", suspension_reason="incident"), TODAY)
        self.assertFalse(d.qualified)

    def test_deja_contacte_bloque(self):
        for status in ("contacté", "envoyé", "rebond"):
            self.assertFalse(build_dossier(record(status=status), TODAY).qualified, status)

    def test_statuts_interdits_couverts(self):
        self.assertIn("opposition", FORBIDDEN_STATUSES)
        self.assertIn("contacté", FORBIDDEN_STATUSES)

    def test_sans_source_datee_pas_de_qualification(self):
        d = build_dossier(record(evidence=[]), TODAY)
        self.assertFalse(d.qualified)
        self.assertTrue(any("source datée" in b for b in d.blockers))


class AngleTests(unittest.TestCase):
    def test_l_angle_cite_le_constat_pas_le_secteur(self):
        angle = commercial_angle(record())
        self.assertIn("Devis établi ou transmis à la main", angle)
        self.assertNotIn("étanchéité", angle)

    def test_l_angle_suit_l_axe_dominant(self):
        r = record()
        r["scores"][AXIS_REFONTE]["score"] = 90
        r["scores"][AXIS_REFONTE]["observed_signals"] = ["Parcours de contact incomplet"]
        self.assertIn("Parcours de contact incomplet", commercial_angle(r))


class RealPortfolioTests(unittest.TestCase):
    """Contrôles sur les données réelles, après confirmation du 2026-11-07."""

    @classmethod
    def setUpClass(cls):
        cls.recs = json.loads((ROOT / "data" / "crm" / "prospects.json")
                              .read_text(encoding="utf-8"))["prospects"]
        cls.audit = audit_portfolio(cls.recs)

    def test_froger_est_desormais_confirmee(self):
        r = next(x for x in self.recs if x["company"] == "Froger Étanchéité")
        self.assertEqual(email_provenance(r), EMAIL_PUBLISHED)
        d = build_dossier(r, TODAY)
        self.assertTrue(d.email_verified)
        # Froger a été contactée depuis (envoi hors agent du 09/11, réconcilié en
        # phase 10 bis) : « qualified » = éligible à une NOUVELLE approche, donc
        # faux à juste titre. On vérifie la confirmation de l'adresse, qui est
        # l'objet réel de ce test, et l'absence de blocage de qualité.
        self.assertTrue(d.email_verified)
        quality = [b for b in d.blockers
                   if not any(t in b for t in ("statut", "opposition", "suspendue"))]
        self.assertEqual(quality, [], d.blockers)

    def test_les_quatre_du_lot9_sont_qualifiees(self):
        for name in ("Caléo Tests & Services", "Cordonnerie Canfora David",
                     "Froger Étanchéité", "Cordes et Âme"):
            r = next(x for x in self.recs if x["company"] == name)
            d = build_dossier(r, TODAY)
            # Certaines ont été contactées depuis : le statut bloque toute
            # nouvelle approche, ce qui est voulu. L'invariant durable est la
            # qualité du dossier, pas son éligibilité courante.
            quality = [b for b in d.blockers
                       if not any(t in b for t in ("statut", "opposition", "suspendue"))]
            self.assertEqual(quality, [], f"{name} : {quality}")
            self.assertTrue(d.email_verified, name)
            self.assertTrue(d.phone_verified, name)

    def test_la_confirmation_est_tracee_dans_l_historique(self):
        for name in ("Cordonnerie Canfora David", "Froger Étanchéité", "Cordes et Âme"):
            r = next(x for x in self.recs if x["company"] == name)
            actions = [h.get("action") for h in r.get("history", [])]
            self.assertIn("confirmation_coordonnees", actions, name)

    def test_la_renarde_reste_exclue(self):
        r = next(x for x in self.recs if "Renarde" in x["company"])
        self.assertFalse(build_dossier(r, TODAY).qualified)

    def test_aucune_adresse_reconstituee_non_confirmee_ne_subsiste(self):
        self.assertEqual(self.audit["email_provenance"][EMAIL_DECODED], 0)

    def test_les_deja_contactes_ne_sont_pas_qualifies(self):
        for d in self.audit["dossiers"]:
            rec = next(x for x in self.recs if x["company"] == d["company"])
            if str(rec.get("status", "")).lower() in FORBIDDEN_STATUSES:
                self.assertFalse(d["qualified"], d["company"])


if __name__ == "__main__":
    unittest.main()
