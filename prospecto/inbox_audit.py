"""Audit fiable de la boîte de réception (lot 5).

Correctif d'un défaut constaté : les lots 1 à 4 concluaient « 0 réponse, 0 rebond »
parce que la recherche Gmail ne portait que sur ``from:<adresse exacte du
prospect>``. Or :

* un rebond arrive de ``mailer-daemon@googlemail.com``, **jamais** du prospect ;
* une réponse peut arriver d'une autre adresse du même domaine
  (``resa@bsp-auto.com`` alors que le CRM connaît ``support@bsp-auto.com``).

Ce module :
1. détecte les rebonds et **extrait le destinataire réel** dans le corps du
   message (en-têtes DSN ``Final-Recipient`` ou formulation Gmail française) ;
2. classe rebond dur / rebond mou / accusé automatique / réponse humaine ;
3. rattache l'événement à la bonne fiche par email, puis domaine, puis
   ``thread_id`` — et n'attribue **jamais** un rebond à l'adresse du démon ;
4. produit des constats horodatés, appliqués au CRM, à la liste de suppression
   et au journal d'envoi sans rien supprimer.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config
from .email_verify import email_domain

INTENT_BOUNCE = "rebond"
INTENT_AUTO_REPLY = "auto_reply"
INTENT_HUMAN = "reponse_humaine"
INTENT_OPT_OUT = "opposition"
INTENT_UNKNOWN = "inconnu"

SEVERITY_HARD = "dur"
SEVERITY_SOFT = "mou"

_BOUNCE_SENDERS = ("mailer-daemon", "postmaster", "mail delivery subsystem",
                   "mail delivery system", "no-reply-aws", "bounces+")
_BOUNCE_SUBJECTS = ("undelivered mail", "delivery status notification", "mail delivery failed",
                    "returned mail", "failure notice", "message non distribu",
                    "n'est pas parvenu", "non remis", "echec de la distribution",
                    "échec de la distribution", "delivery failure")
_AUTO_SUBJECTS = ("ticket reçu", "ticket recu", "accusé de réception", "accuse de reception",
                  "automatic reply", "réponse automatique", "reponse automatique",
                  "out of office", "absence", "nous avons bien reçu", "bien recu votre demande")
_AUTO_HEADERS = ("auto-submitted", "x-autoreply", "x-autorespond", "precedence: auto_reply")
_HARD_MARKERS = ("nxdomain", "address not found", "user unknown", "utilisateur inconnu",
                 "does not exist", "n'existe pas", "550 5.1.1", "550-5.1.1", "5.1.10",
                 "recipient address rejected", "no such user", "domaine introuvable",
                 "wasn't delivered", "not been delivered", "permanent failure",
                 "echec definitif", "échec définitif", "dns type 'mx'")
_SOFT_MARKERS = ("mailbox full", "boite pleine", "boîte pleine", "over quota", "quota",
                 "temporary", "temporaire", "try again later", "4.2.2", "4.4.1", "deferred")
_OPT_OUT_MARKERS = ("ne pas me relancer", "ne plus me contacter", "ne me contactez plus",
                    "désinscrire", "desinscrire", "unsubscribe", "merci de ne plus",
                    "ne plus recevoir", "opposition")

_EMAIL_IN_TEXT = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_RECIPIENT_PATTERNS = (
    re.compile(r"final-recipient:\s*(?:rfc822|rfc822;)\s*([^\s;<>]+@[^\s;<>]+)", re.I),
    re.compile(r"original-recipient:\s*(?:rfc822|rfc822;)\s*([^\s;<>]+@[^\s;<>]+)", re.I),
    re.compile(r"n'est pas parvenu à\s*<?([^\s<>;,)]+@[^\s<>;,)]+)", re.I),
    re.compile(r"n’a pas pu être (?:distribué|remis) à\s*<?([^\s<>;,)]+@[^\s<>;,)]+)", re.I),
    re.compile(r"(?:couldn't be delivered to|wasn't delivered to|not been delivered to|failed permanently[:\s]+)"
               r"\s*<?([^\s<>;,)]+@[^\s<>;,)]+)", re.I),
    re.compile(r"delivery to the following recipient[s]? failed[^:]*:\s*([^\s<>;,)]+@[^\s<>;,)]+)", re.I),
    re.compile(r"<([^\s<>;,)]+@[^\s<>;,)]+)>\s*(?:wasn't|was not|n'a|n’a)", re.I),
)
_ROLE_LOCAL_PARTS = {"mailer-daemon", "postmaster", "noreply", "no-reply", "donotreply"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_bounce_sender(from_email: str) -> bool:
    local = (from_email or "").strip().lower().split("@")[0]
    return any(local.startswith(p) or p in local for p in _BOUNCE_SENDERS)


def extract_bounce_recipient(text: str, sender: str = "") -> str:
    """Extrait l'adresse **destinataire** d'un avis de non-remise.

    Ne retourne jamais l'adresse du démon de messagerie : c'est l'erreur qui
    faisait attribuer le rebond à ``mailer-daemon@googlemail.com``.
    """
    text = text or ""
    for pattern in _RECIPIENT_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip().strip("<>").rstrip(".").lower()
            if candidate and candidate.split("@")[0] not in _ROLE_LOCAL_PARTS:
                return candidate
    # Repli : première adresse du corps qui n'est ni le démon ni l'expéditeur.
    sender = (sender or "").lower()
    for candidate in _EMAIL_IN_TEXT.findall(text):
        candidate = candidate.strip().rstrip(".").lower()
        local = candidate.split("@")[0]
        if local in _ROLE_LOCAL_PARTS or candidate == sender:
            continue
        return candidate
    return ""


def bounce_severity(text: str) -> str:
    low = (text or "").lower()
    if any(m in low for m in _HARD_MARKERS):
        return SEVERITY_HARD
    if any(m in low for m in _SOFT_MARKERS):
        return SEVERITY_SOFT
    return SEVERITY_HARD if "550" in low else SEVERITY_SOFT


def classify_inbound(from_email: str, subject: str, text: str, headers: str = "") -> dict[str, Any]:
    """Classe un message entrant. Le rebond prime sur tout le reste."""
    subject_l = (subject or "").lower()
    text_l = (text or "").lower()
    headers_l = (headers or "").lower()

    if is_bounce_sender(from_email) or any(s in subject_l for s in _BOUNCE_SUBJECTS) \
            or "final-recipient:" in text_l:
        recipient = extract_bounce_recipient(text, from_email)
        return {
            "intent": INTENT_BOUNCE,
            "severity": bounce_severity(text),
            "recipient": recipient,
            "reason": "expéditeur démon de messagerie ou avis de non-remise explicite",
        }
    if any(m in text_l for m in _OPT_OUT_MARKERS):
        return {"intent": INTENT_OPT_OUT, "severity": "", "recipient": from_email,
                "reason": "formulation d'opposition explicite"}
    if any(h in headers_l for h in _AUTO_HEADERS) or any(s in subject_l for s in _AUTO_SUBJECTS) \
            or "auto-submitted" in text_l:
        return {"intent": INTENT_AUTO_REPLY, "severity": "", "recipient": from_email,
                "reason": "accusé de réception ou réponse automatique (preuve de délivrance, pas un intérêt)"}
    return {"intent": INTENT_HUMAN, "severity": "", "recipient": from_email,
            "reason": "message rédigé par une personne"}


@dataclass
class Match:
    record: dict[str, Any] | None
    method: str
    email: str = ""

    @property
    def found(self) -> bool:
        return self.record is not None


def match_prospect(records: Iterable[dict[str, Any]], from_email: str,
                   recipient_hint: str = "", thread_id: str = "",
                   queue_items: Iterable[dict[str, Any]] | None = None) -> Match:
    """Rattache un événement au bon prospect, du plus fiable au plus large.

    Ordre : email exact → email du destinataire de rebond → thread Gmail connu →
    domaine de l'expéditeur → domaine du destinataire de rebond.
    """
    records = list(records)
    queue_items = list(queue_items or [])
    from_email = (from_email or "").strip().lower()
    recipient_hint = (recipient_hint or "").strip().lower()

    for candidate in (from_email, recipient_hint):
        if not candidate:
            continue
        for rec in records:
            if (rec.get("email") or "").strip().lower() == candidate:
                return Match(rec, "email_exact", candidate)

    if thread_id:
        for rec in records:
            known = {rec.get("gmail_thread_id", "")}
            known.update(h.get("thread_id", "") for h in rec.get("exchange_history", []))
            if thread_id in known and "" not in known:
                return Match(rec, "thread_id", recipient_hint or from_email)
        for item in queue_items:
            if item.get("gmail_thread_id") == thread_id or item.get("thread_id") == thread_id:
                target = (item.get("to") or item.get("email") or "").strip().lower()
                for rec in records:
                    if (rec.get("email") or "").strip().lower() == target:
                        return Match(rec, "thread_via_file", target)

    # Un rebond ne doit jamais être rattaché via le domaine du démon.
    if not is_bounce_sender(from_email):
        domain = email_domain(from_email)
        if domain:
            for rec in records:
                if email_domain(rec.get("email", "")) == domain or (rec.get("domain") or "").lower() == domain:
                    return Match(rec, "domaine_expediteur", from_email)
    if recipient_hint:
        domain = email_domain(recipient_hint)
        for rec in records:
            if email_domain(rec.get("email", "")) == domain or (rec.get("domain") or "").lower() == domain:
                return Match(rec, "domaine_destinataire", recipient_hint)
    return Match(None, "aucun", recipient_hint or from_email)


@dataclass
class Finding:
    """Constat d'audit, conservé même si aucune fiche ne correspond."""

    message_id: str
    thread_id: str
    from_email: str
    subject: str
    intent: str
    severity: str
    recipient: str
    company: str
    matched_by: str
    reason: str
    observed_at: str = field(default_factory=_now)
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_inbox(messages: Iterable[dict[str, Any]], records: Iterable[dict[str, Any]],
                queue_items: Iterable[dict[str, Any]] | None = None) -> list[Finding]:
    """Analyse une liste de messages Gmail et produit les constats rattachés."""
    records = list(records)
    queue_items = [i if isinstance(i, dict) else i.to_dict() for i in (queue_items or [])]
    findings: list[Finding] = []
    for msg in messages:
        from_email = msg.get("from", "") or msg.get("from_email", "")
        subject = msg.get("subject", "")
        text = msg.get("text", "") or msg.get("body", "")
        headers = msg.get("headers", "")
        verdict = classify_inbound(from_email, subject, text, headers)
        match = match_prospect(records, from_email, verdict.get("recipient", ""),
                               msg.get("thread_id", ""), queue_items)
        findings.append(Finding(
            message_id=msg.get("id", "") or msg.get("message_id", ""),
            thread_id=msg.get("thread_id", ""),
            from_email=from_email,
            subject=subject,
            intent=verdict["intent"],
            severity=verdict.get("severity", ""),
            recipient=verdict.get("recipient", ""),
            company=(match.record or {}).get("company", ""),
            matched_by=match.method,
            reason=verdict["reason"],
            excerpt=(text or "")[:400],
        ))
    return findings


