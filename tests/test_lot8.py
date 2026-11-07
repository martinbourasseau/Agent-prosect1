"""Lot 8 — personnalisation par interlocuteur, audit Gmail et neuf catégories.

Chaque test verrouille un défaut réellement rencontré pendant la mission du
6 novembre 2026, pour qu'il ne revienne pas au lot suivant.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from prospecto import config
from prospecto.inbox_audit import (
    classify_inbound, INTENT_DELIVERY_CHALLENGE, INTENT_HUMAN, INTENT_AUTO_REPLY,
    INTENT_OPT_OUT, INTENT_BOUNCE,
)
from prospecto.messaging import compose_email, check_email_v4
from prospecto.metrics import pipeline_categories
from prospecto.models import Prospect
from prospecto.personalization import (
    LotRotation, check_lot_diversity, detect_role_family, benefit_for,
    build_demo, DEMO_OPENERS, SITE_ONLY_DEMO_OPENERS, ROLE_BENEFITS,
)
from prospecto.references import load_references, reference_by_id
from prospecto.reconcile import reconcile_sent
from prospecto.sender import Sender
from prospecto.suppression import SuppressionList

ROOT = Path(__file__).resolve().parents[1]
LOT_PATH = ROOT / "data" / "prospects" / "campagne-2026-11-06-lot8.json"
CAMPAIGN_PATH = ROOT / "data" / "campaigns" / "2026-11-06-lot8.json"


def make_prospect(**kw) -> Prospect:
    """Prospect minimal valide pour les tests de composition."""
    base = {"company": "Exemple", "domain": "exemple.fr", "sector": "services",
            "contact_email": "contact@exemple.fr"}
    base.update(kw)
    return Prospect(**base)


def lot8() -> list[dict]:
    return json.loads(LOT_PATH.read_text(encoding="utf-8"))


class RoleAwarePersonalizationTests(unittest.TestCase):
    """La fonction publiée change l'angle ; une fonction inconnue n'invente rien."""

    def test_familles_reconnues(self):
        cases = {
            "Gérant (directeur de la publication)": "dirigeant",
            "Artisan couvreur, seul à son compte": "dirigeant",
            "Président": "dirigeant",
            "Responsable commercial": "commercial",
            "Contact commercial (boîte Sales)": "commercial",
            "Secrétariat": "administratif",
            "Responsable administratif et financier": "administratif",
            "Responsable d'exploitation": "exploitation",
            "Directeur technique": "technique",
        }
        for role, expected in cases.items():
            self.assertEqual(detect_role_family(role), expected, role)

    def test_fonction_inconnue_ne_declenche_aucun_angle(self):
        for role in ("", "Amandine et Damien", "rejoint en 2022", "l.cachat"):
            self.assertEqual(detect_role_family(role), "")

    def test_benefice_explicite_prime_sur_l_angle_par_role(self):
        p = make_prospect(contact_role="Gérant",
                     benefit="un bénéfice écrit pour cette entreprise")
        self.assertEqual(benefit_for(p), "un bénéfice écrit pour cette entreprise")

    def test_benefice_deduit_de_la_fonction(self):
        p = make_prospect(contact_role="Gérant")
        self.assertEqual(benefit_for(p), ROLE_BENEFITS["dirigeant"])

    def test_sans_fonction_ni_benefice_aucune_invention(self):
        self.assertEqual(benefit_for(make_prospect()), "")

    def test_benefice_insere_dans_le_message(self):
        p = Prospect.from_dict({
            "company": "Test SARL", "domain": "test.fr", "sector": "services",
            "contact_email": "contact@test.fr", "contact_role": "Gérant",
            "benefit": "moins de ressaisie pour vos équipes",
            "custom_hook": "Votre formulaire demande trois pièces jointes.",
            "observation": "Elles arrivent souvent incomplètes.",
            "recommended_service": "un dépôt guidé qui contrôle chaque pièce",
            "demo_detail": "démo d'un dossier complet dès le premier envoi",
            "solution_type": "automatisation_admin", "needs": ["automatisation"],
            "evidences": [{"kind": "processus_manuel",
                           "source_url": "https://test.fr/contact",
                           "quote": "Trois pièces jointes sont demandées.",
                           "observed_at": "2026-11-06",
                           "detail": "Les dossiers arrivent incomplets."}]})
        body = compose_email(p, variant="automation_ia", reference=None).body
        self.assertIn("moins de ressaisie pour vos équipes", body)


class DemoOpenerCoherenceTests(unittest.TestCase):
    """Une « maquette » n'a pas de sujet quand la solution n'est pas un site."""

    def test_amorce_maquette_reservee_aux_sites(self):
        self.assertTrue(SITE_ONLY_DEMO_OPENERS)
        for i in SITE_ONLY_DEMO_OPENERS:
            self.assertIn("maquette", DEMO_OPENERS[i].lower())

    def test_pas_de_maquette_pour_une_automatisation(self):
        rotation = LotRotation(["A", "B", "C", "D", "E"])
        for company in rotation.companies:
            for solution in ("automatisation_admin", "devis_automatise",
                             "formulaire_intelligent", "reservation_en_ligne",
                             "commande_en_ligne", "agent_ia"):
                phrase = build_demo("démo d'un dossier complet", company,
                                    rotation=rotation, solution_type=solution)
                self.assertNotIn("maquette", phrase.lower(), (company, solution))

    def test_maquette_reste_possible_pour_un_site(self):
        rotation = LotRotation(["A", "B", "C", "D", "E"])
        seen = [build_demo("démo du site", c, rotation=rotation,
                           solution_type="creation_site") for c in rotation.companies]
        self.assertTrue(any("maquette" in s.lower() for s in seen))

    def test_lot8_aucune_maquette_hors_site(self):
        for entry in json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))["emails"]:
            if entry["solution_type"] not in ("creation_site", "refonte_site"):
                self.assertNotIn("maquette", entry["body"].lower(), entry["company"])


class ReferenceAuthorshipTests(unittest.TestCase):
    """La propriété est déclarée ; la conception n'est pas revendiquée."""

    def test_phrases_sans_revendication_de_conception(self):
        for ref in load_references():
            for sentence in (ref.example_sentence, ref.example_sentence_alt):
                if not sentence:
                    continue
                low = sentence.lower()
                self.assertNotIn("que j'ai conçu", low)
                self.assertNotIn("que je développe", low)
                self.assertNotIn("que j'ai développé", low)

    def test_formulation_neutre_et_nommee(self):
        # v7 : formulation neutre demandée — on nomme le projet, on ne
        # revendique ni la conception ni la propriété.
        for ref in load_references():
            low = ref.example_sentence.lower()
            self.assertIn(ref.name.lower(), low)
            self.assertNotIn("mon groupe", low)

    def test_synatrap_decrit_comme_un_projet_autour_des_agents_ia(self):
        ref = reference_by_id("synatrap")
        self.assertIn("projet autour des agents ia", ref.example_sentence.lower())


