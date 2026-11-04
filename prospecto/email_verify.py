"""Vérification technique des adresses avant toute préparation d'email (lot 5).

Contexte : le lot 2 contenait ``contact@severine-lesourd.com`` alors que le site
officiel est ``severine-lesourd.fr``. Le domaine ``.com`` n'existe pas (NXDOMAIN)
et le message a rebondi. Aucun contrôle technique n'existait avant la création
du brouillon.

Ce module ajoute ce contrôle, **sans jamais prétendre qu'une boîte existe** :

* on vérifie la syntaxe de l'adresse ;
* on résout les enregistrements MX du domaine ;
* à défaut de MX, on regarde s'il existe un enregistrement A (repli RFC 5321,
  livraison possible mais non garantie) ;
* on distingue clairement « domaine inexistant », « domaine sans MX »,
  « erreur DNS transitoire » et « domaine joignable ».

Aucune connexion SMTP n'est ouverte, aucun message de test n'est envoyé :
la vérification est purement DNS, gratuite et sans effet de bord.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config

# Statuts de vérification technique (distincts du niveau de vérification *source*).
MX_OK = "mx_ok"                    # le domaine publie des MX : routage possible
MX_A_FALLBACK = "a_fallback"       # pas de MX mais un A : repli RFC 5321, risqué
MX_NONE = "no_mx"                  # domaine existant, aucun MX ni A : non délivrable
MX_NXDOMAIN = "nxdomain"           # le domaine n'existe pas : non délivrable
MX_DNS_ERROR = "dns_error"         # erreur transitoire : à revérifier, ne pas conclure
MX_BAD_SYNTAX = "syntaxe_invalide"  # adresse mal formée
MX_NOT_CHECKED = "non_verifie"

DELIVERABLE_STATUSES = (MX_OK,)
RISKY_STATUSES = (MX_A_FALLBACK, MX_DNS_ERROR, MX_NOT_CHECKED)
BLOCKING_STATUSES = (MX_NXDOMAIN, MX_NONE, MX_BAD_SYNTAX)

_EMAIL_RE = re.compile(r"^[^@\s,;<>]+@([^@\s,;<>]+\.[^@\s,;<>]+)$")

DOMAIN_CACHE_PATH = config.DATA_DIR / "history" / "domain_checks.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def email_domain(email: str) -> str:
    """Domaine d'une adresse, en minuscules, sans espace."""
    email = (email or "").strip().lower()
    return email.rsplit("@", 1)[-1] if "@" in email else ""


@dataclass
class DomainCheck:
    """Résultat daté d'un contrôle DNS, conservé comme preuve."""

    domain: str
    status: str
    mx_hosts: list[str] = field(default_factory=list)
    checked_at: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def deliverable(self) -> bool:
        return self.status in DELIVERABLE_STATUSES

    @property
    def blocking(self) -> bool:
        return self.status in BLOCKING_STATUSES


def check_domain(domain: str, resolver: Any = None, timeout: float = 5.0) -> DomainCheck:
    """Résout les MX d'un domaine. ``resolver`` est injectable pour les tests."""
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain or "." not in domain:
        return DomainCheck(domain, MX_BAD_SYNTAX, checked_at=_now(), detail="domaine vide ou invalide")

    if resolver is None:
        try:
            import dns.resolver  # dnspython

            resolver = dns.resolver.Resolver()
            resolver.lifetime = timeout
            resolver.timeout = timeout
        except ImportError:  # pragma: no cover - environnement sans dnspython
            return DomainCheck(domain, MX_NOT_CHECKED, checked_at=_now(),
                               detail="dnspython indisponible : contrôle DNS non effectué")

    try:
        answers = resolver.resolve(domain, "MX")
        hosts = sorted({str(r.exchange).rstrip(".").lower() for r in answers if str(r.exchange).rstrip(".")})
        if hosts:
            return DomainCheck(domain, MX_OK, hosts, _now(), f"{len(hosts)} MX publiés")
    except Exception as exc:  # noqa: BLE001 - on classe l'erreur, on ne la propage pas
        name = type(exc).__name__
        if name == "NXDOMAIN" or "NXDOMAIN" in str(exc):
            return DomainCheck(domain, MX_NXDOMAIN, checked_at=_now(),
                               detail="le domaine n'existe pas (NXDOMAIN)")
        if name not in ("NoAnswer", "NoNameservers", "LifetimeTimeout", "Timeout"):
            # Erreur inattendue : on reste prudent, on ne conclut pas.
            return DomainCheck(domain, MX_DNS_ERROR, checked_at=_now(), detail=f"{name}: {exc}"[:200])

    # Pas de MX : repli sur un enregistrement A (RFC 5321 §5.1).
    try:
        answers = resolver.resolve(domain, "A")
        if len(answers):
            return DomainCheck(domain, MX_A_FALLBACK, checked_at=_now(),
                               detail="aucun MX, un A existe : repli SMTP possible mais non garanti")
    except Exception as exc:  # noqa: BLE001
        name = type(exc).__name__
        if name == "NXDOMAIN" or "NXDOMAIN" in str(exc):
            return DomainCheck(domain, MX_NXDOMAIN, checked_at=_now(),
                               detail="le domaine n'existe pas (NXDOMAIN)")
        if name in ("LifetimeTimeout", "Timeout", "NoNameservers"):
            return DomainCheck(domain, MX_DNS_ERROR, checked_at=_now(), detail=f"{name}: délai DNS dépassé")
    return DomainCheck(domain, MX_NONE, checked_at=_now(), detail="domaine sans MX ni A : non délivrable")


