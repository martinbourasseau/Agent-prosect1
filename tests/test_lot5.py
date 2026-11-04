"""Tests du lot 5 : vérification DNS, trois scores indépendants, audit de boîte.

Ces tests couvrent les trois défauts constatés sur les lots 1 à 4 :
1. aucune vérification technique de l'adresse avant préparation (rebond NXDOMAIN) ;
2. un besoin déduit du secteur plutôt que de preuves, sans scores séparés ;
3. une détection des réponses limitée à ``from:<adresse exacte>``, qui ratait
   les rebonds (expédiés par le démon) et les réponses d'une autre adresse.
"""
import json
import tempfile
import unittest
from pathlib import Path

from prospecto import config
from prospecto.crm import CRM
from prospecto.email_verify import (
    check_domain, verify_email, verify_records, DomainCache, email_domain,
    MX_OK, MX_NONE, MX_NXDOMAIN, MX_A_FALLBACK, MX_DNS_ERROR, MX_BAD_SYNTAX,
)
from prospecto.inbox_audit import (
    is_bounce_sender, extract_bounce_recipient, bounce_severity, classify_inbound,
    match_prospect, audit_inbox, apply_findings, save_audit,
    INTENT_BOUNCE, INTENT_AUTO_REPLY, INTENT_HUMAN, INTENT_OPT_OUT,
    SEVERITY_HARD, SEVERITY_SOFT,
)
from prospecto.models import (
    Prospect, Evidence, NEED_REFONTE, NEED_AUTOMATISATION,
    EVIDENCE_SITE_OBSOLETE, EVIDENCE_PROCESS_MANUAL, EVIDENCE_SITE_DOWN,
    EVIDENCE_JOURNEY_GAP, EMAIL_VERIFIED, EMAIL_PUBLIC_UNVERIFIED, EMAIL_NONE,
)
from prospecto.scoring import (
    score_prospect, scores_from_record, commercial_priority, primary_need_from_scores,
    AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA, LEVEL_FORT, LEVEL_FAIBLE,
    PRIORITY_HAUTE, PRIORITY_A_APPROFONDIR,
)
from prospecto.suppression import SuppressionList


class FakeAnswer:
    def __init__(self, exchange):
        self.exchange = exchange


class FakeResolver:
    """Résolveur DNS simulé : aucun accès réseau pendant les tests."""

    def __init__(self, mx=None, a=None, error=None):
        self.mx = mx or {}
        self.a = a or {}
        self.error = error or {}

    def resolve(self, domain, rtype):
        if domain in self.error:
            raise self.error[domain]
        table = self.mx if rtype == "MX" else self.a
        if domain not in table:
            raise _NoAnswer(f"no {rtype} for {domain}")
        return [FakeAnswer(v) for v in table[domain]]


class _NoAnswer(Exception):
    pass


_NoAnswer.__name__ = "NoAnswer"


class _NXDOMAIN(Exception):
    pass


_NXDOMAIN.__name__ = "NXDOMAIN"


GMAIL_BOUNCE = (
    "** Adresse introuvable **\n\n"
    "Votre message n'est pas parvenu à contact@severine-lesourd.com, car le domaine "
    "severine-lesourd.com est introuvable.\n\n"
    "La réponse était :\n\n"
    "DNS Error: DNS type 'mx' lookup of severine-lesourd.com responded with code NXDOMAIN\n"
)
DSN_BOUNCE = (
    "Delivery to the following recipient failed permanently:\n"
    "     jean@example-inexistant.fr\n"
    "Final-Recipient: rfc822; jean@example-inexistant.fr\n"
    "Action: failed\nStatus: 5.1.10\n"
)


def _prospect(**kw):
    base = dict(company="Test SARL", domain="test.fr", contact_email="contact@test.fr",
                sector="Services", needs=[NEED_REFONTE], website="https://test.fr",
                email_verification=EMAIL_VERIFIED)
    base.update(kw)
    return Prospect(**base)


def _ev(kind, quote="extrait observé", url="https://test.fr/page"):
    return Evidence(kind=kind, source_url=url, quote=quote, observed_at="2026-11-04")


