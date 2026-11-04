"""Liste de suppression centralisée (v4) — opposition à la prospection.

Aucun message ne doit être envoyé à une adresse (ou un domaine) présent ici.
Alimentée par : opt-out explicite, refus, rebond dur, plainte, ou ajout manuel.
Vérifiée systématiquement avant tout envoi (sender) et à la qualification.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _domain_of(email: str) -> str:
    return email.split("@", 1)[1].lower().strip() if "@" in email else ""


class SuppressionList:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.SUPPRESSION_PATH
        self.entries: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self.entries = raw.get("entries", [])
            except (json.JSONDecodeError, OSError):
                self.entries = []
        else:
            self.entries = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "count": len(self.entries), "entries": self.entries}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def add(self, email: str = "", domain: str = "", reason: str = "opt-out", source: str = "") -> bool:
        email = email.lower().strip()
        domain = domain.lower().strip() or (_domain_of(email) if email else "")
        if not email and not domain:
            return False
        for e in self.entries:
            if email and e.get("email") == email:
                return False
            if domain and not email and e.get("domain") == domain and not e.get("email"):
                return False
        self.entries.append({
            "email": email, "domain": domain, "reason": reason,
            "source": source, "added_at": _now(),
        })
        self.save()
        return True

    def is_suppressed(self, email: str) -> bool:
        email = (email or "").lower().strip()
        if not email:
            return False
        dom = _domain_of(email)
        for e in self.entries:
            if e.get("email") and e["email"] == email:
                return True
            # Suppression par domaine uniquement si explicitement domain-wide.
            if e.get("domain_wide") and e.get("domain") and e["domain"] == dom:
                return True
        return False

    def remove(self, email: str) -> bool:
        email = email.lower().strip()
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.get("email") != email]
        if len(self.entries) != before:
            self.save()
            return True
        return False

    def count(self) -> int:
        return len(self.entries)
