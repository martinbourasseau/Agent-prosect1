"""Tests du lot 7 : personnalisation v5, rotation par lot, garde-fous anti-générique.

Aucun accès réseau. Ces tests verrouillent les corrections apportées au moteur :
segment observation, familles de solution, amorces variées, contrôle de diversité,
détection des tournures commerciales creuses et comparaison insensible à la casse.
"""
from __future__ import annotations

import unittest

from prospecto import config
from prospecto.messaging import compose_email, check_email_v4, select_cta_demo
from prospecto.models import Prospect, EVIDENCE_PROCESS_MANUAL, NEED_AUTOMATISATION
from prospecto.personalization import (
    CTA_VARIANTS,
    DEMO_OPENERS,
    GENERIC_PATTERNS,
    IA_SOLUTIONS,
    LEGACY_SERVICE_LINES,
    PROPOSITION_OPENERS,
    SOLUTION_TYPES,
    LotRotation,
    build_demo,
    build_proposition,
    check_lot_diversity,
    generic_problems,
    pick_opener,
    uses_legacy_service_line,
)


def prospect(company="Atelier Test", **kw):
    base = dict(
        company=company, domain="exemple.fr", contact_email="contact@exemple.fr",
        sector="Services", city="Nantes", department="44", website="https://exemple.fr/",
        needs=[NEED_AUTOMATISATION],
        custom_hook="Votre page devis demande d'envoyer les pièces par e-mail.",
        recommended_service="un formulaire qui collecte les pièces et prépare le devis",
        demo_detail="démo d'une demande complète transformée en devis",
        evidences=[{"kind": EVIDENCE_PROCESS_MANUAL, "source_url": "https://exemple.fr/contact",
                    "quote": "Envoyez-nous vos pièces par e-mail.", "observed_at": "2026-11-07"}],
    )
    base.update(kw)
    return Prospect.from_dict(base)


class SolutionFamilyTests(unittest.TestCase):
    def test_huit_familles_disponibles(self):
        self.assertEqual(len(SOLUTION_TYPES), 8)

    def test_une_seule_famille_est_ia(self):
        self.assertEqual(len(IA_SOLUTIONS), 1)

    def test_ia_n_est_pas_la_famille_par_defaut(self):
        self.assertEqual(list(SOLUTION_TYPES)[0], "creation_site")

    def test_famille_inconnue_refusee(self):
        p = prospect(solution_type="magie")
        self.assertTrue(any("famille de solution inconnue" in x
                            for x in check_email_v4(compose_email(p), p)))

    def test_famille_connue_acceptee(self):
        p = prospect(solution_type="formulaire_intelligent")
        self.assertEqual(check_email_v4(compose_email(p), p), [])


class ObservationTests(unittest.TestCase):
    def test_observation_incluse_apres_l_accroche(self):
        p = prospect(observation="Chaque dossier revient donc deux fois")
        parts = compose_email(p).body.split("\n\n")
        self.assertEqual(parts[1], p.custom_hook)
        self.assertEqual(parts[2], "Chaque dossier revient donc deux fois.")

    def test_observation_absente_ne_casse_rien(self):
        p = prospect(observation="")
        self.assertEqual(check_email_v4(compose_email(p), p), [])
        self.assertNotIn("\n\n\n\n", compose_email(p).body)

    def test_ponctuation_ajoutee_si_manquante(self):
        p = prospect(observation="Le suivi reste manuel")
        self.assertIn("Le suivi reste manuel.", compose_email(p).body)

    def test_ponctuation_existante_preservee(self):
        p = prospect(observation="Cela vous parle ?")
        self.assertIn("Cela vous parle ?", compose_email(p).body)
        self.assertNotIn("Cela vous parle ?.", compose_email(p).body)


class OpenerTests(unittest.TestCase):
    def test_amorces_stables_sans_lot(self):
        self.assertEqual(pick_opener("A", "demo"), pick_opener("A", "demo"))

    def test_amorce_de_proposition_grammaticale(self):
        for company in ("A", "B", "C", "Bonbon Foliz", "L'Ô de Claise"):
            sentence = build_proposition("un formulaire de devis", company)
            self.assertTrue(sentence.endswith("."))
            self.assertIn("un formulaire de devis", sentence)

    def test_phrase_deja_complete_non_denaturee(self):
        text = "Je modernise votre parcours de commande."
        self.assertEqual(build_proposition(text, "A"), text)

    def test_repli_si_aucune_prestation(self):
        self.assertEqual(build_proposition("", "A", fallback="Trame."), "Trame.")

    def test_demo_toujours_gratuite_et_sans_engagement(self):
        for company in ("A", "B", "C", "D", "E", "F"):
            sentence = build_demo("démo d'un devis", company).lower()
            self.assertIn("sans engagement", sentence)
            self.assertTrue("gratuit" in sentence)
            self.assertTrue("démonstration" in sentence or "maquette" in sentence)

    def test_demo_repli_sans_detail(self):
        self.assertEqual(build_demo("", "A", fallback="Trame démo."), "Trame démo.")


