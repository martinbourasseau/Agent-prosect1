"""Moteur de messages v4 — variantes commerciales, ton sectoriel, exemples ciblés.

8 approches (variantes) pour tester l'efficacité, sans écraser la v3 :
  public_need   → besoin exprimé publiquement
  demo_site     → démonstration gratuite de site web
  refonte       → refonte / modernisation de site
  automation_ia → possibilité d'automatisation par IA
  short_hook    → message très court, accroche forte
  no_site       → entreprise sans site web
  with_example  → intègre un exemple de site pertinent
  synatrap_ia   → solution IA avec SYNATRAP (si le besoin correspond)

Chaque message : objet naturel, 1re phrase personnalisée, observation réelle,
proposition claire (une seule prestation), exemple si utile, démo gratuite si
pertinente, CTA simple, signature pro, opt-out. Jamais de fausse promesse.
"""
from __future__ import annotations

from . import config
from .models import (
    Prospect, GeneratedEmail,
    NEED_SITE_WEB, NEED_REFONTE, NEED_AGENT_IA, NEED_AUTOMATISATION,
)
from .strategy import (
    DEMO_OFFERS, build_hook, public_need_evidence, de_company,
)
from .references import Reference, load_references, select_reference

# ---------------------------------------------------------------------------
# Variantes : drapeaux de composition + objets.
# ---------------------------------------------------------------------------
VARIANTS = {
    "public_need":   {"example": True,  "demo": True,  "short": False},
    "demo_site":     {"example": True,  "demo": True,  "short": False},
    "refonte":       {"example": True,  "demo": True,  "short": False},
    "automation_ia": {"example": True,  "demo": True,  "short": False},
    "short_hook":    {"example": False, "demo": True,  "short": True},
    "no_site":       {"example": True,  "demo": True,  "short": False},
    "with_example":  {"example": True,  "demo": True,  "short": False},
    "synatrap_ia":   {"example": True,  "demo": True,  "short": False},
}

SUBJECTS_V4: dict[str, list[str]] = {
    "public_need":   ["Votre annonce pour {company}", "{company} : j'ai vu votre demande", "À propos de votre projet {company_de}"],
    "demo_site":     ["Une maquette gratuite pour {company} ?", "{company} : voir votre futur site ?", "Et si vous visualisiez le site {company_de} ?"],
    "refonte":       ["Le site {company_de}, en mieux ?", "{company} : un coup de neuf ?", "Moderniser le site {company_de} ?"],
    "automation_ia": ["{company} : du temps en plus ?", "Automatiser une tâche chez {company} ?", "Une idée pour gagner du temps"],
    "short_hook":    ["Une idée pour {company}", "{company} : 30 secondes ?", "Question rapide, {company}"],
    "no_site":       ["{company} sur Google ?", "Et si {company} avait son site ?", "{company} : votre présence en ligne"],
    "with_example":  ["Un exemple pour {company} ?", "{company} : une référence utile", "De quoi s'inspirer pour {company}"],
    "synatrap_ia":   ["Un agent IA pour {company} ?", "{company} : automatiser avec un agent ?", "Une solution IA pour {company}"],
}

# Proposition unique par besoin, orientée bénéfice.
PROPOSITION_V4: dict[str, str] = {
    NEED_SITE_WEB: "Je crée des sites web professionnels qui valorisent votre activité et transforment vos visiteurs en clients.",
    NEED_REFONTE: "Je modernise les sites web pour les rendre plus clairs, plus rapides et plus convaincants.",
    NEED_AGENT_IA: "Je conçois des agents IA qui traitent automatiquement vos demandes et vos tâches répétitives.",
    NEED_AUTOMATISATION: "Je mets en place des automatisations qui vous font gagner du temps sur les tâches répétitives.",
}

# Queue sectorielle optionnelle (ton adapté au secteur, bénéfice concret).
SECTOR_TAIL: dict[str, str] = {
    "batiment": "de quoi mettre en avant vos chantiers et donner envie de vous demander un devis",
    "architecture": "de quoi valoriser vos projets et faciliter la prise de contact",
    "automobile": "de quoi présenter vos véhicules et simplifier la prise de rendez-vous",
    "restauration": "de quoi donner envie et faciliter la réservation",
    "commerce": "de quoi mettre en avant vos produits et faciliter l'achat",
    "sante": "de quoi rassurer vos patients et simplifier la prise de rendez-vous",
    "services": "de quoi présenter clairement vos services et faciliter la demande de devis",
}

