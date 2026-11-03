"""CRM Prospecto — base de prospects enrichie, persistée, sans écrasement.

Règles (mission v3) :
- ne jamais remplacer une donnée déjà enregistrée (fusion : on ne comble que les champs vides) ;
- dédoublonnage par domaine / email + historique des envois ;
- aucune coordonnée fabriquée : email_source indique où l'adresse a été trouvée ;
- chaque opportunité conserve ses preuves (URL) et son niveau de confiance.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CRM_PATH, HISTORY_DIR
from .models import Prospect
from .qualification import QualificationResult, qualify


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "prospect"


def _key(record: dict[str, Any]) -> str:
    domain = (record.get("domain") or "").strip().lower()
    if domain:
        return f"domain:{domain}"
    email = (record.get("email") or "").strip().lower()
    return f"email:{email}" if email else f"name:{_slug(record.get('company', ''))}"


class CRM:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CRM_PATH
        self.records: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.records = raw.get("prospects", [])
        else:
            self.records = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "count": len(self.records), "prospects": self.records}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _find(self, key: str) -> dict[str, Any] | None:
        for r in self.records:
            if _key(r) == key:
                return r
        return None

    def upsert(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Fusionne sans écraser. Retourne (record, created)."""
        key = _key(record)
        existing = self._find(key)
        if existing is None:
            record.setdefault("id", _slug(record.get("company", key)))
            record.setdefault("created_at", _now())
            record["updated_at"] = _now()
            self.records.append(record)
            return record, True
        # Fusion : combler uniquement les champs vides, ne jamais écraser.
        for field, value in record.items():
            if field in ("evidence", "created_at", "id"):
                continue
            if not existing.get(field) and value:
                existing[field] = value
        # Preuves : ajouter les nouvelles sans doublon.
        seen = {(e.get("source_url"), e.get("quote")) for e in existing.get("evidence", [])}
        for ev in record.get("evidence", []):
            if (ev.get("source_url"), ev.get("quote")) not in seen:
                existing.setdefault("evidence", []).append(ev)
        existing["updated_at"] = _now()
        return existing, False

    def import_prospect(self, prospect: Prospect, result: QualificationResult | None = None) -> tuple[dict[str, Any], bool]:
        result = result or qualify(prospect)
        record = {
            "company": prospect.company,
            "website": prospect.website,
            "domain": prospect.domain,
            "sector": prospect.sector,
            "city": prospect.city,
            "department": prospect.department,
            "contact_name": prospect.contact_name,
            "contact_role": prospect.contact_role,
            "email": prospect.contact_email,
            "phone": prospect.phone,
            "source": prospect.source,
            "evidence": [
                {"kind": e.kind, "source_url": e.source_url, "quote": e.quote,
                 "observed_at": e.observed_at, "detail": e.detail}
                for e in prospect.evidences
            ],
            "publication_date": prospect.publication_date,
            "need": prospect.primary_need,
            "needs": prospect.needs,
            "recommended_service": prospect.recommended_service or prospect.primary_need,
            "score": result.score,
            "tier": result.tier,
            "status_crm": result.status,
            "justification": " ; ".join(result.reasons),
            "process_hint": prospect.process_hint,
            "demo_detail": prospect.demo_detail,
            "custom_hook": prospect.custom_hook,
            "custom_subject": prospect.custom_subject,
            "notes": prospect.notes,
            "status": "nouveau",
        }
        return self.upsert(record)

    def mark_history_contacted(self) -> int:
        """Marque les entreprises de l'historique d'envois comme contactées (sans écraser)."""
        count = 0
        if not HISTORY_DIR.exists():
            return 0
        for path in sorted(HISTORY_DIR.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            for entry in raw.get("sent", []):
                record = {
                    "company": entry.get("company", ""),
                    "domain": entry.get("domain", ""),
                    "email": entry.get("email", ""),
                    "status": "contacté",
                    "source": "historique Gmail",
                    "evidence": [],
                }
                rec, created = self.upsert(record)
                rec["status"] = "contacté"
                count += 1
        return count

    def stats(self) -> dict[str, Any]:
        total = len(self.records)
        by_tier: dict[str, int] = {}
        with_email = 0
        expressed = 0
        contacted = 0
        for r in self.records:
            tier = r.get("tier", "a_approfondir")
            by_tier[tier] = by_tier.get(tier, 0) + 1
            if r.get("email"):
                with_email += 1
            if any(e.get("kind") == "public_need" for e in r.get("evidence", [])):
                expressed += 1
            if r.get("status") == "contacté":
                contacted += 1
        return {
            "total": total,
            "by_tier": by_tier,
            "with_email": with_email,
            "expressed_needs": expressed,
            "contacted": contacted,
        }
