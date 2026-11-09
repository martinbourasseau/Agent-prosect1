"""Découverte par identité d'auteur — régressions sur les échecs réels.

Les deux premiers cas sont les pages d'agences qui ont fait échouer la
méthode lexicale les 2026-11-07. Elles contiennent des mots de besoin ;
elles doivent néanmoins être classées en argumentaire de tiers.
"""
from __future__ import annotations

import unittest

from prospecto.discovery import (
    ClaimClass, ProblemKind, SourceYield, analyse_page, classify_authorship,
    detect_broken_mailto, detect_contact_mismatch, detect_form_closure,
    detect_implied_consent, detect_phone_only, detect_qualification_gap,
    DIRECT_SOURCE_CHANNELS, DEPRECATED_CHANNELS,
)

# Extrait réel de la page qui a pollué la requête « besoin exprimé » sur Niort.
EXPRESSWEB = (
    "Vous exercez votre métier à Niort et vous n'avez pas encore de site internet "
    "- ou votre site actuel ne vous ramène aucun client ? C'est exactement pour "
    "ça qu'Expressweb existe. Nous créons des sites simples, efficaces et 100 % "
    "gérables par vous. Toutes nos offres - site vitrine, boutique en ligne, SEO, "
    "pub, applications, automatisation, IA. Agence web et création de site à Niort."
)
STRUCTOLABS = (
    "Cabinet conseil spécialisé automatisation, basé en Charente-Maritime. "
    "Trois services pour les entreprises de Niort. Solutions sur mesure pour "
    "entreprises du secteur assurance. Un diagnostic gratuit de 30 minutes "
    "permet d'identifier vos 3 priorités. Agents IA, direction externalisée."
)


class AuthorshipTests(unittest.TestCase):
    def test_une_agence_qui_cite_les_mots_du_prospect_reste_un_vendeur(self):
        a = classify_authorship(EXPRESSWEB)
        self.assertTrue(a.is_vendor)
        self.assertEqual(a.claim_class, ClaimClass.ARGUMENTAIRE)
        self.assertFalse(a.can_carry_expressed_need)

    def test_le_cabinet_conseil_ia_est_un_vendeur(self):
        a = classify_authorship(STRUCTOLABS)
        self.assertTrue(a.is_vendor)
        self.assertFalse(a.can_carry_expressed_need)

    def test_le_statut_de_vendeur_est_evalue_avant_le_besoin(self):
        # La page contient « votre site … ne vous ramène aucun client » :
        # un motif lexical de besoin. Le vendeur doit primer.
        self.assertIn("votre site", EXPRESSWEB.lower())
        a = classify_authorship(EXPRESSWEB)
        self.assertEqual(a.claim_class, ClaimClass.ARGUMENTAIRE)

    def test_une_entreprise_qui_parle_delle_memee_est_une_demande_directe(self):
        a = classify_authorship(
            "Notre atelier fabrique des selles sur mesure. Nous recherchons "
            "quelqu'un pour refondre notre site, nous n'avons pas le temps de "
            "répondre à chaque demande de devis.")
        self.assertEqual(a.claim_class, ClaimClass.DEMANDE_DIRECTE)
        self.assertFalse(a.is_vendor)
        self.assertTrue(a.can_carry_expressed_need)

    def test_un_avis_client_nest_pas_une_demande(self):
        a = classify_authorship(
            "Nos clients sont satisfaits. Publié sur Google, Trustindex vérifie "
            "que la source originale de l'avis est Google. Un peu déçu que sa "
            "répond pas au téléphone quand on appelle.")
        self.assertEqual(a.claim_class, ClaimClass.TEMOIGNAGE)
        self.assertFalse(a.can_carry_expressed_need,
                         "un avis prouve une friction, pas une intention d'achat")

    def test_sans_marqueur_dauteur_on_ne_conclut_pas(self):
        self.assertEqual(classify_authorship("Bienvenue sur notre site.").claim_class,
                         ClaimClass.HYPOTHESE)
        self.assertEqual(classify_authorship("", quote="un extrait").claim_class,
                         ClaimClass.INDIRECT)

    def test_les_accents_ne_changent_pas_le_classement(self):
        self.assertEqual(classify_authorship(EXPRESSWEB).claim_class,
                         classify_authorship(EXPRESSWEB.upper()).claim_class)


