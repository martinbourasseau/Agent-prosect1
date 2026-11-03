"""Qualification v3 : score fondé preuves + niveaux de priorité CRM + dédoublonnage.

Barème :
- besoin exprimé publiquement : +50 (signal le plus fort)
- lacune vérifiée sur le site : +20 chacune (plafond 40)
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
    gaps = [e for e in prospect.evidences if e.kind == EVIDENCE_WEBSITE_GAP]
    sector_opps = [e for e in prospect.evidences if e.kind == EVIDENCE_SECTOR_OPPORTUNITY]

    if public:
        score += 50
        reasons.append(f"besoin exprimé publiquement (+50) : {public[0].source_url}")
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
    if public and has_email:
        tier = TIER_HAUTE
    elif has_email and (gaps or sector_opps or score >= 40):
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
        key = p.contact_email.strip().lower()
        if key in seen:
            res = QualificationResult(p, res.score, EXCLUDED, ["doublon dans le lot"], res.tier)
        seen.add(key)
        results.append(res)
    return results
