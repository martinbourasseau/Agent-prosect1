"""Contre-signaux explicites — force, portée et effet sur la priorité.

LE DÉFAUT CORRIGÉ
-----------------
`scoring.MATURITY_FACTOR` (0,8) ne s'applique qu'aux automatisations détectées
par le moteur (`report.maturity`). Une preuve typée `maturite_existante`
ajoutée à la main ne réduisait donc **aucun axe** et laissait le champ
`counter_signals` vide. ERM 27 sortait à « haute 71 » avec un contenu à jour et
un prestataire web déjà en place.

POURQUOI NE PAS APPLIQUER 0,8 PARTOUT
------------------------------------
Multiplier mécaniquement chaque axe par 0,8 dès qu'un équipement existe
produirait exactement l'effet indésirable que la mission interdit : **un
équipement existant ne doit pas annuler une opportunité de refonte ou
d'automatisation**. La lecture des 16 fiches concernées montre que la plupart
des contre-signaux **délimitent** le besoin sans le supprimer :

* « la structure de collecte existe déjà, le manque est la persistence » —
  le besoin d'automatisation subsiste ;
* « un formulaire fonctionne, le défaut porte sur le lien e-mail » — le
  besoin de correction subsiste ;
* « encaissement CB sur place » — contre-signal visant le paiement en ligne,
  alors que le besoin poursuivi est une page de planning absente.

À l'inverse, trois contre-signaux **nient** réellement l'opportunité :
formulaire déjà pleinement qualifié, contenu à jour avec prestataire en
place, ou absence explicite de besoin.

MODÈLE RETENU
-------------
Deux dimensions, toutes deux traçables dans la preuve :

1. **Force** — fort / modéré / faible, selon des marqueurs explicites.
2. **Portée** — le contre-signal nie-t-il le besoin poursuivi, ou ne fait-il
   que le délimiter ?

La pénalité s'applique à la **priorité commerciale transversale**, jamais aux
trois scores techniques v8, qui restent des mesures factuelles de l'existant.
Elle est **bornée** pour que l'empilement de plusieurs contre-signaux faibles
ne puisse pas produire l'effet d'un contre-signal fort.

Un besoin **exprimé par l'entreprise** n'est pas annulé par un constat de
l'agent : si une société demande une refonte, sa demande vaut mieux que notre
avis sur son site. Le plancher « exprimé vérifié » reste donc appliqué après
la pénalité, et ce choix est tracé dans les motifs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any, Iterable

from .models import Evidence, EVIDENCE_MATURITY

STRENGTH_STRONG = "fort"
STRENGTH_MODERATE = "modere"
STRENGTH_WEAK = "faible"
STRENGTHS = (STRENGTH_STRONG, STRENGTH_MODERATE, STRENGTH_WEAK)

# Pénalités en points de priorité commerciale. Valeurs justifiées par la
# simulation sur les 16 fiches : un contre-signal fort doit franchir au moins
# un seuil de priorité (70 / 45), un modéré doit rester dans son palier ou
# descendre d'un cran, un faible ne doit pas changer de palier à lui seul.
# Un contre-signal FAIBLE ne déplace pas la priorité (0 point) : il est
# enregistré et rendu visible, mais une mention qui ne fait que délimiter le
# périmètre ne doit pas faire franchir un seuil. Cas limite réel : O Lames
# Déchues est à 71, juste au-dessus du seuil « haute », avec un contre-signal
# visant l'encaissement en carte bancaire alors que le besoin poursuivi est une
# page de planning absente. Une pénalité de 4 points l'aurait rétrogradée sans
# raison commerciale : effet mécanique refusé.
PENALTY_BY_STRENGTH = {
    STRENGTH_STRONG: 24,
    STRENGTH_MODERATE: 11,
    STRENGTH_WEAK: 0,
}
# Empilement : le plus fort compte pleinement, les suivants à taux réduit.
STACK_RATE = 0.4
# Plafond global : aucun cumul ne peut effacer une opportunité à lui seul.
PENALTY_CAP = 32
# Au-delà, un contre-signal est trop ancien pour être opposé au besoin actuel.
FRESHNESS_DAYS = 180

# Marqueurs de NÉGATION du besoin poursuivi. Ce sont eux qui font la
# différence entre « délimiter » et « annuler ».
# Négation ABSOLUE : elle porte sur le besoin lui-même, quel que soit son
# périmètre. Seule celle-ci justifie une force « fort ».
NEGATION_MARKERS = (
    "aucun besoin",
    "contre-signal majeur",
    "pleinement qualifié",
    "pleinement qualifie",
    "besoin déjà résolu",
    "besoin deja resolu",
    "entreprise fermée",
    "entreprise fermee",
    "cessé son activité",
    "cesse son activite",
    "n'est plus en activité",
)

# Négation PARTIELLE : « le besoin n'est pas la création d'un parcours de
# devis » ne nie pas la refonte poursuivie, il en réduit le périmètre. La
# confondre avec une négation absolue rétrogradait à tort la Scierie Labrue et
# Ouest Affûtage, dont les défauts constatés restent réels. Une négation
# partielle est donc MODÉRÉE, jamais forte.
SCOPE_LIMITING_MARKERS = (
    "le besoin n'est pas",
    "le besoin n est pas",
)

# Marqueurs de force FORTE : l'équivalent fonctionnel existe déjà, ou un
# prestataire est en place sur le besoin visé.
STRONG_MARKERS = (
    "prestataire web déjà en place",
    "prestataire web deja en place",
    "déjà pleinement",
    "deja pleinement",
    "site déjà performant",
    "site deja performant",
    "besoin est cosmétique",
    "besoin est cosmetique",
)

# Marqueurs de force MODÉRÉE : une fonctionnalité comparable existe, le
# périmètre du besoin s'en trouve réduit.
MODERATE_MARKERS = (
    "boutique en ligne",
    "qualifie déjà",
    "qualifie deja",
    "grille tarifaire complète",
    "grille tarifaire complete",
    "site structuré",
    "site structure",
    "site multi-activités structuré",
    "consentement configuré",
    "consentement configure",
    "formulaire de demande existe",
    "prestataire web est déjà crédité",
    "prestataire web est deja credite",
    "un prestataire web",
)

# Marqueurs de force FAIBLE : le contre-signal délimite le besoin, ou vise un
# autre besoin que celui poursuivi.
WEAK_MARKERS = (
    "le manque est",
    "le besoin porte sur",
    "présence en ligne existe",
    "presence en ligne existe",
    "un formulaire de contact fonctionne",
    "formulaire fonctionnel existe",
    "contre-signal à un besoin de",
    "contre-signal a un besoin de",
    "n'est pas la création",
    "n'est pas la creation",
    "pas sur le site entier",
    "coordonnées sont joignables",
)


@dataclass(frozen=True)
class CounterSignal:
    """Un contre-signal explicite, qualifié et justifié."""

    quote: str
    source_url: str
    observed_at: str
    strength: str
    negates_need: bool
    fresh: bool
    reliable_source: bool
    penalty: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _text(evidence: Evidence) -> str:
    return f"{evidence.detail or ''} {evidence.quote or ''}".lower()


def _is_fresh(evidence: Evidence, today: date) -> bool:
    raw = evidence.observed_at or evidence.verified_at or ""
    try:
        seen = date.fromisoformat(raw[:10])
    except (ValueError, TypeError):
        # Sans date, le contre-signal n'est pas opposable comme preuve actuelle.
        return False
    return (today - seen).days <= FRESHNESS_DAYS


def classify(evidence: Evidence, today: date | None = None) -> CounterSignal:
    """Qualifie une preuve `maturite_existante` sans modifier aucun score."""
    today = today or date.today()
    text = _text(evidence)
    negates = any(m in text for m in NEGATION_MARKERS)

    scope_limited = any(m in text for m in SCOPE_LIMITING_MARKERS)
    if negates or any(m in text for m in STRONG_MARKERS):
        strength = STRENGTH_STRONG
        matched = [m for m in NEGATION_MARKERS + STRONG_MARKERS if m in text]
    elif scope_limited or any(m in text for m in MODERATE_MARKERS):
        strength = STRENGTH_MODERATE
        matched = [m for m in SCOPE_LIMITING_MARKERS + MODERATE_MARKERS if m in text]
    elif any(m in text for m in WEAK_MARKERS):
        strength = STRENGTH_WEAK
        matched = [m for m in WEAK_MARKERS if m in text]
    else:
        # Aucun marqueur reconnu : prudence, on ne pénalise pas sur une
        # simple mention d'équipement. Une relecture humaine est préférable à
        # une pénalité devinée.
        strength = STRENGTH_WEAK
        matched = []

    fresh = _is_fresh(evidence, today)
    reliable = (evidence.source_type == "site_officiel"
                and evidence.reliability in ("haute", "moyenne"))

    effective = strength
    notes = []
    if not fresh:
        effective = STRENGTH_WEAK
        notes.append("contre-signal ancien ou non daté : force ramenée à faible")
    if not reliable:
        effective = STRENGTH_WEAK
        notes.append("source non officielle ou peu fiable : force ramenée à faible")

    penalty = PENALTY_BY_STRENGTH[effective]
    reason = (f"force {strength}"
              + (" → " + effective if effective != strength else "")
              + (f" (marqueurs : {', '.join(matched[:3])})" if matched
                 else " (aucun marqueur explicite : prudence)")
              + (" ; nie le besoin poursuivi" if negates else " ; délimite le besoin sans l'annuler")
              + (" ; " + " ; ".join(notes) if notes else ""))
    return CounterSignal(
        quote=evidence.quote or "", source_url=evidence.source_url or "",
        observed_at=evidence.observed_at or "", strength=effective,
        negates_need=negates, fresh=fresh, reliable_source=reliable,
        penalty=penalty, reason=reason)


def collect(evidences: Iterable[Evidence], today: date | None = None) -> list[CounterSignal]:
    """Contre-signaux explicites, triés du plus fort au plus faible."""
    signals = [classify(e, today) for e in evidences
               if e.kind == EVIDENCE_MATURITY]
    return sorted(signals, key=lambda s: -s.penalty)


def total_penalty(signals: Iterable[CounterSignal]) -> int:
    """Pénalité bornée : le plus fort compte plein, les autres à taux réduit.

    Sans ce bornage, trois contre-signaux faibles pèseraient autant qu'un
    contre-signal fort, ce qui est mécaniquement faux.
    """
    ordered = sorted((s.penalty for s in signals), reverse=True)
    if not ordered:
        return 0
    total = ordered[0] + sum(p * STACK_RATE for p in ordered[1:])
    return int(min(PENALTY_CAP, round(total)))


def breakdown(signals: Iterable[CounterSignal]) -> dict[str, int]:
    counts = {s: 0 for s in STRENGTHS}
    for sig in signals:
        counts[sig.strength] += 1
    return counts