_STATUS_BY_INTENT = {
    INTENT_BOUNCE: ("rebond", "Adresse non délivrable : corriger ou retirer, aucun nouvel envoi"),
    INTENT_AUTO_REPLY: ("auto_reply", "Accusé automatique reçu : attendre une réponse humaine avant toute relance"),
    INTENT_OPT_OUT: ("opposition", "Opposition enregistrée : aucun contact futur"),
    INTENT_HUMAN: ("réponse_recue", "Analyser la réponse et préparer une réponse personnalisée"),
    INTENT_UNKNOWN: ("réponse_recue", "Analyser manuellement"),
}


def apply_findings(findings: Iterable[Finding], crm: Any, suppression: Any = None,
                   send_log: Any = None, queue: Any = None) -> dict[str, Any]:
    """Applique les constats sans jamais supprimer de donnée ni d'historique."""
    report = {"applied": 0, "bounces": 0, "auto_replies": 0, "human_replies": 0,
              "opt_outs": 0, "unmatched": 0, "suppressed": []}
    for finding in findings:
        record = None
        for rec in crm.records:
            if finding.company and rec.get("company") == finding.company:
                record = rec
                break
        if record is None:
            report["unmatched"] += 1
            continue
        status, next_action = _STATUS_BY_INTENT.get(finding.intent, _STATUS_BY_INTENT[INTENT_UNKNOWN])
        record["status"] = status
        record["email_status"] = status
        record["next_action"] = next_action
        record["last_inbound_at"] = finding.observed_at
        record["reply_intent"] = finding.intent
        record["reply_received"] = finding.intent in (INTENT_HUMAN, INTENT_OPT_OUT)
        if finding.intent == INTENT_BOUNCE:
            record["bounce_severity"] = finding.severity
            record["bounced_address"] = finding.recipient
            report["bounces"] += 1
        elif finding.intent == INTENT_AUTO_REPLY:
            record["delivery_confirmed"] = True  # un accusé prouve la délivrance, pas l'intérêt
            report["auto_replies"] += 1
        elif finding.intent == INTENT_OPT_OUT:
            record["opposed"] = True
            report["opt_outs"] += 1
        else:
            report["human_replies"] += 1
        record.setdefault("exchange_history", []).append({
            "at": finding.observed_at, "direction": "in", "intent": finding.intent,
            "severity": finding.severity, "subject": finding.subject,
            "message_id": finding.message_id, "thread_id": finding.thread_id,
            "from": finding.from_email, "recipient": finding.recipient,
            "matched_by": finding.matched_by, "excerpt": finding.excerpt,
        })
        # Suppression : sur l'adresse destinataire réelle, jamais sur le démon.
        if suppression is not None and finding.intent in (INTENT_BOUNCE, INTENT_OPT_OUT):
            target = finding.recipient or record.get("email", "")
            if target and not is_bounce_sender(target):
                reason = "rebond_dur" if finding.severity == SEVERITY_HARD else (
                    "rebond_mou" if finding.intent == INTENT_BOUNCE else "opt-out")
                suppression.add(email=target, reason=reason, source="audit-inbox")
                report["suppressed"].append(target)
        if send_log is not None and finding.intent == INTENT_BOUNCE:
            target = (finding.recipient or record.get("email", "")).lower()
            for entry in getattr(send_log, "entries", []):
                if (entry.get("to") or "").lower() == target:
                    entry["status"] = "bounced"
                    entry["bounce_severity"] = finding.severity
                    entry["bounced_at"] = finding.observed_at
                    entry["bounce_message_id"] = finding.message_id
        if queue is not None and finding.intent in (INTENT_BOUNCE, INTENT_OPT_OUT):
            target = (finding.recipient or record.get("email", "")).lower()
            for item in getattr(queue, "items", []):
                get = item.get if isinstance(item, dict) else lambda k, d=None: getattr(item, k, d)
                if (get("to") or "").lower() == target and get("status") in ("pending", "approved"):
                    if isinstance(item, dict):
                        item["status"] = "blocked"
                        item["blocked_reason"] = status
                    else:
                        item.status = "blocked"
                        item.reason = status
        report["applied"] += 1
    crm.save()
    if suppression is not None:
        suppression.save()
    if send_log is not None and hasattr(send_log, "save"):
        send_log.save()
    if queue is not None and hasattr(queue, "save"):
        queue.save()
    return report


AUDIT_PATH = config.DATA_DIR / "history" / "inbox_audit.json"


def save_audit(findings: Iterable[Finding], path: Path | None = None) -> Path:
    """Persiste les constats (historique cumulatif, jamais écrasé)."""
    path = path or AUDIT_PATH
    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("findings", [])
        except (json.JSONDecodeError, OSError):
            existing = []
    seen = {f.get("message_id") for f in existing}
    for finding in findings:
        if finding.message_id and finding.message_id in seen:
            continue
        existing.append(finding.to_dict())
        seen.add(finding.message_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated_at": _now(), "count": len(existing), "findings": existing}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
