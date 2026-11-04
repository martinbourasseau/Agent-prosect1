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


def _load_audit() -> list[dict]:
    from .inbox_audit import AUDIT_PATH

    if AUDIT_PATH.exists():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8")).get("findings", [])
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
        "deliverability": _deliverability(log.entries, records, _load_audit()),
        "by_lot": _by_lot(records, log.entries, queue),
        "scoring": _scoring_overview(records),
    }


def _deliverability(entries: list[dict], records: list[dict], audit: list[dict]) -> dict[str, Any]:
    """Distinguer « envoyé » de « délivré » : un message envoyé peut rebondir.

    La présence dans le dossier « Envoyés » ne prouve pas la remise. Seuls un
    accusé de réception, une réponse humaine ou l'absence de rebond après
    vérification de la boîte le suggèrent — et l'absence de rebond n'est pas une
    preuve de délivrance.
    """
    sent = [e for e in entries if e.get("status") in ("sent", "delivered", "bounced", "complained")]
    bounced_entries = [e for e in entries if e.get("status") == "bounced"]
    bounces = [f for f in audit if f.get("intent") == "rebond"]
    autos = [f for f in audit if f.get("intent") == "auto_reply"]
    humans = [f for f in audit if f.get("intent") == "reponse_humaine"]
    opt_outs = [f for f in audit if f.get("intent") == "opposition"]
    hard = [f for f in bounces if f.get("severity") == "dur"]
    confirmed = {f.get("company") for f in autos + humans if f.get("company")}
    bounced_companies = {f.get("company") for f in bounces if f.get("company")}
    dns_blocking = [r for r in records if r.get("email_dns_status") in ("nxdomain", "no_mx", "syntaxe_invalide")]
    total_sent = len(sent)
    return {
        "sent": total_sent,
        "hard_bounces": len(hard),
        "soft_bounces": len(bounces) - len(hard),
        "auto_replies": len(autos),
        "human_replies": len(humans),
        "opt_outs": len(opt_outs),
        "bounce_rate": round(len(bounces) / total_sent * 100, 1) if total_sent else 0.0,
        "human_reply_rate": round(len(humans) / total_sent * 100, 1) if total_sent else 0.0,
        "delivery_confirmed": len(confirmed),
        "delivery_unconfirmed": max(0, total_sent - len(confirmed) - len(bounced_companies)),
        "bounced_companies": sorted(c for c in bounced_companies if c),
        "dns_blocking_addresses": [
            {"company": r.get("company", ""), "email": r.get("email", ""),
             "status": r.get("email_dns_status", "")} for r in dns_blocking
        ],
        "note": ("La présence dans « Envoyés » ne prouve pas la remise. Seuls les accusés et les "
                 "réponses humaines confirment une délivrance ; l'absence de rebond ne la garantit pas."),
    }


def _by_lot(records: list[dict], entries: list[dict], queue: Any) -> list[dict[str, Any]]:
    """Ventilation par lot : découverte, qualification, brouillons, envois, rebonds."""
    lots: dict[str, dict[str, Any]] = {}
    for rec in records:
        lot = rec.get("lot") or "antérieur au suivi par lot"
        b = lots.setdefault(lot, {"lot": lot, "prospects": 0, "haute": 0, "moyenne": 0,
                                  "a_approfondir": 0, "emails_verified": 0, "brouillons": 0,
                                  "envoyés": 0, "rebonds": 0, "réponses": 0})
        b["prospects"] += 1
        tier = rec.get("tier") or rec.get("commercial_priority") or ""
        if tier in b:
            b[tier] += 1
        if rec.get("email_verification") == "verified":
            b["emails_verified"] += 1
        if rec.get("status") == "brouillon_créé":
            b["brouillons"] += 1
        if rec.get("status") == "contacté":
            b["envoyés"] += 1
        if rec.get("status") == "rebond":
            b["rebonds"] += 1
        if rec.get("reply_received"):
            b["réponses"] += 1
    return sorted(lots.values(), key=lambda b: b["lot"])


def _scoring_overview(records: list[dict]) -> dict[str, Any]:
    """Répartition des trois scores indépendants sur les fiches qui les portent."""
    axes = ("site_web", "refonte", "ia_automatisation")
    out: dict[str, Any] = {"scored": 0, "axes": {}}
    for axis in axes:
        buckets = {"fort": 0, "moyen": 0, "faible": 0}
        for rec in records:
            data = (rec.get("scores") or {}).get(axis)
            if data:
                buckets[data.get("level", "faible")] = buckets.get(data.get("level", "faible"), 0) + 1
        out["axes"][axis] = buckets
    out["scored"] = sum(1 for r in records if r.get("scores"))
    priorities: dict[str, int] = {}
    for rec in records:
        pr = rec.get("commercial_priority")
        if pr:
            priorities[pr] = priorities.get(pr, 0) + 1
    out["commercial_priority"] = priorities
    return out
