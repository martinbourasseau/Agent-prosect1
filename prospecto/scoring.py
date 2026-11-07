"""Trois scores indépendants, justifiés et bornés par la preuve (v7).

Ce qui change avec la v7
------------------------
1. **Le contenu des preuves est analysé, plus seulement leur type.** L'axe
   automatisation additionne des signaux opérationnels nommés (devis manuel,
   réservation téléphonique, collecte de pièces, planification à la main…) et
   retranche les contre-signaux de maturité (réservation en ligne, paiement,
   espace client). Deux entreprises du même métier obtiennent donc des scores
   différents dès lors que leurs processus publiés diffèrent. Le secteur n'est
   jamais une entrée du calcul.

2. **Faits et hypothèses sont séparés.** Une preuve marquée `observed=False`
   compte pour moitié et dégrade la confiance. Une possibilité d'amélioration
   n'est pas traitée comme un problème constaté.

3. **La fiabilité de la source pèse.** Le site officiel de l'entreprise fait foi
   sur ses propres processus ; un annuaire pèse moins de la moitié.

4. **Le calcul ne dépend plus de l'ordre des preuves.** Les contributions sont
   triées par poids décroissant, ce qui rend le score reproductible.

5. **Chaque axe expose ses preuves, ses manques et sa confiance.** Un score sans
   preuve reste bas et le dit explicitement.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
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
    EVIDENCE_JOURNEY_GAP, EVIDENCE_MATURITY,
    EMAIL_VERIFIED,
    EMAIL_PUBLIC_UNVERIFIED,
)
from .email_verify import DELIVERABLE_STATUSES, BLOCKING_STATUSES, MX_NOT_CHECKED
from . import opportunity

AXIS_SITE_WEB = "site_web"
AXIS_REFONTE = "refonte"
AXIS_IA = "ia_automatisation"
AXES = (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA)

LEVEL_FORT = "fort"
LEVEL_MOYEN = "moyen"
LEVEL_FAIBLE = "faible"

CONFIDENCE_HIGH = "haute"
CONFIDENCE_MEDIUM = "moyenne"
CONFIDENCE_LOW = "faible"
_CONFIDENCE_ORDER = (CONFIDENCE_LOW, CONFIDENCE_MEDIUM, CONFIDENCE_HIGH)

PRIORITY_HAUTE = "haute"
PRIORITY_MOYENNE = "moyenne"
PRIORITY_BASSE = "basse"
PRIORITY_A_APPROFONDIR = "a_approfondir"

# Pondération de la contribution d'une preuve selon sa source et son statut.
RELIABILITY_FACTOR = {"haute": 1.0, "moyenne": 0.75, "faible": 0.45}
INFERRED_FACTOR = 0.5
# Un processus déjà partiellement automatisé reste perfectible : le contre-signal
# retranche 80 % de son poids, pas 100 %.
MATURITY_FACTOR = 0.8
# Plafond de la contribution « type de preuve » seule : le type est une
# classification du chercheur, pas une observation du processus.
KIND_BASE_IA = 12
FRESHNESS_DAYS = 180


@dataclass
class AxisScore:
    """Note d'un axe : motifs, preuves, manques et confiance."""

    axis: str
    score: int
    level: str
    reasons: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    confidence: str = CONFIDENCE_LOW
    observed_signals: list[str] = field(default_factory=list)
    hypothetical_signals: list[str] = field(default_factory=list)
    counter_signals: list[str] = field(default_factory=list)

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


def _weight_of_detection(det: opportunity.Detection) -> float:
    factor = RELIABILITY_FACTOR.get(det.reliability, 0.75)
    if det.hypothetical:
        factor *= INFERRED_FACTOR
    return det.signal.weight * factor


def _confidence(detections: list[opportunity.Detection], evidences: list[Evidence],
                today: date | None = None, extra_sources: set[str] | None = None) -> str:
    """Confiance = observed + fiabilité + nombre de sources + fraîcheur."""
    if not detections and not evidences:
        return CONFIDENCE_LOW
    contributing = detections or []
    solid = [d for d in contributing if d.observed and d.reliability == "haute"]
    sources = {d.source_url for d in contributing if d.source_url}
    # v7.1 — deux pages qui établissent le même processus sont deux sources,
    # même si un seul signal en a été tiré (le catalogue dédoublonne par
    # signal, pas par page). Sans cela, Canfora restait en confiance moyenne
    # alors que bourrellerie ET sellerie décrivent le même devis en magasin.
    if extra_sources:
        sources |= {s for s in extra_sources if s}
    if not contributing:
        solid_ev = [e for e in evidences if e.observed and e.reliability == "haute"]
        sources = {e.source_url for e in solid_ev if e.source_url}
        solid = solid_ev  # type: ignore[assignment]
    if not solid:
        level = CONFIDENCE_LOW
    elif len(sources) >= 2:
        level = CONFIDENCE_HIGH
    else:
        level = CONFIDENCE_MEDIUM
    if any(not d.observed for d in contributing):
        level = _CONFIDENCE_ORDER[max(0, _CONFIDENCE_ORDER.index(level) - 1)]
    # Fraîcheur : une preuve ancienne ne vaut pas une preuve revérifiée.
    ref = today or date.today()
    stamps = [getattr(e, "verified_at", "") or getattr(e, "observed_at", "") for e in evidences]
    parsed = []
    for stamp in stamps:
        try:
            parsed.append(date.fromisoformat(str(stamp)[:10]))
        except (ValueError, TypeError):
            continue
    if parsed and all((ref - d).days > FRESHNESS_DAYS for d in parsed):
        level = _CONFIDENCE_ORDER[max(0, _CONFIDENCE_ORDER.index(level) - 1)]
    return level


