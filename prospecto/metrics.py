"""Métriques agrégées v4 pour le tableau de bord.

Croise CRM + file de validation + journal d'envoi + réponses pour produire les
indicateurs demandés (volume, coordonnées, envois, réponses, performance des
variantes et des exemples commerciaux).
"""
from __future__ import annotations

from typing import Any

from .crm import CRM
from .queue import ValidationQueue
from .sender import SendLog
from .suppression import SuppressionList
from . import config
import json


def _load_replies() -> list[dict]:
    if config.REPLIES_PATH.exists():
        try:
            return json.loads(config.REPLIES_PATH.read_text(encoding="utf-8")).get("replies", [])
        except (json.JSONDecodeError, OSError):
            return []
    return []


def compute_metrics() -> dict[str, Any]:
    crm = CRM()
    queue = ValidationQueue()
    log = SendLog()
    suppression = SuppressionList()
    replies = _load_replies()

    records = crm.records
    active = [r for r in records if r.get("status") != "contacté"]

    # Coordonnées
    emails_by_verif: dict[str, int] = {}
    phones = 0
    for r in records:
        if r.get("email"):
            v = r.get("email_verification", "public_unverified")
            emails_by_verif[v] = emails_by_verif.get(v, 0) + 1
        if r.get("phone"):
            phones += 1

    # Envois (journal)
    sent = [e for e in log.entries if e.get("status") in ("sent", "delivered")]
    delivered = [e for e in log.entries if e.get("status") == "delivered"]
    bounced = [e for e in log.entries if e.get("status") == "bounced"]
    complained = [e for e in log.entries if e.get("status") == "complained"]
    dry = [e for e in log.entries if e.get("status") == "dry_run"]

    # Réponses
    intents: dict[str, int] = {}
    for rp in replies:
        it = rp.get("intent", "inconnu")
        intents[it] = intents.get(it, 0) + 1
    demos_requested = intents.get("demande_info", 0) + intents.get("demande_rdv", 0) + intents.get("positive", 0)

    # Performance par variante / référence (depuis le journal + file).
    by_variant: dict[str, dict[str, int]] = {}
    by_reference: dict[str, dict[str, int]] = {}
    reply_by_email = {rp.get("from", "").lower(): rp for rp in replies}
    for e in log.entries:
        v = e.get("variant") or "inconnu"
        ref = e.get("reference_id") or "aucune"
        for key, bucket in ((v, by_variant), (ref, by_reference)):
            b = bucket.setdefault(key, {"sent": 0, "replies": 0, "positive": 0})
            if e.get("status") in ("sent", "delivered"):
                b["sent"] += 1
                rp = reply_by_email.get(e.get("to", "").lower())
                if rp:
                    b["replies"] += 1
                    if rp.get("intent") in ("positive", "demande_rdv", "demande_info"):
                        b["positive"] += 1

    return {
        "crm": {
            "total": len(records),
            "active": len(active),
            "qualified": sum(1 for r in active if r.get("tier") in ("haute", "moyenne")),
            "by_tier": crm.stats()["by_tier"],
            "expressed_needs": sum(1 for r in records if any(ev.get("kind") == "public_need" for ev in r.get("evidence", []))),
            "probable": sum(1 for r in active if r.get("tier") == "moyenne"),
            "contacted": sum(1 for r in records if r.get("status") == "contacté"),
        },
        "coordinates": {
            "emails_total": sum(emails_by_verif.values()),
            "emails_by_verification": emails_by_verif,
            "phones": phones,
        },
        "queue": queue.counts(),
        "sending": {
            "sent": len(sent),
            "delivered": len(delivered),
            "bounced": len(bounced),
            "complained": len(complained),
            "dry_run": len(dry),
            "rates": log.rates(),
            "sent_today": log.sent_today(),
        },
        "replies": {
            "total": len(replies),
            "by_intent": intents,
            "positive": intents.get("positive", 0),
            "demos_requested": demos_requested,
            "opt_out": intents.get("opposition", 0),
        },
        "suppression": {"count": suppression.count()},
        "performance": {"by_variant": by_variant, "by_reference": by_reference},
    }
