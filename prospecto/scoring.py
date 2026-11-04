"""Trois scores indépendants et justifiés par prospect (lot 5).

Le besoin « création de site », le besoin « refonte » et le besoin
« agent IA / automatisation » ne se déduisent pas les uns des autres : une
entreprise peut avoir un site excellent et un processus administratif entièrement
manuel, ou un site à reconstruire sans aucun processus à automatiser.

Chaque axe est donc noté séparément, de 0 à 100, à partir de **preuves
observées** (type de preuve + extrait cité + URL). Aucun score n'est attribué
sur la seule base du secteur d'activité : sans preuve, l'axe reste faible et le
motif « aucune preuve » est explicitement conservé.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .models import (
    Evidence,
    Prospect,
    EVIDENCE_PUBLIC_NEED,
    EVIDENCE_WEBSITE_GAP,
    EVIDENCE_SECTOR_OPPORTUNITY,
    EVIDENCE_SITE_ABSENT,
    EVIDENCE_SITE_DOWN,
    EVIDENCE_SITE_OBSOLETE,
    EVIDENCE_PROCESS_MANUAL,
    EVIDENCE_JOURNEY_GAP,
    EMAIL_VERIFIED,
    EMAIL_PUBLIC_UNVERIFIED,
)
from .email_verify import DELIVERABLE_STATUSES, BLOCKING_STATUSES, MX_NOT_CHECKED

AXIS_SITE_WEB = "site_web"
AXIS_REFONTE = "refonte"
AXIS_IA = "ia_automatisation"
AXES = (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA)

LEVEL_FORT = "fort"
LEVEL_MOYEN = "moyen"
LEVEL_FAIBLE = "faible"

PRIORITY_HAUTE = "haute"
PRIORITY_MOYENNE = "moyenne"
PRIORITY_BASSE = "basse"
PRIORITY_A_APPROFONDIR = "a_approfondir"


@dataclass
class AxisScore:
    """Note d'un axe, avec la liste des motifs sourcés qui la produisent."""

    axis: str
    score: int
    level: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _level(score: int) -> str:
    if score >= 70:
        return LEVEL_FORT
    if score >= 40:
        return LEVEL_MOYEN
    return LEVEL_FAIBLE


def _cite(ev: Evidence) -> str:
    quote = (ev.quote or "").strip().replace("\n", " ")
    if len(quote) > 110:
        quote = quote[:107] + "…"
    return f'« {quote} » ({ev.source_url})'


def _score_axis(evidences: list[Evidence], weights: dict[str, int], axis: str,
                base: int, base_reason: str) -> AxisScore:
    total = base
    reasons: list[str] = [base_reason] if base_reason else []
    used = 0
    for ev in evidences:
        weight = weights.get(ev.kind, 0)
        if not weight or used >= 2:  # deux preuves maximum par axe : pas d'empilement
            continue
        total += weight
        used += 1
        reasons.append(f"+{weight} {ev.kind} : {_cite(ev)}")
    if used == 0:
        reasons.append("aucune preuve directe sur cet axe : score volontairement bas")
    total = max(0, min(100, total))
    return AxisScore(axis, total, _level(total), reasons)


