"""Tests v4 : références, variantes de messages, suppression, délivrabilité,
moteur d'envoi (portes de sécurité), réponses, métriques, niveaux de vérification.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from prospecto import config
from prospecto.models import (
    Prospect, Evidence, GeneratedEmail,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
    EMAIL_VERIFIED, EMAIL_PUBLIC_UNVERIFIED, EMAIL_NONE,
)
from prospecto.references import load_references, select_reference, reference_by_id
from prospecto.messaging import compose_email, check_email_v4, select_variant, applicable_variants
from prospecto.suppression import SuppressionList
from prospecto.deliverability import analyze_sender, check_domain
from prospecto.sender import Sender, SendLog, SendCandidate
from prospecto.replies import classify_intent, ReplyHandler, prepare_reply_draft
from prospecto.replies import (
    INTENT_POSITIVE, INTENT_NEGATIVE, INTENT_INFO, INTENT_MEETING,
    INTENT_OPT_OUT, INTENT_AUTO_REPLY, INTENT_BOUNCE,
)


def make_prospect(**kw):
    base = dict(
        company="Atelier Dupont", domain="atelier-dupont.fr",
        contact_email="contact@atelier-dupont.fr", sector="batiment",
        needs=[NEED_SITE_WEB],
        evidences=[Evidence(EVIDENCE_SECTOR_OPPORTUNITY, "https://exemple.fr",
                            "activité récente", "2026-11-04", "opportunité sectorielle")],
        email_verification=EMAIL_VERIFIED,
        # v5 : tout message doit partir d'une observation réelle. Le jeu d'essai
        # en fournit une, comme le fait chaque fiche du CRM en production.
        custom_hook="Votre page contact ne propose qu'un numéro de téléphone pour demander un devis.",
    )
    base.update(kw)
    return Prospect(**base)


class TestEmailVerificationLevels(unittest.TestCase):
    def test_none_allowed_without_email(self):
        p = make_prospect(contact_email="", email_verification=EMAIL_NONE)
        self.assertEqual(p.validate(), [])

    def test_empty_email_requires_none(self):
        p = make_prospect(contact_email="", email_verification=EMAIL_PUBLIC_UNVERIFIED)
        self.assertTrue(any("none" in e for e in p.validate()))

    def test_email_with_none_rejected(self):
        p = make_prospect(email_verification=EMAIL_NONE)
        self.assertTrue(any("none" in e for e in p.validate()))

    def test_invalid_email_rejected(self):
        p = make_prospect(contact_email="pas-un-email")
        self.assertTrue(any("invalide" in e for e in p.validate()))


class TestReferences(unittest.TestCase):
    def test_load_two_references(self):
        refs = load_references()
        ids = {r.id for r in refs}
        self.assertIn("groupe-bourasseau", ids)
        self.assertIn("synatrap", ids)

    def test_site_selects_groupe(self):
        p = make_prospect(needs=[NEED_SITE_WEB], sector="commerce")
        ref = select_reference(p)
        self.assertIsNotNone(ref)
        self.assertEqual(ref.id, "groupe-bourasseau")

    def test_refonte_selects_groupe(self):
        p = make_prospect(needs=[NEED_REFONTE])
        self.assertEqual(select_reference(p).id, "groupe-bourasseau")

    def test_ia_selects_synatrap(self):
        p = make_prospect(needs=[NEED_AGENT_IA], sector="services")
        self.assertEqual(select_reference(p).id, "synatrap")

    def test_automation_selects_synatrap(self):
        p = make_prospect(needs=[NEED_AUTOMATISATION], sector="commerce")
        self.assertEqual(select_reference(p).id, "synatrap")

    def test_authorship_not_personal_claim(self):
        for r in load_references():
            self.assertEqual(r.authorship_status, "owner_declared")

    def test_reference_by_id(self):
        self.assertIsNotNone(reference_by_id("synatrap"))
        self.assertIsNone(reference_by_id("inexistant"))


class TestMessaging(unittest.TestCase):
    def test_compose_site_demo(self):
        p = make_prospect(needs=[NEED_SITE_WEB], sector="commerce")
        email = compose_email(p)
        self.assertEqual(check_email_v4(email, p), [])
        self.assertTrue(email.reference_id)
        self.assertEqual(email.message_version, "v4")

    def test_compose_ia(self):
        p = make_prospect(needs=[NEED_AGENT_IA], sector="services")
        email = compose_email(p)
        self.assertEqual(check_email_v4(email, p), [])
        self.assertEqual(email.reference_id, "synatrap")

    def test_public_need_variant(self):
        p = make_prospect(needs=[NEED_REFONTE], evidences=[
            Evidence(EVIDENCE_PUBLIC_NEED, "https://codeur.com/x", "besoin", "2026-11-04", "annonce publique")])
        self.assertEqual(select_variant(p), "public_need")
        email = compose_email(p)
        self.assertEqual(check_email_v4(email, p), [])

    def test_all_applicable_variants_compose(self):
        p = make_prospect(needs=[NEED_SITE_WEB], sector="commerce")
        for v in applicable_variants(p):
            email = compose_email(p, variant=v)
            self.assertEqual(check_email_v4(email, p), [], f"variante {v} invalide")

    def test_opt_out_present(self):
        p = make_prospect()
        email = compose_email(p)
        self.assertIn("ne pas me relancer", email.body)

    def test_demo_is_free_limited(self):
        p = make_prospect(needs=[NEED_SITE_WEB])
        email = compose_email(p)
        self.assertIn("gratuit", email.body.lower())
        self.assertIn("sans engagement", email.body.lower())


class TestSuppression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "suppression.json"
        self.sl = SuppressionList(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_check(self):
        self.assertTrue(self.sl.add(email="stop@x.fr", reason="opt-out"))
        self.assertTrue(self.sl.is_suppressed("stop@x.fr"))
        self.assertFalse(self.sl.is_suppressed("autre@x.fr"))

    def test_duplicate_add(self):
        self.sl.add(email="stop@x.fr")
        self.assertFalse(self.sl.add(email="stop@x.fr"))
        self.assertEqual(self.sl.count(), 1)

    def test_remove(self):
        self.sl.add(email="stop@x.fr")
        self.assertTrue(self.sl.remove("stop@x.fr"))
        self.assertFalse(self.sl.is_suppressed("stop@x.fr"))

    def test_domain_wide(self):
        self.sl.add(domain="x.fr", reason="opposition")
        self.assertTrue(self.sl.is_suppressed("nimporte@x.fr"))


class TestDeliverability(unittest.TestCase):
    def test_gmail_is_free_provider(self):
        rep = analyze_sender("martin.bourasseau4@gmail.com")
        self.assertTrue(rep.is_free_provider)
        self.assertFalse(rep.ok_for_bulk)
        self.assertTrue(rep.warnings)

    def test_custom_domain_structure(self):
        rep = check_domain("exemple-inexistant-12345.fr")
        self.assertFalse(rep.is_free_provider)
        self.assertFalse(rep.ok_for_bulk)  # pas de SPF/DKIM/DMARC


class TestSender(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.tmp.name) / "settings.json"
        self.settings = {
            "enabled": False, "dry_run": True, "transport": "dry_run",
            "sender": {"email": "contact@exemple.fr", "name": "Martin"},
            "quality": {"allowed_email_verification": [EMAIL_VERIFIED], "min_score": 40},
            "limits": {"daily_limit": 20, "ramp_up": [5, 10], "ramp_up_day_index": 0, "max_per_run": 20},
            "stop_conditions": {"max_bounce_rate": 0.05, "max_complaint_rate": 0.001,
                                "min_sent_before_rate_check": 20, "auto_pause_on_breach": True},
        }
        self.settings_path.write_text(json.dumps(self.settings))
        self.patchers = [
            mock.patch.object(config, "SUPPRESSION_PATH", Path(self.tmp.name) / "sup.json"),
            mock.patch.object(config, "SEND_LOG_PATH", Path(self.tmp.name) / "log.json"),
        ]
        for p in self.patchers:
            p.start()
        self.sender = Sender(self.settings_path)

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        self.tmp.cleanup()

    def _record(self, **kw):
        base = dict(company="A", email="a@x.fr", tier="haute", score=60,
                    email_verification=EMAIL_VERIFIED, status="email_préparé",
                    proposed_email={"subject": "s", "body": "b", "queue_id": "q1"})
        base.update(kw)
        return base

    def test_selects_verified_only(self):
        recs = [self._record(), self._record(email="b@x.fr", email_verification=EMAIL_PUBLIC_UNVERIFIED)]
        cands = self.sender.select_candidates(recs, [])
        self.assertEqual([c.to for c in cands], ["a@x.fr"])

    def test_excludes_suppressed(self):
        self.sender.suppression.add(email="a@x.fr", reason="opt-out")
        self.assertEqual(self.sender.select_candidates([self._record()], []), [])

    def test_excludes_already_sent(self):
        queue = [{"to": "a@x.fr", "status": "sent"}]
        self.assertEqual(self.sender.select_candidates([self._record()], queue), [])

    def test_includes_pending(self):
        queue = [{"to": "a@x.fr", "status": "pending"}]
        self.assertEqual(len(self.sender.select_candidates([self._record()], queue)), 1)

    def test_excludes_low_score(self):
        self.assertEqual(self.sender.select_candidates([self._record(score=20)], []), [])

    def test_excludes_contacted(self):
        self.assertEqual(self.sender.select_candidates([self._record(status="contacté")], []), [])

    def test_ramp_up_cap(self):
        recs = [self._record(email=f"u{i}@x.fr") for i in range(10)]
        plan = self.sender.build_plan(self.sender.select_candidates(recs, []))
        self.assertEqual(len(plan), 5)  # ramp_up[0]

    def test_dry_run_sends_nothing(self):
        plan = self.sender.build_plan(self.sender.select_candidates([self._record()], []))
        res = self.sender.execute(plan, transport="dry_run")
        self.assertEqual(res[0]["status"], "dry_run")
        self.assertEqual(self.sender.log.rates()["sent"], 0)

    def test_preflight_blocks_when_disabled(self):
        ok, issues = self.sender.preflight()
        self.assertFalse(ok)
        self.assertTrue(any("activ" in i.lower() for i in issues))

    def test_stop_on_bounce(self):
        for i in range(25):
            self.sender.log.record(to=f"u{i}@x.fr", status="bounced" if i < 5 else "sent")
        stop, reason = self.sender.check_stop_conditions()
        self.assertTrue(stop)
        self.assertIn("rebond", reason.lower())


class TestReplies(unittest.TestCase):
    def test_classify_positive(self):
        self.assertEqual(classify_intent("Oui, cela m'intéresse beaucoup"), INTENT_POSITIVE)

    def test_classify_opt_out(self):
        self.assertEqual(classify_intent("Merci de ne plus me contacter"), INTENT_OPT_OUT)

    def test_classify_negative(self):
        self.assertEqual(classify_intent("Non merci, pas intéressé"), INTENT_NEGATIVE)

    def test_classify_meeting(self):
        self.assertEqual(classify_intent("On peut se faire un rendez-vous ?"), INTENT_MEETING)

    def test_classify_info(self):
        self.assertEqual(classify_intent("Pouvez-vous m'envoyer plus d'informations et vos tarifs ?"), INTENT_INFO)

    def test_classify_bounce(self):
        self.assertEqual(classify_intent("Mailer-Daemon: address not found 550"), INTENT_BOUNCE)

    def test_classify_auto_reply(self):
        self.assertEqual(classify_intent("Je suis actuellement absent, réponse automatique"), INTENT_AUTO_REPLY)

    def test_opt_out_no_followup(self):
        draft = prepare_reply_draft("A", INTENT_OPT_OUT)
        self.assertIn("ne vous recontacterai plus", draft)

    def test_process_reply_updates_crm_and_suppresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(config, "SUPPRESSION_PATH", Path(tmp) / "sup.json"), \
                 mock.patch.object(config, "REPLIES_PATH", Path(tmp) / "replies.json"):
                crm = mock.Mock()
                crm.records = [{"company": "A", "email": "a@x.fr", "contact_name": ""}]
                handler = ReplyHandler(crm)
                res = handler.process_reply("a@x.fr", "Merci de ne plus me contacter")
                self.assertEqual(res.intent, INTENT_OPT_OUT)
                self.assertTrue(res.suppressed)
                self.assertFalse(res.follow_up_allowed)
                self.assertTrue(crm.save.called)
                self.assertEqual(crm.records[0]["status"], "opposition")


class TestMetrics(unittest.TestCase):
    def test_compute_metrics_structure(self):
        from prospecto.metrics import compute_metrics
        m = compute_metrics()
        for key in ("crm", "coordinates", "queue", "sending", "replies", "suppression", "performance"):
            self.assertIn(key, m)
        self.assertIn("emails_by_verification", m["coordinates"])
        self.assertIn("by_variant", m["performance"])


if __name__ == "__main__":
    unittest.main()


class TestSenderIdentity(unittest.TestCase):
    def test_official_name_present(self):
        p = make_prospect()
        email = compose_email(p)
        self.assertIn(config.SENDER_NAME, email.body)
        self.assertEqual(check_email_v4(email, p), [])

    def test_wrong_name_rejected(self):
        p = make_prospect()
        email = compose_email(p)
        wrong_name = "Martin Boiss" + "eau"
        email.body = email.body.replace(config.SENDER_NAME, wrong_name)
        problems = check_email_v4(email, p)
        self.assertTrue(any("variante orthographique" in x for x in problems))

    def test_missing_signature_rejected(self):
        p = make_prospect()
        email = compose_email(p)
        email.body = email.body.replace(config.SENDER_NAME, "")
        problems = check_email_v4(email, p)
        self.assertTrue(any("signature" in x for x in problems))
