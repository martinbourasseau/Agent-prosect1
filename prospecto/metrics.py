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


def merge_inbound(replies: list[dict], audit: list[dict]) -> list[dict]:
    """Fusionne journal des réponses et audit de boîte, sans double compte.

    Un même message peut être présent dans les deux sources : l'identifiant
    Gmail sert de clé, sinon le couple (expéditeur, objet).
    """
    out: list[dict] = []
    seen: set[str] = set()
    for entry in list(replies) + list(audit):
        key = entry.get("message_id") or entry.get("id") or (
            f"{(entry.get('from') or entry.get('from_email') or '').lower()}|{entry.get('subject', '')}")
        if key in seen:
            continue
        seen.add(key)
        out.append(entry)
    return out


def _load_audit() -> list[dict]:
    from .inbox_audit import AUDIT_PATH

    if AUDIT_PATH.exists():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8")).get("findings", [])
        except (json.JSONDecodeError, OSError):
            return []
    return []


SUSPENDED_STATUSES = {"suspendu", "suspended"}

# Intentes produits par une personne, par opposition aux accusés automatiques
# et aux rebonds émis par un serveur de messagerie.
HUMAN_INTENTS = {"reponse_humaine", "opposition", "demande_info", "demande_rdv",
                 "positive", "negative", "question", "rdv"}


def _is_suspended(record: dict) -> bool:
    """Vrai si la fiche est explicitement suspendue (aucun envoi possible)."""
    if record.get("suspended_at"):
        return True
    return any(str(record.get(k) or "").strip().lower() in SUSPENDED_STATUSES
               for k in ("status", "status_crm", "email_status", "contactability"))


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

    # Réponses — lot 6 : l'audit de boîte est la source de vérité quand le
    # journal historique des réponses n'existe pas. Sans cette fusion, une
    # opposition ou un accusé constaté dans Gmail restait compté à zéro ici
    # alors qu'il apparaissait déjà dans « deliverability ».
    audit_findings = _load_audit()
    inbound = merge_inbound(replies, audit_findings)
    intents: dict[str, int] = {}
    for rp in inbound:
        it = rp.get("intent", "inconnu")
        intents[it] = intents.get(it, 0) + 1
    demos_requested = intents.get("demande_info", 0) + intents.get("demande_rdv", 0) + intents.get("positive", 0)

    # Performance par variante / référence (depuis le journal + file).
    by_variant: dict[str, dict[str, int]] = {}
    by_reference: dict[str, dict[str, int]] = {}
    reply_by_email = {rp.get("from", "").lower(): rp for rp in inbound}
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

    metrics = {
        "crm": {
            "total": len(records),
            "active": len(active),
            "qualified": sum(1 for r in active if r.get("tier") in ("haute", "moyenne")),
            "by_tier": crm.stats()["by_tier"],
            "expressed_needs": sum(1 for r in records if any(ev.get("kind") == "public_need" for ev in r.get("evidence", []))),
            "probable": sum(1 for r in active if r.get("tier") == "moyenne"),
            "contacted": sum(1 for r in records if r.get("status") == "contacté"),
            # Lot 7 : une fiche suspendue (adresse non confirmée) reste au CRM
            # avec son brouillon, mais n'est pas envoyable. On l'expose pour que
            # le tableau de bord ne la confonde pas avec un brouillon prêt.
            "suspended": sum(1 for r in records if _is_suspended(r)),
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
            "total": len(inbound),
            "by_intent": intents,
            "positive": intents.get("positive", 0),
            "demos_requested": demos_requested,
            "opt_out": intents.get("opposition", 0),
            "sources": {"journal_reponses": len(replies), "audit_boite": len(audit_findings)},
        },
        "suppression": {"count": suppression.count()},
        "performance": {"by_variant": by_variant, "by_reference": by_reference},
        "deliverability": _deliverability(log.entries, records, audit_findings),
        "by_lot": _by_lot(records, log.entries, queue),
        "scoring": _scoring_overview(records),
    }
    metrics["pipeline"] = pipeline_categories(metrics, queue.items)
    metrics["portefeuille"] = portfolio_categories(records)
    metrics["exploration"] = _exploration_overview()
    metrics["qualification"] = _qualification_overview(records)
    metrics["recherche"] = _search_overview(records)
    metrics["revue_portefeuille"] = _review_overview()
    return metrics


