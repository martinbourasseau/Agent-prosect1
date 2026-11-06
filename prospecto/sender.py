"""Moteur d'envoi v4 — envoi automatisé sous contrôles stricts.

Pipeline : pré-vol (activation + délivrabilité) → sélection des prospects qualifiés
(email vérifié, non supprimé, non contacté, score suffisant) → dédoublonnage →
montée en charge (daily limit / ramp-up) → envoi par transport → journalisation →
mise à jour CRM/file → conditions d'arrêt (rebonds / plaintes).

Transports :
  - dry_run        : simule, n'envoie rien (défaut).
  - smtp           : envoi réel via SMTP (env PROSPECTO_SMTP_*). Automatisable.
  - gmail_connector: prépare un plan d'envoi pour le connecteur Gmail (exécuté par
                     l'agent), puis enregistrement via record_sent().

AUCUN envoi tant que la campagne n'est pas activée explicitement ET que les
contrôles de sécurité/délivrabilité ne sont pas passés. dry_run par défaut.
"""
from __future__ import annotations

import json
import os
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from . import config
from .models import EMAIL_VERIFIED
from .suppression import SuppressionList
from .deliverability import analyze_sender, provider_daily_limit

SETTINGS_PATH = config.CAMPAIGN_SETTINGS_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_settings(path: Path | None = None) -> dict[str, Any]:
    path = path or SETTINGS_PATH
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"enabled": False, "dry_run": True}


