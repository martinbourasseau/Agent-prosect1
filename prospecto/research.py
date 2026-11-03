"""Recherche web : audit factuel de sites (capacité reconstruite et versionnée).

Reproduit les constats utilisés dans les emails du 03/11 matin :
HTTPS, formulaire de contact/devis, bouton d'appel à l'action visible.
Les constats sont bornés aux pages analysées (« sur les pages consultées »)
et ne prétendent jamais à un problème qui n'existe pas.

L'analyse porte sur du HTML déjà récupéré (par l'agent ou un fetch local) :
aucun accès réseau dans ce module, donc testable et sans dépendance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .models import Evidence, EVIDENCE_WEBSITE_GAP

_CTA_WORDS = (
    "devis", "appeler", "appelez", "contactez", "rendez-vous", "rdv",
    "réserver", "reserver", "estimation", "demander une",
)
_FORM_RE = re.compile(r"<form[\s>]", re.IGNORECASE)
_MAILTO_RE = re.compile(r'href=["\']mailto:', re.IGNORECASE)
_TEL_RE = re.compile(r'href=["\']tel:', re.IGNORECASE)
_BUTTON_RE = re.compile(r"<(button|a)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class SiteAudit:
    url: str
    https_ok: bool
    has_contact_form: bool
    has_mailto: bool
    has_tel_link: bool
    has_visible_cta: bool
    gaps: list[str]

    def to_evidences(self, observed_at: str | None = None) -> list[Evidence]:
        observed_at = observed_at or date.today().isoformat()
        return [
            Evidence(
                kind=EVIDENCE_WEBSITE_GAP,
                source_url=self.url,
                quote=gap,
                observed_at=observed_at,
                detail=gap,
            )
            for gap in self.gaps
        ]


def audit_html(html: str, url: str) -> SiteAudit:
    """Audit factuel d'une page HTML. Constats bornés à la page analysée."""
    https_ok = url.lower().startswith("https://")
    has_contact_form = bool(_FORM_RE.search(html))
    has_mailto = bool(_MAILTO_RE.search(html))
    has_tel_link = bool(_TEL_RE.search(html))

    has_visible_cta = False
    for match in _BUTTON_RE.finditer(html):
        text = _TAG_RE.sub(" ", match.group(2)).lower()
        if any(word in text for word in _CTA_WORDS):
            has_visible_cta = True
            break
    # Un lien mailto/tel visible vaut aussi point de contact direct.
    if has_mailto or has_tel_link:
        has_visible_cta = True

    gaps: list[str] = []
    if not https_ok:
        gaps.append(
            "Le site ne s'affichait pas en connexion sécurisée (HTTPS) lors de mon passage."
        )
    if not has_contact_form and not has_mailto:
        gaps.append(
            "Je n'ai trouvé aucun formulaire de contact ou de demande de devis "
            "sur les pages que j'ai ouvertes."
        )
    if not has_visible_cta:
        gaps.append(
            "Aucun bouton bien visible (« demander un devis », « nous appeler ») "
            "n'apparaît sur les pages consultées."
        )

    return SiteAudit(
        url=url,
        https_ok=https_ok,
        has_contact_form=has_contact_form,
        has_mailto=has_mailto,
        has_tel_link=has_tel_link,
        has_visible_cta=has_visible_cta,
        gaps=gaps,
    )