class LotRotationTests(unittest.TestCase):
    def test_aucune_repetition_tant_que_le_lot_tient_dans_le_jeu(self):
        companies = [f"Entreprise {i}" for i in range(len(PROPOSITION_OPENERS))]
        rot = LotRotation(companies)
        picked = [pick_opener(c, "proposition", rot) for c in companies]
        self.assertEqual(len(set(picked)), len(companies))

    def test_reproductible_quel_que_soit_l_ordre_d_entree(self):
        a = LotRotation(["C", "A", "B"])
        b = LotRotation(["B", "C", "A"])
        for company in ("A", "B", "C"):
            self.assertEqual(pick_opener(company, "cta", a), pick_opener(company, "cta", b))

    def test_segments_decales_entre_eux(self):
        rot = LotRotation(["A"])
        self.assertNotEqual(rot.index("A", "proposition"), rot.index("A", "demo"))

    def test_entreprise_hors_lot_ne_plante_pas(self):
        rot = LotRotation(["A", "B"])
        self.assertIn(pick_opener("Inconnue", "demo", rot), DEMO_OPENERS)

    def test_lot_plus_grand_que_le_jeu_repasse_par_le_debut(self):
        companies = [f"E{i}" for i in range(len(DEMO_OPENERS) + 2)]
        rot = LotRotation(companies)
        picked = [pick_opener(c, "demo", rot) for c in companies]
        self.assertEqual(len(picked), len(companies))
        self.assertLessEqual(len(set(picked)), len(DEMO_OPENERS))

    def test_cta_utilise_la_rotation_du_lot(self):
        rot = LotRotation(["A", "B"])
        self.assertEqual(select_cta_demo(prospect("A"), rot), pick_opener("A", "cta", rot))


class DiversityTests(unittest.TestCase):
    def _lot(self, n):
        companies = [f"Entreprise {i}" for i in range(n)]
        rot = LotRotation(companies)
        return [compose_email(prospect(c), "automation_ia", rotation=rot) for c in companies]

    def test_lot_diversifie_conforme(self):
        report = check_lot_diversity(self._lot(5))
        self.assertTrue(report.ok, report.problems)
        self.assertEqual(report.distinct_subjects, 5)
        self.assertEqual(report.distinct_proposition_openers, 5)

    def test_corps_duplique_detecte(self):
        emails = self._lot(2)
        emails[1].body = emails[0].body
        self.assertIn("corps de message dupliqués dans le lot",
                      check_lot_diversity(emails).problems)

    def test_objet_duplique_detecte(self):
        emails = self._lot(2)
        emails[1].subject = emails[0].subject
        self.assertIn("objets dupliqués dans le lot", check_lot_diversity(emails).problems)

    def test_amorce_majoritaire_detectee(self):
        emails = self._lot(5)
        opener = PROPOSITION_OPENERS[0]
        for email in emails[:3]:
            parts = email.body.split("\n\n")
            parts[2] = opener + "un formulaire de devis."
            email.body = "\n\n".join(parts)
        problems = check_lot_diversity(emails).problems
        self.assertTrue(any("amorce de proposition identique" in p for p in problems), problems)

    def test_petit_lot_tolere_une_repetition(self):
        self.assertTrue(check_lot_diversity(self._lot(2)).ok)

    def test_lot_vide(self):
        self.assertTrue(check_lot_diversity([]).ok)


class GenericGuardTests(unittest.TestCase):
    def test_accroche_generique_interdite(self):
        self.assertTrue(generic_problems("Je suis tombé sur votre entreprise et je voulais vous proposer mes services."))

    def test_fausse_urgence_interdite(self):
        self.assertTrue(generic_problems("Profitez de cette offre limitée."))

    def test_compliment_artificiel_interdit(self):
        self.assertTrue(generic_problems("Votre magnifique site mérite mieux."))

    def test_realisation_deja_faite_interdite(self):
        self.assertTrue(generic_problems("J'ai déjà réalisé pour vous une maquette."))

    def test_promesse_de_resultat_interdite(self):
        self.assertTrue(generic_problems("Je vous garantis un doublement des ventes."))

    def test_texte_sobre_accepte(self):
        self.assertEqual(generic_problems("Votre page devis demande cinq informations par e-mail."), [])

    def test_trame_heritage_reconnue(self):
        self.assertTrue(uses_legacy_service_line(LEGACY_SERVICE_LINES[0] + "."))

    def test_trame_heritage_refusee_quand_prestation_connue(self):
        p = prospect()
        email = compose_email(p)
        email.body = email.body.replace(
            build_proposition(p.recommended_service, p.company), LEGACY_SERVICE_LINES[3] + ".")
        self.assertTrue(any("présentation de services générique" in x
                            for x in check_email_v4(email, p)))

    def test_accroche_de_repli_refusee(self):
        p = prospect(custom_hook="")
        self.assertTrue(any("accroche de repli générique" in x
                            for x in check_email_v4(compose_email(p), p)))

    def test_motifs_compiles(self):
        import re
        for pattern, _ in GENERIC_PATTERNS:
            re.compile(pattern)