class OperationalProblemTests(unittest.TestCase):
    def test_formulaire_ferme_est_le_signal_le_plus_fort(self):
        p = detect_form_closure("Bonjour :) Ce formulaire est maintenant fermé")
        self.assertIsNotNone(p)
        self.assertEqual(p.kind, ProblemKind.FORM_CLOSED)
        self.assertEqual(p.severity, "forte")
        self.assertFalse(p.proves_purchase_intent)

    def test_formulaire_sain_ne_declenche_rien(self):
        self.assertIsNone(detect_form_closure("Envoyer ma demande de devis"))

    def test_formulaire_identite_seule_ne_qualifie_pas(self):
        p = detect_qualification_gap(["Nom *", "Téléphone", "Email *", "Message *"])
        self.assertIsNotNone(p)
        self.assertEqual(p.kind, ProblemKind.NO_QUALIFICATION)

    def test_formulaire_deja_qualifie_est_un_contre_signal(self):
        # Cas réel : Abc Forage 34 et L'Atelier du Marin, écartés à juste titre.
        self.assertIsNone(detect_qualification_gap(
            ["Nom", "Email", "Objet de la demande", "Adresse d'intervention",
             "L'accès est-il difficile ?", "Type de bateau"]))

    def test_pas_de_champs_lus_pas_de_conclusion(self):
        self.assertIsNone(detect_qualification_gap([]))

    def test_reservation_telephonique_seule(self):
        self.assertIsNotNone(detect_phone_only("RESERVATION UNIQUEMENT PAR TELEPHONE"))
        self.assertIsNotNone(detect_phone_only(
            "La réservation d'un séjour peut se faire par téléphone ou e-mail"))

    def test_schema_email_au_lieu_de_mailto(self):
        p = detect_broken_mailto("[mail](email:saintbrieuc@ouestaffutage.com)")
        self.assertIsNotNone(p)
        self.assertEqual(p.severity, "forte")

    def test_adresse_inversee_antispam(self):
        self.assertIsNotNone(detect_broken_mailto("moc.liamg%40etiehcnateregorf"))

    def test_mailto_correct_ne_declenche_rien(self):
        self.assertIsNone(detect_broken_mailto("mailto:contact@exemple.fr"))

    def test_numeros_divergents(self):
        self.assertIsNotNone(detect_contact_mismatch(["06 63 02 64 47", "06 16 12 55 42"]))
        self.assertIsNone(detect_contact_mismatch(["02 96 94 58 54", "0296945854"]))

    def test_consentement_implicite_releve_mais_faible(self):
        p = detect_implied_consent(
            "Si vous continuez à utiliser ce site, nous supposerons que vous en êtes satisfait.")
        self.assertIsNotNone(p)
        self.assertEqual(p.severity, "faible")

    def test_aucun_probleme_ne_prouve_une_intention_dachat(self):
        r = analyse_page(
            "Ce formulaire est maintenant fermé. Réservation uniquement par téléphone.",
            url="https://exemple.fr/contact",
            form_fields=["Nom", "Email", "Message"], phones=["0102030405", "0607080910"])
        self.assertGreaterEqual(r["problem_count"], 3)
        self.assertTrue(all(not p["proves_purchase_intent"] for p in r["problems"]))
        self.assertEqual(r["strongest_severity"], "forte")


class SourceYieldTests(unittest.TestCase):
    def test_taux_brut_et_taux_lisse_sont_distincts(self):
        y = SourceYield("site_officiel", examined=42, qualified=13,
                        prior_strength=8, prior_rate=0.15)
        self.assertAlmostEqual(y.raw_rate, 13 / 42, places=6)
        self.assertNotAlmostEqual(y.raw_rate, y.smoothed_rate, places=3)

    def test_le_lissage_ecrase_les_grandes_series_nulles(self):
        y = SourceYield("annuaire_pro", examined=34, qualified=0,
                        prior_strength=8, prior_rate=0.15)
        self.assertEqual(y.raw_rate, 0.0)
        self.assertGreater(y.smoothed_rate, 0.0,
                           "0,029 n'est pas un taux brut : c'est le prior qui parle")

    def test_comparaison_refusee_entre_methodes_differentes(self):
        a = SourceYield("site_officiel", examined=42, qualified=13,
                        prior_strength=8, prior_rate=0.15)
        b = SourceYield("site_officiel", examined=42, qualified=13)
        self.assertFalse(a.comparable_with(b),
                         "lisser d'un côté et pas de l'autre n'est pas comparable")
        self.assertTrue(a.comparable_with(
            SourceYield("annuaire_pro", prior_strength=8, prior_rate=0.15)))

    def test_comparaison_refusee_entre_perimetres_de_comptage(self):
        a = SourceYield("x", counting_method="registre_exploration")
        b = SourceYield("y", counting_method="requetes_web")
        self.assertFalse(a.comparable_with(b))

    def test_le_canal_qui_a_echoue_est_explicitement_abandonne(self):
        names = {n for n, _ in DEPRECATED_CHANNELS}
        self.assertIn("recherche_besoin_exprime_web", names)
        self.assertIn("annuaire_pro_seul", names)

    def test_les_canaux_directs_excluent_la_recherche_lexicale(self):
        names = {n for n, _, _ in DIRECT_SOURCE_CHANNELS}
        self.assertIn("appel_offres", names)
        self.assertTrue(all(n.startswith("site_officiel") or n == "appel_offres"
                            for n in names))


if __name__ == "__main__":
    unittest.main()
