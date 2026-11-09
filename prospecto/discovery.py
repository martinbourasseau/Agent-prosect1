"""Découverte commerciale par identité d'auteur, et non par vocabulaire.

POURQUOI CE MODULE EXISTE
------------------------
Les requêtes lexicales de « besoin exprimé » ont échoué deux fois de suite.
La cause n'est pas un manque de mots-clés : les agences et les vendeurs
rédigent leur argumentaire **en citant les mots du prospect** (« votre site ne
vous ramène aucun client », « nous n'avons pas le temps de répondre au
téléphone »). Un motif lexical côté client capture donc aussi la page du
vendeur qui le lui promet. Ajouter des exclusions ne peut pas corriger cela :
le texte fautif est une citation, pas une erreur de requête.

Le déplacement de méthode est le suivant : on ne classe plus **ce que dit le
texte**, on classe **qui parle**. Une page qui vend la prestation que nous
vendons n'est jamais une demande exprimée par l'entreprise, quelle que soit
la formulation qu'elle emploie.

Six classes, par autorité décroissante (voir `ClaimClass`) :

    demande_directe   l'entreprise parle d'elle-même et demande
    probleme_observe  constat fait sur son propre parcours client
    temoignage_client avis publié par un client, hébergé par l'entreprise
    signal_indirect   indice, sans demande ni constat direct
    argumentaire_tiers un prestataire vend — JAMAIS une demande
    hypothese         supposition non étayée

Seules les deux premières peuvent porter un besoin « exprimé » au sens du
scoring. Un témoignage client est un problème observé, pas une demande : il
prouve une friction, pas une intention d'achat.

MESURE DU RENDEMENT
-------------------
`SourceYield` sépare explicitement le taux brut du taux lissé, et refuse de
comparer deux sources dont le dénominateur n'est pas compté de la même façon.
Voir la docstring de la classe : c'est l'erreur de lecture que ce module doit
empêcher de reproduire.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------
def _plain(text: str) -> str:
    """Minuscules sans accents, pour comparer sans être piégé par la typo."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text.lower()).strip()


# --------------------------------------------------------------------------
# 1. Qui parle ?
# --------------------------------------------------------------------------
class ClaimClass(str, Enum):
    DEMANDE_DIRECTE = "demande_directe_entreprise"
    PROBLEME_OBSERVE = "probleme_directement_observe"
    TEMOIGNAGE = "temoignage_client_publie"
    INDIRECT = "signal_indirect"
    ARGUMENTAIRE = "argumentaire_commercial_tiers"
    HYPOTHESE = "hypothese_non_verifiee"


#: Ce que nous vendons. Une page qui VEND ces prestations est un concurrent.
#: Ce ne sont pas des mots de besoin : ce sont des mots d'OFFRE, à la première
#: personne du vendeur (« nous créons », « nos offres », « à partir de … € »).
VENDOR_OFFER = (
    "creation de site", "creation de sites", "creons votre site",
    "refonte de site", "refonte de votre site", "site vitrine",
    "agence web", "agence digitale", "agence de communication",
    "freelance", "developpeur web", "webdesigner", "webmaster",
    "referencement seo", "consultant seo", "community manager",
    "agents ia", "agent ia", "automatisation pour", "chatbot sur mesure",
    "nos offres", "nos formules", "nos tarifs", "nos prestations web",
    "demandez votre devis gratuit", "audit gratuit", "diagnostic gratuit",
    "accompagnement seo", "creation site internet",
)

#: Marqueurs de vente explicites : une offre commerciale adressée à un tiers.
VENDOR_PITCH = (
    "nous vous accompagnons", "nous accompagnons", "on vous met",
    "nous créons", "nous creons", "nous réalisons votre", "nous realisons votre",
    "confiez-nous votre site", "boostez", "developpez votre visibilite",
    "votre site ne vous", "votre activite est invisible",
    "places limitees", "offre de lancement", "a partir de",
    "nos clients", "ils nous font confiance", "portfolio", "realisations clients",
)

