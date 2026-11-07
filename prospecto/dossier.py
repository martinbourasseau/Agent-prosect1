"""Dossier de qualification — phase 10, section F.

Le CRM portait déjà la plupart des champs, mais rien ne vérifiait qu'une fiche
est réellement complète avant de rédiger, et rien ne distinguait une adresse
**publiée et vérifiée** d'une adresse **reconstituée** par nos soins.

Deux règles y sont appliquées strictement :

1. **Aucune coordonnée devinée.** Une adresse n'est exploitable que si elle est
   publiée par l'entreprise sur une source datée. Le contrôle DNS prouve que le
   domaine route, pas que la boîte existe : les deux mentions restent séparées.

2. **Une adresse décodée n'est pas confirmée.** Froger Étanchéité publie
   `mailto:moc.liamg%40etiehcnateregorf`. L'inversion est déterministe et donne
   `frogeretancheite@gmail.com`, mais c'est une reconstruction : tant qu'une
   autre source publique ne la confirme pas, elle reste non confirmée et ne
   peut pas justifier un envoi.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any, Iterable
from urllib.parse import unquote

from .email_verify import DELIVERABLE_STATUSES, BLOCKING_STATUSES, MX_NOT_CHECKED
from .scoring import AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA, scores_from_record

# Statuts CRM qui interdisent toute nouvelle approche, quelle que soit la
# qualité de l'opportunité. Une opposition est définitive.
FORBIDDEN_STATUSES = frozenset({
    "opposition", "opposé", "suspendu", "suspendue", "rebond", "bounced",
    "non_contactable", "contacté", "contactée", "envoyé", "envoyée", "sent",
})

EMAIL_PUBLISHED = "publiee"
EMAIL_DECODED = "decodee_non_confirmee"
EMAIL_ABSENT = "absente"

AXES = (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA)

SERVICE_BY_AXIS = {
    AXIS_SITE_WEB: "création de site vitrine",
    AXIS_REFONTE: "refonte de site",
    AXIS_IA: "automatisation et agent IA",
}


def decode_obfuscated_mailto(href: str) -> str:
    """Décode un mailto volontairement brouillé, sans rien inventer.

    Ne traite que deux transformations réversibles constatées : l'encodage
    pourcent et l'inversion complète de la chaîne. Le résultat est une
    RECONSTITUTION, jamais une confirmation.
    """
    raw = (href or "").strip()
    if raw.lower().startswith("mailto:"):
        raw = raw[7:]
    raw = unquote(raw).split("?")[0].strip()
    if "@" in raw and _looks_like_email(raw):
        return raw.lower()
    reversed_raw = raw[::-1]
    if "@" in reversed_raw and _looks_like_email(reversed_raw):
        return reversed_raw.lower()
    return ""


def _looks_like_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$", value))


def email_provenance(rec: dict[str, Any]) -> str:
    """D'où vient l'adresse : publiée, reconstituée, ou absente.

    Un statut explicite prime toujours : c'est une décision tracée. Froger a
    été reconstituée puis CONFIRMÉE par une publication en clair ; la note qui
    raconte cette confirmation contient le mot « reconstituée » et ne doit pas
    la faire rétrograder. À défaut de statut explicite, on reste prudent et on
    cherche les traces d'une reconstitution dans les notes.
    """
    if not (rec.get("email") or "").strip():
        return EMAIL_ABSENT
    explicit = rec.get("email_provenance")
    if explicit in (EMAIL_PUBLISHED, EMAIL_DECODED):
        return explicit
    blob = " ".join(str(rec.get(k, "")) for k in
                    ("notes", "email_source", "justification")).lower()
    if any(cue in blob for cue in ("décod", "decod", "reconstitu", "inversé", "inverse",
                                   "mail obfus", "mailto mal")):
        return EMAIL_DECODED
    return EMAIL_PUBLISHED


def email_publication_evidence(rec: dict[str, Any]) -> dict[str, str]:
    """Preuve datée que l'entreprise publie bien cette adresse.

    On cherche l'adresse dans une preuve dont la source est le site officiel
    (ou le même domaine que l'adresse). Une adresse vue seulement dans un
    annuaire ou un moteur ne suffit pas.
    """
    email = (rec.get("email") or "").strip().lower()
    if not email:
        return {}
    domain = email.split("@")[-1]
    for e in rec.get("evidence") or []:
        blob = json.dumps(e, ensure_ascii=False).lower()
        if email not in blob:
            continue
        url = str(e.get("source_url", ""))
        official = (e.get("source_type") == "site_officiel" or domain in url)
        if official and e.get("observed_at"):
            return {"url": url, "date": e["observed_at"],
                    "type": e.get("source_type", "")}
    return {}


@dataclass
class Dossier:
    """Ce qu'exige la section F pour qu'une fiche soit qualifiée."""

    company: str = ""
    activity: str = ""
    city: str = ""
    department: str = ""
    website: str = ""
    manager: str = ""
    manager_public: bool = False
    email: str = ""
    email_provenance: str = EMAIL_ABSENT
    email_domain_status: str = ""
    email_verified: bool = False
    email_verification_basis: str = ""
    email_publication: dict[str, str] = field(default_factory=dict)
    phone: str = ""
    phone_verification: str = "non_verifie"
    phone_verified: bool = False
    sources: list[dict[str, str]] = field(default_factory=list)
    problem: str = ""
    concrete_evidence: str = ""
    scores: dict[str, int] = field(default_factory=dict)
    confidence: str = "faible"
    recommended_service: str = ""
    commercial_angle: str = ""
    blockers: list[str] = field(default_factory=list)
    qualified: bool = False
    evaluated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def commercial_angle(rec: dict[str, Any], scores: dict[str, Any] | None = None) -> str:
    """Un angle d'approche ancré sur une preuve, pas sur le secteur.

    L'angle reprend le constat le mieux établi de l'axe dominant. Il reste
    factuel : il décrit ce qui a été vu, jamais un bénéfice promis.
    """
    scores = scores or rec.get("scores") or {}
    best = max(AXES, key=lambda a: int((scores.get(a) or {}).get("score", 0)))
    axis = scores.get(best) or {}
    observed = axis.get("observed_signals") or []
    lead = observed[0] if observed else ""
    if best == AXIS_IA:
        if lead:
            return (f"Partir du constat « {lead} » et proposer de réduire la reprise "
                    "manuelle correspondante, sans changer leurs habitudes de travail.")
        return ("Ouvrir sur le traitement des demandes entrantes, à partir d'un "
                "exemple concret de leur parcours actuel.")
    if best == AXIS_REFONTE:
        if lead:
            return (f"Montrer le point précis « {lead} » et proposer une correction "
                    "ciblée du parcours, plutôt qu'une refonte générale.")
        return ("Ouvrir sur le parcours de contact observé et proposer une "
                "amélioration bornée et vérifiable.")
    if lead:
        return (f"Partir de « {lead} » pour proposer une présence en ligne qui "
                "présente l'activité et capte les demandes.")
    return ("Ouvrir sur la présentation de l'activité et la façon dont un client "
            "peut les trouver aujourd'hui.")


def build_dossier(rec: dict[str, Any], today: date | None = None) -> Dossier:
    """Assemble le dossier et liste précisément ce qui manque."""
    scores = rec.get("scores") or scores_from_record(rec)
    prov = email_provenance(rec)
    dns = rec.get("email_dns_status") or MX_NOT_CHECKED
    # Vocabulaire réel du CRM : « verified » = publiée et contrôlée ;
    # « public_unverified » = vue quelque part mais pas recoupée. Les deux ne
    # sont pas interchangeables : la section F exige publiée ET vérifiée.
    email_verif = str(rec.get("email_verification") or "")
    publication = email_publication_evidence(rec)
    # Deux fondements acceptables, jamais une supposition : soit une
    # vérification explicite déjà tracée, soit une preuve datée que
    # l'entreprise publie l'adresse sur son propre site. Le MX ne prouve que le
    # routage du domaine, il ne vérifie pas l'existence de la boîte.
    basis = ("vérification explicite tracée" if email_verif == "verified"
             else "adresse citée sur source officielle datée" if publication else "")
    email_ok = (prov == EMAIL_PUBLISHED and dns in DELIVERABLE_STATUSES
                and bool(basis))
    phone_verif = str(rec.get("phone_verification") or "non_verifie")
    phone_ok = bool((rec.get("phone") or "").strip()) and phone_verif == "verified"

    evidences = rec.get("evidence") or []
    sources = [{"url": e.get("source_url", ""), "date": e.get("observed_at", ""),
                "type": e.get("source_type", ""), "kind": e.get("kind", "")}
               for e in evidences if e.get("source_url")]
    concrete = next((e.get("quote", "") for e in evidences
                     if e.get("observed", True) and e.get("quote")), "")

    best = max(AXES, key=lambda a: int((scores.get(a) or {}).get("score", 0)))
    confidence = (scores.get(best) or {}).get("confidence", "faible")

    d = Dossier(
        company=rec.get("company", ""),
        activity=rec.get("sector", ""),
        city=rec.get("city", ""),
        department=str(rec.get("department", "")),
        website=rec.get("website", ""),
        manager=rec.get("contact_name", ""),
        manager_public=bool(rec.get("contact_name_source")),
        email=rec.get("email", ""),
        email_provenance=prov,
        email_domain_status=dns,
        email_verified=email_ok,
        email_verification_basis=basis,
        email_publication=publication,
        phone=rec.get("phone", ""),
        phone_verification=phone_verif,
        phone_verified=phone_ok,
        sources=sources,
        problem=rec.get("need", "") or rec.get("justification", ""),
        concrete_evidence=concrete,
        scores={a: int((scores.get(a) or {}).get("score", 0)) for a in AXES},
        confidence=confidence,
        recommended_service=rec.get("recommended_service") or SERVICE_BY_AXIS[best],
        commercial_angle=commercial_angle(rec, scores),
        evaluated_at=(today or date.today()).isoformat(),
    )

    # --- Ce qui manque, énoncé sans détour -------------------------------
    if not d.company:
        d.blockers.append("nom officiel absent")
    if not d.activity:
        d.blockers.append("activité non renseignée")
    if not d.city and not d.department:
        d.blockers.append("localisation absente")
    if prov == EMAIL_ABSENT:
        d.blockers.append("aucune adresse professionnelle publiée : à identifier, "
                          "jamais à deviner")
    elif prov == EMAIL_DECODED:
        d.blockers.append("adresse reconstituée depuis un lien brouillé : non "
                          "confirmée, une source publique indépendante est requise")
    elif dns in BLOCKING_STATUSES:
        d.blockers.append(f"domaine de l'adresse non routable ({dns})")
    elif dns not in DELIVERABLE_STATUSES:
        d.blockers.append(f"routage du domaine non vérifié ({dns})")
    elif not basis and email_verif == "public_unverified":
        d.blockers.append("adresse publiée mais non recoupée : vérification "
                          "indépendante requise")
    elif not basis:
        d.blockers.append(f"adresse non vérifiée ({email_verif or 'statut absent'}), "
                          "aucune preuve datée de publication")
    if not d.sources:
        d.blockers.append("aucune source datée")
    if not d.concrete_evidence:
        d.blockers.append("aucune preuve concrète citée")
    if str(rec.get("status", "")).lower() in FORBIDDEN_STATUSES:
        d.blockers.append(f"statut « {rec.get('status')} » : aucune nouvelle approche")
    if rec.get("opposed"):
        d.blockers.append("opposition enregistrée : contact définitivement exclu")
    if rec.get("suspension_reason"):
        d.blockers.append("fiche suspendue")

    d.qualified = not d.blockers
    return d


def audit_portfolio(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Dossiers de tout le portefeuille, avec le motif de chaque blocage."""
    dossiers = [build_dossier(r).to_dict() for r in records]
    reasons: dict[str, int] = {}
    for d in dossiers:
        for b in d["blockers"]:
            reasons[b] = reasons.get(b, 0) + 1
    return {
        "examined": len(dossiers),
        "qualified": sum(1 for d in dossiers if d["qualified"]),
        "email_provenance": {
            p: sum(1 for d in dossiers if d["email_provenance"] == p)
            for p in (EMAIL_PUBLISHED, EMAIL_DECODED, EMAIL_ABSENT)
        },
        "email_verified": sum(1 for d in dossiers if d["email_verified"]),
        "phone_verified": sum(1 for d in dossiers if d["phone_verified"]),
        "blocker_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "dossiers": dossiers,
    }
