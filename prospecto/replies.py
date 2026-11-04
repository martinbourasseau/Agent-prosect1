"""Réception & interprétation des réponses v4.

Détecte les réponses, les associe au bon prospect, classe l'intention, met à jour
le CRM, prépare une réponse personnalisée et planifie les relances autorisées.
Aucune relance après opposition ou refus explicite. Les rebonds/plaintes
alimentent la liste de suppression.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .suppression import SuppressionList

INTENT_POSITIVE = "positive"
INTENT_NEGATIVE = "negative"
INTENT_INFO = "demande_info"
INTENT_MEETING = "demande_rdv"
INTENT_OPT_OUT = "opposition"
INTENT_AUTO_REPLY = "auto_reply"
INTENT_BOUNCE = "rebond"
INTENT_UNKNOWN = "inconnu"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


# Mots-clés par intention (normalisés sans accents). Ordre = priorité.
_KEYWORDS: list[tuple[str, list[str]]] = [
    (INTENT_BOUNCE, ["mailer-daemon", "delivery status", "undelivered", "address not found",
                     "utilisateur inconnu", "user unknown", "550 ", "5.1.1", "boite pleine",
                     "mailbox full", "message non distribue", "echec de la distribution"]),
    (INTENT_OPT_OUT, ["ne pas me relancer", "ne me contactez plus", "ne plus me contacter",
                      "desinscrire", "desabonner", "unsubscribe", "stop", "supprimez",
                      "ne plus recevoir", "opposition", "merci de ne plus", "cessez de m'ecrire"]),
    (INTENT_AUTO_REPLY, ["absence", "conge", "out of office", "actuellement absent",
                         "reponse automatique", "automatic reply", "en conges", "je suis absent"]),
    (INTENT_NEGATIVE, ["pas interesse", "pas interessee", "cela ne m'interesse",
                       "je n'ai pas besoin", "pas besoin", "non merci", "sans moi",
                       "je decline", "pas pour le moment", "ne correspond pas"]),
    (INTENT_MEETING, ["rendez-vous", "rdv", "un appel", "rencontrer", "disponible",
                      "creneau", "discuter de vive voix", "quand etes-vous", "planifier",
                      "on peut s'appeler", "un echange"]),
    (INTENT_INFO, ["plus d'infos", "plus d'informations", "informations", "comment cela",
                   "combien", "tarif", "prix", "details", "en savoir plus", "pouvez-vous m'expliquer",
                   "quelle est", "concretement", "des exemples"]),
    (INTENT_POSITIVE, ["oui", "interesse", "interessee", "avec plaisir", "d'accord",
                       "pourquoi pas", "curieux", "interessant", "partant", "je veux bien",
                       "bonne idee", "volontiers", "ca m'interesse"]),
]


def classify_intent(text: str) -> str:
    n = _norm(text or "")
    for intent, words in _KEYWORDS:
        if any(w in n for w in words):
            return intent
    return INTENT_UNKNOWN


@dataclass
class ReplyResult:
    email: str
    company: str
    intent: str
    crm_status: str
    next_action: str
    reply_draft: str
    suppressed: bool
    follow_up_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email, "company": self.company, "intent": self.intent,
            "crm_status": self.crm_status, "next_action": self.next_action,
            "reply_draft": self.reply_draft, "suppressed": self.suppressed,
            "follow_up_allowed": self.follow_up_allowed,
        }


_STATUS_MAP = {
    INTENT_POSITIVE: ("réponse_positive", "Proposer un créneau / la démonstration", True),
    INTENT_MEETING: ("demande_rdv", "Planifier le rendez-vous", True),
    INTENT_INFO: ("demande_info", "Envoyer les informations / la démo", True),
    INTENT_NEGATIVE: ("refus", "Aucune relance (refus explicite)", False),
    INTENT_OPT_OUT: ("opposition", "Aucun contact futur (opposition)", False),
    INTENT_AUTO_REPLY: ("auto_reply", "Relancer plus tard si autorisé", True),
    INTENT_BOUNCE: ("rebond", "Adresse invalide — suppression", False),
    INTENT_UNKNOWN: ("réponse_recue", "Analyser manuellement la réponse", True),
}


def prepare_reply_draft(company: str, intent: str, contact_name: str = "") -> str:
    greeting = f"Bonjour {contact_name.split()[0]}," if contact_name else "Bonjour,"
    sig = config.signature()
    if intent == INTENT_POSITIVE:
        body = ("Ravi que cela vous parle ! Je vous propose de vous montrer concrètement ce que "
                "je peux réaliser pour vous. Quel créneau vous conviendrait pour un court échange ?")
    elif intent == INTENT_MEETING:
        body = ("Avec plaisir. Je suis disponible cette semaine — dites-moi le créneau qui vous "
                "arrange et je m'adapte. Nous pourrons regarder ensemble votre projet.")
    elif intent == INTENT_INFO:
        body = ("Bien sûr. Je peux vous préparer une première démonstration personnalisée, gratuite "
                "et sans engagement, pour que vous visualisiez le résultat. Souhaitez-vous que je vous l'envoie ?")
    elif intent in (INTENT_NEGATIVE, INTENT_OPT_OUT):
        body = ("Merci pour votre retour, c'est bien noté : je ne vous recontacterai plus. "
                "Je vous souhaite une excellente continuation.")
    elif intent == INTENT_AUTO_REPLY:
        body = ""  # pas de réponse à un message automatique
    else:
        body = ("Merci pour votre message. Pourriez-vous m'en dire un peu plus sur votre besoin ? "
                "Je pourrai ainsi vous proposer quelque chose de vraiment adapté.")
    if not body:
        return ""
    return f"{greeting}\n\n{body}\n\n{sig}\n"


class ReplyHandler:
    def __init__(self, crm: Any, suppression: SuppressionList | None = None) -> None:
        self.crm = crm
        self.suppression = suppression or SuppressionList()
        self.path = config.REPLIES_PATH
        self.replies: list[dict[str, Any]] = []
        if self.path.exists():
            try:
                self.replies = json.loads(self.path.read_text(encoding="utf-8")).get("replies", [])
            except (json.JSONDecodeError, OSError):
                self.replies = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "count": len(self.replies), "replies": self.replies}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _find_record(self, email: str) -> dict | None:
        email = email.lower().strip()
        for r in self.crm.records:
            if (r.get("email") or "").lower() == email:
                return r
        return None

    def process_reply(self, from_email: str, text: str, subject: str = "",
                      message_id: str = "", thread_id: str = "") -> ReplyResult:
        intent = classify_intent(text)
        rec = self._find_record(from_email)
        company = rec.get("company", "") if rec else ""
        contact_name = rec.get("contact_name", "") if rec else ""
        status, next_action, follow_up = _STATUS_MAP[intent]

        suppressed = False
        if intent == INTENT_OPT_OUT:
            suppressed = self.suppression.add(email=from_email, reason="opt-out", source="reply")
        elif intent == INTENT_NEGATIVE:
            suppressed = self.suppression.add(email=from_email, reason="refus", source="reply")
        elif intent == INTENT_BOUNCE:
            suppressed = self.suppression.add(email=from_email, reason="rebond_dur", source="reply")

        # Mise à jour CRM (sans écraser l'historique).
        if rec is not None:
            rec["status"] = status
            rec["next_action"] = next_action
            rec["reply_received"] = True
            rec["reply_intent"] = intent
            rec["last_reply_at"] = _now()
            if intent in (INTENT_NEGATIVE, INTENT_OPT_OUT, INTENT_BOUNCE):
                rec["opposed"] = True
            rec.setdefault("exchange_history", []).append({
                "at": _now(), "direction": "in", "intent": intent,
                "subject": subject, "message_id": message_id, "excerpt": (text or "")[:400],
            })
            self.crm.save()

        draft = prepare_reply_draft(company, intent, contact_name)
        result = ReplyResult(
            email=from_email, company=company, intent=intent, crm_status=status,
            next_action=next_action, reply_draft=draft, suppressed=suppressed,
            follow_up_allowed=follow_up and not suppressed,
        )
        self.replies.append({"at": _now(), "from": from_email, "subject": subject,
                             "message_id": message_id, "thread_id": thread_id, **result.to_dict()})
        self._save()
        return result