#: L'entreprise parle d'elle-même. Première personne du sujet, pas du vendeur.
SELF_VOICE = (
    "nous recherchons", "nous cherchons", "nous souhaitons", "nous aimerions",
    "nous avons besoin", "notre site est", "notre site ne", "nous n'avons pas le temps",
    "nous recruiting", "nous recrutons", "je recherche", "je souhaite",
    "notre ancien site", "nous devons", "il nous faudrait",
)

#: Un client parle de l'entreprise, sur le site de l'entreprise.
REVIEW_MARKERS = (
    "avis google", "publie sur", "trustindex", "avis clients",
    "temoignage", "ils témoignent", "ce que nos clients disent",
    "je recommande", "je ne recommande pas", "note :", "/5",
)


@dataclass
class Authorship:
    """Résultat de l'analyse « qui parle ? » sur une page."""

    claim_class: ClaimClass
    is_vendor: bool
    vendor_signals: list[str] = field(default_factory=list)
    self_signals: list[str] = field(default_factory=list)
    review_signals: list[str] = field(default_factory=list)
    confidence: str = "faible"
    rationale: str = ""

    @property
    def can_carry_expressed_need(self) -> bool:
        """Seule une demande de l'entreprise elle-même peut être « exprimée ».

        Un problème observé est réel mais n'est pas une demande : il alimente
        l'axe « observé ». Un argumentaire de tiers ne prouve rien du tout sur
        le besoin de l'entreprise visitée.
        """
        return self.claim_class == ClaimClass.DEMANDE_DIRECTE and not self.is_vendor

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["claim_class"] = self.claim_class.value
        d["can_carry_expressed_need"] = self.can_carry_expressed_need
        return d


def classify_authorship(page_text: str, *, url: str = "",
                        quote: str = "") -> Authorship:
    """Classe une page d'après l'identité de son auteur, pas son vocabulaire.

    L'ordre des tests est délibéré : **le statut de vendeur est évalué en
    premier et il est éliminatoire**. Une agence qui cite « votre site ne vous
    ramène aucun client » contient aussi des mots de besoin ; si l'on testait
    le besoin d'abord, elle serait classée à tort en demande directe.
    """
    text = _plain(page_text)
    q = _plain(quote)
    vendor = [s for s in VENDOR_OFFER if s in text]
    pitch = [s for s in VENDOR_PITCH if s in text]
    selfv = [s for s in SELF_VOICE if s in text or s in q]
    reviews = [s for s in REVIEW_MARKERS if s in text]

    # Une offre + une adresse commerciale = vendeur, sans ambiguïté.
    is_vendor = len(vendor) >= 2 or (len(vendor) >= 1 and len(pitch) >= 1)

    if is_vendor:
        return Authorship(
            ClaimClass.ARGUMENTAIRE, True, vendor + pitch, selfv, reviews,
            confidence="haute" if len(vendor) >= 2 else "moyenne",
            rationale=("La page vend elle-même la prestation (offre + "
                       "argumentaire). Ses mots de besoin sont des citations "
                       "adressées à ses prospects, pas une demande de "
                       "l'auteur. Jamais une demande exprimée."))

    if selfv:
        return Authorship(
            ClaimClass.DEMANDE_DIRECTE, False, vendor, selfv, reviews,
            confidence="moyenne",
            rationale=("L'entreprise parle d'elle-même à la première personne "
                       "et sans vendre la prestation. À dater et à rattacher "
                       "à une personne identifiée avant de qualifier."))

    if reviews:
        return Authorship(
            ClaimClass.TEMOIGNAGE, False, vendor, selfv, reviews,
            confidence="moyenne",
            rationale=("Avis de client hébergé par l'entreprise : prouve une "
                       "friction vécue, pas une intention d'achat. La date de "
                       "l'avis doit être établie."))

    if q:
        return Authorship(
            ClaimClass.INDIRECT, False, vendor, selfv, reviews,
            confidence="faible",
            rationale=("Extrait sans marqueur d'auteur : indice seulement. "
                       "Ne peut pas porter un besoin exprimé."))

    return Authorship(
        ClaimClass.HYPOTHESE, False, vendor, selfv, reviews,
        confidence="faible",
        rationale="Aucun marqueur d'auteur ni extrait : hypothèse non vérifiée.")


