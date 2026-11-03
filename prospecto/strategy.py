"""Stratégie commerciale v3 — hook percutant, prestation unique, démo gratuite.

Implémente docs/strategie-commerciale-v3.md :
- accroche (hook) dès la première phrase, fondée sur une preuve vérifiable ;
- une seule prestation principale (web OU IA/automatisation), pas le catalogue ;
- objet court, naturel, personnalisé et intrigant sans être racoleur ;
- démonstration gratuite limitée, argument central ;
- appel à l'action simple.
Les accroches/objets sur mesure (custom_hook/custom_subject) priment sur les
valeurs générées, pour une personnalisation maximale sans sacrifier les garde-fous.
"""
from __future__ import annotations

from .models import (
    NEED_SITE_WEB,
    NEED_REFONTE,
    NEED_AGENT_IA,
    NEED_AUTOMATISATION,
    EVIDENCE_PUBLIC_NEED,
    EVIDENCE_WEBSITE_GAP,
    Prospect,
    Evidence,
)

# ---------------------------------------------------------------------------
# Démonstration gratuite par besoin (toujours limitée, jamais complète).
# ---------------------------------------------------------------------------
DEMO_OFFERS: dict[str, str] = {
    NEED_SITE_WEB: "une première maquette de page d'accueil personnalisée pour votre entreprise",
    NEED_REFONTE: "un aperçu visuel d'une nouvelle direction graphique pour votre site",
    NEED_AGENT_IA: "la démonstration d'un cas d'usage concret adapté à votre activité",
    NEED_AUTOMATISATION: "une illustration du fonctionnement d'un processus automatisé chez vous",
}

DEMO_TEMPLATE = (
    "Je peux vous préparer gratuitement une première démonstration personnalisée, "
    "sans engagement : {offer}."
)

# ---------------------------------------------------------------------------
# Prestation unique (une seule par email), orientée bénéfice.
# ---------------------------------------------------------------------------
POSITIONING_V3: dict[str, str] = {
    NEED_SITE_WEB: (
        "Je crée des sites web modernes et professionnels, pensés pour valoriser "
        "votre savoir-faire et transformer vos visiteurs en clients."
    ),
    NEED_REFONTE: (
        "Je modernise les sites web pour les rendre plus clairs, plus rapides "
        "et plus convaincants."
    ),
    NEED_AGENT_IA: (
        "Je développe des agents IA qui traitent automatiquement les demandes, "
        "réponses et tâches répétitives."
    ),
    NEED_AUTOMATISATION: (
        "Je mets en place des automatisations qui font gagner du temps sur "
        "les tâches répétitives."
    ),
}

# ---------------------------------------------------------------------------
# Objets v3 : courts, naturels, intrigants mais honnêtes.
# ---------------------------------------------------------------------------
SUBJECTS_V3: dict[str, list[str]] = {
    NEED_SITE_WEB: [
        "Une idée pour {company} ?",
        "{company} : votre site vitrine ?",
        "Et si {company} avait son site ?",
    ],
    NEED_REFONTE: [
        "Une idée pour le site {company_de} ?",
        "{company} : un coup de neuf ?",
        "Votre site {company_de}, en mieux ?",
    ],
    NEED_AGENT_IA: [
        "Un assistant IA pour {company} ?",
        "Une idée pour vos demandes clients",
        "{company} : du temps en plus ?",
    ],
    NEED_AUTOMATISATION: [
        "{company} : automatiser {process} ?",
        "Une idée pour gagner du temps",
        "Gagner du temps chez {company} ?",
    ],
}