class CaseInsensitiveGuardTests(unittest.TestCase):
    """Régression : « Sans engagement » en tête de phrase était jugé absent."""

    def test_mention_en_capitale_reconnue(self):
        p = prospect()
        email = compose_email(p)
        email.body = email.body.replace("sans engagement", "Sans engagement")
        self.assertEqual(check_email_v4(email, p), [])

    def test_mention_reellement_absente_toujours_refusee(self):
        p = prospect()
        email = compose_email(p)
        email.body = email.body.replace("sans engagement", "sans condition")
        email.body = email.body.replace("Sans engagement", "Sans condition")
        self.assertTrue(any("sans engagement" in x for x in check_email_v4(email, p)))

    def test_opt_out_en_capitale_reconnu(self):
        p = prospect()
        email = compose_email(p)
        email.body = email.body.replace("ne pas me relancer", "Ne pas me relancer")
        self.assertEqual(check_email_v4(email, p), [])


class BudgetTests(unittest.TestCase):
    def test_plafond_documente_a_170_mots(self):
        self.assertEqual(config.MAX_BODY_WORDS, 170)

    def test_structure_complete_reste_sous_le_plafond(self):
        p = prospect(observation="Chaque dossier revient donc deux fois avant d'être complet.")
        self.assertEqual(check_email_v4(compose_email(p), p), [])

    def test_amorces_demo_plus_courtes_que_la_v4(self):
        v4 = ("Je peux vous préparer gratuitement une première démonstration personnalisée, "
              "sans engagement : ")
        self.assertTrue(all(len(o.split()) < len(v4.split()) for o in DEMO_OPENERS))


class IdentityTests(unittest.TestCase):
    def test_signature_exacte_sur_toutes_les_variantes(self):
        for variant in ("automation_ia", "refonte", "synatrap_ia", "with_example",
                        "demo_site", "short_hook"):
            body = compose_email(prospect(), variant).body
            self.assertIn("Martin BOURASSEAU", body)
            self.assertNotIn("boisseau", body.lower())
            self.assertIn("https://prospecto.website", body)
            self.assertIn("ne pas me relancer", body.lower())

    def test_jeu_de_cta_etendu(self):
        self.assertEqual(len(CTA_VARIANTS), 7)
        self.assertEqual(len(set(CTA_VARIANTS)), 7)


if __name__ == "__main__":
    unittest.main()


class ReferenceCoherenceTests(unittest.TestCase):
    """La référence ne doit pas annoncer de l'IA quand on propose un formulaire."""

    def test_synatrap_presente_comme_automatisation_pour_un_formulaire(self):
        from prospecto.messaging import load_references
        refs = {r.id: r for r in load_references()}
        if "synatrap" not in refs:
            self.skipTest("bibliothèque de références absente")
        # v7 : mieux qu'une reformulation, la référence hors sujet est retirée.
        p = prospect(solution_type="formulaire_intelligent")
        body = compose_email(p, "synatrap_ia", reference=refs["synatrap"]).body
        self.assertNotIn("synatrap.com", body)
        self.assertNotIn("agents IA", body.split("Création de sites web")[0])

    def test_synatrap_garde_le_cadrage_ia_pour_un_agent(self):
        from prospecto.messaging import load_references
        refs = {r.id: r for r in load_references()}
        if "synatrap" not in refs:
            self.skipTest("bibliothèque de références absente")
        p = prospect(solution_type="agent_ia")
        body = compose_email(p, "synatrap_ia", reference=refs["synatrap"]).body
        self.assertIn("synatrap.com", body)
        self.assertIn("projet autour des agents IA", body)

    def test_sans_famille_de_solution_aucune_reference_forcee(self):
        from prospecto.messaging import load_references
        refs = {r.id: r for r in load_references()}
        if "synatrap" not in refs:
            self.skipTest("bibliothèque de références absente")
        p = prospect(solution_type="")
        body = compose_email(p, "synatrap_ia", reference=refs["synatrap"]).body
        self.assertNotIn("synatrap.com", body)

    def test_repli_si_aucune_formulation_alternative(self):
        from prospecto.references import Reference
        ref = Reference(id="x", name="X", url="https://x.fr", example_sentence="Base : {url}")
        self.assertEqual(ref.sentence(use_alt=True), "Base : https://x.fr")


