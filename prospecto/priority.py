"""Priorité commerciale transversale — calibration v9.

POURQUOI CE MODULE EXISTE
-------------------------
En v8, la priorité commerciale était `max(score des trois axes)`. Cela créait
une inversion : un besoin **exprimé par l'entreprise** plafonnait à 34 sur son
axe, tandis qu'une lacune **déduite par l'agent** atteignait 98 en refonte. Une
entreprise qui écrit « nous cherchons à automatiser nos devis » passait donc
derrière une entreprise dont on avait seulement inféré un site vieillissant.

La cause est structurelle : les trois axes mesurent des choses différentes
(absence de site, défauts d'un site, charge manuelle) et leurs barèmes ne sont
pas commensurables. Les additionner ou prendre leur maximum compare des choux
et des carottes.

CE QUE CE MODULE FAIT — ET NE FAIT PAS
--------------------------------------
Les trois scores v8 sont **conservés à l'identique**. Ce module ajoute une
quatrième lecture, transversale, qui répond à une autre question : « à quel
point cela vaut-il la peine d'engager une conversation commerciale ? »

Elle combine quatre critères explicables :

1. **Classe de signal** — qui affirme le besoin ? L'entreprise elle-même
   (exprimé), un constat direct (observé), un indice (indirect) ou une
   supposition du chercheur (hypothétique). C'est le critère dominant.
2. **Pertinence par rapport à l'offre** — la demande correspond-elle à ce que
   nous vendons réellement ? Une demande de logo ou de gestion Google Ads est
   un besoin exprimé, mais hors offre : elle ne doit pas devenir une priorité.
3. **Vérification** — le besoin exprimé est-il adossé à une preuve datée sur
   une source officielle ?
4. **Magnitude** — l'ampleur mesurée par les axes, mais **bornée** à 28 points
   pour qu'elle ne puisse plus écraser la classe de signal.

La contactabilité reste une question séparée : sans adresse joignable, la
priorité est plafonnée à « à approfondir », jamais « haute ».
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any

from .models import (
    Evidence, Prospect, SIGNAL_EXPRESSED, SIGNAL_OBSERVED, SIGNAL_INDIRECT,
    SIGNAL_HYPOTHETICAL, EVIDENCE_PUBLIC_NEED,
)
from .email_verify import DELIVERABLE_STATUSES, BLOCKING_STATUSES, MX_NOT_CHECKED
from . import counter_signals as cs

ENGINE_VERSION = "v10-priority"

AXES = ("site_web", "refonte", "ia_automatisation")

# --------------------------------------------------------------------------
# 1. Périmètre de l'offre. Une demande exprimée hors de ce périmètre ne doit
#    pas hériter de la priorité maximale simplement parce qu'elle est exprimée.
# --------------------------------------------------------------------------
OFFER_SCOPE: dict[str, tuple[str, ...]] = {
    "site_web": (
        "site internet", "site web", "site vitrine", "creation de site",
        "creer un site", "boutique en ligne", "e-commerce", "ecommerce",
        "shopify", "woocommerce", "presence en ligne", "one-page", "one page",
        "vitrine", "site marchand",
    ),
    "refonte": (
        "refonte", "refondre", "moderniser", "(site obsolete)", "obsolete",
        "vieux site", "site vieillissant", "reprise du site", "nouveau site",
        "responsive", "mobile", "lenteur", "site lent", "wordpress",
        "referencement", "seo", "site existant", "ameliorer notre site",
    ),
    "ia_automatisation": (
        "automatiser", "automatisation", "automatique", "intelligence artificielle",
        "agent ia", "outil ia", "ia", "chatbot", "devis", "reservation",
        "inscription", "relance", "crm", "relation client", "secretariat",
        "saisie", "ressaisie", "tableur", "excel", "formulaire", "messagerie",
        "centraliser", "qualifier", "categoriser", "administratif", "facturation",
        "prise de rendez-vous", "rdv", "standard telephonique", "emails",
        "newsletter", "infolettre", "mailing", "contenu recurrent",
    ),
}

# Demandes réelles mais que nous ne servons pas. Présence = hors offre, même
# si la formulation contient un mot du périmètre (« site » dans « application »).
OUT_OF_SCOPE: tuple[str, ...] = (
    "application mobile", "application ios", "application android",
    "logo", "identite visuelle", "charte graphique", "graphisme", "plaquette",
    "google ads", "sea ", "campagne publicitaire", "regie publicitaire",
    "community management", "gestion des reseaux sociaux", "reseaux sociaux",
    "photographie", "video", "montage video", "traduction", "redaction web",
    "hebergement seul", "nom de domaine seul", "maintenance informatique",
    "depannage informatique", "poste de travail", "serveur",
    # Externalisation de la force de vente : nous construisons des systèmes,
    # nous ne prenons pas de rendez-vous commerciaux à la place du client.
    # Distinct de « prise de rendez-vous » (module de réservation), qui est
    # bien dans l'offre.
    "rendez-vous qualifies", "decideurs d'entreprise", "prospection commerciale",
    "teleprospection", "leads qualifies", "generer des leads", "force de vente",
)

RELEVANCE_IN_SCOPE = 1.0
RELEVANCE_UNCLEAR = 0.65
RELEVANCE_OUT_OF_SCOPE = 0.30

RELEVANCE_PROPOSE = "propose"
RELEVANCE_INCERTAINE = "incertaine"
RELEVANCE_HORS_OFFRE = "hors_offre"

# --------------------------------------------------------------------------
# 2. Base par classe de signal, plus une magnitude bornée.
#
#    PREMIÈRE TENTATIVE, REJETÉE PAR LA SIMULATION : base observé 40 et
#    plafond de magnitude 28 donnaient un maximum de 68 à tout problème
#    seulement observé. Aucun ne pouvait donc atteindre « haute » (70), et la
#    catégorie s'effondrait de 11 fiches à 2. Le plafond ne traduisait pas un
#    jugement commercial : il interdisait mécaniquement une classe entière.
#
#    CALIBRATION RETENUE : l'avantage de l'exprimé est un ÉCART DE BASE à
#    magnitude égale (+24 sur l'observé), pas un plafond imposé à l'observé.
#    La magnitude peut porter jusqu'à 42 points, ce qui laisse un problème
#    massif directement constaté atteindre « haute » — tout en garantissant
#    qu'à ampleur comparable, l'exprimé vérifié passe devant.
#
#    Invariant vérifiable : pour toute valeur d'axe v,
#    valeur(exprimé vérifié, v) - valeur(observé, v) = 24.
# --------------------------------------------------------------------------
BASE_BY_CLASS: dict[str, int] = {
    "exprime_verifie": 58,
    "exprime_non_verifie": 44,
    SIGNAL_OBSERVED: 34,
    SIGNAL_INDIRECT: 18,
    SIGNAL_HYPOTHETICAL: 8,
    # Besoin réel et exprimé, mais que nous ne servons pas : la base est
    # basse ET la magnitude est nulle, pour qu'il ne remonte pas par l'ampleur.
    "exprime_hors_offre": 18,
}

MAGNITUDE_CAP = 42
MAGNITUDE_RATE = 0.42

TIER_HAUTE = "haute"
TIER_MOYENNE = "moyenne"
TIER_BASSE = "basse"
TIER_A_APPROFONDIR = "a_approfondir"

THRESHOLD_HAUTE = 70
THRESHOLD_MOYENNE = 45
THRESHOLD_BASSE = 25

_CLASS_ORDER = (SIGNAL_HYPOTHETICAL, SIGNAL_INDIRECT, SIGNAL_OBSERVED, SIGNAL_EXPRESSED)

CONFIDENCE_HIGH = "haute"
CONFIDENCE_MEDIUM = "moyenne"
CONFIDENCE_LOW = "faible"

FRESH_DAYS = 180


def _norm(text: str) -> str:
    """Minuscules sans accents, pour comparer des formulations françaises."""
    import unicodedata
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


@dataclass
class CommercialAssessment:
    """Lecture transversale, indépendante des trois scores d'axe."""

    value: int
    tier: str
    signal_class: str
    signal_class_label: str
    relevance: str
    relevance_factor: float
    matched_services: list[str] = field(default_factory=list)
    verified: bool = False
    base: int = 0
    magnitude: int = 0
    best_axis: str = ""
    best_axis_score: int = 0
    confidence: str = CONFIDENCE_LOW
    reasons: list[str] = field(default_factory=list)
    counter_signals: list[str] = field(default_factory=list)
    counter_signal_penalty: int = 0
    counter_signal_details: list[dict[str, Any]] = field(default_factory=list)
    driving_evidence: list[dict[str, Any]] = field(default_factory=list)
    contactable: bool = False
    capped_by_contactability: bool = False
    floor_applied: bool = False
    evaluated_at: str = ""
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_CLASS_LABELS = {
    "exprime_verifie": "besoin exprimé et vérifié",
    "exprime_non_verifie": "besoin exprimé, vérification incomplète",
    SIGNAL_OBSERVED: "problème directement observé",
    SIGNAL_INDIRECT: "signal indirect",
    SIGNAL_HYPOTHETICAL: "opportunité hypothétique",
    "exprime_hors_offre": "besoin exprimé mais hors de notre offre",
}


