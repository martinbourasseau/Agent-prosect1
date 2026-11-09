"""Marchés publics — qualification d'avis publiés par des acheteurs identifiables.

POURQUOI CE CANAL
-----------------
La recherche lexicale de « besoin exprimé » est structurellement captée par les
agences web, qui citent les mots du prospect dans leur argumentaire. Un avis de
marché échappe à ce défaut : **l'auteur est l'acheteur**, le besoin est daté,
chiffré et publié sous sa responsabilité. C'est le canal où une demande
exprimée est réellement vérifiable.

CE QUE CE MODULE REFUSE
-----------------------
* Une annonce publiée par un **prestataire privé** n'est pas une demande
  d'acheteur public. Le pilote a rencontré une page commerciale listant des
  « marchés en cours » anonymisés (« Métropole de …… ») : ce sont des exemples
  inventés, pas des avis. Ils sont écartés, pas comptés.
* Un **avis d'attribution** n'est pas une opportunité : le marché est déjà pris.
* Un avis **expiré** n'est pas une opportunité, même parfaitement pertinent.
* Un marché **hors de portée** d'une petite structure n'est pas une
  opportunité, même ouvert.

CATÉGORIES
----------
A — directement exploitable : avis ouvert, acheteur identifié, besoin dans le
    périmètre de l'offre, procédure accessible, montant connu ou raisonnable.
B — intéressant mais une vérification ou une capacité manque (règlement de
    consultation non lu, références exigées inconnues, allotissement, montant
    élevé, échéance très proche).
C — non pertinent ou inaccessible : expiré, attribué, hors périmètre, hors de
    portée, ou auteur non acheteur.

Aucune candidature n'est déposée, aucun acheteur n'est contacté.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any, Iterable

CATEGORY_A = "A"
CATEGORY_B = "B"
CATEGORY_C = "C"
CATEGORIES = (CATEGORY_A, CATEGORY_B, CATEGORY_C)

# Auteur de l'avis. Seul un acheteur public peut porter une demande.
AUTHOR_BUYER = "acheteur_public"
AUTHOR_VENDOR = "prestataire_prive"
AUTHOR_AGGREGATOR = "agregateur"

# Types d'avis qui ne sont pas des mises en concurrence ouvertes.
NON_COMPETITION_TYPES = ("attribution", "intention_de_conclure", "avis_preinformation")

# Au-delà, un marché annuel de cette taille dépasse ce qu'une micro-entreprise
# peut porter seule : references, effectifs, assurance et trésorerie.
VALUE_CEILING_EUR = 60_000
# En deçà de ce délai, préparer une réponse sérieuse devient improbable.
MIN_DAYS_TO_RESPOND = 7
# Un avis publié depuis longtemps sans échéance connue ne peut pas être présumé
# ouvert : les fenêtres de réponse usuelles vont de 30 à 60 jours.
STALE_NOTICE_DAYS = 120

# Périmètre réel de l'offre : création, refonte, maintenance web, applications,
# automatisation et agents conversationnels.
SCOPE_TERMS = (
    "site internet", "site web", "sites internet", "refonte", "web",
    "maintenance", "hebergement", "hébergement", "application", "applicatif",
    "automatisation", "intelligence artificielle", "agent conversationnel",
    "assistant", "chatbot", "numerique", "numérique", "digitalisation",
    "intranet", "portail", "developpement", "développement",
    "programme ia", "systèmes d'ia", "systemes d'ia", "solution d'ia",
    "solutions d'ia", "acculturation",
)
OUT_OF_SCOPE_TERMS = (
    "signalétique", "signaletique", "impression", "magazine", "bulletin",
    "transcription", "evenements", "événements", "congrès", "communication globale",
    "identité visuelle seule", "gpu", "puissance de calcul",
)


@dataclass
class TenderNotice:
    """Un avis examiné. Les champs non vérifiés restent explicitement vides."""

    ref: str
    title: str
    buyer: str
    source: str
    official_url: str
    author: str = AUTHOR_BUYER
    notice_type: str = "concurrence"
    published_at: str = ""
    deadline: str = ""
    estimated_value_eur: float | None = None
    value_verified: bool = False
    procedure: str = ""
    cpv: tuple[str, ...] = ()
    sector: str = ""
    scope_summary: str = ""
    requirements: str = ""
    unverified: tuple[str, ...] = ()
    notes: str = ""
    pages_read: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["cpv"] = list(self.cpv)
        d["unverified"] = list(self.unverified)
        d["pages_read"] = list(self.pages_read)
        return d


@dataclass
class TenderAssessment:
    ref: str
    category: str
    reasons: list[str] = field(default_factory=list)
    days_left: int | None = None
    expired: bool = False
    in_scope: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _days_left(deadline: str, today: date) -> int | None:
    if not deadline:
        return None
    try:
        return (date.fromisoformat(deadline[:10]) - today).days
    except (ValueError, TypeError):
        return None


def in_scope(notice: TenderNotice) -> bool:
    text = f"{notice.title} {notice.scope_summary}".lower()
    if any(term in text for term in OUT_OF_SCOPE_TERMS):
        # Un marché de communication globale peut contenir du web, mais le
        # périmètre dominant n'est pas le nôtre : il ne devient pas une
        # opportunité par la seule présence du mot « site ».
        return any(term in text for term in ("refonte du site", "site internet institutionnel"))
    return any(term in text for term in SCOPE_TERMS)


def assess_tender(notice: TenderNotice, today: date | None = None) -> TenderAssessment:
    """Classe un avis. L'ordre des refus est volontairement éliminatoire."""
    today = today or date.today()
    reasons: list[str] = []
    days = _days_left(notice.deadline, today)
    scoped = in_scope(notice)

    # 1. L'auteur doit être l'acheteur. Défaut éliminatoire, comme en découverte.
    if notice.author != AUTHOR_BUYER:
        return TenderAssessment(
            notice.ref, CATEGORY_C,
            [f"auteur « {notice.author} » : une annonce de prestataire ou un "
             "relais d'agrégateur n'est pas une demande d'acheteur public"],
            days_left=days, in_scope=scoped)

    # 2. Un marché déjà attribué n'est plus à prendre.
    if notice.notice_type in NON_COMPETITION_TYPES:
        return TenderAssessment(
            notice.ref, CATEGORY_C,
            [f"type d'avis « {notice.notice_type} » : le marché n'est pas ouvert "
             "à la concurrence"], days_left=days, in_scope=scoped)

    # 3. Expiration.
    if days is None:
        # Avis ancien sans échéance publiée : le présenter comme ouvert serait
        # une affirmation sans preuve.
        try:
            published = date.fromisoformat(notice.published_at[:10]) if notice.published_at else None
        except (ValueError, TypeError):
            published = None
        if published is not None and (today - published).days > STALE_NOTICE_DAYS:
            return TenderAssessment(
                notice.ref, CATEGORY_C,
                [f"avis publié il y a {(today - published).days} jours sans échéance "
                 "connue : ouverture non établie, ne peut être présumé ouvert"],
                days_left=None, in_scope=scoped)
        reasons.append("date limite non publiée : échéance non vérifiable")
        expired = False
    elif days < 0:
        return TenderAssessment(
            notice.ref, CATEGORY_C,
            [f"consultation expirée depuis {-days} jour(s) : aucune action possible"],
            days_left=days, expired=True, in_scope=scoped)
    else:
        expired = False

    # 4. Périmètre de l'offre.
    if not scoped:
        return TenderAssessment(
            notice.ref, CATEGORY_C,
            ["objet hors du périmètre de l'offre (ni web, ni automatisation)"],
            days_left=days, in_scope=False)

    # 5. Portée financière.
    if notice.estimated_value_eur is not None and notice.estimated_value_eur > VALUE_CEILING_EUR:
        return TenderAssessment(
            notice.ref, CATEGORY_C,
            [f"montant publié {notice.estimated_value_eur:,.0f} € : hors de portée "
             "d'une micro-entreprise seule (références, effectifs, trésorerie)"],
            days_left=days, in_scope=True)

    # 6. Accessible : A si rien ne manque, B sinon.
    reasons.append("avis ouvert, acheteur public identifié, besoin dans le périmètre")
    if notice.procedure:
        reasons.append(f"procédure : {notice.procedure}")
    if notice.value_verified and notice.estimated_value_eur is not None:
        reasons.append(f"montant vérifié sur l'avis : {notice.estimated_value_eur:,.0f} € HT")

    blockers = list(notice.unverified)
    if days is not None and days < MIN_DAYS_TO_RESPOND:
        blockers.append(f"échéance dans {days} jour(s) : délai de réponse court")
    if days is None:
        blockers.append("échéance à confirmer sur le profil d'acheteur")
    if notice.estimated_value_eur is None:
        blockers.append("montant non publié")
    if notice.procedure and "formalis" in notice.procedure.lower():
        blockers.append("procédure formalisée : capacités et références probablement exigées")

    if blockers:
        return TenderAssessment(notice.ref, CATEGORY_B, reasons + blockers,
                                days_left=days, in_scope=True)
    return TenderAssessment(notice.ref, CATEGORY_A, reasons, days_left=days, in_scope=True)