class SuspensionSafetyTests(unittest.TestCase):
    """Une fiche suspendue ne doit jamais devenir un candidat à l'envoi."""

    def _record(self, **kw):
        base = {
            "company": "Test", "email": "test@example.fr", "tier": "haute",
            "email_verification": "verified", "score": 90, "status": "brouillon_créé",
            "proposed_email": {"subject": "s", "body": "b", "queue_id": "q1"},
            "id": "test", "campaign": "c", "variant": "refonte",
        }
        base.update(kw)
        return base

    def test_statut_suspendu_bloque(self):
        from prospecto.sender import Sender
        s = Sender()
        for field in ("status", "status_crm", "email_status", "contactability"):
            with self.subTest(field=field):
                r = self._record(**{field: "suspendu"})
                self.assertTrue(s._is_blocked(r))
                self.assertEqual(s.select_candidates([r], []), [])

    def test_horodatage_de_suspension_bloque_seul(self):
        from prospecto.sender import Sender
        s = Sender()
        r = self._record(suspended_at="2026-11-07T10:00:00+00:00")
        self.assertTrue(s._is_blocked(r))
        self.assertEqual(s.select_candidates([r], []), [])

    def test_opposition_et_rebond_bloquent(self):
        from prospecto.sender import Sender
        s = Sender()
        for st in ("opposition", "opposed", "désinscrit", "bounced", "plainte"):
            with self.subTest(status=st):
                self.assertTrue(s._is_blocked(self._record(status=st)))

    def test_casse_et_espaces_ignores(self):
        from prospecto.sender import Sender
        self.assertTrue(Sender()._is_blocked(self._record(status="  SUSPENDU  ")))

    def test_fiche_saine_reste_selectionnable(self):
        from prospecto.sender import Sender
        s = Sender()
        r = self._record()
        self.assertFalse(s._is_blocked(r))
        self.assertEqual(len(s.select_candidates([r], [])), 1)

    def test_suspension_dans_la_file_bloque_aussi(self):
        from prospecto.sender import Sender
        s = Sender()
        r = self._record()
        queue = [{"to": "test@example.fr", "status": "suspended"}]
        self.assertEqual(s.select_candidates([r], queue), [])

    def test_metriques_comptent_les_suspendus(self):
        from prospecto.metrics import _is_suspended
        self.assertTrue(_is_suspended({"status": "suspendu"}))
        self.assertTrue(_is_suspended({"suspended_at": "2026-11-07"}))
        self.assertFalse(_is_suspended({"status": "brouillon_créé"}))


class HumanReplyCountingTests(unittest.TestCase):
    """Une opposition est une réponse humaine, pas un silence."""

    def test_opposition_comptee_comme_reponse_humaine(self):
        from prospecto.metrics import _deliverability
        audit = [{"company": "A", "intent": "opposition"}]
        entries = [{"to": "a@a.fr", "status": "sent"}]
        d = _deliverability(entries, [], audit)
        self.assertEqual(d["human_replies"], 1)
        self.assertEqual(d["opt_outs"], 1)

    def test_accuse_automatique_pas_humain(self):
        from prospecto.metrics import _deliverability
        audit = [{"company": "B", "intent": "auto_reply"}]
        d = _deliverability([{"to": "b@b.fr", "status": "sent"}], [], audit)
        self.assertEqual(d["human_replies"], 0)
        self.assertEqual(d["auto_replies"], 1)

    def test_rebond_pas_humain(self):
        from prospecto.metrics import _deliverability
        audit = [{"company": "C", "intent": "rebond", "severity": "dur"}]
        d = _deliverability([{"to": "c@c.fr", "status": "sent"}], [], audit)
        self.assertEqual(d["human_replies"], 0)
        self.assertEqual(d["hard_bounces"], 1)

    def test_demande_de_rdv_comptee_humaine(self):
        from prospecto.metrics import _deliverability
        audit = [{"company": "D", "intent": "demande_rdv"}]
        d = _deliverability([{"to": "d@d.fr", "status": "sent"}], [], audit)
        self.assertEqual(d["human_replies"], 1)

    def test_metriques_reelles_coherentes(self):
        from prospecto.metrics import compute_metrics
        m = compute_metrics()
        d = m["deliverability"]
        self.assertGreaterEqual(d["human_replies"], d["opt_outs"],
                                "toute opposition est une réponse humaine")