def verify_email(email: str, resolver: Any = None, timeout: float = 5.0) -> dict[str, Any]:
    """Contrôle une adresse : syntaxe + DNS du domaine. Ne teste jamais la boîte."""
    email = (email or "").strip()
    match = _EMAIL_RE.match(email.lower())
    if not match:
        return {"email": email, "domain": "", "status": MX_BAD_SYNTAX,
                "mx_hosts": [], "checked_at": _now(), "detail": "adresse mal formée"}
    check = check_domain(match.group(1), resolver=resolver, timeout=timeout)
    return {"email": email, **check.to_dict()}


class DomainCache:
    """Cache persistant des contrôles DNS (preuve horodatée, réutilisable)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DOMAIN_CACHE_PATH
        self.entries: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            try:
                self.entries = json.loads(self.path.read_text(encoding="utf-8")).get("domains", {})
            except (json.JSONDecodeError, OSError):
                self.entries = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _now(), "count": len(self.entries), "domains": self.entries}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def check(self, domain: str, resolver: Any = None, refresh: bool = False,
              timeout: float = 5.0) -> dict[str, Any]:
        domain = (domain or "").strip().lower()
        if not refresh and domain in self.entries:
            return self.entries[domain]
        result = check_domain(domain, resolver=resolver, timeout=timeout).to_dict()
        self.entries[domain] = result
        return result


def verify_records(records: Iterable[dict[str, Any]], cache: DomainCache | None = None,
                   refresh: bool = False, resolver: Any = None) -> dict[str, Any]:
    """Vérifie les domaines de tous les enregistrements CRM et annote chaque fiche.

    Renseigne ``email_dns_status``, ``email_dns_checked_at`` et ``email_dns_detail``.
    Une fiche bloquée reçoit ``next_action`` explicite, sans jamais être supprimée.
    """
    cache = cache or DomainCache()
    summary = {"checked": 0, "deliverable": 0, "risky": 0, "blocking": 0, "no_email": 0, "details": []}
    for rec in records:
        email = (rec.get("email") or "").strip()
        if not email:
            summary["no_email"] += 1
            continue
        domain = email_domain(email)
        result = cache.check(domain, resolver=resolver, refresh=refresh)
        status = result.get("status", MX_NOT_CHECKED)
        rec["email_dns_status"] = status
        rec["email_dns_checked_at"] = result.get("checked_at", "")
        rec["email_dns_detail"] = result.get("detail", "")
        summary["checked"] += 1
        if status in DELIVERABLE_STATUSES:
            summary["deliverable"] += 1
        elif status in BLOCKING_STATUSES:
            summary["blocking"] += 1
            rec["next_action"] = "Adresse non délivrable : corriger le domaine puis revérifier (aucun envoi)"
        else:
            summary["risky"] += 1
        summary["details"].append({"company": rec.get("company", ""), "email": email, "status": status})
    cache.save()
    return summary