# Démo gratuite : distinction démo limitée / création complète (prestation).
DEMO_SITE_PHRASE = (
    "Je peux vous réaliser gratuitement une première maquette personnalisée de votre futur site, "
    "sans engagement — de quoi visualiser concrètement le résultat avant de décider."
)
DEMO_IA_PHRASE = (
    "Je peux vous montrer gratuitement une démonstration concrète de la solution envisagée, "
    "sans engagement, sur un cas réel de votre activité."
)

CTA_SIMPLE = "Seriez-vous ouvert à un court échange pour en parler ?"
CTA_DEMO = "Cela vous dirait de la découvrir ?"

# Lot 6 : trois formulations d'appel à l'action, toutes aussi simples et sans
# engagement, pour que deux messages d'un même lot ne se terminent pas de la
# même façon. Le choix est déterministe (même entreprise -> même CTA) afin que
# la régénération d'un message reste reproductible.
CTA_DEMO_VARIANTS = (
    "Cela vous dirait de la découvrir ?",
    "Souhaitez-vous que je vous montre cela sur un cas concret de votre activité ?",
    "Un échange de quinze minutes vous conviendrait-il pour voir à quoi cela ressemblerait ?",
)


def select_cta_demo(prospect: Prospect) -> str:
    """Choisit un CTA stable pour cette entreprise (rotation déterministe)."""
    key = prospect.company or prospect.contact_email or ""
    return CTA_DEMO_VARIANTS[sum(ord(c) for c in key) % len(CTA_DEMO_VARIANTS)]


def applicable_variants(prospect: Prospect) -> list[str]:
    """Variantes pertinentes pour ce prospect (pour rotation A/B)."""
    need = prospect.primary_need
    out: list[str] = []
    if public_need_evidence(prospect) is not None:
        out.append("public_need")
    if need in (NEED_AGENT_IA, NEED_AUTOMATISATION):
        out += ["synatrap_ia", "automation_ia"]
    if need == NEED_REFONTE:
        out.append("refonte")
    if need == NEED_SITE_WEB:
        out.append("no_site" if not prospect.website else "demo_site")
    out += ["with_example", "short_hook"]
    # dédoublonne en gardant l'ordre
    seen, uniq = set(), []
    for v in out:
        if v not in seen:
            seen.add(v); uniq.append(v)
    return uniq or ["demo_site"]


def select_variant(prospect: Prospect, override: str = "") -> str:
    if override and override in VARIANTS:
        return override
    need = prospect.primary_need
    if public_need_evidence(prospect) is not None:
        return "public_need"
    if need in (NEED_AGENT_IA, NEED_AUTOMATISATION):
        return "synatrap_ia"
    if need == NEED_REFONTE:
        return "refonte"
    if need == NEED_SITE_WEB:
        return "no_site" if not prospect.website else "demo_site"
    return "demo_site"


def _subject(prospect: Prospect, variant: str) -> str:
    if prospect.custom_subject.strip():
        s = prospect.custom_subject.strip()
        return s if len(s) <= config.MAX_SUBJECT_CHARS else "Une idée pour votre entreprise ?"
    variants = SUBJECTS_V4.get(variant, SUBJECTS_V4["demo_site"])
    idx = sum(ord(c) for c in prospect.company) % len(variants)
    fmt = dict(company=prospect.company, company_de=de_company(prospect.company))
    subject = variants[idx].format(**fmt)
    if len(subject) > config.MAX_SUBJECT_CHARS:
        subject = "Une idée pour votre entreprise ?"
    return subject


def _proposition(prospect: Prospect) -> str:
    need = prospect.primary_need or NEED_SITE_WEB
    base = prospect.recommended_service.strip() or PROPOSITION_V4[need]
    # Si la prestation recommandée commence en minuscule, on en fait une phrase complète.
    if base and base[0].islower():
        base = "Je peux vous proposer " + base
    # Queue sectorielle (bénéfice web) uniquement pour les besoins web, sans prestation sur mesure.
    tail = SECTOR_TAIL.get((prospect.sector or "").lower(), "")
    if tail and need in (NEED_SITE_WEB, NEED_REFONTE) and not prospect.recommended_service.strip():
        base = base.rstrip(".") + " — " + tail + "."
    if base and base[-1] not in ".!?":
        base += "."
    return base


def _demo_phrase(prospect: Prospect) -> str:
    """Phrase de démonstration.

    Lot 6 — correction : le détail de démonstration researched était ignoré dès
    que le besoin principal était « automatisation » ou « agent IA », ce qui
    produisait une phrase générique identique pour tous ces prospects. Le détail
    personnalisé prime désormais quel que soit l'axe ; les phrases génériques ne
    servent plus que de repli.
    """
    detail = prospect.demo_detail.strip()
    if detail:
        return (
            "Je peux vous préparer gratuitement une première démonstration personnalisée, "
            f"sans engagement : {detail}."
        )
    if prospect.primary_need in (NEED_AGENT_IA, NEED_AUTOMATISATION):
        return DEMO_IA_PHRASE
    return DEMO_SITE_PHRASE