def _kind_contributions(evidences: list[Evidence], weights: dict[str, int],
                        limit: int = 2) -> tuple[int, list[str], list[Evidence]]:
    """Contribution des types de preuve, plus forte d'abord (ordre indépendant)."""
    ranked = sorted(
        ((weights.get(ev.kind, 0), i, ev) for i, ev in enumerate(evidences)),
        key=lambda t: (-t[0], t[1]),
    )
    total, reasons, used = 0, [], []
    for weight, _i, ev in ranked:
        if not weight or len(used) >= limit:
            continue
        factor = RELIABILITY_FACTOR.get(ev.reliability, 0.75)
        if not ev.observed:
            factor *= INFERRED_FACTOR
        gained = int(round(weight * factor))
        total += gained
        tag = "" if ev.observed else " [hypothèse, non un fait observé]"
        reasons.append(f"+{gained} {ev.kind} : {_cite(ev)}{tag}")
        used.append(ev)
    return total, reasons, used


def _det_reason(det: opportunity.Detection, gained: int, sign: str = "+") -> str:
    """Justification nominative : signal, extrait réel, motif trouvé, source."""
    tag = "" if det.observed else " [hypothèse]"
    quote = (det.quote or "").strip().replace("\n", " ")
    if len(quote) > 90:
        quote = quote[:87] + "…"
    return (f"{sign}{gained} {det.signal.label} — « {quote} » "
            f"[motif : {det.matched_pattern}] ({det.source_url}){tag}")


def _det_evidence(det: opportunity.Detection) -> dict[str, Any]:
    return det.to_dict()