def score_prospect(prospect: Prospect) -> dict[str, Any]:
    """Calcule les trois scores. Retourne un dict sérialisable pour le CRM."""
    evs = prospect.evidences
    has_site = bool(prospect.website or prospect.domain)
    down = any(e.kind == EVIDENCE_SITE_DOWN for e in evs)
    absent = any(e.kind == EVIDENCE_SITE_ABSENT for e in evs)

    # --- Axe 1 : création de site -------------------------------------------
    if absent:
        base, base_reason = 80, "aucun site identifié : présence en ligne à créer"
    elif down:
        base, base_reason = 75, "site existant mais indisponible : présence en ligne à reconstruire"
    elif has_site:
        base, base_reason = 5, "un site est déjà en ligne : pas de création à proprement parler"
    else:
        base, base_reason = 0, "présence en ligne non documentée"
    site = _score_axis(evs, {EVIDENCE_SITE_ABSENT: 15, EVIDENCE_SITE_DOWN: 15}, AXIS_SITE_WEB,
                       base, base_reason)

    # --- Axe 2 : refonte ----------------------------------------------------
    refonte = _score_axis(
        evs,
        {EVIDENCE_SITE_OBSOLETE: 50, EVIDENCE_JOURNEY_GAP: 40, EVIDENCE_WEBSITE_GAP: 30,
         EVIDENCE_SITE_DOWN: 20, EVIDENCE_PUBLIC_NEED: 10},
        AXIS_REFONTE, 5 if has_site else 0,
        "site existant à moderniser" if has_site else "pas de site à refondre",
    )

    # --- Axe 3 : agent IA / automatisation ----------------------------------
    ia_base = 10 if prospect.process_hint else 0
    ia_reason = ("processus concret observé : " + prospect.process_hint[:120]) if prospect.process_hint else ""
    ia = _score_axis(
        evs,
        {EVIDENCE_PROCESS_MANUAL: 60, EVIDENCE_PUBLIC_NEED: 30, EVIDENCE_JOURNEY_GAP: 20,
         EVIDENCE_SECTOR_OPPORTUNITY: 0},
        AXIS_IA, ia_base, ia_reason,
    )

    scores = {s.axis: s.to_dict() for s in (site, refonte, ia)}
    scores["priority"] = commercial_priority(prospect, scores)
    scores["best_axis"] = max(AXES, key=lambda a: scores[a]["score"])
    return scores


def commercial_priority(prospect: Prospect, scores: dict[str, Any]) -> str:
    """Priorité commerciale = meilleur axe + contactabilité réelle.

    Un excellent besoin sans adresse joignable n'est pas une priorité haute :
    il devient « à approfondir » (recherche de coordonnées), jamais « haute ».
    """
    best = max(int(scores[a]["score"]) for a in AXES)
    dns = getattr(prospect, "email_dns_status", "") or MX_NOT_CHECKED
    email = (prospect.contact_email or "").strip()
    if not email or prospect.email_verification == "none" or dns in BLOCKING_STATUSES:
        return PRIORITY_A_APPROFONDIR
    contactable = prospect.email_verification == EMAIL_VERIFIED and dns in DELIVERABLE_STATUSES
    published = prospect.email_verification in (EMAIL_VERIFIED, EMAIL_PUBLIC_UNVERIFIED)
    if best >= 70 and contactable:
        return PRIORITY_HAUTE
    if best >= 70 and published:
        return PRIORITY_MOYENNE
    if best >= 40 and published:
        return PRIORITY_MOYENNE
    return PRIORITY_BASSE


def scores_from_record(record: dict[str, Any]) -> dict[str, Any]:
    """Recalcule les scores d'une fiche CRM déjà importée (preuves conservées)."""
    evs = [Evidence(**{k: v for k, v in e.items() if k in Evidence.__dataclass_fields__})
           for e in record.get("evidence", [])]
    prospect = Prospect(
        company=record.get("company", ""),
        domain=record.get("domain", ""),
        contact_email=record.get("email", ""),
        sector=record.get("sector", ""),
        needs=record.get("needs") or ([record["need"]] if record.get("need") else []),
        evidences=evs,
        website=record.get("website", ""),
        process_hint=record.get("process_hint", ""),
        email_verification=record.get("email_verification", EMAIL_PUBLIC_UNVERIFIED),
    )
    prospect.email_dns_status = record.get("email_dns_status", MX_NOT_CHECKED)  # type: ignore[attr-defined]
    return score_prospect(prospect)


def primary_need_from_scores(scores: dict[str, Any]) -> str:
    """Besoin principal déduit des scores (et non du secteur)."""
    from .models import NEED_SITE_WEB, NEED_REFONTE, NEED_AUTOMATISATION

    mapping = {AXIS_SITE_WEB: NEED_SITE_WEB, AXIS_REFONTE: NEED_REFONTE, AXIS_IA: NEED_AUTOMATISATION}
    return mapping[max(AXES, key=lambda a: scores[a]["score"])]
