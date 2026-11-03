"""Génération d'emails v3 — hook percutant, prestation unique, démo gratuite.

Chaque email :
- accroche spécifique dès la 1re phrase (preuve vérifiable obligatoire) ;
- une seule prestation principale, orientée bénéfice ;
- démonstration gratuite limitée au centre ;
- objet court et naturel ; CTA simple ; opt-out ; signature portfolio ;
- lien d'exemple uniquement s'il est dans la whitelist officielle (data/realisations.json) ;
- très court, naturel, humain — jamais de problème inventé.
"""
from __future__ import annotations

import json
import re

from . import config
from .models import Prospect, GeneratedEmail
from .strategy import (
    DEMO_OFFERS,
    DEMO_TEMPLATE,
    POSITIONING_V3,
    build_subject,
    build_hook,
    public_need_evidence,
    website_gap_evidences,
)


class GenerationError(ValueError):
    """L'email ne respecte pas la stratégie : il ne doit pas être mis en file."""


def _greeting(prospect: Prospect) -> str:
    if prospect.contact_name:
        # Prénom seul pour une salutation naturelle et chaleureuse (TPE/dirigeants).
        first_name = prospect.contact_name.strip().split()[0]
        return f"Bonjour {first_name},"
    return "Bonjour,"


def load_realisations_whitelist() -> set[str]:
    """URLs d'exemples autorisées (transmises par Martin). Vide tant qu'non fournies."""
    path = config.REALISATIONS_PATH
    if not path.exists():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    urls = set()
    for item in raw.get("realisations", []):
        url = item.get("url") if isinstance(item, dict) else item
        if url:
            urls.add(url.strip())
    return urls


def _example_line(prospect: Prospect) -> str:
    """Lien d'exemple pertinent, seulement s'il est whitelisté (anti-mensonge)."""
    if not prospect.example_urls:
        return ""
    whitelist = load_realisations_whitelist()
    approved = [u for u in prospect.example_urls if u.strip() in whitelist]
    if not approved:
        return ""
    # Un seul lien maximum pour ne pas surcharger le message.
    return f"Un exemple de ce que je réalise : {approved[0]}"


def generate_email(prospect: Prospect) -> GeneratedEmail:
    """Génère l'email v3. Lève GenerationError si la stratégie n'est pas respectée."""
    errors = prospect.validate()
    if errors:
        raise GenerationError("prospect invalide : " + " ; ".join(errors))

    need = prospect.primary_need
    if need not in DEMO_OFFERS:
        raise GenerationError(f"besoin principal inconnu : {need!r}")

    # Un lien d'exemple non whitelisté est une erreur (on ne présente rien de faux).
    if prospect.example_urls:
        whitelist = load_realisations_whitelist()
        bad = [u for u in prospect.example_urls if u.strip() not in whitelist]
        if bad:
            raise GenerationError(
                "liens d'exemple non autorisés (whitelist data/realisations.json) : " + ", ".join(bad)
            )

    subject = build_subject(prospect)
    hook = build_hook(prospect)
    positioning = POSITIONING_V3[need]
    demo_offer = prospect.demo_detail.strip() or DEMO_OFFERS[need]
    demo = DEMO_TEMPLATE.format(offer=demo_offer)

    parts = [_greeting(prospect), hook, positioning]
    example = _example_line(prospect)
    if example:
        parts.append(example)
    parts += [demo, config.CTA_V3, config.OPT_OUT_LINE, config.signature()]
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
    """Garde-fous v3 : retourne la liste des violations (vide = conforme)."""
    problems: list[str] = []
    body = email.body
    words = len(re.findall(r"\S+", body))

    if words > config.MAX_BODY_WORDS:
        problems.append(f"corps trop long : {words} mots (max {config.MAX_BODY_WORDS})")
    if words < config.MIN_BODY_WORDS:
        problems.append(f"corps trop court : {words} mots (min {config.MIN_BODY_WORDS})")
    if not email.subject.strip():
        problems.append("objet vide")
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

    # Anti-invention : l'accroche doit s'appuyer sur une preuve du type annoncé.
    if prospect is not None:
        if ("annonce" in body or "votre demande" in body) and public_need_evidence(prospect) is None:
            problems.append("accroche mentionnant une annonce sans preuve public_need")
        if "relevé un point concret" in body and not website_gap_evidences(prospect):
            problems.append("constat de site annoncé sans preuve website_gap")
        if prospect.example_urls:
            whitelist = load_realisations_whitelist()
            if any(u.strip() not in whitelist for u in prospect.example_urls):
                problems.append("lien d'exemple hors whitelist")
    return problems
