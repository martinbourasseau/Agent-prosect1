"""Consolidation en lecture seule des messages sortis.

POURQUOI CE MODULE
------------------
Deux journaux décrivent les envois, et aucun des deux n'est complet :

* `data/history/send-log.json` — journal de production, écrit par l'agent.
  **Fichier protégé : ce module ne l'écrit jamais.**
* `data/history/reconciliations.json` — envois constatés dans Gmail mais
  effectués hors agent (dépôt puis envoi manuel depuis l'interface).

Le tableau de bord ne lisait que le premier et affichait 60 alors que 68
messages étaient réellement sortis. Ce module produit la vue consolidée,
**sans jamais modifier un journal** et sans jamais inventer un message pour
atteindre un total attendu.

RÈGLE DE DÉDOUBLONNAGE
----------------------
Les rapprochements historiques ne nomment que des entreprises : la plupart
désignent des messages **déjà** présents dans le journal de production. Les
additionner bêtement aurait donné 97 au lieu de 68.

Une identité est donc cherchée dans cet ordre, de la plus fiable à la plus
faible, et la première disponible est retenue :

1. `gmail_message_id` — identifiant du message envoyé, preuve la plus forte ;
2. `gmail_thread_id` — un brouillon et le message envoyé qui en découle
   partagent le même fil : c'est ainsi qu'un même message apparaît avec deux
   identifiants différents selon le journal ;
3. `queue_id` — référence de file, stable pour les lots anciens ;
4. adresse + objet, puis adresse + campagne ;
5. entreprise seule — identité **faible**, signalée comme telle.

**Deux messages d'identifiants distincts adressés à la même entreprise restent
deux messages.** Deux lots différents peuvent légitimement écrire deux fois à
la même adresse : dédupliquer sur l'adresse seule effacerait un envoi réel.

Un message sans identité exploitable est conservé mais **marqué** ; il n'est
jamais fusionné par défaut, car fusionner sans preuve perdrait un envoi.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from prospecto import config

ORIGIN_PRODUCTION = "production"
ORIGIN_RECONCILIATION = "rapprochement"

# Statuts du journal qui correspondent à un message réellement sorti.
OUTBOUND_STATUSES = ("sent", "delivered", "bounced", "complained")

# Bases d'identité, de la plus forte à la plus faible.
IDENTITY_ORDER = (
    "gmail_message_id",
    "gmail_thread_id",
    "queue_id",
    "adresse_objet",
    "adresse_campagne",
    "entreprise",
    "aucune",
)
WEAK_IDENTITIES = ("entreprise", "aucune")


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


@dataclass(frozen=True)
class OutboundMessage:
    """Un message sorti, tel qu'il est prouvé par un journal."""

    key: str
    identity_basis: str
    origin: str
    to: str = ""
    subject: str = ""
    company: str = ""
    campaign: str = ""
    at: str = ""
    status: str = "sent"
    gmail_message_id: str = ""
    gmail_thread_id: str = ""
    queue_id: str = ""
    accepted_by_provider: bool = False

    @property
    def weak_identity(self) -> bool:
        return self.identity_basis in WEAK_IDENTITIES

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key, "identity_basis": self.identity_basis,
            "origin": self.origin, "to": self.to, "subject": self.subject,
            "company": self.company, "campaign": self.campaign, "at": self.at,
            "status": self.status, "gmail_message_id": self.gmail_message_id,
            "gmail_thread_id": self.gmail_thread_id, "queue_id": self.queue_id,
            "accepted_by_provider": self.accepted_by_provider,
        }


@dataclass
class Duplicate:
    """Une occurrence écartée, avec la raison — pour audit, jamais silencieuse."""

    reason: str
    origin: str
    matched_key: str
    company: str = ""
    gmail_message_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"reason": self.reason, "origin": self.origin,
                "matched_key": self.matched_key, "company": self.company,
                "gmail_message_id": self.gmail_message_id}


