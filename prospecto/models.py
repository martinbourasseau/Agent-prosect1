"""Modèles de données : preuves, prospects, emails générés."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any

# Types de besoins (un seul besoin principal par email)
NEED_SITE_WEB = "site_web"          # création de site (pas de site exploitable)
NEED_REFONTE = "refonte"            # site existant à améliorer (lacunes vérifiées)
NEED_AGENT_IA = "agent_ia"          # assistant IA (tri, réponses, comptes rendus…)
NEED_AUTOMATISATION = "automatisation"  # processus répétitif à automatiser

NEEDS = (NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION)

# Types de preuves
EVIDENCE_PUBLIC_NEED = "public_need"        # besoin exprimé publiquement (priorité 1)
EVIDENCE_WEBSITE_GAP = "website_gap"        # lacune vérifiée sur le site (priorité 2)
EVIDENCE_SECTOR_OPPORTUNITY = "sector_opportunity"  # opportunité sectorielle (priorité 3)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Evidence:
    """Preuve conservée : toute affirmation d'un email doit s'y appuyer."""

    kind: str
    source_url: str
    quote: str
    observed_at: str  # date ISO d'observation
    detail: str = ""  # reformulation factuelle utilisable dans l'email

    def validate(self) -> list[str]:
        errors = []
        if self.kind not in (
            EVIDENCE_PUBLIC_NEED,
            EVIDENCE_WEBSITE_GAP,
            EVIDENCE_SECTOR_OPPORTUNITY,
        ):
            errors.append(f"type de preuve inconnu : {self.kind}")
        if not self.source_url:
            errors.append("preuve sans source URL")
        if not self.quote:
            errors.append("preuve sans extrait cité")
        if not self.observed_at:
            errors.append("preuve sans date d'observation")
        return errors


@dataclass
class Prospect:
    """Entreprise prospecte, avec besoins identifiés et preuves."""

    company: str
    domain: str
    contact_email: str
    sector: str
    needs: list[str] = field(default_factory=list)
    evidences: list[Evidence] = field(default_factory=list)
    location: str = ""
    contact_name: str = ""  # prénom du contact, seulement s'il est connu avec certitude
    website: str = ""
    process_hint: str = ""  # processus concret observé (devis, RDV, e-mails entrants…)
    demo_detail: str = ""  # précision optionnelle du livrable limité de la démo gratuite
    notes: str = ""

    @property
    def primary_need(self) -> str | None:
        return self.needs[0] if self.needs else None

    def validate(self) -> list[str]:
        errors = []
        if not self.company:
            errors.append("entreprise sans nom")
        if not _EMAIL_RE.match(self.contact_email or ""):
            errors.append(f"email de contact invalide : {self.contact_email!r}")
        if not self.needs:
            errors.append("aucun besoin identifié")
        for need in self.needs:
            if need not in NEEDS:
                errors.append(f"besoin inconnu : {need}")
        if not self.evidences:
            errors.append("aucune preuve conservée")
        for ev in self.evidences:
            errors.extend(ev.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Prospect":
        data = dict(raw)
        data["evidences"] = [Evidence(**e) for e in data.get("evidences", [])]
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class GeneratedEmail:
    """Email personnalisé, prêt pour la file de validation (jamais envoyé directement)."""

    to: str
    subject: str
    body: str
    company: str
    need: str
    evidence_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
