"""File de validation humaine des emails.

États : pending → approved / rejected → sent.
Aucun envoi automatique : l'export Gmail crée des BROUILLONS, et le passage
à « sent » n'intervient qu'après confirmation d'envoi réel.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import QUEUE_PATH
from .models import GeneratedEmail

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
SENT = "sent"
STATUSES = (PENDING, APPROVED, REJECTED, SENT)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class QueueItem:
    id: str
    campaign: str
    to: str
    company: str
    subject: str
    body: str
    need: str
    evidence_sources: list[str]
    status: str = PENDING
    created_at: str = ""
    updated_at: str = ""
    gmail_draft_id: str | None = None
    gmail_message_id: str | None = None
    decision_reason: str = ""
    history: list[dict[str, str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.history is None:
            self.history = []
        if not self.created_at:
            self.created_at = _now()
        self.updated_at = self.updated_at or self.created_at

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "QueueItem":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in known})


class ValidationQueue:
    """File persistée en JSON (versionnable, sans secret)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or QUEUE_PATH
        self.items: list[QueueItem] = []
        self.load()

    # -- persistance ---------------------------------------------------------
    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.items = [QueueItem.from_dict(i) for i in raw.get("items", [])]
        else:
            self.items = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "items": [i.to_dict() for i in self.items]}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # -- opérations ----------------------------------------------------------
    def add(self, email: GeneratedEmail, campaign: str) -> QueueItem:
        # Dédoublonnage : un seul email en attente par destinataire + campagne.
        for item in self.items:
            if item.to.lower() == email.to.lower() and item.campaign == campaign and item.status != REJECTED:
                raise ValueError(f"déjà en file : {email.to} ({campaign})")
        seq = sum(1 for i in self.items if i.campaign == campaign) + 1
        item = QueueItem(
            id=f"{campaign}-{seq:03d}",
            campaign=campaign,
            to=email.to,
            company=email.company,
            subject=email.subject,
            body=email.body,
            need=email.need,
            evidence_sources=email.evidence_sources,
        )
        item.history.append({"at": _now(), "action": "created", "status": PENDING})
        self.items.append(item)
        self.save()
        return item

    def get(self, item_id: str) -> QueueItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(f"élément introuvable : {item_id}")

    def _transition(self, item_id: str, status: str, reason: str = "") -> QueueItem:
        item = self.get(item_id)
        item.status = status
        item.updated_at = _now()
        if reason:
            item.decision_reason = reason
        item.history.append({"at": _now(), "action": status, "reason": reason})
        self.save()
        return item

    def approve(self, item_id: str) -> QueueItem:
        item = self.get(item_id)
        if item.status not in (PENDING, REJECTED):
            raise ValueError(f"approbation impossible depuis l'état {item.status}")
        return self._transition(item_id, APPROVED)

    def reject(self, item_id: str, reason: str = "") -> QueueItem:
        item = self.get(item_id)
        if item.status == SENT:
            raise ValueError("impossible de rejeter un email déjà envoyé")
        return self._transition(item_id, REJECTED, reason)

    def attach_draft(self, item_id: str, draft_id: str) -> QueueItem:
        item = self.get(item_id)
        item.gmail_draft_id = draft_id
        item.updated_at = _now()
        item.history.append({"at": _now(), "action": "gmail_draft_created", "draft_id": draft_id})
        self.save()
        return item

    def mark_sent(self, item_id: str, gmail_message_id: str = "") -> QueueItem:
        item = self.get(item_id)
        if item.status != APPROVED:
            raise ValueError("seul un email approuvé peut être marqué envoyé")
        item.gmail_message_id = gmail_message_id or item.gmail_message_id
        return self._transition(item_id, SENT)

    def reconcile_external_send(
        self,
        item_id: str,
        gmail_sent_message_id: str,
        sent_at: str = "",
        source: str = "",
    ) -> QueueItem:
        """Acter un envoi effectué HORS de l'agent, constaté dans Gmail.

        `mark_sent` exige l'état « approuvé » : c'est le garde-fou du circuit
        normal (validation humaine puis envoi par l'agent). Un brouillon déposé
        puis envoyé à la main depuis Gmail n'a jamais traversé ce circuit ;
        l'exiger ici obligerait à fabriquer une approbation qui n'a pas eu lieu.

        Cette méthode n'autorise rien : elle **constate** un fait déjà observé.
        L'identifiant du brouillon est conservé dans l'historique, car Gmail
        attribue un nouvel identifiant au message envoyé tout en gardant le
        même fil. Aucun envoi n'est déclenché.
        """
        item = self.get(item_id)
        if item.status == SENT:
            raise ValueError("élément déjà marqué envoyé : rapprochement répété")
        if not gmail_sent_message_id:
            raise ValueError("un identifiant de message envoyé est requis comme preuve")
        previous_status = item.status
        previous_draft_message_id = item.gmail_message_id
        item.gmail_message_id = gmail_sent_message_id
        item.status = SENT
        item.updated_at = _now()
        item.decision_reason = "envoi constaté hors agent, réconcilié depuis Gmail"
        item.history.append({
            "at": _now(), "action": "external_send_reconciled",
            "status_before": previous_status, "status_after": SENT,
            "gmail_sent_message_id": gmail_sent_message_id,
            "gmail_draft_message_id": previous_draft_message_id,
            "sent_at_observed": sent_at, "source": source,
            "reason": ("brouillon envoyé depuis l'interface Gmail ; l'agent n'a "
                       "effectué aucun envoi (enabled=false, dry_run=true)"),
        })
        self.save()
        return item

    def list(self, status: str | None = None, campaign: str | None = None) -> list[QueueItem]:
        result = self.items
        if status:
            result = [i for i in result if i.status == status]
        if campaign:
            result = [i for i in result if i.campaign == campaign]
        return result

    def counts(self) -> dict[str, int]:
        """Compte tous les statuts présents, pas seulement les quatre d'origine.

        Les statuts « draft », « obsolete » et « suspended » ont été introduits
        par les lots 6 à 9. En ne renvoyant que STATUSES, ce compteur rendait
        invisibles les brouillons Gmail et la file neutralisée.
        """
        seen = list(STATUSES) + sorted({i.status for i in self.items} - set(STATUSES))
        counts = {s: sum(1 for i in self.items if i.status == s) for s in seen}
        # Total explicite : la somme des statuts doit valoir la taille de la file.
        counts["total"] = len(self.items)
        counts["ouverts"] = sum(counts.get(s, 0) for s in (PENDING, APPROVED, "draft"))
        return counts
