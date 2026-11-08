"""Planificateur de recherche — phase 10, section E.

Trois manques de `sources.plan_queries()` sont comblés ici :

1. **Aucune mémoire des requêtes.** Le registre d'exploration garde les
   entreprises examinées, pas les recherches menées : la même requête pouvait
   être relancée indéfiniment. `SearchHistory` conserve chaque piste exécutée,
   sa date, son lot et ce qu'elle a rapporté.

2. **Aucune performance par source.** Les familles de sources tournaient modulo
   le catalogue : une source qui n'avait jamais rien donné comptait autant
   qu'une source ayant produit des prospects qualifiés. Le rendement observé
   pilote désormais l'ordre, avec un lissage qui évite de sur-réagir à un
   seul coup de chance.

3. **Une couverture mesurée en départements seulement.** Cinquante-et-un
   départements pouvaient tous appartenir aux mêmes trois régions. La
   couverture est désormais suivie par région : c'est l'unité qui garantit
   une exploration réellement nationale.

Le planificateur ne tire rien au hasard non reproductible : la rotation dérive
de l'historique, donc deux appels successifs diffèrent, mais un même état
redonne le même plan (tests possibles).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config
from .sources import (
    SECTOR_POOL, TERRITORY_POOL, SOURCE_CATALOGUE, SOURCE_BY_TYPE,
    ExplorationLedger, coverage, _norm,
)

SEARCH_HISTORY_PATH = config.DATA_DIR / "history" / "search-history.json"

# Découpage administratif français. Sert à mesurer l'étalement de la couverture,
# pas à restreindre la recherche : toute région reste explorable.
REGIONS: dict[str, tuple[str, ...]] = {
    "Auvergne-Rhône-Alpes": ("01", "03", "07", "15", "26", "38", "42", "43", "63",
                             "69", "73", "74"),
    "Bourgogne-Franche-Comté": ("21", "25", "39", "58", "70", "71", "89", "90"),
    "Bretagne": ("22", "29", "35", "56"),
    "Centre-Val de Loire": ("18", "28", "36", "37", "41", "45"),
    "Corse": ("2A", "2B"),
    "Grand Est": ("08", "10", "51", "52", "54", "55", "57", "67", "68", "88"),
    "Hauts-de-France": ("02", "59", "60", "62", "80"),
    "Île-de-France": ("75", "77", "78", "91", "92", "93", "94", "95"),
    "Normandie": ("14", "27", "50", "61", "76"),
    "Nouvelle-Aquitaine": ("16", "17", "19", "23", "24", "33", "40", "47", "64",
                           "79", "86", "87"),
    "Occitanie": ("09", "11", "12", "30", "31", "32", "34", "46", "48", "65",
                  "66", "81", "82"),
    "Pays de la Loire": ("44", "49", "53", "72", "85"),
    "Provence-Alpes-Côte d'Azur": ("04", "05", "06", "13", "83", "84"),
}
DEPT_TO_REGION = {d: r for r, depts in REGIONS.items() for d in depts}

# Une piste qui cherche un besoin déjà publié vaut mieux qu'une piste qui
# espère en déduire un. Ces familles portent la section « opportunités publiées ».
# Prior du rendement : taux de base et nombre d'observations virtuelles.
PRIOR_RATE = 0.15
PRIOR_STRENGTH = 8

EXPRESSED_NEED_SOURCES = ("appel_projet", "presse_locale")
# Ces requêtes ont d'abord été testées sans exclusion : elles ne ramenaient QUE
# des agences web vendant la prestation ( Corse : 3 agences, 0 prospect). Le
# bruit est structurel, pas accidentel — les agences optimisent précisément ces
# formulations. Les exclusions et le filtre négatif sont donc obligatoires.
NEED_QUERY_EXCLUSIONS = (
    '-agence -"agence web" -freelance -prestataire -développeur -developpeur '
    '-"création de site" -"creation de site" -refonte -devis-gratuit -tarifs'
)
NEED_QUERIES: tuple[str, ...] = (
    "\"nous recherchons quelqu'un\" site internet {city}",
    '"notre site est obsolète" {city}',
    "\"nous n'avons pas de site\" {city}",
    '"appel à candidatures" numérique {city}',
    '"nous souhaitons automatiser" {city}',
    '"nous cherchons un prestataire" {city}',
)


def region_of(department: str) -> str:
    return DEPT_TO_REGION.get(str(department).strip(), "hors métropole")


def fingerprint(query: str) -> str:
    """Identité d'une requête, insensible à la casse et aux espaces superflus."""
    return " ".join(_norm(query).split())