def _qualification_overview(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Section K — ce qui est réellement vérifié, et ce qui bloque."""
    from .dossier import audit_portfolio
    audit = audit_portfolio(records)
    audit.pop("dossiers", None)          # la vue n'a pas besoin des 83 dossiers
    return audit


def _search_overview(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Section K — sources les plus performantes et couverture nationale."""
    from .planner import SearchPlanner, SearchHistory
    from .sources import ExplorationLedger
    try:
        planner = SearchPlanner(records, ExplorationLedger(), SearchHistory())
    except (OSError, ValueError):
        return {"note": "registre ou historique indisponible"}
    ov = planner.overview()
    ov["note"] = ("Rendement = qualifiés / examinés, lissé par un prior de 8 "
                  "observations à 15 %. Une source jamais essayée reste "
                  "préférée à une source mauvaise prouvée.")
    return ov


def _review_overview() -> dict[str, Any]:
    """Section K — faux positifs, faux négatifs, décisions d'approfondissement.

    Chiffres lus dans les archives réelles, jamais recalculés à la volée : la
    revue est un constat daté, pas une estimation permanente.
    """
    out: dict[str, Any] = {}
    audit_path = config.DATA_DIR / "history" / "audit-portefeuille-phase10.json"
    if audit_path.exists():
        raw = json.loads(audit_path.read_text(encoding="utf-8"))
        findings = raw.get("findings") or raw.get("constats") or []
        tags: dict[str, int] = {}
        for f in findings:
            for t in (f.get("tags") or []):
                tags[t] = tags.get(t, 0) + 1
        out["audit_phase10"] = {"constats": len(findings), "par_tag": tags}
    deep = config.DATA_DIR / "history" / "approfondissement-lot9-2026-11-07.json"
    if deep.exists():
        raw = json.loads(deep.read_text(encoding="utf-8"))
        out["approfondissement_lot9"] = {
            "total": raw.get("total", 0), "reexaminees": raw.get("reviewed", 0),
            "decisions": raw.get("decisions", {})}
    lot10 = config.DATA_DIR / "history" / "lot10-exploration-2026-11-07.json"
    if lot10.exists():
        raw = json.loads(lot10.read_text(encoding="utf-8"))
        out["lot10"] = {"examinees": raw.get("examined", 0),
                        "objectif": 60, "objectif_atteint": raw.get("objective_reached", False),
                        "decisions": raw.get("decisions", {}),
                        "nouveaux_departements": raw.get("new_departments", [])}
    gmail = config.DATA_DIR / "history" / "audit-gmail-phase10.json"
    if gmail.exists():
        raw = json.loads(gmail.read_text(encoding="utf-8"))
        out["gmail_phase10"] = raw.get("classification", {})
    return out


# Ordre de priorité de la partition : une fiche ne tombe que dans une case.
# Une entreprise en opposition reste « opposition » même si elle a été
# contactée ; un rebond reste « rebond ». Sinon les catégories se recouvraient
# et le total dépassait la taille du CRM.
_PORTFOLIO_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("oppositions", ("opposition",)),
    ("suspendus", ("suspendu",)),
    ("rebonds", ("rebond", "non_delivrable")),
    ("contactes", ("contacté", "auto_reply", "réponse_humaine")),
    ("brouillons_en_attente", ("brouillon_en_attente", "brouillon_créé", "email_préparé")),
    ("a_investiguer", ("a_approfondir", "non_contactable")),
    ("decouverts", ("nouveau", "decouvert", "")),
)


def portfolio_categories(records: list[dict]) -> dict[str, Any]:
    """Partition exclusive du CRM par étape de cycle de vie.

    « Qualifiés » est une lecture transversale (priorité commerciale) et non
    une étape : elle est publiée à part, avec la mention qu'elle ne s'ajoute
    pas, pour ne pas induire un double comptage.
    """
    out = {key: 0 for key, _ in _PORTFOLIO_RULES}
    autres: dict[str, int] = {}
    for r in records:
        status = (r.get("status") or "").strip()
        for key, values in _PORTFOLIO_RULES:
            if status in values:
                out[key] += 1
                break
        else:
            autres[status] = autres.get(status, 0) + 1
            out.setdefault("autres", 0)
            out["autres"] += 1
    priorities: dict[str, int] = {}
    for r in records:
        p = r.get("commercial_priority") or "(non scorée)"
        priorities[p] = priorities.get(p, 0) + 1
    out["total"] = len(records)
    out["controle_exclusif"] = (
        sum(v for k, v in out.items()
            if k not in ("total", "controle_exclusif", "qualifies", "autres_details"))
        == len(records))
    out["qualifies"] = priorities.get("haute", 0) + priorities.get("moyenne", 0)
    out["priorities"] = priorities
    out["autres_details"] = autres
    out["definitions"] = {
        "decouverts": "fiches créées, aucun message préparé",
        "a_investiguer": "opportunité non établie ou entreprise non contactable : à approfondir",
        "brouillons_en_attente": "message prêt, en attente de validation humaine ; rien n'est parti",
        "contactes": "message sorti vers l'entreprise, délivrance non présumée",
        "qualifies": "lecture transversale (priorité haute ou moyenne) : ne s'ajoute pas aux étapes",
    }
    return out