class TestEmailVerify(unittest.TestCase):
    def test_syntaxe_invalide(self):
        self.assertEqual(verify_email("pas-une-adresse")["status"], MX_BAD_SYNTAX)
        self.assertEqual(verify_email("")["status"], MX_BAD_SYNTAX)

    def test_domaine_extrait(self):
        self.assertEqual(email_domain("Contact@Example.FR"), "example.fr")
        self.assertEqual(email_domain("sans-arobase"), "")

    def test_mx_ok(self):
        r = FakeResolver(mx={"example.fr": ["mx1.example.fr.", "mx2.example.fr."]})
        res = check_domain("example.fr", resolver=r)
        self.assertEqual(res.status, MX_OK)
        self.assertTrue(res.deliverable)
        self.assertIn("mx1.example.fr", res.mx_hosts)
        self.assertTrue(res.checked_at)

    def test_nxdomain_est_bloquant(self):
        r = FakeResolver(error={"inexistant.com": _NXDOMAIN("NXDOMAIN")})
        res = check_domain("inexistant.com", resolver=r)
        self.assertEqual(res.status, MX_NXDOMAIN)
        self.assertTrue(res.blocking)
        self.assertFalse(res.deliverable)

    def test_repli_a_sans_mx(self):
        r = FakeResolver(a={"example.fr": ["1.2.3.4"]})
        self.assertEqual(check_domain("example.fr", resolver=r).status, MX_A_FALLBACK)

    def test_domaine_sans_mx_ni_a(self):
        self.assertEqual(check_domain("example.fr", resolver=FakeResolver()).status, MX_NONE)

    def test_erreur_dns_ne_conclut_pas(self):
        class Timeout(Exception):
            pass
        Timeout.__name__ = "LifetimeTimeout"
        r = FakeResolver(error={"example.fr": Timeout("slow")})
        res = check_domain("example.fr", resolver=r)
        self.assertEqual(res.status, MX_DNS_ERROR)
        self.assertFalse(res.blocking)  # une erreur transitoire n'est pas un rejet

    def test_verify_records_annote_et_bloque(self):
        records = [
            {"company": "OK", "email": "a@ok.fr"},
            {"company": "KO", "email": "a@ko.com"},
            {"company": "SansEmail", "email": ""},
        ]
        r = FakeResolver(mx={"ok.fr": ["mx.ok.fr."]}, error={"ko.com": _NXDOMAIN("NXDOMAIN")})
        with tempfile.TemporaryDirectory() as tmp:
            cache = DomainCache(Path(tmp) / "dns.json")
            summary = verify_records(records, cache=cache, resolver=r)
            self.assertEqual(summary["checked"], 2)
            self.assertEqual(summary["deliverable"], 1)
            self.assertEqual(summary["blocking"], 1)
            self.assertEqual(summary["no_email"], 1)
            self.assertEqual(records[0]["email_dns_status"], MX_OK)
            self.assertEqual(records[1]["email_dns_status"], MX_NXDOMAIN)
            self.assertIn("non délivrable", records[1]["next_action"])
            self.assertTrue((Path(tmp) / "dns.json").exists())

    def test_cache_evite_une_nouvelle_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = DomainCache(Path(tmp) / "dns.json")
            r = FakeResolver(mx={"ok.fr": ["mx.ok.fr."]})
            cache.check("ok.fr", resolver=r)
            cache.save()
            reloaded = DomainCache(Path(tmp) / "dns.json")
            # Résolveur qui échouerait : le cache doit répondre sans le consulter.
            again = reloaded.check("ok.fr", resolver=FakeResolver(error={"ok.fr": _NXDOMAIN("x")}))
            self.assertEqual(again["status"], MX_OK)