class DeliveryChallengeTests(unittest.TestCase):
    """Un challenge Mailinblack n'est ni une réponse, ni une délivrance."""

    TEXT = ("Un clic pour délivrer votre email ! Je demande à tout nouvel expéditeur "
            "de confirmer qu'il est bien humain.")

    def test_challenge_reconnu_par_expediteur(self):
        res = classify_inbound("alpha_mecanique@invitations.mailinblack.com",
                               "Re: vos demandes de devis", "Bonjour")
        self.assertEqual(res["intent"], INTENT_DELIVERY_CHALLENGE)

    def test_challenge_reconnu_par_le_corps(self):
        res = classify_inbound("contact@entreprise.fr", "Re: devis", self.TEXT)
        self.assertEqual(res["intent"], INTENT_DELIVERY_CHALLENGE)

    def test_challenge_n_est_pas_une_reponse_humaine(self):
        res = classify_inbound("x@invitations.mailinblack.com", "Re:", self.TEXT)
        self.assertNotIn(res["intent"], (INTENT_HUMAN, INTENT_AUTO_REPLY))

    def test_vraie_reponse_humaine_reste_humaine(self):
        res = classify_inbound("dirigeant@entreprise.fr", "Re: votre message",
                               "Bonjour, votre sujet m'intéresse, quels sont vos tarifs ?")
        self.assertEqual(res["intent"], INTENT_HUMAN)

    def test_opposition_prime_sur_le_challenge(self):
        res = classify_inbound("x@invitations.mailinblack.com", "Re:",
                               "Ne pas me relancer. " + self.TEXT)
        self.assertEqual(res["intent"], INTENT_OPT_OUT)

    def test_rebond_prime_sur_tout(self):
        res = classify_inbound("mailer-daemon@googlemail.com",
                               "Delivery Status Notification (Failure)", self.TEXT)
        self.assertEqual(res["intent"], INTENT_BOUNCE)

    def test_challenge_exclu_des_delivrances_confirmees(self):
        from prospecto.metrics import _deliverability
        entries = [{"to": "a@x.fr", "status": "sent", "company": "A"}]
        audit = [{"intent": INTENT_DELIVERY_CHALLENGE, "company": "A",
                  "recipient": "a@x.fr"}]
        d = _deliverability(entries, [], audit)
        self.assertEqual(d["delivery_challenges"], 1)
        self.assertEqual(d["delivery_confirmed"], 0)