def save_settings(settings: dict[str, Any], path: Path | None = None) -> None:
    path = path or SETTINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class SendLog:
    """Journal des envois / rebonds / plaintes (source des taux d'arrêt)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.SEND_LOG_PATH
        self.entries: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.entries = json.loads(self.path.read_text(encoding="utf-8")).get("entries", [])
            except (json.JSONDecodeError, OSError):
                self.entries = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "count": len(self.entries), "entries": self.entries}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def record(self, **fields: Any) -> dict[str, Any]:
        entry = {"at": _now(), **fields}
        self.entries.append(entry)
        self.save()
        return entry

    def sent_today(self) -> int:
        return sum(1 for e in self.entries if e.get("status") == "sent" and e.get("at", "").startswith(_today()))

    def rates(self) -> dict[str, float]:
        sent = [e for e in self.entries if e.get("status") in ("sent", "delivered", "bounced", "complained")]
        n = len(sent)
        if not n:
            return {"bounce_rate": 0.0, "complaint_rate": 0.0, "sent": 0}
        bounced = sum(1 for e in sent if e.get("status") == "bounced")
        complained = sum(1 for e in sent if e.get("status") == "complained")
        return {"bounce_rate": bounced / n, "complaint_rate": complained / n, "sent": n}


@dataclass
class SendCandidate:
    company: str
    to: str
    subject: str
    body: str
    email_verification: str
    score: int
    queue_id: str = ""
    campaign: str = ""
    variant: str = ""
    reference_id: str = ""
    crm_id: str = ""


class Sender:
    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or SETTINGS_PATH
        self.settings = load_settings(self.settings_path)
        self.suppression = SuppressionList()
        self.log = SendLog()

    # -- pré-vol -------------------------------------------------------------
    def preflight(self) -> tuple[bool, list[str]]:
        issues: list[str] = []
        s = self.settings
        if not s.get("enabled"):
            issues.append("Campagne non activée (enabled=false). Activation explicite requise.")
        sender_email = s.get("sender", {}).get("email", config.SENDER_EMAIL)
        rep = analyze_sender(sender_email)
        s.setdefault("deliverability", {})["last_checked_at"] = _now()
        s["deliverability"]["last_result"] = rep.to_dict()
        if s.get("deliverability", {}).get("require_spf") and not rep.spf_present:
            issues.append("SPF absent/introuvable pour le domaine expéditeur.")
        if s.get("deliverability", {}).get("require_dkim") and not rep.dkim_present:
            issues.append("DKIM non détecté pour le domaine expéditeur.")
        if s.get("deliverability", {}).get("require_dmarc") and not rep.dmarc_present:
            issues.append("DMARC absent pour le domaine expéditeur.")
        if rep.is_free_provider:
            issues.append(
                f"Domaine expéditeur gratuit ({rep.provider}) : prospection de masse déconseillée/interdite par les CGU."
            )
        save_settings(s, self.settings_path)
        return (len(issues) == 0), issues

    # -- sélection -----------------------------------------------------------
    # Statuts qui interdisent tout envoi, quelle que soit la qualité de la fiche.
    # « suspendu » couvre le cas Uzès Location : brouillon conservé mais adresse
    # non confirmée. Sans ce garde-fou, une fiche suspendue mais bien scorée et
    # vérifiée pourrait être sélectionnée par le seul filtre de vérification.
    BLOCKED_STATUSES = {
        "suspendu", "suspended", "opposition", "opposed", "opposée",
        "désinscrit", "desinscrit", "unsubscribed", "bounced", "rebond",
        "complained", "plainte", "écarté", "ecarte", "exclu",
        # Lot 8 : une fiche sans adresse publique n'est pas envoyable. Elle était
        # scorée « fort » en automatisation et passait donc les autres filtres.
        "non_contactable", "aucune_adresse_publique", "non_trouve", "inconnu",
    }

    def _is_blocked(self, record: dict) -> bool:
        # Aucune adresse = aucun envoi possible, quel que soit le score.
        if not str(record.get("email") or "").strip():
            return True
        for key in ("status", "status_crm", "email_status", "contactability"):
            if str(record.get(key) or "").strip().lower() in self.BLOCKED_STATUSES:
                return True
        return bool(record.get("suspended_at"))

    def select_candidates(self, crm_records: list[dict], queue_items: list[dict]) -> list[SendCandidate]:
        s = self.settings
        allowed = set(s.get("quality", {}).get("allowed_email_verification", [EMAIL_VERIFIED]))
        min_score = s.get("quality", {}).get("min_score", 40)
        # Dédoublonnage : uniquement les adresses DÉJÀ envoyées. Les emails en attente /
        # approuvés sont précisément ceux qu'il faut envoyer (préparés, pas encore partis).
        already = {i.get("to", "").lower() for i in queue_items if i.get("status") == "sent"}
        already |= {e.get("to", "").lower() for e in self.log.entries if e.get("status") in ("sent", "delivered")}
        contacted = {r.get("email", "").lower() for r in crm_records if r.get("status") == "contacté"}
        # Une suspension posée dans la file vaut aussi blocage, même si le CRM
        # n'a pas encore été resynchronisé.
        already |= {i.get("to", "").lower() for i in queue_items
                    if str(i.get("status") or "").strip().lower() in self.BLOCKED_STATUSES}

        out: list[SendCandidate] = []
        for r in crm_records:
            email = (r.get("email") or "").lower()
            if not email or r.get("status") == "contacté":
                continue
            if self._is_blocked(r):
                continue
            if r.get("tier") not in ("haute", "moyenne"):
                continue
            if r.get("email_verification", "public_unverified") not in allowed:
                continue
            if (r.get("score") or 0) < min_score:
                continue
            if self.suppression.is_suppressed(email):
                continue
            if email in already or email in contacted:
                continue
            proposed = r.get("proposed_email") or {}
            if not proposed.get("body"):
                continue
            out.append(SendCandidate(
                company=r.get("company", ""), to=email,
                subject=proposed.get("subject", ""), body=proposed.get("body", ""),
                email_verification=r.get("email_verification", "public_unverified"),
                score=r.get("score", 0), queue_id=proposed.get("queue_id", ""),
                campaign=r.get("campaign", ""), variant=r.get("variant", ""),
                reference_id=r.get("reference_id", ""), crm_id=r.get("id", ""),
            ))
        # Priorité aux meilleurs scores.
        out.sort(key=lambda c: -c.score)
        return out

    def build_plan(self, candidates: list[SendCandidate]) -> list[SendCandidate]:
        s = self.settings
        limits = s.get("limits", {})
        ramp = limits.get("ramp_up", [])
        day_idx = limits.get("ramp_up_day_index", 0)
        daily = ramp[day_idx] if ramp and day_idx < len(ramp) else limits.get("daily_limit", 20)
        remaining_today = max(0, daily - self.log.sent_today())
        cap = min(remaining_today, limits.get("max_per_run", daily))
        return candidates[:cap]

    # -- conditions d'arrêt --------------------------------------------------
    def check_stop_conditions(self) -> tuple[bool, str]:
        s = self.settings
        sc = s.get("stop_conditions", {})
        rates = self.log.rates()
        if rates["sent"] < sc.get("min_sent_before_rate_check", 20):
            return False, ""
        if rates["bounce_rate"] > sc.get("max_bounce_rate", 0.05):
            return True, f"Taux de rebond anormal : {rates['bounce_rate']:.1%}"
        if rates["complaint_rate"] > sc.get("max_complaint_rate", 0.001):
            return True, f"Taux de plainte anormal : {rates['complaint_rate']:.2%}"
        return False, ""

    # -- exécution -----------------------------------------------------------
    def execute(self, plan: list[SendCandidate], transport: str | None = None) -> list[dict[str, Any]]:
        s = self.settings
        transport = transport or s.get("transport", "dry_run")
        if s.get("dry_run", True):
            transport = "dry_run"
        stop, reason = self.check_stop_conditions()
        if stop and s.get("stop_conditions", {}).get("auto_pause_on_breach", True):
            s["enabled"] = False
            save_settings(s, self.settings_path)
            return [{"status": "paused", "reason": reason}]

        results = []
        delay = s.get("limits", {}).get("min_delay_seconds", 45)
        for i, cand in enumerate(plan):
            # Ultime vérification suppression (a pu changer depuis la sélection).
            if self.suppression.is_suppressed(cand.to):
                results.append({"to": cand.to, "status": "skipped_suppressed"})
                continue
            if transport == "dry_run":
                res = {"to": cand.to, "company": cand.company, "status": "dry_run", "subject": cand.subject}
            elif transport == "smtp":
                res = self._send_smtp(cand)
            elif transport == "gmail_connector":
                res = {"to": cand.to, "company": cand.company, "status": "ready_for_connector",
                       "subject": cand.subject, "body": cand.body, "queue_id": cand.queue_id}
            else:
                res = {"to": cand.to, "status": "error", "error": f"transport inconnu : {transport}"}
            # Journalise (sauf plan connector non encore envoyé).
            if res["status"] not in ("ready_for_connector",):
                self.log.record(to=cand.to, company=cand.company, subject=cand.subject,
                        status=res["status"], campaign=cand.campaign, variant=cand.variant,
                        reference_id=cand.reference_id, queue_id=cand.queue_id,
                        message_id=res.get("message_id", ""))
            results.append(res)
            if transport == "smtp" and i < len(plan) - 1:
                time.sleep(delay)
        return results

    def _send_smtp(self, cand: SendCandidate) -> dict[str, Any]:
        host = os.environ.get("PROSPECTO_SMTP_HOST", "")
        port = int(os.environ.get("PROSPECTO_SMTP_PORT", "587"))
        user = os.environ.get("PROSPECTO_SMTP_USER", "")
        password = os.environ.get("PROSPECTO_SMTP_PASSWORD", "")
        if not host or not user or not password:
            return {"to": cand.to, "status": "error", "error": "SMTP non configuré (env PROSPECTO_SMTP_*)."}
        s = self.settings
        msg = EmailMessage()
        msg["From"] = f"{s['sender']['name']} <{s['sender']['email']}>"
        msg["To"] = cand.to
        msg["Subject"] = cand.subject
        if s.get("sender", {}).get("reply_to"):
            msg["Reply-To"] = s["sender"]["reply_to"]
        msg.set_content(cand.body)
        try:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(user, password)
                smtp.send_message(msg)
            return {"to": cand.to, "company": cand.company, "status": "sent",
                    "subject": cand.subject, "message_id": msg.get("Message-ID", "")}
        except Exception as exc:  # noqa: BLE001
            return {"to": cand.to, "status": "error", "error": str(exc)}

    def record_sent(self, to: str, message_id: str = "", company: str = "", campaign: str = "") -> dict:
        """Enregistre un envoi réel effectué via le connecteur Gmail."""
        return self.log.record(to=to, company=company, campaign=campaign,
                               status="sent", message_id=message_id)

    def record_bounce(self, to: str, reason: str = "") -> dict:
        self.suppression.add(email=to, reason="rebond_dur", source="bounce")
        return self.log.record(to=to, status="bounced", reason=reason)

    def record_complaint(self, to: str) -> dict:
        self.suppression.add(email=to, reason="plainte", source="complaint")
        return self.log.record(to=to, status="complained")
