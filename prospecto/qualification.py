"""Qualification v3 : score fondé preuves + niveaux de priorité CRM + dédoublonnage.

Barème :
- besoin exprimé publiquement : +50 (signal le plus fort)
- lacune vérifiée sur le site : +20 chacune (plafond 40)
- processus manuel documenté (lot 5) : +50 (besoin réel, aussi fort qu'un besoin exprimé)
- site indisponible / absent (lot 5) : +50 / +40
- parcours client incomplet (lot 5) : +30
- site daté (lot 5) : +20 (compté dans le plafond « lacunes »)
- opportunité sectorielle documentée : +10
- secteur connu : +10
- prénom du contact connu : +5

Niveaux (mission v3) :
- haute          : besoin explicitement exprimé + contact email exploitable
- moyenne        : besoin fortement probable, éléments concrets + contact
- a_approfondir  : opportunité intéressante mais informations insuffisantes
On ne rejette pas les opportunités moyennes : elles sont conservées avec leur niveau.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import HISTORY_DIR, TIER_HAUTE, TIER_MOYENNE, TIER_A_APPROFONDIR
from .models import (
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
)
from .strategy import KNOWN_SECTORS

QUALIFIED = "qualified"
REVIEW = "a_revoir"
NOT_QUALIFIED = "non_qualifie"
EXCLUDED = "exclu"

_TIER_TO_STATUS = {
    TIER_HAUTE: QUALIFIED,
    TIER_MOYENNE: REVIEW,
    TIER_A_APPROFONDIR: NOT_QUALIFIED,
}


@dataclass
class QualificationResult:
    prospect: Prospect
    score: int
    status: str
    reasons: list[str] = field(default_factory=list)
    tier: str = TIER_A_APPROFONDIR

    def to_dict(self) -> dict[str, Any]:
        return {
            "company": self.prospect.company,
            "contact_email": self.prospect.contact_email,
            "score": self.score,
            "status": self.status,
            "tier": self.tier,
            "reasons": self.reasons,
        }


def load_contacted_emails(history_dir: Path | None = None) -> set[str]:
    history_dir = history_dir or HISTORY_DIR
    contacted: set[str] = set()
    if not history_dir.exists():
        return contacted
    for path in sorted(history_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for entry in raw.get("sent", []):
            if entry.get("email"):
                contacted.add(entry["email"].strip().lower())
    return contacted


def load_contacted_domains(history_dir: Path | None = None) -> set[str]:
    history_dir = history_dir or HISTORY_DIR
    domains: set[str] = set()
    if not history_dir.exists():
        return domains
    for path in sorted(history_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for entry in raw.get("sent", []):
            if entry.get("domain"):
                domains.add(entry["domain"].strip().lower())
    return domains


def qualify(
    prospect: Prospect,
    contacted_emails: set[str] | None = None,
    contacted_domains: set[str] | None = None,
) -> QualificationResult:
    contacted_emails = contacted_emails if contacted_emails is not None else load_contacted_emails()
    contacted_domains = contacted_domains if contacted_domains is not None else load_contacted_domains()

    reasons: list[str] = []
    score = 0

    errors = prospect.validate()
    if errors:
        return QualificationResult(prospect, 0, NOT_QUALIFIED, [f"invalide : {e}" for e in errors], TIER_A_APPROFONDIR)

    email = prospect.contact_email.strip().lower()
    domain = (prospect.domain or "").strip().lower()
    if email in contacted_emails or (domain and domain in contacted_domains):
        return QualificationResult(prospect, 0, EXCLUDED, ["déjà contacté (historique d'envois)"], TIER_A_APPROFONDIR)

    public = [e for e in prospect.evidences if e.kind == EVIDENCE_PUBLIC_NEED]
    gaps = [e for e in prospect.evidences if e.kind in (EVIDENCE_WEBSITE_GAP, EVIDENCE_SITE_OBSOLETE)]
    sector_opps = [e for e in prospect.evidences if e.kind == EVIDENCE_SECTOR_OPPORTUNITY]
    manual = [e for e in prospect.evidences if e.kind == EVIDENCE_PROCESS_MANUAL]
    down = [e for e in prospect.evidences if e.kind == EVIDENCE_SITE_DOWN]
    absent = [e for e in prospect.evidences if e.kind == EVIDENCE_SITE_ABSENT]
    journey = [e for e in prospect.evidences if e.kind == EVIDENCE_JOURNEY_GAP]

    if public:
        score += 50
        reasons.append(f"besoin exprimé publiquement (+50) : {public[0].source_url}")
    if manual:
        score += 50
        reasons.append(f"processus manuel documenté (+50) : {manual[0].source_url}")
    if down:
        score += 50
        reasons.append(f"site indisponible constaté (+50) : {down[0].source_url}")
    elif absent:
        score += 40
        reasons.append(f"aucune présence en ligne exploitable (+40) : {absent[0].source_url}")
    if journey:
        score += 30
        reasons.append(f"parcours client incomplet (+30) : {journey[0].source_url}")
    if gaps:
        bonus = min(20 * len(gaps), 40)
        score += bonus
        reasons.append(f"{len(gaps)} lacune(s) vérifiée(s) sur le site (+{bonus})")
    if sector_opps:
        score += 10
        reasons.append("opportunité sectorielle documentée (+10)")
    if prospect.sector in KNOWN_SECTORS:
        score += 10
        reasons.append(f"secteur connu ({prospect.sector}) (+10)")
    if prospect.contact_name:
        score += 5
        reasons.append("prénom du contact connu (+5)")

    # Niveau de priorité (ne pas rejeter les opportunités moyennes).
    has_email = bool(prospect.contact_email and "@" in prospect.contact_email)
    documented = bool(public or manual or down)
    if documented and has_email:
        tier = TIER_HAUTE
    elif has_email and (gaps or sector_opps or journey or absent or score >= 40):
        tier = TIER_MOYENNE
    else:
        tier = TIER_A_APPROFONDIR

    status = _TIER_TO_STATUS[tier]
    return QualificationResult(prospect, score, status, reasons, tier)


def qualify_batch(prospects: list[Prospect]) -> list[QualificationResult]:
    contacted_emails = load_contacted_emails()
    contacted_domains = load_contacted_domains()
    seen: set[str] = set()
    results = []
    for p in prospects:
        res = qualify(p, contacted_emails, contacted_domains)
        # Clé de dédoublonnage : domaine > email > nom (les prospects sans
        # domaine/email ne doivent pas collisionner sur une clé vide).
        key = (p.domain or "").strip().lower() or p.contact_email.strip().lower() or p.company.strip().lower()
        if key and key in seen:
            res = QualificationResult(p, res.score, EXCLUDED, ["doublon dans le lot"], res.tier)
        if key:
            seen.add(key)
        results.append(res)
    return results