# ---------------------------------------------------------------------------
# Mémoire des recherches
# ---------------------------------------------------------------------------
@dataclass
class SearchRecord:
    query: str
    sector: str = ""
    department: str = ""
    source_type: str = ""
    lot: str = ""
    executed_at: str = ""
    examined: int = 0
    retained: int = 0
    qualified: int = 0
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SearchHistory:
    """Journal persistant des pistes de recherche exécutées."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or SEARCH_HISTORY_PATH
        self.entries: list[dict[str, Any]] = []
        self.updated_at = ""
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = raw.get("entries", [])
            self.updated_at = raw.get("updated_at", "")

    def already_run(self, query: str) -> bool:
        key = fingerprint(query)
        return any(fingerprint(e.get("query", "")) == key for e in self.entries)

    def record(self, query: str, **kw: Any) -> dict[str, Any]:
        """Trace une piste. Ne dédoublonne pas : l'appelant teste `already_run`."""
        entry = SearchRecord(
            query=query,
            executed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **{k: v for k, v in kw.items() if k in SearchRecord.__dataclass_fields__
               and k not in ("query", "executed_at")},
        ).to_dict()
        self.entries.append(entry)
        return entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.path.write_text(json.dumps(
            {"updated_at": self.updated_at, "count": len(self.entries),
             "entries": self.entries}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    def stats(self) -> dict[str, Any]:
        by_source: dict[str, dict[str, int]] = {}
        for e in self.entries:
            row = by_source.setdefault(e.get("source_type", "?"),
                                       {"queries": 0, "examined": 0,
                                        "retained": 0, "qualified": 0})
            row["queries"] += 1
            for k in ("examined", "retained", "qualified"):
                row[k] += int(e.get(k, 0) or 0)
        return {
            "queries": len(self.entries),
            "distinct_queries": len({fingerprint(e.get("query", "")) for e in self.entries}),
            "by_source": by_source,
            "departments": sorted({e.get("department", "") for e in self.entries
                                   if e.get("department")}),
            "regions": sorted({region_of(e["department"]) for e in self.entries
                               if e.get("department")}),
        }


# ---------------------------------------------------------------------------
# Rendement des sources
# ---------------------------------------------------------------------------
@dataclass
class SourcePerformance:
    """Ce qu'une famille de sources a réellement produit.

    `yield_score` est une moyenne a posteriori : on ajoute PRIOR_STRENGTH
    observations virtuelles au taux PRIOR_RATE avant de calculer le ratio.
    Sans cela, une source 1/1 (0,43) écrasait une source 12/40 (0,29) : un seul
    coup de chance décidait de la stratégie. Avec un prior de 8, il faut
    environ huit observations pour que le taux constaté l'emporte, et une
    source jamais essayée (0,15) reste préférée à une source mauvaise prouvée
    (31 examens, 0 qualifié -> 0,03) sans être préférée à une bonne source
    prouvée (12 examens, 4 qualifiés -> 0,26).
    """

    source_type: str
    examined: int = 0
    retained: int = 0
    qualified: int = 0
    queries: int = 0

    @property
    def qualification_rate(self) -> float:
        return self.qualified / self.examined if self.examined else 0.0

    @property
    def yield_score(self) -> float:
        return ((self.qualified + PRIOR_STRENGTH * PRIOR_RATE)
                / (self.examined + PRIOR_STRENGTH))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["qualification_rate"] = round(self.qualification_rate, 4)
        d["yield_score"] = round(self.yield_score, 4)
        return d


def source_performance(ledger: ExplorationLedger,
                       records: Iterable[dict[str, Any]],
                       history: SearchHistory | None = None) -> list[SourcePerformance]:
    """Classe les familles de sources d'après les résultats constatés.

    Une entreprise est « qualifiée » si elle a été retenue ET si le CRM lui
    reconnaît une adresse exploitable : une retenue sans coordonnées vérifiées
    n'a pas encore produit de prospect.
    """
    crm = list(records)
    by_domain = {_norm(r.get("domain", "")): r for r in crm if r.get("domain")}
    by_company = {_norm(r.get("company", "")): r for r in crm if r.get("company")}

    perf = {s.type: SourcePerformance(s.type) for s in SOURCE_CATALOGUE}
    for e in ledger.entries:
        row = perf.setdefault(e.get("source_type", "autre"),
                              SourcePerformance(e.get("source_type", "autre")))
        row.examined += 1
        if e.get("decision") == "retenue":
            row.retained += 1
            rec = (by_domain.get(_norm(e.get("domain", "")))
                   or by_company.get(_norm(e.get("company", ""))))
            if rec and rec.get("email") and rec.get("email_verification") not in ("none", "", None):
                row.qualified += 1
    if history is not None:
        for q, row in history.stats()["by_source"].items():
            perf.setdefault(q, SourcePerformance(q)).queries = row["queries"]
    return sorted(perf.values(), key=lambda p: (-p.yield_score, -p.examined, p.source_type))


# ---------------------------------------------------------------------------
# Couverture nationale
# ---------------------------------------------------------------------------
def territorial_coverage(records: Iterable[dict[str, Any]],
                         ledger: ExplorationLedger | None = None) -> dict[str, Any]:
    """Départements et régions réellement travaillés, pool compris."""
    cov = coverage(records)
    depts = set(cov.departments)
    if ledger is not None:
        depts.update(str(e.get("department", "")).strip() for e in ledger.entries
                     if e.get("department"))
    regions = {region_of(d) for d in depts}
    regions.discard("hors métropole")
    return {
        "departments": sorted(depts),
        "department_count": len(depts),
        "regions": sorted(regions),
        "region_count": len(regions),
        "regions_total": len(REGIONS),
        "unexplored_regions": sorted(set(REGIONS) - regions),
        "by_region": {r: sorted(d for d in depts if region_of(d) == r)
                      for r in sorted(regions)},
    }


# ---------------------------------------------------------------------------
# Planification
# ---------------------------------------------------------------------------
@dataclass
class PlannedQuery:
    query: str
    sector: str
    keywords: str
    department: str
    city: str
    region: str
    source_type: str
    track: str                      # "besoin_exprime" ou "exploration"
    rationale: str = ""
    priority: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SearchPlanner:
    """Propose les prochaines recherches, sans répéter ni s'enfermer."""

    def __init__(self, records: Iterable[dict[str, Any]],
                 ledger: ExplorationLedger | None = None,
                 history: SearchHistory | None = None) -> None:
        self.records = list(records)
        self.ledger = ledger if ledger is not None else ExplorationLedger()
        self.history = history if history is not None else SearchHistory()
        self.coverage = territorial_coverage(self.records, self.ledger)
        self.performance = source_performance(self.ledger, self.records, self.history)

    # -- secteurs ---------------------------------------------------------
    def fresh_sectors(self) -> list[tuple[str, str]]:
        """Secteurs dont aucun terme significatif n'a déjà été travaillé."""
        from .opportunity import normalize
        seen: set[str] = set()
        for sector in coverage(self.records).sectors:
            raw = normalize(sector).replace("_", " ").replace("-", " ")
            seen.update(w for w in raw.split() if len(w) > 4)
        seen.update(self.ledger.examined_sector_terms())
        fresh = []
        for label, keywords in SECTOR_POOL:
            words = {w for w in normalize(label).replace("_", " ").replace("-", " ").split()
                     if len(w) > 4}
            if not (words & seen):
                fresh.append((label, keywords))
        return fresh or list(SECTOR_POOL)

    # -- territoires ------------------------------------------------------
    def ranked_territories(self) -> list[tuple[str, str]]:
        """Départements jamais touchés d'abord, régions peu couvertes ensuite.

        À égalité, l'ordre tourne selon la taille de l'historique : deux plans
        successifs ne retombent pas sur les mêmes préfectures.
        """
        touched = set(self.coverage["departments"])
        per_region = {r: len(ds) for r, ds in self.coverage["by_region"].items()}
        offset = len(self.history.entries)
        scored = []
        for i, (dept, city) in enumerate(TERRITORY_POOL):
            region = region_of(dept)
            novelty = 0 if dept in touched else 2
            spread = 1 / (1 + per_region.get(region, 0))
            rotation = ((i + offset) % len(TERRITORY_POOL)) / len(TERRITORY_POOL)
            scored.append((-(novelty + spread + 0.3 * rotation), dept, city))
        scored.sort()
        return [(d, c) for _, d, c in scored]

    # -- sources ----------------------------------------------------------
    def ranked_sources(self) -> list[str]:
        return [p.source_type for p in self.performance if p.source_type in SOURCE_BY_TYPE]

    # -- plan -------------------------------------------------------------
    def plan(self, count: int = 12, expressed_share: float = 0.4) -> list[PlannedQuery]:
        """Construit `count` pistes inédites, needs-first puis exploration.

        `expressed_share` réserve une part du plan aux besoins déjà publiés :
        c'est la leçon de l'audit, où les demandes explicites avec budget
        étaient les meilleures affaires du portefeuille et les moins bien
        notées.
        """
        sectors = self.fresh_sectors()
        territories = self.ranked_territories()
        sources = self.ranked_sources()
        perf = {p.source_type: p.yield_score for p in self.performance}
        offset = len(self.history.entries)
        want_needs = max(1, int(round(count * expressed_share)))
        out: list[PlannedQuery] = []
        used_queries: set[str] = set()

        # 1. Besoins publiés. On balaie les territoires les moins explorés.
        for i in range(len(territories) * len(NEED_QUERIES)):
            if len(out) >= want_needs:
                break
            dept, city = territories[i % len(territories)]
            template = NEED_QUERIES[(i + offset) % len(NEED_QUERIES)]
            query = template.format(city=city) + " " + NEED_QUERY_EXCLUSIONS
            key = fingerprint(query)
            if key in used_queries or self.history.already_run(query):
                continue
            used_queries.add(key)
            source = EXPRESSED_NEED_SOURCES[i % len(EXPRESSED_NEED_SOURCES)]
            out.append(PlannedQuery(
                query=query, sector="besoin exprimé publiquement", keywords="",
                department=dept, city=city, region=region_of(dept),
                source_type=source, track="besoin_exprime",
                rationale=("besoin déjà publié : signal de niveau exprimé, "
                           f"territoire {dept} "
                           + ("jamais exploré" if dept not in self.coverage["departments"]
                              else "peu couvert")),
                priority=round(2.0 + perf.get(source, 0.15), 4),
            ))

        # 2. Exploration de secteurs et territoires neufs, sources performantes.
        for i in range(len(sectors) * len(territories) * len(sources)):
            if len(out) >= count:
                break
            # Pas premiers entre eux : secteur, territoire et source avancent à
            # des rythmes différents. Un même plan balaie ainsi plusieurs
            # départements au lieu d'épuiser un territoire avant d'en changer.
            label, keywords = sectors[(i * 5 + offset) % len(sectors)]
            dept, city = territories[(i + offset) % len(territories)]
            source = sources[(i * 3 + offset) % len(sources)]
            suffix = {
                "site_officiel": "site officiel contact",
                "annuaire_pro": "annuaire professionnel",
                "registre_public": "siret adresse entreprise",
                "page_professionnelle": "page professionnelle",
                "presse_locale": "article presse locale entreprise",
                "appel_projet": "appel à projets demande de prestation",
                "autre": "catalogue tarifs",
            }.get(source, "contact")
            query = f"{keywords} {city} {suffix}"
            key = fingerprint(query)
            if key in used_queries or self.history.already_run(query):
                continue
            used_queries.add(key)
            out.append(PlannedQuery(
                query=query, sector=label, keywords=keywords,
                department=dept, city=city, region=region_of(dept),
                source_type=source, track="exploration",
                rationale=("secteur non travaillé ; "
                           + ("département jamais exploré" if dept not in
                              self.coverage["departments"] else "département peu couvert")
                           + f" ; source rendement {perf.get(source, 0.15):.2f}"),
                priority=round(1.0 + perf.get(source, 0.15), 4),
            ))
        return out[:count]

    def overview(self) -> dict[str, Any]:
        return {
            "as_of": date.today().isoformat(),
            "coverage": self.coverage,
            "source_performance": [p.to_dict() for p in self.performance],
            "search_history": self.history.stats(),
            "fresh_sectors_available": len(self.fresh_sectors()),
        }
