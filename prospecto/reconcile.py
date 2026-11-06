"""Réconciliation des envois réalisés hors agent (lot 6).

Constat du 6 novembre 2026 : les 15 brouillons des lots 4 et 5 ont été envoyés
manuellement depuis Gmail le 5 novembre à 14:34. Le CRM et la file les croyaient
encore « brouillon_créé » / « pending », ce qui faussait toutes les métriques.

Ce module rapproche l'état local de la réalité observée dans Gmail, **sans jamais
supprimer ni écraser l'historique** :

* la file passe de ``pending`` à ``sent`` avec la preuve (identifiant du message) ;
* le journal d'envoi reçoit une entrée horodatée marquée « observé dans Gmail » ;
* le CRM passe à ``contacté`` et reçoit la date d'envoi réelle ;
* chaque transition est tracée dans l'historique de l'élément.

Aucun envoi n'est effectué ici : le module ne fait que constater et enregistrer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config

RECONCILE_PATH = config.DATA_DIR / "history" / "reconciliations.json"

OBSERVED_SOURCE = "gmail_manual_observed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ReconcileResult:
    matched: int = 0
    already_sent: int = 0
    unmatched: list[str] = field(default_factory=list)
    updated_companies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def reconcile_sent(observed: Iterable[dict[str, Any]], crm: Any, queue: Any,
                   send_log: Any = None, observed_at: str = "") -> ReconcileResult:
    """Aligne la file, le CRM et le journal sur les envois constatés dans Gmail.

    ``observed`` est une liste de dicts ``{to, subject, gmail_message_id,
    gmail_thread_id, sent_at}`` relevés dans le dossier « Envoyés ».
    Le rapprochement se fait par identifiant de message, puis par destinataire
    et objet — jamais par approximation.
    """
    result = ReconcileResult()
    observed = list(observed)
    stamp = observed_at or _now()

    for obs in observed:
        to = (obs.get("to") or "").strip().lower()
        subject = (obs.get("subject") or "").strip()
        msg_id = obs.get("gmail_message_id", "")
        item = None
        for candidate in getattr(queue, "items", []):
            if msg_id and getattr(candidate, "gmail_message_id", "") == msg_id:
                item = candidate
                break
        if item is None:
            for candidate in getattr(queue, "items", []):
                if (getattr(candidate, "to", "") or "").strip().lower() == to and \
                        (getattr(candidate, "subject", "") or "").strip() == subject:
                    item = candidate
                    break
        if item is None:
            result.unmatched.append(f"{to} — {subject}")
            continue

        if item.status == "sent":
            result.already_sent += 1
        else:
            previous = item.status
            item.status = "sent"
            item.updated_at = stamp
            item.history.append({
                "at": stamp, "action": "reconciled_sent",
                "reason": f"envoi constaté dans Gmail (statut précédent : {previous})",
                "source": OBSERVED_SOURCE, "gmail_message_id": msg_id,
            })
            result.matched += 1

        if msg_id:
            item.gmail_message_id = msg_id
        if obs.get("gmail_thread_id"):
            item.gmail_thread_id = obs["gmail_thread_id"]

        record = None
        for rec in crm.records:
            if (rec.get("email") or "").strip().lower() == to:
                record = rec
                break
        if record is not None:
            # Ne jamais rétrograder un statut plus avancé (réponse, opposition, rebond).
            if record.get("status") not in ("opposition", "rebond", "refus", "réponse_recue",
                                            "réponse_positive", "demande_info", "demande_rdv",
                                            "auto_reply"):
                record["status"] = "contacté"
            record["email_status"] = record.get("email_status") or "envoyé"
            if record.get("email_status") in ("brouillon_créé", "en_attente_validation", "non_contacté"):
                record["email_status"] = "envoyé"
            record["sent_at"] = record.get("sent_at") or obs.get("sent_at") or stamp
            record["send_source"] = OBSERVED_SOURCE
            if msg_id:
                record["gmail_message_id"] = msg_id
            if obs.get("gmail_thread_id"):
                record["gmail_thread_id"] = obs["gmail_thread_id"]
            if not record.get("next_action") or "brouillon" in (record.get("next_action") or "").lower():
                record["next_action"] = "Surveiller réponse, accusé ou rebond dans la boîte de réception"
            result.updated_companies.append(record.get("company", to))

        if send_log is not None:
            known = any((e.get("to") or "").lower() == to and
                        (e.get("subject") or "") == subject for e in send_log.entries)
            if not known:
                send_log.record(to=to, subject=subject, company=(record or {}).get("company", ""),
                                campaign=getattr(item, "campaign", ""), status="sent",
                                gmail_message_id=msg_id, source=OBSERVED_SOURCE,
                                at=obs.get("sent_at") or stamp)

    queue.save()
    crm.save()
    if send_log is not None:
        send_log.save()
    _append_history(result, stamp)
    return result


def _append_history(result: ReconcileResult, stamp: str, path: Path | None = None) -> None:
    path = path or RECONCILE_PATH
    entries: list[dict[str, Any]] = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding="utf-8")).get("reconciliations", [])
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append({"at": stamp, **result.to_dict()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"updated_at": stamp, "count": len(entries), "reconciliations": entries},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