class _Item:
    def __init__(self, **kw):
        self.status = kw.get("status", "pending")
        self.to = kw.get("to", "")
        self.subject = kw.get("subject", "")
        self.campaign = kw.get("campaign", "")
        self.gmail_message_id = kw.get("gmail_message_id", "")
        self.gmail_draft_id = kw.get("gmail_draft_id", None)
        self.updated_at = ""
        self.history = []

    def save(self):
        pass


class _Queue:
    def __init__(self, items):
        self.items = items

    def save(self):
        pass


class _CRM:
    def __init__(self, records):
        self.records = records

    def save(self):
        pass


class _Log:
    def __init__(self):
        self.entries = []

    def record(self, **kw):
        self.entries.append(kw)

    def save(self):
        pass


class ReconcileWithoutQueueTests(unittest.TestCase):
    """Huit envois du 3 novembre n'avaient aucune entrée en file : ils étaient perdus."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.history_path = Path(self._tmp.name) / "reconciliations.json"
        self.rec = {"email": "deja@exemple.fr", "company": "Déjà Contacté",
                    "status": "non_contacté"}
        self.crm = _CRM([self.rec])
        self.queue = _Queue([])
        self.log = _Log()
        self.obs = [{"to": "deja@exemple.fr", "subject": "Bonjour",
                     "gmail_message_id": "msg-1", "sent_at": "2026-11-03"}]

    def test_envoi_sans_file_est_journalise(self):
        res = reconcile_sent(self.obs, self.crm, self.queue, self.log,
                           history_path=self.history_path)
        self.assertEqual(res.recorded_without_queue, 1)
        self.assertEqual(len(self.log.entries), 1)
        self.assertEqual(self.rec["status"], "contacté")
        self.assertEqual(self.rec["gmail_message_id"], "msg-1")

    def test_historique_trace_la_transition(self):
        reconcile_sent(self.obs, self.crm, self.queue, self.log,
                           history_path=self.history_path)
        self.assertTrue(any(h["action"] == "reconciled_sent_without_queue"
                            for h in self.rec.get("history", [])))

    def test_pas_de_double_comptage(self):
        reconcile_sent(self.obs, self.crm, self.queue, self.log,
                           history_path=self.history_path)
        res = reconcile_sent(self.obs, self.crm, self.queue, self.log,
                           history_path=self.history_path)
        self.assertEqual(res.recorded_without_queue, 0)
        self.assertEqual(len(self.log.entries), 1)

    def test_statut_avance_non_retrograde(self):
        for advanced in ("opposition", "rebond", "demande_rdv", "suspendu"):
            self.rec["status"] = advanced
            reconcile_sent(self.obs, self.crm, self.queue, self.log,
                           history_path=self.history_path)
            self.assertEqual(self.rec["status"], advanced)

    def test_destinataire_inconnu_reste_signale(self):
        res = reconcile_sent([{"to": "personne@autre.fr", "subject": "X"}],
                             self.crm, self.queue, self.log,
                             history_path=self.history_path)
        self.assertEqual(len(res.unmatched), 1)


class PipelineCategoriesTests(unittest.TestCase):
    """Les neuf catégories doivent rester exclusives côté délivrance."""

    def _metrics(self, **kw):
        d = {"sent": 46, "delivery_confirmed": 3, "hard_bounces": 1, "soft_bounces": 0,
             "delivery_challenges": 1, "human_replies": 1, "auto_replies": 2,
             "opt_outs": 1}
        d.update(kw)
        return {"deliverability": d}

    def test_somme_des_categories_exclusives(self):
        p = pipeline_categories(self._metrics(), [])
        self.assertEqual(p["delivres_confirmes"] + p["delivrance_non_confirmee"]
                         + p["rebonds"] + p["challenges_delivrance"], p["envoyes"])
        self.assertTrue(p["controle_exclusif"])

    def test_envoye_n_est_pas_delivre(self):
        p = pipeline_categories(self._metrics(), [])
        self.assertEqual(p["envoyes"], 46)
        self.assertEqual(p["delivres_confirmes"], 3)
        self.assertGreater(p["delivrance_non_confirmee"], 0)

    def test_statut_draft_compte_comme_brouillon(self):
        items = [_Item(status="draft", gmail_draft_id="r1"),
                 _Item(status="pending", gmail_draft_id="r2"),
                 _Item(status="approved", gmail_draft_id="r3")]
        self.assertEqual(pipeline_categories(self._metrics(), items)["brouillons"], 3)

    def test_suspendu_et_obsolete_exclus_des_brouillons(self):
        items = [_Item(status="suspended", gmail_draft_id="r1"),
                 _Item(status="obsolete"), _Item(status="sent", gmail_draft_id="r2")]
        p = pipeline_categories(self._metrics(), items)
        self.assertEqual(p["brouillons"], 0)
        self.assertEqual(p["en_attente"], 0)
        self.assertEqual(p["suspendus"], 1)
        self.assertEqual(p["obsoletes"], 1)

    def test_prepare_sans_brouillon_est_en_attente(self):
        p = pipeline_categories(self._metrics(), [_Item(status="pending")])
        self.assertEqual(p["en_attente"], 1)
        self.assertEqual(p["brouillons"], 0)

    def test_opposition_compte_aussi_comme_reponse_humaine(self):
        p = pipeline_categories(self._metrics(), [])
        self.assertEqual(p["oppositions"], 1)
        self.assertEqual(p["reponses_humaines"], 1)

    def test_definitions_fournies(self):
        p = pipeline_categories(self._metrics(), [])
        for key in ("envoyes", "delivres_confirmes", "delivrance_non_confirmee",
                    "challenges_delivrance", "brouillons", "en_attente"):
            self.assertIn(key, p["definitions"])


class Lot8DataIntegrityTests(unittest.TestCase):
    """Qualification : preuves datées, aucune adresse déduite du domaine."""

    def setUp(self):
        self.lot = lot8()

    def test_cinq_fiches(self):
        self.assertEqual(len(self.lot), 5)

    def test_preuves_datees_et_sourcees(self):
        for p in self.lot:
            self.assertGreaterEqual(len(p["evidences"]), 3, p["company"])
            for ev in p["evidences"]:
                self.assertTrue(ev["source_url"].startswith("https://"), p["company"])
                self.assertEqual(ev["observed_at"], "2026-11-06", p["company"])
                self.assertTrue(ev["quote"].strip(), p["company"])
                self.assertTrue(ev["detail"].strip(), p["company"])

    def test_preuves_sur_le_domaine_du_prospect(self):
        for p in self.lot:
            for ev in p["evidences"]:
                self.assertIn(p["domain"], ev["source_url"], p["company"])

    def test_domaine_email_correspond_au_site_sauf_exception_documentee(self):
        for p in self.lot:
            email = p.get("contact_email") or ""
            if not email:
                continue
            edom = email.split("@")[1].lower()
            if edom != p["domain"]:
                # Seules exceptions tolérées : boîte grand public d'un artisan,
                # ou domaine de messagerie distinct du site, explicitement noté.
                self.assertIn(edom, ("gmail.com", "lecentreformation.fr"), p["company"])
                self.assertTrue(p["notes"].strip())

    def test_prospect_sans_email_sans_brouillon(self):
        campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
        drafted = {e["to"].lower() for e in campaign["emails"]}
        for p in self.lot:
            if not p.get("contact_email"):
                self.assertEqual(p["email_verification"], "non_trouve")
                self.assertFalse(drafted & {""}, p["company"])
                self.assertTrue(any(s["company"] == p["company"]
                                    for s in campaign["prospects_sans_brouillon"]))

    def test_quatre_brouillons_pour_quatre_adresses(self):
        contactables = [p for p in self.lot if p.get("contact_email")]
        campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(contactables), 4)
        self.assertEqual(len(campaign["emails"]), 4)
        self.assertEqual({p["contact_email"] for p in contactables},
                         {e["to"] for e in campaign["emails"]})

    def test_responsable_et_fonction_renseignes_ou_vide(self):
        for p in self.lot:
            if p.get("contact_name"):
                self.assertTrue(p["contact_role"].strip(), p["company"])
                self.assertTrue(p["contact_name_source"].startswith("https://"))

    def test_solutions_variees_et_non_systematiquement_ia(self):
        types = [p["solution_type"] for p in self.lot]
        self.assertEqual(len(set(types)), 5)
        self.assertNotIn("agent_ia", types)


class Lot8MessageQualityTests(unittest.TestCase):
    """Les messages réellement stockés respectent les garde-fous."""

    def setUp(self):
        self.campaign = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
        self.by_company = {p["company"]: p for p in lot8()}

    def test_check_email_v4_sur_chaque_message(self):
        for e in self.campaign["emails"]:
            pr = Prospect.from_dict(self.by_company[e["company"]])
            from prospecto.models import GeneratedEmail
            em = GeneratedEmail(to=e["to"], subject=e["subject"], body=e["body"],
                                company=e["company"], need=e["need"],
                                evidence_sources=e["evidence_sources"])
            self.assertEqual(check_email_v4(em, pr), [], e["company"])

    def test_signature_officielle(self):
        for e in self.campaign["emails"]:
            self.assertIn("Martin BOURASSEAU", e["body"])
            self.assertIn("Création de sites web · Refonte · Agents IA · Automatisation", e["body"])
            self.assertIn("https://prospecto.website", e["body"])
            self.assertNotIn("Boisseau", e["body"])

    def test_opt_out_present(self):
        for e in self.campaign["emails"]:
            self.assertIn("ne pas me relancer", e["body"])

    def test_observation_verifiee_presente_dans_chaque_message(self):
        for e in self.campaign["emails"]:
            obs = self.by_company[e["company"]]["observation"]
            self.assertIn(obs, e["body"], e["company"])

    def test_diversite_du_lot(self):
        from prospecto.models import GeneratedEmail
        emails = [GeneratedEmail(to=e["to"], subject=e["subject"], body=e["body"],
                                 company=e["company"], need=e["need"],
                                 evidence_sources=e["evidence_sources"])
                  for e in self.campaign["emails"]]
        rep = check_lot_diversity(emails)
        self.assertEqual(rep.problems, [])
        self.assertEqual(rep.distinct_ctas, 4)
        self.assertEqual(rep.distinct_subjects, 4)

    def test_longueur_sous_le_plafond(self):
        for e in self.campaign["emails"]:
            self.assertLessEqual(len(re.findall(r"\S+", e["body"])),
                                 config.MAX_BODY_WORDS, e["company"])

    def test_brouillons_traces_avec_label(self):
        self.assertEqual(self.campaign["gmail_label_id"], "Label_6")
        self.assertEqual(self.campaign["gmail_label_name"], "Prospection/2026-11-06-lot8")
        self.assertEqual(self.campaign["drafts_created"], 4)
        self.assertFalse(self.campaign["sent"])
        # Audit du 6/11 : 3 des 4 brouillons ont été envoyés manuellement depuis
        # Gmail à 16:40. Seul Ripaud est resté brouillon. Le test suit la réalité
        # vérifiée dans Gmail au lieu de la figer sur l'état initial.
        for d in self.campaign["drafts"]:
            self.assertTrue(d["gmail_draft_id"])
            self.assertTrue(d["gmail_message_id"])
            self.assertIn(d["status"], ("draft", "sent"))
        still_draft = [d for d in self.campaign["drafts"] if d["status"] == "draft"]
        self.assertEqual([d["to"] for d in still_draft], ["info@ripaudpepinieres.com"])


class Lot8SafetyTests(unittest.TestCase):
    """Oppositions, suspensions et adresses non vérifiées restent hors d'atteinte."""

    def test_liste_de_suppression_intacte(self):
        sup = SuppressionList()
        for email in ("celarenarde@gmail.com", "contact@severine-lesourd.com"):
            self.assertTrue(sup.is_suppressed(email), email)

    def test_aucun_destinataire_du_lot8_en_suppression(self):
        sup = SuppressionList()
        for p in lot8():
            email = p.get("contact_email") or ""
            if email:
                self.assertFalse(sup.is_suppressed(email), email)

    def test_uzes_reste_suspendu(self):
        crm = json.loads((ROOT / "data" / "crm" / "prospects.json").read_text(encoding="utf-8"))
        rec = next(r for r in crm["prospects"]
                   if r.get("email") == "uzeslocation.30700@gmail.com")
        self.assertTrue(Sender()._is_blocked(rec))

    def test_b3r_et_gallia_absents_du_lot8(self):
        for p in lot8():
            self.assertNotIn("gallia", (p.get("contact_email") or "").lower())
            self.assertNotIn("gallia", p["domain"].lower())

    def test_prospect_sans_email_non_contactable(self):
        crm = json.loads((ROOT / "data" / "crm" / "prospects.json").read_text(encoding="utf-8"))
        rec = next(r for r in crm["prospects"] if r.get("company") == "Beaujolais Réception")
        self.assertEqual(rec.get("contactability"), "non_contactable")
        self.assertTrue(Sender()._is_blocked(rec))

    def test_preflight_reste_bloque(self):
        # preflight() persiste son résultat DNS dans le fichier de réglages :
        # on travaille sur une copie pour ne pas réécrire la production.
        import shutil
        import tempfile
        from prospecto.sender import SETTINGS_PATH

        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "v4-settings.json"
            shutil.copyfile(SETTINGS_PATH, isolated)
            ok, issues = Sender(settings_path=isolated).preflight()
        self.assertFalse(ok, "aucun envoi ne doit être autorisé dans cet état")
        self.assertTrue(any("enabled=false" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
