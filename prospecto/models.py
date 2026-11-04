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

# Types de preuves ajoutés au lot 5 : ils alimentent les trois scores indépendants.
EVIDENCE_SITE_ABSENT = "site_absent"          # aucune présence en ligne exploitable
EVIDENCE_SITE_DOWN = "site_indisponible"      # site hors service / hébergement suspendu
EVIDENCE_SITE_OBSOLETE = "site_obsolete"      # site daté (techno, ergonomie, mobile)
EVIDENCE_PROCESS_MANUAL = "processus_manuel"  # processus administratif répétitif observé
EVIDENCE_JOURNEY_GAP = "parcours_incomplet"   # parcours client cassé ou inachevé

EVIDENCE_KINDS = (
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
    EVIDENCE_SITE_ABSENT, EVIDENCE_SITE_DOWN, EVIDENCE_SITE_OBSOLETE,
    EVIDENCE_PROCESS_MANUAL, EVIDENCE_JOURNEY_GAP,
)

# Niveaux de vérification d'un email (v4) — ne jamais présenter un supposé comme vérifié.
EMAIL_VERIFIED = "verified"                    # vérifié (source fiable / testé)
EMAIL_PUBLIC_UNVERIFIED = "public_unverified"  # public mais non vérifié
EMAIL_PROBABLE = "probable"                    # probable, à vérifier
EMAIL_NONE = "none"                            # aucun email trouvé
EMAIL_VERIFICATIONS = (EMAIL_VERIFIED, EMAIL_PUBLIC_UNVERIFIED, EMAIL_PROBABLE, EMAIL_NONE)

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
        if self.kind not in EVIDENCE_KINDS:
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
    custom_hook: str = ""  # accroche sur mesure (v3) — sinon générée depuis les preuves
    custom_subject: str = ""  # objet sur mesure (v3) — sinon généré depuis le besoin
    example_urls: list[str] = field(default_factory=list)  # liens réalisations (whitelist obligatoire)
    city: str = ""
    department: str = ""
    phone: str = ""
    contact_role: str = ""
    source: str = ""  # source de découverte (plateforme, presse, annuaire…)
    publication_date: str = ""  # date de publication du besoin, si connue
    recommended_service: str = ""  # prestation unique recommandée (formulation bénéfique)
    email_verification: str = EMAIL_PUBLIC_UNVERIFIED  # niveau de vérification de l'email (v4)
    notes: str = ""
    # Suivi de portefeuille (lot 5).
    lot: str = ""                       # campagne / lot de découverte
    discovered_at: str = ""             # date de découverte (ISO)
    email_status: str = ""              # statut du cycle email (préparé, brouillon, rebond…)
    next_action: str = ""               # prochaine action commerciale explicite
    scores: dict[str, Any] = field(default_factory=dict)  # 3 axes indépendants + priorité
    commercial_priority: str = ""       # haute / moyenne / basse / a_approfondir
    email_dns_status: str = ""          # contrôle MX du domaine (voir email_verify)
    phone_verification: str = ""        # niveau de vérification du téléphone
    contact_name_source: str = ""       # URL où le responsable est publié

    @property
    def primary_need(self) -> str | None:
        return self.needs[0] if self.needs else None

    def validate(self) -> list[str]:
        errors = []
        if not self.company:
            errors.append("entreprise sans nom")
        if self.email_verification not in EMAIL_VERIFICATIONS:
            errors.append(f"niveau de vérification email inconnu : {self.email_verification!r}")
        if self.contact_email:
            if not _EMAIL_RE.match(self.contact_email):
                errors.append(f"email de contact invalide : {self.contact_email!r}")
            if self.email_verification == EMAIL_NONE:
                errors.append("email présent mais niveau de vérification 'none'")
        elif self.email_verification != EMAIL_NONE:
            errors.append("aucun email : le niveau de vérification doit être 'none'")
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
    # Métadonnées v4 (variante A/B, référence commerciale, version de message).
    variant: str = ""
    reference_id: str = ""
    example_url: str = ""
    message_version: str = "v3"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