class TestScoring(unittest.TestCase):
    def test_axes_independants_site_sans_processus(self):
        p = _prospect(evidences=[_ev(EVIDENCE_SITE_OBSOLETE)])
        s = score_prospect(p)
        self.assertGreaterEqual(s[AXIS_REFONTE]["score"], 50)
        self.assertLess(s[AXIS_IA]["score"], 40)
        self.assertLess(s[AXIS_SITE_WEB]["score"], 20)

    def test_axes_independants_processus_sans_refonte(self):
        p = _prospect(evidences=[_ev(EVIDENCE_PROCESS_MANUAL), _ev(EVIDENCE_PROCESS_MANUAL, "second")],
                      process_hint="devis par email")
        s = score_prospect(p)
        self.assertGreaterEqual(s[AXIS_IA]["score"], 70)
        self.assertLess(s[AXIS_REFONTE]["score"], 20)
        self.assertEqual(s["best_axis"], AXIS_IA)

    def test_site_indisponible_donne_creation(self):
        p = _prospect(evidences=[_ev(EVIDENCE_SITE_DOWN, "This site is currently suspended")])
        s = score_prospect(p)
        self.assertGreaterEqual(s[AXIS_SITE_WEB]["score"], 70)
        self.assertEqual(primary_need_from_scores(s), "site_web")

    def test_aucune_preuve_donne_score_faible_et_motif(self):
        p = _prospect(evidences=[_ev("sector_opportunity")])
        s = score_prospect(p)
        for axis in (AXIS_REFONTE, AXIS_IA):
            self.assertEqual(s[axis]["level"], LEVEL_FAIBLE)
            self.assertTrue(any("aucune preuve" in r for r in s[axis]["reasons"]))

    def test_justification_cite_la_source(self):
        p = _prospect(evidences=[_ev(EVIDENCE_PROCESS_MANUAL, "bulletin à renvoyer",
                                     "https://test.fr/cgv.pdf")])
        s = score_prospect(p)
        joined = " ".join(s[AXIS_IA]["reasons"])
        self.assertIn("https://test.fr/cgv.pdf", joined)
        self.assertIn("bulletin à renvoyer", joined)

    def test_scores_plafonnes_a_deux_preuves(self):
        evs = [_ev(EVIDENCE_PROCESS_MANUAL, f"preuve {i}") for i in range(6)]
        s = score_prospect(_prospect(evidences=evs, process_hint="flux"))
        self.assertLessEqual(s[AXIS_IA]["score"], 100)
        cited = [r for r in s[AXIS_IA]["reasons"] if r.startswith("+")]
        self.assertEqual(len(cited), 2)

    def test_priorite_basse_sans_adresse(self):
        p = _prospect(contact_email="", email_verification=EMAIL_NONE,
                      evidences=[_ev(EVIDENCE_PROCESS_MANUAL)])
        p.email_dns_status = MX_OK
        self.assertEqual(commercial_priority(p, score_prospect(p)), PRIORITY_A_APPROFONDIR)

    def test_priorite_bloquee_si_domaine_inexistant(self):
        p = _prospect(evidences=[_ev(EVIDENCE_PROCESS_MANUAL)])
        p.email_dns_status = MX_NXDOMAIN
        self.assertEqual(commercial_priority(p, score_prospect(p)), PRIORITY_A_APPROFONDIR)

    def test_priorite_haute_si_besoin_fort_et_adresse_verifiee(self):
        p = _prospect(evidences=[_ev(EVIDENCE_PROCESS_MANUAL)], process_hint="devis")
        p.email_dns_status = MX_OK
        self.assertEqual(commercial_priority(p, score_prospect(p)), PRIORITY_HAUTE)

    def test_scores_depuis_une_fiche_crm(self):
        record = {"company": "X", "domain": "x.fr", "website": "https://x.fr",
                  "email": "a@x.fr", "email_verification": EMAIL_VERIFIED,
                  "email_dns_status": MX_OK, "needs": [NEED_AUTOMATISATION],
                  "process_hint": "devis reçus par email puis chiffrage manuel",
                  "evidence": [{"kind": EVIDENCE_PROCESS_MANUAL, "source_url": "https://x.fr",
                                "quote": "q", "observed_at": "2026-11-04", "detail": ""}]}
        s = scores_from_record(record)
        self.assertGreaterEqual(s[AXIS_IA]["score"], 55)
        self.assertEqual(s["priority"], PRIORITY_HAUTE)