def offer_relevance(evidences: list[Evidence]) -> tuple[str, float, list[str], list[str]]:
    """La demande correspond-elle à ce que nous vendons ?

    On ne juge que les besoins **exprimés** : un défaut de site observé est par
    construction dans notre périmètre. Une demande explicite hors offre
    (logo, application mobile, Google Ads) est en revanche rétrogradée.
    """
    expressed = [e for e in evidences
                 if e.kind == EVIDENCE_PUBLIC_NEED and e.signal_level == SIGNAL_EXPRESSED]
    if not expressed:
        return RELEVANCE_PROPOSE, RELEVANCE_IN_SCOPE, [], []

    matched: set[str] = set()
    out_hits: list[str] = []
    for ev in expressed:
        text = _norm(f"{ev.quote} {ev.detail}")
        for term in OUT_OF_SCOPE:
            if term in text:
                out_hits.append(term.strip())
        for service, terms in OFFER_SCOPE.items():
            if any(t in text for t in terms):
                matched.add(service)

    if matched:
        # Une demande mixte (« logo + site ») reste dans l'offre : la partie
        # qui nous concerne est réelle. Les termes hors offre sont signalés.
        return RELEVANCE_PROPOSE, RELEVANCE_IN_SCOPE, sorted(matched), sorted(set(out_hits))
    if out_hits:
        return RELEVANCE_HORS_OFFRE, RELEVANCE_OUT_OF_SCOPE, [], sorted(set(out_hits))
    return RELEVANCE_INCERTAINE, RELEVANCE_UNCLEAR, [], []