def _exploration_overview() -> dict[str, Any]:
    """Ce qui a été examiné puis écarté : le travail invisible des lots."""
    from .sources import ExplorationLedger
    try:
        ledger = ExplorationLedger()
    except (OSError, ValueError):
        return {"examined": 0, "by_decision": {}, "note": "journal indisponible"}
    stats = ledger.stats()
    stats["note"] = ("Structures examinées pendant la recherche, y compris écartées. "
                     "Une structure écartée n'est pas une fiche et ne sera pas "
                     "réexaminée au prochain lot.")
    return stats


def pipeline_categories(metrics: dict[str, Any], queue_items: list[Any]) -> dict[str, Any]:
    """Les neuf catégories demandées, sans jamais assimiler envoyé et délivré.

    Les catégories de délivrance sont exclusives et se somment au nombre de
    messages sortis. Les catégories de réponse se recouvrent volontairement
    (une opposition est aussi une réponse humaine) et ne se somment pas.
    """
    d = metrics.get("deliverability", {})
    out = int(d.get("sent", 0))
    confirmed = int(d.get("delivery_confirmed", 0))
    bounces = int(d.get("hard_bounces", 0)) + int(d.get("soft_bounces", 0))
    challenges = int(d.get("delivery_challenges", 0))
    # « draft » et « pending » désignent tous deux un message non envoyé : les
    # ignorer séparément sous-comptait les brouillons du lot 7.
    open_items = [i for i in queue_items
                  if getattr(i, "status", "") in ("pending", "draft", "approved")]
    drafts = [i for i in open_items if getattr(i, "gmail_draft_id", None)]
    waiting = [i for i in open_items if not getattr(i, "gmail_draft_id", None)]
    return {
        "envoyes": out,
        "delivres_confirmes": confirmed,
        "delivrance_non_confirmee": max(0, out - confirmed - bounces - challenges),
        "rebonds": bounces,
        "challenges_delivrance": challenges,
        "reponses_humaines": int(d.get("human_replies", 0)),
        "reponses_automatiques": int(d.get("auto_replies", 0)),
        "oppositions": int(d.get("opt_outs", 0)),
        "brouillons": len(drafts),
        "en_attente": len(waiting),
        "suspendus": sum(1 for i in queue_items if getattr(i, "status", "") == "suspended"),
        "obsoletes": sum(1 for i in queue_items if getattr(i, "status", "") == "obsolete"),
        "controle_exclusif": confirmed + max(0, out - confirmed - bounces - challenges)
                             + bounces + challenges == out,
        "definitions": {
            "envoyes": "messages sortis, rebonds compris : la présence dans « Envoyés » ne prouve pas la remise",
            "delivres_confirmes": "accusé de réception ou réponse humaine rattachant le message à une entreprise",
            "delivrance_non_confirmee": "ni preuve de remise, ni rebond, ni challenge : statut inconnu, pas « délivré »",
            "challenges_delivrance": "message retenu par un système de vérification d'expéditeur : remise non acquise",
            "brouillons": "éléments en file porteurs d'un brouillon Gmail, en attente de validation",
            "en_attente": "éléments en file sans brouillon Gmail (adresse absente, suspendus, à qualifier)",
        },
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
    challenges = [f for f in audit if f.get("intent") == "challenge_delivrance"]
    # Une opposition est écrite par un humain : la compter seulement en
    # « oppositions » affichait 0 réponse humaine alors qu'un dirigeant avait
    # répondu. Les deux compteurs se recouvrent volontairement (mêmes messages,
    # deux lectures : qui a répondu / ce qu'il a demandé).
    humans = [f for f in audit if f.get("intent") in HUMAN_INTENTS]
    opt_outs = [f for f in audit if f.get("intent") == "opposition"]
    hard = [f for f in bounces if f.get("severity") == "dur"]
    # Un challenge ne prouve PAS la délivrance : il signale au contraire que le
    # message attend une validation. Il ne doit pas entrer dans « confirmed ».
    confirmed = {f.get("company") for f in autos + humans if f.get("company")}
    bounced_companies = {f.get("company") for f in bounces if f.get("company")}
    dns_blocking = [r for r in records if r.get("email_dns_status") in ("nxdomain", "no_mx", "syntaxe_invalide")]
    total_sent = len(sent)
    return {
        "sent": total_sent,
        "hard_bounces": len(hard),
        "soft_bounces": len(bounces) - len(hard),
        "auto_replies": len(autos),
        "delivery_challenges": len(challenges),
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