# --------------------------------------------------------------------------
# 2. Problèmes opérationnels observables
# --------------------------------------------------------------------------
class ProblemKind(str, Enum):
    FORM_CLOSED = "formulaire_ferme_ou_inutilisable"
    NO_QUALIFICATION = "demande_sans_qualification"
    PHONE_ONLY = "reservation_telephonique_seule"
    CONTACT_MISMATCH = "coordonnees_incoherentes"
    CONTRADICTORY = "informations_contradictoires"
    BROKEN_MAILTO = "lien_email_casse"
    HIDDEN_CONTACT = "contact_difficile_a_trouver"
    REPETITIVE_MANUAL = "demandes_repetitives_manuelles"
    IMPLIED_CONSENT = "consentement_cookies_implicite"


#: Champs qui qualifient réellement une demande. Un formulaire qui ne demande
#: que l'identité et un message libre laisse tout le cadrage à faire à la main.
IDENTITY_FIELDS = ("nom", "prenom", "email", "e-mail", "telephone", "téléphone",
                   "message", "societe", "société", "entreprise", "objet", "sujet")


@dataclass
class OperationalProblem:
    kind: ProblemKind
    quote: str
    detail: str
    severity: str = "moyenne"          # faible | moyenne | forte
    proves_purchase_intent: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


def detect_form_closure(page_text: str) -> OperationalProblem | None:
    """Un formulaire de demande mort est le signal le plus fort et le plus net.

    Il ne demande aucune interprétation : le parcours n'existe plus.
    """
    t = _plain(page_text)
    for marker in ("ce formulaire est maintenant ferme",
                   "ce formulaire est ferme", "form is closed",
                   "this form is no longer accepting",
                   "formulaire indisponible", "les inscriptions sont closes"):
        if marker in t:
            return OperationalProblem(
                ProblemKind.FORM_CLOSED, marker,
                "Le parcours de demande en ligne est inopérant : aucun client "
                "ne peut déposer une demande par ce formulaire.",
                severity="forte")
    return None


def detect_qualification_gap(fields: Iterable[str]) -> OperationalProblem | None:
    """Un formulaire ne demandant que l'identité ne qualifie pas la demande.

    `fields` sont les libellés réellement lus sur la page. On ne déduit rien
    d'un formulaire dont on n'a pas lu les champs.
    """
    labels = [_plain(f) for f in fields if f and f.strip()]
    if not labels:
        return None
    substantive = [f for f in labels
                   if not any(f == i or f.startswith(i) for i in IDENTITY_FIELDS)]
    if substantive:
        return None
    return OperationalProblem(
        ProblemKind.NO_QUALIFICATION, " / ".join(labels),
        "Le formulaire ne recueille que l'identité et un message libre : "
        "aucune caractéristique du projet, donc cadrage à refaire par échange "
        "pour chaque demande.",
        severity="moyenne")


def detect_phone_only(page_text: str) -> OperationalProblem | None:
    t = _plain(page_text)
    # « se fait » / « peut se faire » / « se font » : la conjugaison ne doit
    # pas décider si le signal est détecté. On compare le canal, pas le verbe.
    for marker in ("reservation uniquement par telephone",
                   "reservations uniquement par telephone",
                   "uniquement par telephone", "commandez par telephone",
                   "par telephone ou e-mail", "par telephone ou par e-mail",
                   "par telephone ou en boutique", "par telephone uniquement"):
        if marker in t:
            return OperationalProblem(
                ProblemKind.PHONE_ONLY, marker,
                "Aucun canal de dépôt autonome : la demande passe par un "
                "échange humain (appel ou e-mail), donc chaque réservation "
                "mobilise une personne. Un formulaire de contact n'est pas "
                "un système de réservation.",
                severity="moyenne")
    return None