@dataclass
class ConsolidatedOutbound:
    messages: list[OutboundMessage] = field(default_factory=list)
    duplicates: list[Duplicate] = field(default_factory=list)
    unattributed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.messages)

    @property
    def from_production(self) -> int:
        return sum(1 for m in self.messages if m.origin == ORIGIN_PRODUCTION)

    @property
    def from_reconciliation(self) -> int:
        return sum(1 for m in self.messages if m.origin == ORIGIN_RECONCILIATION)

    @property
    def accepted_by_provider(self) -> int:
        """Messages pour lesquels le fournisseur a renvoyé un identifiant.

        C'est une preuve d'**acceptation**, jamais de remise en boîte.
        """
        return sum(1 for m in self.messages if m.accepted_by_provider)

    def summary(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "journal_production": self.from_production,
            "rapproches": self.from_reconciliation,
            "acceptes_par_fournisseur": self.accepted_by_provider,
            "doublons_ecartes": len(self.duplicates),
            "non_attribuables": len(self.unattributed),
            "identites_faibles": sum(1 for m in self.messages if m.weak_identity),
            "par_base_identite": {
                b: sum(1 for m in self.messages if m.identity_basis == b)
                for b in IDENTITY_ORDER
                if any(m.identity_basis == b for m in self.messages)
            },
        }


def _identity(fields: dict[str, Any]) -> tuple[str, str]:
    """Retourne (clé canonique, base d'identité) — voir l'ordre en docstring."""
    gid = _norm(fields.get("gmail_message_id"))
    if gid:
        return "gmail:" + gid, "gmail_message_id"
    tid = _norm(fields.get("gmail_thread_id"))
    if tid:
        return "thread:" + tid, "gmail_thread_id"
    qid = _norm(fields.get("queue_id"))
    if qid:
        return "queue:" + qid, "queue_id"
    to = _norm(fields.get("to"))
    subject = _norm(fields.get("subject"))
    if to and subject:
        return f"addr:{to}|subj:{subject}", "adresse_objet"
    campaign = _norm(fields.get("campaign"))
    if to and campaign:
        return f"addr:{to}|camp:{campaign}", "adresse_campagne"
    company = _norm(fields.get("company"))
    if company:
        return "company:" + company, "entreprise"
    return "", "aucune"


