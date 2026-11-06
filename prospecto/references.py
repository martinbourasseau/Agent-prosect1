"""Bibliothèque de références commerciales (v4).

Charge data/references.json (extensible sans code) et sélectionne automatiquement
la référence la plus pertinente selon le besoin et le secteur du prospect.

Règle d'honnêteté : chaque référence porte un statut de paternité. On n'utilise
que des références activées, et la formulation (claim) reste attributive et vraie.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .models import Prospect, NEED_AGENT_IA, NEED_AUTOMATISATION


@dataclass
class Reference:
    id: str
    name: str
    url: str
    enabled: bool = True
    kind: str = ""
    positioning: str = ""
    visual_identity: str = ""
    structure: str = ""
    features: list[str] = field(default_factory=list)
    sector_tags: list[str] = field(default_factory=list)
    need_tags: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    best_for: str = ""
    authorship_status: str = "owner_declared"
    authorship_note: str = ""
    claim: str = ""
    example_sentence: str = ""
    # Lot 7 : formulation de repli quand la prestation proposée n'est pas un
    # agent IA. Annoncer « Côté agents IA » devant un simple formulaire serait
    # incohérent avec la proposition ; on présente alors la référence pour ce
    # qu'elle est aussi (plateforme, automatisation), sans surenchère.
    example_sentence_alt: str = ""
    added_at: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Reference":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in known})

    def sentence(self, use_alt: bool = False) -> str:
        tpl = self.example_sentence
        if use_alt and self.example_sentence_alt:
            tpl = self.example_sentence_alt
        return (tpl or "Un exemple de réalisation : {url}").format(url=self.url, name=self.name)


def load_references(path: Path | None = None) -> list[Reference]:
    path = path or config.REFERENCES_PATH
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [Reference.from_dict(r) for r in raw.get("references", [])]


# v7 — pertinence réelle d'une référence.
# Jusqu'au lot 8, tout besoin « automatisation » attirait SYNATRAP (+4), y compris
# pour un simple formulaire de devis : les 11 brouillons des lots 6 et 7 citent
# donc une plateforme d'agents IA sans rapport avec la solution proposée.
# Une référence n'est désormais insérée que si elle éclaire la solution retenue.
REFERENCE_RELEVANT_SOLUTIONS = {
    "plateforme_agents_ia": frozenset({"agent_ia"}),
    "site_institutionnel": frozenset({"creation_site", "refonte_site"}),
}


def reference_is_relevant(ref: Reference, prospect: Prospect) -> bool:
    """Une référence n'est utile que si elle illustre la solution proposée.

    Sans solution_type renseigné on reste prudent : aucune référence n'est
    ajoutée plutôt que d'en plaquer une hors sujet.
    """
    solution = (getattr(prospect, "solution_type", "") or "").strip()
    allowed = REFERENCE_RELEVANT_SOLUTIONS.get(ref.kind)
    if allowed is None:
        return False
    return solution in allowed


def select_reference(prospect: Prospect, refs: list[Reference] | None = None) -> Reference | None:
    """Choisit la référence la plus pertinente (besoin d'abord, secteur ensuite).

    - Agents IA / automatisation → SYNATRAP en priorité.
    - Site web / refonte → Groupe Bourasseau en priorité (image pro / institutionnel).
    Score : +3 si le besoin correspond, +1 par tag secteur commun. Aucune → None.
    """
    refs = refs if refs is not None else load_references()
    need = prospect.primary_need
    sector = (prospect.sector or "").lower()
    best, best_score = None, 0
    for ref in refs:
        if not ref.enabled:
            continue
        if not reference_is_relevant(ref, prospect):
            continue
        score = 0
        if need and need in ref.need_tags:
            score += 3
        if sector and sector in [t.lower() for t in ref.sector_tags]:
            score += 1
        # Adéquation forte entre la nature du besoin et le type de référence :
        # site/refonte → site institutionnel ; IA/automatisation → plateforme d'agents.
        if need in ("site_web", "refonte") and ref.kind == "site_institutionnel":
            score += 4
        if need in (NEED_AGENT_IA, NEED_AUTOMATISATION) and ref.kind == "plateforme_agents_ia":
            score += 4
        if score > best_score:
            best, best_score = ref, score
    return best


def reference_by_id(ref_id: str, refs: list[Reference] | None = None) -> Reference | None:
    refs = refs if refs is not None else load_references()
    for r in refs:
        if r.id == ref_id:
            return r
    return None