_HONORIFICS = {"dr", "docteur", "m", "mr", "mme", "mlle", "monsieur", "madame", "maitre", "maître", "me"}


def _greeting(prospect: Prospect) -> str:
    if prospect.contact_name:
        tokens = prospect.contact_name.strip().split()
        # Ignore les civilités en tête (Dr, M., Mme...) pour ne pas saluer « Bonjour Dr, ».
        while tokens and tokens[0].lower().rstrip(".") in _HONORIFICS:
            tokens = tokens[1:]
        if tokens:
            return f"Bonjour {tokens[0]},"
    return "Bonjour,"


def compose_email(
    prospect: Prospect,
    variant: str = "",
    reference: Reference | None = None,
) -> GeneratedEmail:
    """Compose un email v4. Lève ValueError si le prospect est invalide."""
    errors = prospect.validate()
    if errors:
        raise ValueError("prospect invalide : " + " ; ".join(errors))

    variant = select_variant(prospect, variant)
    flags = VARIANTS[variant]
    need = prospect.primary_need or NEED_SITE_WEB

    # Référence : fournie explicitement, sinon sélection automatique.
    refs = load_references()
    if reference is None and flags["example"]:
        reference = select_reference(prospect, refs)

    subject = _subject(prospect, variant)
    hook = build_hook(prospect)
    proposition = _proposition(prospect)

    parts = [_greeting(prospect), hook]
    if not flags["short"]:
        parts.append(proposition)
    else:
        # Version courte : proposition condensée en une ligne.
        parts.append(PROPOSITION_V4[need])

    example_url = ""
    if flags["example"] and reference is not None and reference.enabled:
        parts.append(reference.sentence())
        example_url = reference.url

    if flags["demo"]:
        parts.append(_demo_phrase(prospect))

    parts.append(select_cta_demo(prospect) if flags["demo"] else CTA_SIMPLE)
    parts.append(config.OPT_OUT_LINE)
    parts.append(config.signature())
    body = "\n\n".join(parts) + "\n"

    return GeneratedEmail(
        to=prospect.contact_email,
        subject=subject,
        body=body,
        company=prospect.company,
        need=need,
        evidence_sources=[ev.source_url for ev in prospect.evidences],
        variant=variant,
        reference_id=reference.id if reference else "",
        example_url=example_url,
        message_version="v4",
    )


def check_email_v4(email: GeneratedEmail, prospect: Prospect | None = None) -> list[str]:
    """Garde-fous v4. Retourne la liste des violations (vide = conforme)."""
    import re
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
    # Argument démo gratuite (maquette ou démonstration), toujours sans engagement.
    if not any(w in body for w in ("démonstration", "maquette")):
        problems.append("argument central manquant : démonstration / maquette")
    if not any(w in body for w in ("gratuitement", "gratuite")):
        problems.append("démonstration non annoncée comme gratuite")
    if "sans engagement" not in body:
        problems.append("mention « sans engagement » manquante")
    if "ne pas me relancer" not in body:
        problems.append("opt-out manquant")
    if config.PORTFOLIO_URL not in body:
        problems.append("signature portfolio manquante")
    if "**" in body or "__" in body:
        problems.append("markdown dans un email texte brut")
    lowered = body.lower()
    for forbidden in config.FORBIDDEN_PROMISES:
        if forbidden in lowered:
            problems.append(f"promesse interdite : {forbidden}")
    # Honnêteté de l'exemple : l'URL doit venir de la bibliothèque de références.
    if email.example_url:
        refs = load_references()
        if not any(r.url == email.example_url and r.enabled for r in refs):
            problems.append(f"exemple hors bibliothèque de références : {email.example_url}")
    # Anti-invention : un hook « annonce » doit reposer sur une preuve publique.
    if prospect is not None and "J'ai lu votre annonce" in body:
        if public_need_evidence(prospect) is None:
            problems.append("hook « annonce » sans besoin public prouvé")
    # Identité expéditeur : orthographe exacte imposée, aucune variante tolérée.
    if "boisseau" in lowered:
        problems.append("identité expéditeur incorrecte : variante orthographique interdite")
    if config.SENDER_NAME not in body:
        problems.append(f"signature expéditeur manquante ou incorrecte (attendu : {config.SENDER_NAME})")
    return problems