def score_prospect(prospect: Prospect, today: date | None = None) -> dict[str, Any]:
    """Calcule les trois scores. Retourne un dict sérialisable pour le CRM."""
    evs = list(prospect.evidences)
    has_site = bool(prospect.website or prospect.domain)
    down = any(e.kind == EVIDENCE_SITE_DOWN for e in evs)
    absent = any(e.kind == EVIDENCE_SITE_ABSENT for e in evs)
    report = opportunity.analyze(evs, prospect.process_hint)

    # --- Axe 1 : création de site -------------------------------------------
    if absent:
        base, base_reason = 80, "aucun site identifié : présence en ligne à créer"
    elif down:
        base, base_reason = 75, "site existant mais indisponible : présence en ligne à reconstruire"
    elif has_site:
        base, base_reason = 5, "un site est déjà en ligne : pas de création à proprement parler"
    else:
        base, base_reason = 0, "présence en ligne non documentée"
    kind_total, kind_reasons, kind_used = _kind_contributions(
        evs, {EVIDENCE_SITE_ABSENT: 15, EVIDENCE_SITE_DOWN: 15})
    presence_total = 0
    presence_reasons, presence_ev = [], []
    for det in report.presence:
        gained = int(round(_weight_of_detection(det)))
        presence_total += gained
        presence_reasons.append(_det_reason(det, gained))
        presence_ev.append(_det_evidence(det))
    site_total = base + kind_total + presence_total
    site_reasons = ([base_reason] if base_reason else []) + kind_reasons + presence_reasons
    site_missing = []
    if has_site and not absent:
        site_missing.append("un site existe déjà : la création n'est pas le bon service")
    if not has_site:
        site_missing.append("confirmer l'absence de site officiel (annuaire, registre, page professionnelle)")
    if not report.presence and not absent and not down and not has_site:
        site_missing.append("aucune observation directe sur la présence en ligne")
    site = AxisScore(AXIS_SITE_WEB, max(0, min(100, site_total)), _level(max(0, min(100, site_total))),
                     site_reasons or ["aucune preuve directe sur cet axe : score volontairement bas"],
                     presence_ev, site_missing,
                     _confidence(report.presence, kind_used or evs, today),
                     [d.signal.label for d in report.presence if d.observed],
                     [d.signal.label for d in report.presence if not d.observed])

    # --- Axe 2 : refonte ----------------------------------------------------
    ref_kind_total, ref_kind_reasons, ref_kind_used = _kind_contributions(
        evs, {EVIDENCE_SITE_OBSOLETE: 50, EVIDENCE_JOURNEY_GAP: 40, EVIDENCE_WEBSITE_GAP: 30,
              EVIDENCE_SITE_DOWN: 20, EVIDENCE_PUBLIC_NEED: 10})
    ref_signal_total, ref_reasons, ref_ev = 0, [], []
    for det in report.refonte:
        gained = int(round(_weight_of_detection(det)))
        ref_signal_total += gained
        ref_reasons.append(_det_reason(det, gained))
        ref_ev.append(_det_evidence(det))
    ref_base = 5 if has_site else 0
    ref_total = max(0, min(100, ref_base + ref_kind_total + ref_signal_total))
    ref_all_reasons = (["site existant à moderniser" if has_site else "pas de site à refondre"]
                       + ref_kind_reasons + ref_reasons)
    if not ref_kind_reasons and not ref_reasons:
        ref_all_reasons.append("aucune preuve directe sur cet axe : score volontairement bas")
    ref_missing = []
    if not any(d.signal.id == "mobile_degrade" for d in report.refonte):
        ref_missing.append("comportement sur mobile non vérifié")
    if not has_site:
        ref_missing.append("aucun site à évaluer")
    ref_sources = ({d.source_url for d in report.refonte if d.source_url}
                   | {e.source_url for e in evs if e.source_url and e.observed
                      and e.kind in (EVIDENCE_JOURNEY_GAP, EVIDENCE_WEBSITE_GAP,
                                     EVIDENCE_SITE_OBSOLETE)})
    if len(ref_sources) < 2:
        ref_missing.append("une seule page observée : vérifier le parcours de contact sur une seconde page")
    refonte = AxisScore(AXIS_REFONTE, ref_total, _level(ref_total), ref_all_reasons, ref_ev,
                        ref_missing, _confidence(report.refonte, ref_kind_used or evs, today,
                                                 extra_sources=ref_sources),
                        [d.signal.label for d in report.refonte if d.observed],
                        [d.signal.label for d in report.refonte if not d.observed])

    # --- Axe 3 : agent IA / automatisation ----------------------------------
    # Le secteur n'intervient nulle part. Seuls les processus publiés comptent.
    process_evidences = [e for e in evs
                         if e.kind in (EVIDENCE_PROCESS_MANUAL, EVIDENCE_JOURNEY_GAP)]
    ia_base = KIND_BASE_IA if process_evidences else 0
    ia_reasons = []
    if ia_base:
        ia_reasons.append(f"+{ia_base} processus manuel signalé par le chercheur "
                          f"(type de preuve seul, volontairement plafonné)")
    auto_total, auto_ev = 0, []
    for det in report.automation:
        gained = int(round(_weight_of_detection(det)))
        auto_total += gained
        ia_reasons.append(_det_reason(det, gained))
        auto_ev.append(_det_evidence(det))
    maturity_total = 0
    for det in report.maturity:
        lost = int(round(_weight_of_detection(det) * MATURITY_FACTOR))
        maturity_total += lost
        ia_reasons.append(_det_reason(det, lost, sign="-"))
    ia_total = max(0, min(100, ia_base + auto_total - maturity_total))
    if not report.automation and not process_evidences:
        ia_reasons.append("aucune preuve directe sur cet axe : score volontairement bas")
    ia_missing = []
    if not report.automation:
        ia_missing.append("aucun processus entrant décrit publiquement : observer comment "
                          "arrivent et sont traitées les demandes (devis, réservation, dossier)")
    if not report.maturity and not any(e.kind == EVIDENCE_MATURITY for e in evs):
        ia_missing.append("ce qui est déjà automatisé n'est pas documenté "
                          "(réservation en ligne, paiement, espace client, réponse automatique)")
    ia_sources = ({d.source_url for d in report.automation if d.source_url}
                  | {e.source_url for e in process_evidences
                     if e.source_url and e.observed})
    if len(ia_sources) < 2:
        ia_missing.append("processus observé sur une seule page : confirmer sur une seconde source")
    if prospect.process_hint and not report.automation:
        ia_missing.append("le processus est affirmé dans process_hint mais aucune citation ne l'établit")
    ia = AxisScore(AXIS_IA, ia_total, _level(ia_total), ia_reasons, auto_ev, ia_missing,
                   _confidence(report.automation, process_evidences or evs, today,
                               extra_sources=ia_sources),
                   [d.signal.label for d in report.automation if d.observed],
                   [d.signal.label for d in report.automation if not d.observed],
                   [d.signal.label for d in report.maturity])

    scores = {s.axis: s.to_dict() for s in (site, refonte, ia)}
    scores["priority"] = commercial_priority(prospect, scores)
    scores["best_axis"] = max(AXES, key=lambda a: scores[a]["score"])
    scores["engine_version"] = "v7.1"
    scores["opportunity_report"] = report.to_dict()
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
