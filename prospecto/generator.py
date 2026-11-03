"""Génération d'emails personnalisés — stratégie v2, avec garde-fous.

Chaque email :
- adapte la première phrase au besoin réel (preuve obligatoire) ;
- propose une seule prestation principale ;
- cite au plus un exemple de réalisation adapté au secteur ;
- décline l'objet « Une idée pour [Entreprise] ? » ;
- place la démonstration gratuite limitée au centre ;
- reste court, naturel, professionnel, avec opt-out ;
- n'invente jamais de problème (les constats viennent des preuves).
"""
from __future__ import annotations

import re

from . import config
from .models import (
    Prospect,
    GeneratedEmail,
    NEED_SITE_WEB,
    NEED_REFONTE,
    NEED_AGENT_IA,
    NEED_AUTOMATISATION,
)
from .strategy import (
    DEMO_OFFERS,
    DEMO_SENTENCE,
    POSITIONING,
    build_subject,
    build_opening,
    realisation_example,
    public_need_evidence,
)

CTA_QUESTION = "Est-ce que cela pourrait vous intéresser ?"


class GenerationError(ValueError):
    """L'email ne respecte pas la stratégie : il ne doit pas être mis en file."""


def _greeting(prospect: Prospect) -> str:
    if prospect.contact_name:
        return f"Bonjour {prospect.contact_name},"
    return "Bonjour,"


def _positioning_sentence(prospect: Prospect) -> str:
    need = prospect.primary_need or NEED_SITE_WEB
    base = POSITIONING[need]
    example = realisation_example(prospect.sector, need)
    if example:
        return f"{base} : {example}."
    return f"{base}."


def generate_email(prospect: Prospect) -> GeneratedEmail:
    """Génère l'email v2. Lève GenerationError si la stratégie n'est pas respectée."""
    errors = prospect.validate()
    if errors:
        raise GenerationError("prospect invalide : " + " ; ".join(errors))

    need = prospect.primary_need
    if need not in DEMO_OFFERS:
        raise GenerationError(f"besoin principal inconnu : {need!r}")

    subject = build_subject(prospect)
    opening = build_opening(prospect)
    positioning = _positioning_sentence(prospect)
    demo = DEMO_SENTENCE.format(demo=DEMO_OFFERS[need])

    parts = [
        _greeting(prospect),
        opening,
        positioning,
        demo,
        CTA_QUESTION,
        config.OPT_OUT_LINE,
        config.signature(),
    ]
    body = "\n\n".join(parts) + "\n"

    email = GeneratedEmail(
        to=prospect.contact_email,
        subject=subject,
        body=body,
        company=prospect.company,
        need=need,
        evidence_sources=[ev.source_url for ev in prospect.evidences],
    )
    problems = check_email(email, prospect)
    if problems:
        raise GenerationError(" ; ".join(problems))
    return email


def check_email(email: GeneratedEmail, prospect: Prospect | None = None) -> list[str]:
    """Garde-fous : retourne la liste des violations (vide = conforme)."""
    problems: list[str] = []
    body = email.body
    words = len(re.findall(r"\S+", body))

    if words > config.MAX_BODY_WORDS:
        problems.append(f"corps trop long : {words} mots (max {config.MAX_BODY_WORDS})")
    if words < config.MIN_BODY_WORDS:
        problems.append(f"corps trop court : {words} mots (min {config.MIN_BODY_WORDS})")
    if len(email.subject) > config.MAX_SUBJECT_CHARS:
        problems.append(f"objet trop long : {len(email.subject)} caractères")
    if "démonstration" not in body:
        problems.append("argument central manquant : démonstration")
    if "gratuitement" not in body and "gratuite" not in body:
        problems.append("démonstration non annoncée comme gratuite")
    if "sans engagement" not in body:
        problems.append("mention « sans engagement » manquante")
    if "ne pas me relancer" not in body:
        problems.append("opt-out manquant")
    if "**" in body or "__" in body:
        problems.append("markdown dans un email texte brut")
    lowered = body.lower()
    for forbidden in config.FORBIDDEN_PROMISES:
        if forbidden in lowered:
            problems.append(f"promesse interdite : {forbidden}")
    if config.PORTFOLIO_URL not in body:
        problems.append("portfolio absent de la signature")
    if "Une idée pour" not in email.subject and "idée" not in email.subject.lower():
        problems.append("objet non conforme à la référence « Une idée pour… ? »")

    # Anti-invention : si l'ouverture annonce des constats, des preuves doivent exister.
    if prospect is not None and "voici ce que j'y ai relevé" in body:
        from .strategy import website_gap_evidences

        if not website_gap_evidences(prospect):
            problems.append("constats annoncés sans preuve website_gap")
    return problems