def consolidate_outbound(
    entries: Iterable[dict[str, Any]],
    reconciliations: Iterable[dict[str, Any]],
    records: Iterable[dict[str, Any]] = (),
) -> ConsolidatedOutbound:
    """Fusionne les deux journaux sans double compte et sans écriture.

    `entries` provient du journal de production, `reconciliations` du journal
    des rapprochements, `records` du CRM (pour résoudre une entreprise en
    adresse quand un rapprochement ancien ne nomme que l'entreprise).
    """
    out = ConsolidatedOutbound()
    by_key: dict[str, OutboundMessage] = {}
    # Index secondaires : un même message peut être décrit par son id de
    # message dans un journal et par son id de fil dans l'autre.
    by_thread: dict[str, str] = {}
    by_address_subject: dict[tuple[str, str], str] = {}
    by_address: dict[str, list[str]] = {}
    companies = {_norm(r.get("company")): r for r in records}
    emails = {_norm(r.get("email")): r for r in records if r.get("email")}

    def register(msg: OutboundMessage) -> None:
        by_key[msg.key] = msg
        out.messages.append(msg)
        if msg.gmail_thread_id:
            by_thread[_norm(msg.gmail_thread_id)] = msg.key
        if msg.to and msg.subject:
            by_address_subject[(_norm(msg.to), _norm(msg.subject))] = msg.key
        if msg.to:
            by_address.setdefault(_norm(msg.to), []).append(msg.key)

    # 1. Le journal de production fait foi : il est chargé en premier.
    for index, entry in enumerate(entries):
        if entry.get("status", "sent") not in OUTBOUND_STATUSES:
            continue
        key, basis = _identity(entry)
        if not key:
            # Aucune identité : on conserve le message, sans le fusionner.
            key = f"index:production:{index}"
        if key in by_key:
            out.duplicates.append(Duplicate(
                reason="identifiant deja present dans le journal de production",
                origin=ORIGIN_PRODUCTION, matched_key=key,
                company=entry.get("company", ""),
                gmail_message_id=entry.get("gmail_message_id", "")))
            continue
        to = entry.get("to", "")
        rec = emails.get(_norm(to))
        register(OutboundMessage(
            key=key, identity_basis=basis, origin=ORIGIN_PRODUCTION,
            to=to, subject=entry.get("subject", ""),
            company=entry.get("company") or (rec.get("company", "") if rec else ""),
            campaign=entry.get("campaign", ""), at=entry.get("at", ""),
            status=entry.get("status", "sent"),
            gmail_message_id=entry.get("gmail_message_id", ""),
            gmail_thread_id=entry.get("gmail_thread_id", ""),
            queue_id=entry.get("queue_id", ""),
            accepted_by_provider=bool(entry.get("gmail_message_id")),
        ))

    # 2. Les rapprochements : ajoutés seulement s'ils prouvent un message neuf.
    for recon in reconciliations:
        sent_messages = recon.get("sent_messages") or []
        for sm in sent_messages:
            company = sm.get("company", "")
            rec = companies.get(_norm(company))
            to = sm.get("to") or (rec.get("email", "") if rec else "")
            fields = {**sm, "to": to, "company": company,
                      "campaign": sm.get("campaign") or recon.get("campaign", "")}
            key, basis = _identity(fields)
            existing = by_key.get(key)
            # Un brouillon et son message envoyé partagent le fil : même si
            # l'identifiant diffère, c'est le même message sorti.
            if existing is None and sm.get("gmail_thread_id"):
                k = by_thread.get(_norm(sm["gmail_thread_id"]))
                existing = by_key.get(k) if k else None
            if existing is not None:
                out.duplicates.append(Duplicate(
                    reason="message deja compte (meme identifiant ou meme fil)",
                    origin=ORIGIN_RECONCILIATION, matched_key=existing.key,
                    company=company, gmail_message_id=sm.get("gmail_message_id", "")))
                continue
            if not key:
                out.unattributed.append({
                    "company": company, "at": recon.get("at", ""),
                    "reason": "rapprochement sans identifiant de message exploitable"})
                continue
            register(OutboundMessage(
                key=key, identity_basis=basis, origin=ORIGIN_RECONCILIATION,
                to=to, subject=sm.get("subject", ""), company=company,
                campaign=fields["campaign"], at=sm.get("at") or recon.get("at", ""),
                status="sent", gmail_message_id=sm.get("gmail_message_id", ""),
                gmail_thread_id=sm.get("gmail_thread_id", ""),
                queue_id=sm.get("queue_id", ""),
                accepted_by_provider=bool(sm.get("gmail_message_id")),
            ))

        # Rapprochements anciens : ils ne nomment que des entreprises. Ils
        # désignent presque toujours des messages DÉJÀ journalisés. On les
        # rattache, on ne les ajoute pas.
        if sent_messages:
            continue
        for company in recon.get("updated_companies") or []:
            rec = companies.get(_norm(company))
            to = _norm(rec.get("email")) if rec else ""
            matched = by_address.get(to, [])
            if matched:
                out.duplicates.append(Duplicate(
                    reason="entreprise deja presente au journal de production",
                    origin=ORIGIN_RECONCILIATION, matched_key=matched[0],
                    company=company))
            else:
                # Pas d'identifiant, pas de trace : ajouter serait inventer.
                out.unattributed.append({
                    "company": company, "at": recon.get("at", ""),
                    "reason": ("rapprochement sans identifiant de message et sans "
                               "envoi correspondant au journal : non ajouté"),
                })
    return out


def load_outbound(records: Iterable[dict[str, Any]] | None = None) -> ConsolidatedOutbound:
    """Vue consolidée des fichiers réels. Lecture seule."""
    if records is None:
        from prospecto.crm import CRM
        records = CRM().records
    entries: list[dict[str, Any]] = []
    log_path = config.SEND_LOG_PATH
    if log_path.exists():
        try:
            payload = json.loads(log_path.read_text(encoding="utf-8"))
            entries = payload if isinstance(payload, list) else payload.get("entries", [])
        except (json.JSONDecodeError, OSError):
            entries = []
    recons: list[dict[str, Any]] = []
    rp = config.DATA_DIR / "history" / "reconciliations.json"
    if rp.exists():
        try:
            recons = json.loads(rp.read_text(encoding="utf-8")).get("reconciliations", [])
        except (json.JSONDecodeError, OSError):
            recons = []
    return consolidate_outbound(entries, recons, records)