# Exemples de réalisations par secteur (fallback, utilisés seulement si pas de
# lien whitelist fourni). Références réelles : prospecto.website, SYNATRAP.
REALISATIONS: dict[str, dict[str, str]] = {
    "batiment": {
        NEED_SITE_WEB: "présentation des prestations et demande de devis en ligne",
        NEED_REFONTE: "mise en avant des réalisations et devis simplifié",
        NEED_AGENT_IA: "tri des demandes de devis et premières réponses",
        NEED_AUTOMATISATION: "confirmations et rappels de rendez-vous",
    },
    "architecture": {
        NEED_SITE_WEB: "portfolio de projets et prise de contact facilitée",
        NEED_REFONTE: "mise en valeur des projets et navigation modernisée",
        NEED_AGENT_IA: "qualification des demandes entrantes",
        NEED_AUTOMATISATION: "suivi automatique des demandes de devis",
    },
    "automobile": {
        NEED_SITE_WEB: "présentation des véhicules et prise de RDV en ligne",
        NEED_REFONTE: "prise de rendez-vous atelier simplifiée",
        NEED_AGENT_IA: "réponse aux demandes d'essai et de devis",
        NEED_AUTOMATISATION: "rappels d'entretien et de rendez-vous",
    },
    "services": {
        NEED_SITE_WEB: "présentation des services et devis en ligne",
        NEED_REFONTE: "parcours de demande de devis simplifié",
        NEED_AGENT_IA: "tri et première réponse aux e-mails entrants",
        NEED_AUTOMATISATION: "traitement automatique des demandes entrantes",
    },
    "commerce": {
        NEED_SITE_WEB: "vitrine des produits et contact direct",
        NEED_REFONTE: "mise en avant des produits et commande simplifiée",
        NEED_AGENT_IA: "réponses aux questions clients fréquentes",
        NEED_AUTOMATISATION: "confirmations de commande et suivi client",
    },
    "restauration": {
        NEED_SITE_WEB: "menu, horaires et réservation en ligne",
        NEED_REFONTE: "réservation et mise en avant de la carte",
        NEED_AGENT_IA: "réponse aux demandes de réservation",
        NEED_AUTOMATISATION: "confirmations et rappels de réservation",
    },
    "sante": {
        NEED_SITE_WEB: "présentation du cabinet et prise de rendez-vous",
        NEED_REFONTE: "prise de rendez-vous et informations patients",
        NEED_AGENT_IA: "orientation des demandes patients",
        NEED_AUTOMATISATION: "rappels de rendez-vous",
    },
    "default": {
        NEED_SITE_WEB: "présentation de l'activité et contact facilité",
        NEED_REFONTE: "design et navigation modernisés",
        NEED_AGENT_IA: "tri des demandes et premières réponses",
        NEED_AUTOMATISATION: "processus répétitifs traités automatiquement",
    },
}
KNOWN_SECTORS = set(REALISATIONS) - {"default"}


def realisation_example(sector: str, need: str) -> str:
    table = REALISATIONS.get(sector, REALISATIONS["default"])
    return table.get(need, "")


def public_need_evidence(prospect: Prospect) -> Evidence | None:
    for ev in prospect.evidences:
        if ev.kind == EVIDENCE_PUBLIC_NEED:
            return ev
    return None


def website_gap_evidences(prospect: Prospect) -> list[Evidence]:
    return [ev for ev in prospect.evidences if ev.kind == EVIDENCE_WEBSITE_GAP]


def de_company(name: str) -> str:
    """« de Quattro » mais « d'Akla » : élision française devant voyelle/h."""
    if name and name[0].lower() in "aàâeéèêëiîïoôuùûyh":
        return f"d'{name}"
    return f"de {name}"


def build_subject(prospect: Prospect) -> str:
    """Objet court : sur mesure si fourni, sinon décliné selon le besoin."""
    if prospect.custom_subject.strip():
        subject = prospect.custom_subject.strip()
        return subject if len(subject) <= 70 else "Une idée pour votre entreprise ?"
    need = prospect.primary_need or NEED_SITE_WEB
    variants = SUBJECTS_V3[need]
    # Variation déterministe basée sur le nom (pas d'aléatoire reproductible cassé).
    idx = sum(ord(c) for c in prospect.company) % len(variants)
    fmt = dict(
        company=prospect.company,
        company_de=de_company(prospect.company),
        process=prospect.process_hint or "certaines tâches",
    )
    subject = variants[idx].format(**fmt)
    if len(subject) > 70:
        subject = variants[0].format(**fmt)
    if len(subject) > 70:
        subject = "Une idée pour votre entreprise ?"
    return subject


def build_hook(prospect: Prospect) -> str:
    """Accroche v3 : spécifique, crédible, fondée sur une preuve.

    Priorité : custom_hook > besoin public > lacune site > processus > neutre.
    Jamais de problème inventé, jamais de fausse urgence ni flatterie.
    """
    if prospect.custom_hook.strip():
        return prospect.custom_hook.strip()

    public = public_need_evidence(prospect)
    if public is not None:
        detail = (public.detail or public.quote).strip()
        return f"J'ai lu votre annonce : {detail}."

    gaps = website_gap_evidences(prospect)
    if gaps and prospect.primary_need in (NEED_REFONTE, NEED_SITE_WEB):
        first = (gaps[0].detail or gaps[0].quote).strip()
        return f"En parcourant votre site ({prospect.domain}), j'ai relevé un point concret : {first}"

    if prospect.primary_need in (NEED_AGENT_IA, NEED_AUTOMATISATION) and prospect.process_hint:
        return (
            f"En découvrant {prospect.company}, j'ai vu que {prospect.process_hint} : "
            "une piste concrète pour vous faire gagner du temps."
        )

    return (
        f"En découvrant {prospect.company}, j'ai identifié une possibilité intéressante "
        "pour développer votre activité."
    )


# Compat ascendante (tests / ancien code).
def build_opening(prospect: Prospect) -> str:
    return build_hook(prospect)