@dataclass
class TenderPilot:
    notices: list[TenderNotice]
    today: date
    rejected_non_buyers: list[dict[str, Any]] = field(default_factory=list)

    def assessments(self) -> list[TenderAssessment]:
        return [assess_tender(n, self.today) for n in self.notices]

    def summary(self) -> dict[str, Any]:
        rows = self.assessments()
        counts = {c: sum(1 for r in rows if r.category == c) for c in CATEGORIES}
        by_ref = {n.ref: n for n in self.notices}
        return {
            "date_reference": self.today.isoformat(),
            "consultations_examinees": len(self.notices),
            "acheteurs_publics": sum(1 for n in self.notices if n.author == AUTHOR_BUYER),
            "annonces_non_acheteurs_ecartees": (
                len(self.rejected_non_buyers)
                + sum(1 for n in self.notices if n.author != AUTHOR_BUYER)),
            "categories": counts,
            "expirees": sum(1 for r in rows if r.expired),
            "sources": sorted({n.source for n in self.notices}),
            "secteurs": sorted({n.sector for n in self.notices if n.sector}),
            "montants_verifies": sum(1 for n in self.notices if n.value_verified),
            "exploitables": [
                {"ref": r.ref, "titre": by_ref[r.ref].title,
                 "acheteur": by_ref[r.ref].buyer, "categorie": r.category,
                 "echeance": by_ref[r.ref].deadline, "jours_restants": r.days_left,
                 "url_officielle": by_ref[r.ref].official_url}
                for r in rows if r.category in (CATEGORY_A, CATEGORY_B)
            ],
        }


PILOT_PATH = "history/pilote-marches-publics-2026-11-09.json"


def load_pilot(path=None) -> tuple["TenderPilot", dict[str, Any]]:
    """Charge le pilote archivé. Les champs hors modèle restent dans le brut."""
    import json
    from datetime import date as _date
    from . import config

    path = path or (config.DATA_DIR / PILOT_PATH)
    raw = json.loads(path.read_text(encoding="utf-8"))
    fields = TenderNotice.__dataclass_fields__
    notices = []
    for row in raw["consultations"]:
        kwargs = {k: v for k, v in row.items() if k in fields}
        for key in ("cpv", "unverified", "pages_read"):
            if key in kwargs and isinstance(kwargs[key], list):
                kwargs[key] = tuple(kwargs[key])
        notices.append(TenderNotice(**kwargs))
    today = _date.fromisoformat(raw["date_reference"])
    return TenderPilot(notices, today,
                       list(raw.get("annonces_non_acheteurs_ecartees", []))), raw