def _is_verified(ev: Evidence) -> bool:
    """Le besoin est-il publié par l'entreprise elle-même, et relu directement ?

    ATTENTION — piège du modèle : `Evidence.__post_init__` renseigne
    `verified_at` avec `observed_at` dès qu'il est vide. Un test naïf du type
    « verified_at non vide » est donc TOUJOURS vrai et ne distingue rien.

    La vérification repose par conséquent sur l'autorité de la source et la
    fiabilité de la lecture, pas sur la seule présence d'une date :
    - `site_officiel` : l'entreprise parle sur son propre site ;
    - `reliability == haute` : extrait lu sur la page, pas dans un résultat de
      moteur de recherche ;
    - `observed` : la source a réellement été consultée.
    Une annonce vue sur une page professionnelle tierce (Facebook, LinkedIn)
    ou rapportée avec une fiabilité moyenne reste « exprimé non vérifié ».
    """
    return bool(ev.source_url and (ev.verified_at or ev.observed_at)
                and ev.source_type == "site_officiel"
                and ev.reliability == "haute" and ev.observed)


def driving_class(evidences: list[Evidence], relevance: str) -> tuple[str, bool, list[Evidence]]:
    """Classe de signal la plus forte, et les preuves qui la portent."""
    usable = [e for e in evidences if e.observed]
    if not usable:
        usable = list(evidences)
    if not usable:
        return SIGNAL_HYPOTHETICAL, False, []

    expressed = [e for e in usable
                 if e.kind == EVIDENCE_PUBLIC_NEED and e.signal_level == SIGNAL_EXPRESSED]
    if expressed:
        if relevance == RELEVANCE_HORS_OFFRE:
            return "exprime_hors_offre", False, expressed
        verified = [e for e in expressed if _is_verified(e)]
        if verified:
            return "exprime_verifie", True, verified
        return "exprime_non_verifie", False, expressed

    best = SIGNAL_HYPOTHETICAL
    for ev in usable:
        lvl = ev.signal_level or SIGNAL_INDIRECT
        if _CLASS_ORDER.index(lvl) > _CLASS_ORDER.index(best):
            best = lvl
    carriers = [e for e in usable if (e.signal_level or SIGNAL_INDIRECT) == best]
    return best, False, carriers


