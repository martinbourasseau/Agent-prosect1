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

# v7 — jusqu'ici le modèle ne savait exprimer que des manques. Une entreprise
# déjà outillée n'avait donc aucun moyen d'être créditée de ce qui fonctionne,
# et un simple signal de confiance était rangé dans « opportunité sectorielle ».
EVIDENCE_MATURITY = "maturite_existante"      # ce qui est DÉJÀ en place (contre-signal)
EVIDENCE_TRUST = "signal_confiance"           # identité, accréditation, antériorité

EVIDENCE_KINDS = (
    EVIDENCE_PUBLIC_NEED, EVIDENCE_WEBSITE_GAP, EVIDENCE_SECTOR_OPPORTUNITY,
    EVIDENCE_SITE_ABSENT, EVIDENCE_SITE_DOWN, EVIDENCE_SITE_OBSOLETE,
    EVIDENCE_PROCESS_MANUAL, EVIDENCE_JOURNEY_GAP,
    EVIDENCE_MATURITY, EVIDENCE_TRUST,
)

# v8 — les quatre niveaux demandés : besoin exprimé, problème observé, signal
# indirect, opportunité hypothétique. Ils ne se confondent ni avec le type de
# preuve ni avec la fiabilité de la source :
#   * fiabilité  = à quel point la SOURCE est digne de confiance ;
#   * niveau     = à quel point le SIGNAL est direct.
# Un article de presse très fiable peut porter un signal purement indirect.
SIGNAL_EXPRESSED = "exprime"          # l'entreprise ou son responsable le dit
SIGNAL_OBSERVED = "observe"           # problème constaté directement sur la source
SIGNAL_INDIRECT = "indirect"          # indice à combiner, pas un besoin établi
SIGNAL_HYPOTHETICAL = "hypothetique"  # supposition du chercheur

SIGNAL_LEVELS = (SIGNAL_EXPRESSED, SIGNAL_OBSERVED, SIGNAL_INDIRECT, SIGNAL_HYPOTHETICAL)

KIND_DEFAULT_LEVEL = {
    EVIDENCE_PUBLIC_NEED: SIGNAL_EXPRESSED,
    EVIDENCE_WEBSITE_GAP: SIGNAL_OBSERVED,
    EVIDENCE_SITE_ABSENT: SIGNAL_OBSERVED,
    EVIDENCE_SITE_DOWN: SIGNAL_OBSERVED,
    EVIDENCE_SITE_OBSOLETE: SIGNAL_OBSERVED,
    EVIDENCE_PROCESS_MANUAL: SIGNAL_OBSERVED,
    EVIDENCE_JOURNEY_GAP: SIGNAL_OBSERVED,
    EVIDENCE_MATURITY: SIGNAL_OBSERVED,
    EVIDENCE_TRUST: SIGNAL_OBSERVED,
    # Une déduction sectorielle n'a jamais été une observation.
    EVIDENCE_SECTOR_OPPORTUNITY: SIGNAL_INDIRECT,
}

# Niveaux de vérification d'un email (v4) — ne jamais présenter un supposé comme vérifié.
EMAIL_VERIFIED = "verified"                    # vérifié (source fiable / testé)
EMAIL_PUBLIC_UNVERIFIED = "public_unverified"  # public mais non vérifié
EMAIL_PROBABLE = "probable"                    # probable, à vérifier
EMAIL_NONE = "none"                            # aucun email trouvé
EMAIL_VERIFICATIONS = (EMAIL_VERIFIED, EMAIL_PUBLIC_UNVERIFIED, EMAIL_PROBABLE, EMAIL_NONE)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# v7 — diversification des sources. Chaque type porte un niveau de fiabilité par
# défaut : le site officiel de l'entreprise fait foi sur ses propres processus,
# un annuaire ou un agrégateur beaucoup moins.
SOURCE_TYPES = (
    "site_officiel", "annuaire_pro", "registre_public", "page_professionnelle",
    "presse_locale", "appel_projet", "autre",
)
RELIABILITY_LEVELS = ("haute", "moyenne", "faible")
SOURCE_RELIABILITY = {
    "site_officiel": "haute",
    "registre_public": "haute",
    "appel_projet": "haute",
    "page_professionnelle": "moyenne",
    "presse_locale": "moyenne",
    "annuaire_pro": "faible",
    "autre": "faible",
}


@dataclass
class Evidence:
    """Preuve conservée : toute affirmation d'un email doit s'y appuyer."""

    kind: str
    source_url: str
    quote: str
    observed_at: str  # date ISO de consultation de la source
    detail: str = ""  # reformulation factuelle utilisable dans l'email
    # v7 — traçabilité et distinction fait / hypothèse
    source_type: str = "site_officiel"   # voir SOURCE_TYPES
    reliability: str = ""                # haute / moyenne / faible ; déduite si vide
    verified_at: str = ""                # dernière revérification ; défaut observed_at
    observed: bool = True                # False = opportunité supposée, non un fait
    # v8 — force du signal, indépendante du type de preuve et de la fiabilité
    # de la source. Une entreprise qui DIT chercher une solution n'est pas au
    # même niveau qu'un indice repéré dans un article de presse.
    signal_level: str = ""               # voir SIGNAL_LEVELS ; déduit si vide

    def __post_init__(self) -> None:
        if not self.reliability:
            self.reliability = SOURCE_RELIABILITY.get(self.source_type, "moyenne")
        if not self.verified_at:
            self.verified_at = self.observed_at
        if not self.signal_level:
            self.signal_level = KIND_DEFAULT_LEVEL.get(self.kind, SIGNAL_INDIRECT)
        # Une non-observation ne peut jamais être un fait exprimé ou observé.
        if not self.observed and self.signal_level in (SIGNAL_EXPRESSED, SIGNAL_OBSERVED):
            self.signal_level = SIGNAL_HYPOTHETICAL

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
        if self.source_type not in SOURCE_TYPES:
            errors.append(f"type de source inconnu : {self.source_type}")
        if self.reliability not in RELIABILITY_LEVELS:
            errors.append(f"niveau de fiabilité inconnu : {self.reliability}")
        if self.signal_level not in SIGNAL_LEVELS:
            errors.append(f"niveau de signal inconnu : {self.signal_level}")
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
    # Personnalisation v5 (lot 7) : l'accroche énonce le fait vérifiable,
    # l'observation en tire la conséquence concrète pour l'entreprise.
    observation: str = ""
    solution_type: str = ""  # famille de solution retenue (voir personalization)
    # v6 : bénéfice professionnel formulé pour CET interlocuteur. Vérifié à la
    # main, il prime sur l'angle déduit de la fonction.
    benefit: str = ""
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
