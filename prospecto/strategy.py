"""Stratégie commerciale v2 : personnalisation intelligente et démo gratuite.

Implémente docs/strategie-commerciale.md :
- première phrase adaptée au besoin réel (besoin public cité en priorité) ;
- une seule prestation principale par email ;
- exemples de réalisations adaptés au secteur ;
- objet décliné de « Une idée pour [Entreprise] ? » ;
- démonstration gratuite limitée selon le besoin.
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
# Démonstration gratuite par besoin (toujours limitée, jamais une réalisation
# complète — docs/strategie-commerciale.md §4).
# ---------------------------------------------------------------------------
DEMO_OFFERS: dict[str, str] = {
    NEED_SITE_WEB: (
        "une première maquette de page d'accueil personnalisée pour votre entreprise"
    ),
    NEED_REFONTE: (
        "un aperçu visuel d'amélioration d'une page clé de votre site"
    ),
    NEED_AGENT_IA: (
        "un exemple concret de fonctionnement adapté à votre activité"
    ),
    NEED_AUTOMATISATION: (
        "une illustration du processus qui pourrait être automatisé chez vous"
    ),
}

DEMO_SENTENCE = (
    "Je vous propose de créer une première démonstration personnalisée, "
    "gratuitement et sans engagement : {demo}."
)

# ---------------------------------------------------------------------------
# Prestation principale (une seule par email) et positionnement.
# ---------------------------------------------------------------------------
POSITIONING: dict[str, str] = {
    NEED_SITE_WEB: (
        "Je crée des sites web modernes et professionnels pour des entreprises "
        "comme la vôtre"
    ),
    NEED_REFONTE: (
        "Je conçois et modernise des sites web pour des entreprises comme la vôtre"
    ),
    NEED_AGENT_IA: (
        "Je crée des agents IA qui automatisent des tâches et font gagner du temps "
        "aux entreprises comme la vôtre"
    ),
    NEED_AUTOMATISATION: (
        "Je mets en place des automatisations qui font gagner du temps "
        "aux entreprises comme la vôtre"
    ),
}

# ---------------------------------------------------------------------------
# Objets : déclinaisons courtes de « Une idée pour [Entreprise] ? ».
# ---------------------------------------------------------------------------
SUBJECTS: dict[str, list[str]] = {
    NEED_SITE_WEB: [
        "Une idée pour {company} ?",
        "Une idée pour votre présence en ligne ?",
    ],
    NEED_REFONTE: [
        "Une idée pour le site {company_de} ?",
        "Une idée pour {company} ?",
    ],
    NEED_AGENT_IA: [
        "Une idée pour gagner du temps chez {company} ?",
        "Une idée pour {company} ?",
    ],
    NEED_AUTOMATISATION: [
        "Une idée pour vos {process} chez {company} ?",
        "Une idée pour gagner du temps chez {company} ?",
    ],
}

# ---------------------------------------------------------------------------
# Exemples de réalisations, adaptés au secteur (1 maximum par email).
# Références réelles : prospecto.website (réalisations présentées) et SYNATRAP
# (agent IA de tri de tickets, projet de Martin — cité, jamais modifié).
# ---------------------------------------------------------------------------
REALISATIONS: dict[str, dict[str, str]] = {
    "batiment": {
        NEED_SITE_WEB: "présentation claire des prestations et demande de devis en ligne",
        NEED_REFONTE: "mise en avant des réalisations et demande de devis simplifiée",
        NEED_AGENT_IA: "tri des demandes de devis et préparation de premières réponses",
        NEED_AUTOMATISATION: "confirmations et rappels de rendez-vous envoyés automatiquement",
    },
    "architecture": {
        NEED_SITE_WEB: "portfolio de projets et prise de contact facilitée",
        NEED_REFONTE: "mise en valeur des projets et navigation modernisée",
        NEED_AGENT_IA: "qualification des demandes entrantes avant réponse",
        NEED_AUTOMATISATION: "suivi automatique des demandes de devis",
    },
    "automobile": {
        NEED_SITE_WEB: "présentation des véhicules et services, prise de RDV en ligne",
        NEED_REFONTE: "prise de rendez-vous atelier simplifiée",
        NEED_AGENT_IA: "réponse aux demandes d'essai et de devis",
        NEED_AUTOMATISATION: "rappels d'entretien et de rendez-vous atelier",
    },
    "services": {
        NEED_SITE_WEB: "présentation des services et demande de devis en ligne",
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
        NEED_AGENT_IA: "réponse aux demandes de réservation et d'événements",
        NEED_AUTOMATISATION: "confirmations et rappels de réservation",
    },
    "sante": {
        NEED_SITE_WEB: "présentation du cabinet et prise de rendez-vous",
        NEED_REFONTE: "prise de rendez-vous et informations patients clarifiées",
        NEED_AGENT_IA: "orientation des demandes patients",
        NEED_AUTOMATISATION: "rappels de rendez-vous",
    },
    "default": {
        NEED_SITE_WEB: "présentation de l'activité et prise de contact facilitée",
        NEED_REFONTE: "design et navigation modernisés, contact simplifié",
        NEED_AGENT_IA: "tri des demandes entrantes et premières réponses préparées",
        NEED_AUTOMATISATION: "processus répétitifs traités automatiquement",
    },
}

# Secteurs connus pour le bonus de qualification.
KNOWN_SECTORS = set(REALISATIONS) - {"default"}


def realisation_example(sector: str, need: str) -> str:
    """Un exemple de réalisation adapté au secteur, ou None si non pertinent."""
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
    """Objet court, décliné selon le besoin principal."""
    need = prospect.primary_need or NEED_SITE_WEB
    variants = SUBJECTS[need]
    # Choix déterministe : variante orientée processus si un processus est observé.
    idx = 0
    if need == NEED_AUTOMATISATION and prospect.process_hint:
        idx = 0
    fmt = dict(
        company=prospect.company,
        company_de=de_company(prospect.company),
        process=prospect.process_hint or "tâches",
    )
    subject = variants[idx].format(**fmt)
    if len(subject) > 70:
        subject = variants[-1].format(**fmt)
    if len(subject) > 70:
        # Repli sans nom d'entreprise : l'objet reste court en toutes circonstances.
        subject = "Une idée pour votre entreprise ?"
    return subject


def build_opening(prospect: Prospect) -> str:
    """Première(s) phrase(s) : au besoin réellement identifié, jamais inventé.

    Priorité 1 : besoin exprimé publiquement → on cite la demande et sa source.
    Priorité 2 : lacunes vérifiées sur le site → constats factuels bornés.
    Sinon : découverte neutre et honnête (pas de problème prétendu).
    """
    public = public_need_evidence(prospect)
    if public is not None:
        detail = public.detail or public.quote
        return f"J'ai vu que {detail}."

    gaps = website_gap_evidences(prospect)
    if gaps and prospect.primary_need in (NEED_REFONTE, NEED_SITE_WEB):
        lines = [
            f"J'ai consulté quelques pages de votre site ({prospect.domain}) ; "
            "voici ce que j'y ai relevé :"
        ]
        for ev in gaps[:3]:
            lines.append(f"— {ev.detail or ev.quote}")
        return "\n\n".join([lines[0], "\n".join(lines[1:])])

    if prospect.primary_need in (NEED_AGENT_IA, NEED_AUTOMATISATION) and prospect.process_hint:
        return (
            f"En découvrant {prospect.company}, j'ai identifié une piste concrète "
            f"autour de {prospect.process_hint}."
        )

    return (
        f"J'ai découvert {prospect.company} et identifié quelques possibilités "
        "pour développer votre activité grâce au web et à l'intelligence artificielle."
    )