def detect_broken_mailto(html_or_text: str) -> OperationalProblem | None:
    """Schéma `email:` au lieu de `mailto:`, ou adresse inversée anti-spam."""
    t = html_or_text or ""
    m = re.search(r"email:[\w.+-]+@[\w.-]+", t)
    if m:
        return OperationalProblem(
            ProblemKind.BROKEN_MAILTO, m.group(0),
            "Le schéma « email: » n'est pas reconnu par les clients mail : ce "
            "lien ne fonctionne pas.", severity="forte")
    m = re.search(r"\bmoc\.[\w%.-]+", t)
    if m:
        return OperationalProblem(
            ProblemKind.BROKEN_MAILTO, m.group(0),
            "Chaîne anti-spam inversée restée dans le lien : l'adresse est "
            "inutilisable en l'état.", severity="forte")
    return None


def detect_implied_consent(page_text: str) -> OperationalProblem | None:
    """Consentement par poursuite de navigation : non conforme (CNIL/RGPD).

    Signal annexe utile, mais ce n'est pas une demande exprimée et cela ne
    doit jamais devenir l'argument principal d'une approche commerciale.
    """
    t = _plain(page_text)
    for marker in ("nous supposerons que vous en etes satisfait",
                   "en poursuivant votre navigation, vous acceptez",
                   "en continuant a utiliser ce site, vous acceptez"):
        if marker in t:
            return OperationalProblem(
                ProblemKind.IMPLIED_CONSENT, marker,
                "Consentement déduit de la poursuite de navigation : ne "
                "satisfait pas l'exigence de consentement explicite.",
                severity="faible")
    return None


def detect_contact_mismatch(phones: Iterable[str]) -> OperationalProblem | None:
    """Deux numéros différents pour la même action sur une même page."""
    digits = sorted({re.sub(r"\D", "", p) for p in phones if p})
    digits = [d for d in digits if len(d) >= 9]
    if len(digits) >= 2:
        return OperationalProblem(
            ProblemKind.CONTACT_MISMATCH, " / ".join(digits),
            "Plusieurs numéros distincts publiés : risque d'appel aboutissant "
            "au mauvais interlocuteur.", severity="moyenne")
    return None


def analyse_page(page_text: str, *, url: str = "",
                 form_fields: Iterable[str] = (),
                 phones: Iterable[str] = ()) -> dict[str, Any]:
    """Analyse complète d'une page : qui parle, et quelles frictions sont visibles.

    Aucune de ces frictions ne prouve une intention d'achat : c'est pourquoi
    `proves_purchase_intent` reste False partout. Elles alimentent l'axe
    « problème observé », jamais l'axe « besoin exprimé ».
    """
    authorship = classify_authorship(page_text, url=url)
    problems: list[OperationalProblem] = []
    for found in (detect_form_closure(page_text),
                  detect_qualification_gap(form_fields),
                  detect_phone_only(page_text),
                  detect_broken_mailto(page_text),
                  detect_contact_mismatch(phones),
                  detect_implied_consent(page_text)):
        if found is not None:
            problems.append(found)
    return {
        "url": url,
        "authorship": authorship.to_dict(),
        "problems": [p.to_dict() for p in problems],
        "problem_count": len(problems),
        "strongest_severity": max((p.severity for p in problems),
                                 key={"faible": 0, "moyenne": 1, "forte": 2}.get,
                                 default=None),
        "note": ("Un problème observé n'est pas une intention d'achat. "
                 "Un argumentaire de tiers n'est pas une demande de "
                 "l'entreprise."),
    }