class TestInboxAudit(unittest.TestCase):
    def test_detection_expediteur_demon(self):
        self.assertTrue(is_bounce_sender("mailer-daemon@googlemail.com"))
        self.assertTrue(is_bounce_sender("postmaster@outlook.com"))
        self.assertFalse(is_bounce_sender("resa@bsp-auto.com"))

    def test_extraction_destinataire_gmail_fr(self):
        self.assertEqual(extract_bounce_recipient(GMAIL_BOUNCE, "mailer-daemon@googlemail.com"),
                         "contact@severine-lesourd.com")

    def test_extraction_destinataire_dsn(self):
        self.assertEqual(extract_bounce_recipient(DSN_BOUNCE, "mailer-daemon@google.com"),
                         "jean@example-inexistant.fr")

    def test_ne_rend_jamais_le_demon(self):
        text = "Message de mailer-daemon@googlemail.com à propos de postmaster@x.fr"
        self.assertEqual(extract_bounce_recipient(text, "mailer-daemon@googlemail.com"), "")

    def test_severite_dure_et_molle(self):
        self.assertEqual(bounce_severity(GMAIL_BOUNCE), SEVERITY_HARD)
        self.assertEqual(bounce_severity("Mailbox full, over quota"), SEVERITY_SOFT)

    def test_classification(self):
        self.assertEqual(classify_inbound("mailer-daemon@googlemail.com",
                                          "Delivery Status Notification (Failure)", GMAIL_BOUNCE)["intent"],
                         INTENT_BOUNCE)
        self.assertEqual(classify_inbound("resa@bsp-auto.com", "Bsp-auto : Ticket Reçu - Sujet",
                                          "Votre demande a bien été prise en compte")["intent"],
                         INTENT_AUTO_REPLY)
        self.assertEqual(classify_inbound("dir@acme.fr", "Re: votre message",
                                          "Bonjour, pouvez-vous m'envoyer une maquette ?")["intent"],
                         INTENT_HUMAN)
        self.assertEqual(classify_inbound("dir@acme.fr", "Re:", "Merci de ne plus me contacter")["intent"],
                         INTENT_OPT_OUT)

    def test_rattachement_par_domaine_quand_adresse_differente(self):
        records = [{"company": "BSP Auto", "email": "support@bsp-auto.com", "domain": "bsp-auto.com"}]
        m = match_prospect(records, "resa@bsp-auto.com")
        self.assertTrue(m.found)
        self.assertEqual(m.record["company"], "BSP Auto")
        self.assertEqual(m.method, "domaine_expediteur")

    def test_rattachement_rebond_par_destinataire_extrait(self):
        records = [{"company": "Pension", "email": "contact@severine-lesourd.com",
                    "domain": "severine-lesourd.fr"}]
        m = match_prospect(records, "mailer-daemon@googlemail.com", "contact@severine-lesourd.com")
        self.assertEqual(m.record["company"], "Pension")
        self.assertEqual(m.method, "email_exact")

    def test_rattachement_par_thread(self):
        records = [{"company": "A", "email": "a@a.fr", "gmail_thread_id": "T1"}]
        m = match_prospect(records, "inconnu@ailleurs.fr", thread_id="T1")
        self.assertTrue(m.found)
        self.assertEqual(m.method, "thread_id")

    def test_pas_de_rattachement_abusif_via_domaine_du_demon(self):
        records = [{"company": "Google", "email": "x@googlemail.com"}]
        m = match_prospect(records, "mailer-daemon@googlemail.com")
        self.assertFalse(m.found)

    def test_audit_et_application_bout_en_bout(self):
        records = [
            {"company": "Pension", "email": "contact@severine-lesourd.com", "domain": "severine-lesourd.fr"},
            {"company": "BSP Auto", "email": "support@bsp-auto.com", "domain": "bsp-auto.com"},
        ]
        messages = [
            {"id": "m1", "thread_id": "t1", "from": "mailer-daemon@googlemail.com",
             "subject": "Delivery Status Notification (Failure)", "text": GMAIL_BOUNCE},
            {"id": "m2", "thread_id": "t2", "from": "resa@bsp-auto.com",
             "subject": "Bsp-auto : Ticket Reçu - Sujet", "text": "Votre demande a bien été prise en compte"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            crm_path = Path(tmp) / "crm.json"
            crm_path.write_text(json.dumps({"prospects": records}), encoding="utf-8")
            crm = CRM(crm_path)
            sup = SuppressionList(Path(tmp) / "sup.json")

            class Log:
                def __init__(self):
                    self.entries = [{"to": "contact@severine-lesourd.com", "status": "sent"}]

                def save(self):
                    pass

            log = Log()
            findings = audit_inbox(messages, crm.records)
            self.assertEqual([f.intent for f in findings], [INTENT_BOUNCE, INTENT_AUTO_REPLY])
            report = apply_findings(findings, crm, sup, log)
            self.assertEqual(report["bounces"], 1)
            self.assertEqual(report["auto_replies"], 1)
            self.assertEqual(report["unmatched"], 0)
            pension = next(r for r in crm.records if r["company"] == "Pension")
            bsp = next(r for r in crm.records if r["company"] == "BSP Auto")
            self.assertEqual(pension["status"], "rebond")
            self.assertEqual(pension["bounce_severity"], SEVERITY_HARD)
            self.assertEqual(len(pension["exchange_history"]), 1)
            self.assertTrue(bsp["delivery_confirmed"])
            self.assertFalse(bsp["reply_received"])  # un accusé n'est pas une réponse humaine
            self.assertEqual(log.entries[0]["status"], "bounced")
            self.assertTrue(sup.is_suppressed("contact@severine-lesourd.com"))
            self.assertFalse(sup.is_suppressed("mailer-daemon@googlemail.com"))
            path = save_audit(findings, Path(tmp) / "audit.json")
            save_audit(findings, Path(tmp) / "audit.json")  # idempotent
            self.assertEqual(len(json.loads(path.read_text())["findings"]), 2)


class TestModelesEtMetriques(unittest.TestCase):
    def test_nouveaux_champs_survivent_au_round_trip(self):
        p = _prospect(lot="2026-11-04-lot5", discovered_at="2026-11-04",
                      email_status="brouillon_créé", next_action="valider",
                      commercial_priority="haute", email_dns_status=MX_OK,
                      scores={"refonte": {"score": 75}},
                      evidences=[_ev(EVIDENCE_JOURNEY_GAP)])
        again = Prospect.from_dict(json.loads(json.dumps(p.to_dict())))
        self.assertEqual(again.lot, "2026-11-04-lot5")
        self.assertEqual(again.email_status, "brouillon_créé")
        self.assertEqual(again.scores["refonte"]["score"], 75)
        self.assertEqual(again.evidences[0].kind, EVIDENCE_JOURNEY_GAP)
        self.assertEqual(again.validate(), [])

    def test_deliverabilite_distingue_envoye_et_delivre(self):
        from prospecto.metrics import _deliverability

        entries = [{"to": "a@a.fr", "status": "sent"}, {"to": "b@b.fr", "status": "bounced"},
                   {"to": "c@c.fr", "status": "sent"}]
        audit = [{"intent": "rebond", "severity": "dur", "company": "B"},
                 {"intent": "auto_reply", "company": "A"}]
        d = _deliverability(entries, [], audit)
        self.assertEqual(d["sent"], 3)
        self.assertEqual(d["hard_bounces"], 1)
        self.assertEqual(d["auto_replies"], 1)
        self.assertEqual(d["human_replies"], 0)
        self.assertEqual(d["delivery_confirmed"], 1)
        self.assertEqual(d["delivery_unconfirmed"], 1)
        self.assertEqual(d["bounce_rate"], 33.3)

    def test_ventilation_par_lot(self):
        from prospecto.metrics import _by_lot

        records = [{"lot": "L5", "tier": "haute", "email_verification": "verified",
                    "status": "brouillon_créé"},
                   {"lot": "L5", "tier": "moyenne", "status": "contacté"},
                   {"tier": "haute", "status": "rebond"}]
        lots = {b["lot"]: b for b in _by_lot(records, [], None)}
        self.assertEqual(lots["L5"]["prospects"], 2)
        self.assertEqual(lots["L5"]["brouillons"], 1)
        self.assertEqual(lots["L5"]["envoyés"], 1)
        self.assertIn("antérieur au suivi par lot", lots)


class TestIdentiteInchangee(unittest.TestCase):
    def test_signature_officielle(self):
        self.assertEqual(config.SENDER_NAME, "Martin BOURASSEAU")
        sig = config.signature()
        self.assertIn("Martin BOURASSEAU", sig)
        self.assertIn("Création de sites web · Refonte · Agents IA · Automatisation", sig)
        self.assertNotIn("Boiss" + "eau", sig)


if __name__ == "__main__":
    unittest.main()