def _confidence(carriers: list[Evidence], today: date) -> str:
    if not carriers:
        return CONFIDENCE_LOW
    reliable = [e for e in carriers if e.reliability == "haute"]
    fresh = 0
    for ev in carriers:
        stamp = ev.verified_at or ev.observed_at
        if not stamp:
            continue
        try:
            seen = date.fromisoformat(stamp[:10])
        except ValueError:
            continue
        if (today - seen).days <= FRESH_DAYS:
            fresh += 1
    if reliable and fresh and any(_is_verified(e) for e in carriers):
        return CONFIDENCE_HIGH
    if reliable or fresh:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def assess(prospect: Prospect, scores: dict[str, Any],
           today: date | None = None) -> CommercialAssessment:
    """Calcule la priorité transversale sans toucher aux trois scores d'axe."""
    today = today or date.today()
    evidences = list(prospect.evidences or [])

    relevance, factor, matched, out_hits = offer_relevance(evidences)
    signal_class, verified, carriers = driving_class(evidences, relevance)

    # Magnitude : bornée, et nulle si la demande est hors offre — inutile
    # d'additionner l'ampleur d'un problème que nous ne résolvons pas.
    axis_scores = {a: int((scores.get(a) or {}).get("score", 0)) for a in AXES}
    best_axis = max(AXES, key=lambda a: axis_scores[a])
    best_value = axis_scores[best_axis]
    magnitude = 0 if relevance == RELEVANCE_HORS_OFFRE else min(
        MAGNITUDE_CAP, int(round(best_value * MAGNITUDE_RATE)))
    # Un besoin exprimé vérifié et pertinent ne doit jamais descendre sous le
    # seuil « haute » à cause d'un site techniquement correct : c'est exactement
    # l'entreprise qu'il faut appeler en premier.

    base = BASE_BY_CLASS.get(signal_class, BASE_BY_CLASS[SIGNAL_INDIRECT])
    value = max(0, min(100, int(round(base * factor)) + magnitude))

    # v10 — contre-signaux explicites. Les preuves typées « maturite_existante »
    # n'étaient lues par aucun moteur : MATURITY_FACTOR ne porte que sur les
    # automatisations auto-détectées. Elles réduisent désormais la priorité
    # transversale, JAMAIS les trois scores techniques v8, qui décrivent
    # factuellement l'existant. La pénalité est bornée et une simple mention
    # d'équipement (force faible) ne déplace pas la priorité.
    signals = cs.collect(evidences, today)
    penalty = cs.total_penalty(signals)
    before_penalty = value
    if penalty:
        value = max(0, value - penalty)

    reasons = []
    if signals:
        counts = cs.breakdown(signals)
        reasons.append(
            f"contre-signaux explicites : {counts['fort']} fort(s), "
            f"{counts['modere']} modéré(s), {counts['faible']} faible(s) "
            f"→ pénalité bornée -{penalty} ({before_penalty} -> {value})")
        for sig in signals:
            reasons.append("contre-signal — " + sig.reason)
    # Plancher explicite : si l'entreprise demande elle-même une prestation que
    # nous vendons et que la demande est vérifiée, elle passe en tête de liste
    # même si son site est techniquement correct. C'est le cas que la v8
    # pénalisait. Le plancher n'est PAS accordé à toute demande exprimée : il
    # exige la vérification ET l'adéquation à l'offre (une demande non vérifiée
    # reste « moyenne », une demande hors offre reste « basse »).
    floor_applied = False
    # Le plancher est appliqué APRÈS la pénalité, volontairement : si une
    # entreprise demande elle-même une prestation que nous vendons, sa demande
    # vaut mieux que notre constat sur son équipement. Un contre-signal ne doit
    # pas annuler une demande explicite — il informera la conversation.
    if signal_class == "exprime_verifie" and relevance == RELEVANCE_PROPOSE and value < THRESHOLD_HAUTE:
        if penalty:
            reasons.append("plancher maintenu malgré les contre-signaux : une demande "
                           "explicite de l'entreprise prime sur notre constat d'équipement")
        reasons.append(f"plancher « besoin exprimé vérifié et pertinent » : "
                       f"{value} -> {THRESHOLD_HAUTE} (un site techniquement correct "
                       f"ne doit pas pénaliser une demande explicite)")
        value = THRESHOLD_HAUTE
        floor_applied = True

    reasons += [
        f"{_CLASS_LABELS.get(signal_class, signal_class)} : base {base}",
        f"pertinence offre : {relevance} (×{factor:.2f})"
        + (f" — services concernés : {', '.join(matched)}" if matched else ""),
        f"magnitude bornée : +{magnitude} (meilleur axe {best_axis} = {best_value}, "
        f"plafond {MAGNITUDE_CAP})",
    ]
    if out_hits:
        reasons.append(f"termes hors offre relevés : {', '.join(out_hits)}")

    # Contactabilité : question distincte, elle plafonne sans effacer la valeur.
    contact = scores.get("contactability") or {}
    email = (prospect.contact_email or "").strip()
    dns = getattr(prospect, "email_dns_status", "") or MX_NOT_CHECKED
    contactable = bool(email) and dns in DELIVERABLE_STATUSES and not contact.get("blockers")

    if value >= THRESHOLD_HAUTE:
        tier = TIER_HAUTE
    elif value >= THRESHOLD_MOYENNE:
        tier = TIER_MOYENNE
    elif value >= THRESHOLD_BASSE:
        tier = TIER_BASSE
    else:
        tier = TIER_BASSE

    capped = False
    if not contactable and tier in (TIER_HAUTE, TIER_MOYENNE):
        tier = TIER_A_APPROFONDIR
        capped = True
        reasons.append("adresse non joignable : priorité plafonnée à « à approfondir » "
                       "(la valeur commerciale est conservée telle quelle)")
    if relevance == RELEVANCE_HORS_OFFRE and tier in (TIER_HAUTE, TIER_MOYENNE):
        tier = TIER_BASSE
        capped = True
        reasons.append("demande hors offre : ne devient pas une priorité malgré sa force")

    counter: list[str] = []
    for axis in AXES:
        for item in (scores.get(axis) or {}).get("counter_signals", []):
            if item not in counter:
                counter.append(item)
    # Les contre-signaux explicites alimentent enfin ce champ, qui restait vide
    # alors que les preuves existaient : c'était le défaut signalé par l'audit.
    for sig in signals:
        label = (sig.quote or sig.source_url or "contre-signal")[:160]
        if label not in counter:
            counter.append(label)

    return CommercialAssessment(
        value=value, tier=tier, signal_class=signal_class,
        signal_class_label=_CLASS_LABELS.get(signal_class, signal_class),
        relevance=relevance, relevance_factor=factor, matched_services=matched,
        verified=verified, base=base, magnitude=magnitude,
        best_axis=best_axis, best_axis_score=best_value,
        confidence=_confidence(carriers, today), reasons=reasons,
        counter_signals=counter,
        counter_signal_penalty=penalty,
        counter_signal_details=[sig.to_dict() for sig in signals],
        driving_evidence=[{"quote": e.quote, "source_url": e.source_url,
                           "observed_at": e.observed_at, "verified_at": e.verified_at,
                           "signal_level": e.signal_level} for e in carriers[:4]],
        contactable=contactable, capped_by_contactability=capped,
        floor_applied=floor_applied, evaluated_at=today.isoformat(),
    )