# --------------------------------------------------------------------------
# 3. Rendement des sources, avec dénominateurs explicites
# --------------------------------------------------------------------------
@dataclass
class SourceYield:
    """Rendement d'une source, dénominateur et méthode de comptage explicites.

    PIÈGE À NE PAS REPRODUIRE
    -------------------------
    Deux nombres circulaient dans les rapports : « sites officiels 0,352 » et
    « annuaires 0,029 ». Ce ne sont **pas** des taux de qualification bruts :
    ce sont les `yield_score` de `planner.py`, c'est-à-dire des moyennes a
    posteriori `(qualifiés + 8 × 0,15) / (examinés + 8)`. Le lissage remonte
    les petites séries et écrase les grandes séries nulles. Les comparer à un
    taux brut, ou à un chiffre calculé sur un autre périmètre, est une erreur
    de lecture. Cette classe porte donc la méthode avec le nombre, et
    `comparable_with` refuse la comparaison entre méthodes différentes.
    """

    source_type: str
    examined: int = 0
    sites_verified: int = 0
    needs_documented: int = 0
    qualified: int = 0
    contacts_verified: int = 0
    queries: int = 0
    counting_method: str = "registre_exploration"
    prior_strength: float = 0.0
    prior_rate: float = 0.0

    @property
    def raw_rate(self) -> float:
        return self.qualified / self.examined if self.examined else 0.0

    @property
    def smoothed_rate(self) -> float:
        denom = self.examined + self.prior_strength
        if not denom:
            return 0.0
        return (self.qualified + self.prior_strength * self.prior_rate) / denom

    def comparable_with(self, other: "SourceYield") -> bool:
        return (self.counting_method == other.counting_method
                and self.prior_strength == other.prior_strength
                and self.prior_rate == other.prior_rate)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["raw_rate"] = round(self.raw_rate, 4)
        d["smoothed_rate"] = round(self.smoothed_rate, 4)
        return d


#: Canaux où l'auteur d'une demande est identifiable, à privilégier. Les
#: requêtes de besoin exprimé en web général en sont explicitement exclues.
DIRECT_SOURCE_CHANNELS = (
    ("site_officiel_contact", "Page contact ou devis du site de l'entreprise",
     "L'auteur est l'entreprise ; les champs du formulaire sont lisibles."),
    ("site_officiel_reservation", "Page de réservation",
     "Révèle si la demande est autonome ou téléphonique."),
    ("site_officiel_tarifs", "Page tarifs / conditions",
     "Révèle les règles manuelles (délais, acomptes, canaux imposés)."),
    ("site_officiel_faq", "FAQ",
     "L'entreprise y écrit elle-même ses contraintes d'organisation."),
    ("site_officiel_avis", "Avis clients hébergés par l'entreprise",
     "Témoignage publié : friction vécue, date à établir."),
    ("site_officiel_recrutement", "Page recrutement",
     "Un poste administratif recruté révèle une charge manuelle."),
    ("site_officiel_mentions", "Mentions légales",
     "Identité, SIREN et souvent une adresse publiée en clair."),
    ("appel_offres", "Avis d'appel d'offres / marché public",
     "Demande explicite, auteur identifié, budget et échéance connus."),
)

#: À abandonner : produit du volume sans opportunité, ou capte les vendeurs.
DEPRECATED_CHANNELS = (
    ("recherche_besoin_exprime_web",
     "Les agences citent les mots du prospect dans leur argumentaire. Deux "
     "tentatives, deux échecs, 0 prospect. Les exclusions lexicales ne "
     "peuvent pas distinguer une citation d'une demande."),
    ("annuaire_pro_seul",
     "34 structures examinées, 0 qualifiée. Pas d'adresse publiée vérifiable "
     "et pas de parcours client observable."),
)
