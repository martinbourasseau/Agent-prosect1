"""Diversification de la recherche et mémoire d'exploration (v7).

Deux problèmes concrets des lots 1 à 8
--------------------------------------
1. Les recherches tournaient autour des mêmes secteurs (traiteur, location,
   formation, artisans) et retombaient sur les mêmes entreprises. Rien ne
   mémorisait qu'une structure avait déjà été examinée puis écartée.
2. Une seule source était réellement utilisée : le site officiel, trouvé par
   moteur. Les annuaires, registres, pages professionnelles, presse locale et
   appels à projets n'étaient pas exploités comme sources distinctes.

Ce module fournit :
* un catalogue de sources typées, avec leur fiabilité par défaut et leurs
  conditions d'accès à respecter ;
* un état des lieux de la couverture du CRM (secteurs, départements, domaines) ;
* un planificateur de requêtes qui propose des territoires et secteurs NON
  couverts, en faisant tourner les types de sources ;
* un registre d'exploration persistant : toute entreprise examinée y est
  inscrite, y compris écartée, avec le motif. Elle ne sera pas réexaminée.

Aucun accès réseau n'est effectué ici et aucun contournement n'est prévu :
le catalogue indique explicitement quand une source impose des conditions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config
from .models import SOURCE_TYPES, SOURCE_RELIABILITY

EXPLORATION_PATH = config.DATA_DIR / "history" / "exploration-ledger.json"


@dataclass(frozen=True)
class Source:
    """Une famille de sources publiques et la façon correcte de l'utiliser."""

    type: str
    label: str
    examples: tuple[str, ...]
    access_note: str

    @property
    def reliability(self) -> str:
        return SOURCE_RELIABILITY.get(self.type, "faible")


SOURCE_CATALOGUE: tuple[Source, ...] = (
    Source("site_officiel", "Site officiel de l'entreprise",
           ("page contact", "page devis / réservation", "CGV / mentions légales", "FAQ"),
           "Lecture publique des pages. Respecter robots.txt ; ne pas contourner "
           "CAPTCHA ni protection anti-robot. Source de référence sur ses propres processus."),
    Source("annuaire_pro", "Annuaire professionnel accessible",
           ("chambres de métiers", "annuaires sectoriels publics", "ordres professionnels"),
           "Ne pas aspirer en masse. Beaucoup d'annuaires interdisent la réutilisation "
           "automatisée : vérifier les CGU. Fiabilité faible, sert à repérer puis vérifier "
           "sur le site officiel."),
    Source("registre_public", "Registre et donnée publique",
           ("SIRENE / annuaire des entreprises", "registres consulaires",
            "répertoire national des associations (exclu du périmètre)"),
           "Données publiques réutilisables. Utile pour confirmer l'existence, l'adresse "
           "et le dirigeant, pas pour déduire une adresse e-mail."),
    Source("page_professionnelle", "Page professionnelle publique",
           ("page entreprise d'un réseau professionnel", "vitrine d'artisan publiée"),
           "Lire uniquement ce qui est public. Ne pas collecter de profils personnels. "
           "Souvent incomplet : recouper avec le site officiel."),
    Source("presse_locale", "Article de presse locale",
           ("PQR départementale", "presse économique régionale", "site d'actualité local"),
           "Utile pour un contexte vérifiable (reprise, agrandissement, difficulté annoncée). "
           "Ne pas citer un article derrière paywall. Distinguer le fait rapporté du commentaire."),
    Source("appel_projet", "Appel à projets ou demande de prestation publique",
           ("marchés publics ouverts", "appels à candidatures publiés par une CCI",
            "demandes de devis publiées par une structure privée"),
           "Ne retenir que les demandes réellement publiques et ouvertes. Une demande "
           "publiée est un besoin exprimé : fiabilité haute, mais vérifier la date de clôture."),
    Source("autre", "Autre source pertinente",
           ("catalogue PDF public", "documentation technique publiée"),
           "À qualifier au cas par cas. Fiabilité faible par défaut."),
)

SOURCE_BY_TYPE = {s.type: s for s in SOURCE_CATALOGUE}

# Secteurs volontairement distincts de ceux déjà travaillés (traiteur, location de
# matériel, formation, couverture, pépinière, négoce industriel, bien-être).
SECTOR_POOL: tuple[tuple[str, str], ...] = (
    ("pisciniste — entretien et rénovation de bassins", "piscine entretien rénovation"),
    ("menuiserie — escaliers sur mesure", "escalier bois sur mesure"),
    ("sellerie — bourrellerie et réparation d'articles équestres", "sellerie bourrelier"),
    ("lutherie — réparation d'instruments", "luthier réparation instruments"),
    ("horlogerie — réparation et entretien", "horloger réparation montres"),
    ("couture — retouches et confection sur mesure", "couturière retouches sur mesure"),
    ("taxidermie — naturalisme", "taxidermiste naturaliste"),
    ("affûtage — outils et lames professionnelles", "affutage outils professionnel"),
    ("ferronnerie — métallerie d'art", "ferronnier metallerie art"),
    ("vitrerie — miroiterie et dépannage", "miroitier vitrier depannage"),
    ("ramonage — fumisterie", "ramoneur fumiste"),
    ("forage — puits et sondages", "forage puits entreprise"),
    ("assainissement — vidange et entretien", "vidange assainissement entreprise"),
    ("démolition — désamiantage et curage", "curage demolition entreprise"),
    ("étanchéité — toitures terrasses", "etancheite toiture terrasse"),
    ("isolation — soufflage et combles", "isolation combles soufflee"),
    ("photovoltaïque — pose et maintenance", "installateur photovoltaique maintenance"),
    ("bornes de recharge — installation", "installation bornes recharge entreprise"),
    ("domotique — intégration", "integrateur domotique"),
    ("sécurité incendie — extincteurs et vérifications", "verificateur extincteurs"),
    ("contrôle d'accès — interphonie", "installateur interphonie controle acces"),
    ("nettoyage industriel — remise en état", "nettoyage industriel remise en etat"),
    ("dératisation — nuisibles professionnels", "deratisation entreprise 3D"),
    ("blanchisserie industrielle", "blanchisserie industrielle"),
    ("pressing — traitement du cuir", "pressing traitement cuir"),
    ("cordonnerie — réparation", "cordonnier réparation"),
    ("relieur — restauration de livres", "relieur restauration livres"),
    ("encadrement — galerie et atelier", "encadreur atelier"),
    ("imprimerie — façonnage et petit format", "imprimeur faconnage"),
    ("signalétique — marquage et lettrage", "signaletique marquage lettrage"),
    ("gravure — personnalisation", "gravure personnalisation entreprise"),
    ("moulistes — plastiques et résines", "mouliste plasturgie resin"),
    ("prototypage — impression 3D à façon", "impression 3D a facon service"),
    ("métrologie — étalonnage d'instruments", "metrologie etalonnage"),
    ("bureau d'études — calcul et structure", "bureau etudes structure"),
    ("géomètre — topographie", "geometre topographie cabinet"),
    ("contrôle technique — poids lourds", "controle technique poids lourds"),
    ("carrosserie — véhicules utilitaires", "carrossier utilitaires"),
    ("pneumatique — agricoles et TP", "pneumatique agricole monteur"),
    ("levage — manutention et grues", "location grue levage manutention"),
    ("transport — exceptionnel et convoiement", "convoiement transport exceptionnel"),
    ("entreposage — stockage frigorifique", "entreposage frigorifique"),
    ("affrètement — commissionnaire de transport", "affreteur commissionnaire transport"),
    ("douane — conseil et formalités", "commissionnaire douane conseil"),
    ("laboratoire — analyses agroalimentaires", "laboratoire analyse agroalimentaire"),
    ("abattoir — atelier de découpe", "atelier decoupe abattoir prestation"),
    ("conserverie — façonnage à façon", "conserverie facon"),
    ("torréfaction — café de spécialité", "torrefacteur cafe specialite"),
    ("malterie — brasserie artisanale", "malterie brasserie artisanale"),
    ("cidrerie — pressoir à façon", "pressoir cidrerie facon"),
)

# Territoires : couples (département, ville pivot) pour ancrer les requêtes.
TERRITORY_POOL: tuple[tuple[str, str], ...] = (
    ("02", "Saint-Quentin"), ("03", "Moulins"), ("04", "Digne-les-Bains"),
    ("05", "Gap"), ("07", "Aubenas"), ("08", "Charleville-Mézières"),
    ("09", "Foix"), ("10", "Troyes"), ("11", "Carcassonne"), ("12", "Rodez"),
    ("15", "Aurillac"), ("16", "Angoulême"), ("17", "Saintes"), ("18", "Bourges"),
    ("19", "Brive-la-Gaillarde"), ("21", "Beaune"), ("22", "Saint-Brieuc"),
    ("23", "Guéret"), ("24", "Périgueux"), ("26", "Valence"), ("27", "Évreux"),
    ("2A", "Ajaccio"), ("2B", "Bastia"), ("32", "Auch"), ("35", "Fougères"),
    ("40", "Mont-de-Marsan"), ("41", "Blois"), ("42", "Roanne"), ("43", "Le Puy-en-Velay"),
    ("46", "Cahors"), ("47", "Agen"), ("48", "Mende"), ("51", "Châlons-en-Champagne"),
    ("52", "Chaumont"), ("53", "Laval"), ("54", "Lunéville"), ("57", "Thionville"),
    ("58", "Nevers"), ("60", "Compiègne"), ("61", "Alençon"), ("63", "Issoire"),
    ("64", "Pau"), ("65", "Tarbes"), ("66", "Perpignan"), ("70", "Vesoul"),
    ("71", "Mâcon"), ("72", "La Flèche"), ("73", "Chambéry"), ("74", "Annecy"),
    ("79", "Niort"), ("80", "Abbeville"), ("81", "Albi"), ("82", "Montauban"),
    ("84", "Carpentras"), ("85", "Fontenay-le-Comte"), ("86", "Châtellerault"),
    ("88", "Épinal"), ("89", "Sens"), ("90", "Belfort"), ("91", "Étampes"),
    ("95", "Pontoise"),
)


def _norm(text: str) -> str:
    return (text or "").strip().lower()


@dataclass
class Coverage:
    """Ce que le CRM couvre déjà, pour ne pas le réexplorer."""

    sectors: set[str] = field(default_factory=set)
    departments: set[str] = field(default_factory=set)
    domains: set[str] = field(default_factory=set)
    emails: set[str] = field(default_factory=set)
    companies: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {k: sorted(v) for k, v in asdict(self).items()}


def coverage(records: Iterable[dict[str, Any]]) -> Coverage:
    cov = Coverage()
    for r in records:
        if r.get("sector"):
            cov.sectors.add(_norm(r["sector"]))
        if r.get("department"):
            cov.departments.add(str(r["department"]).strip())
        if r.get("domain"):
            cov.domains.add(_norm(r["domain"]))
        if r.get("email"):
            cov.emails.add(_norm(r["email"]))
        if r.get("company"):
            cov.companies.add(_norm(r["company"]))
    return cov


@dataclass
class QuerySpec:
    """Une piste de recherche : secteur + territoire + type de source."""

    sector_label: str
    keywords: str
    department: str
    city: str
    source_type: str
    query: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_queries(records: Iterable[dict[str, Any]], count: int = 12,
                 ledger: "ExplorationLedger | None" = None) -> list[QuerySpec]:
    """Propose des requêtes sur des secteurs et territoires non couverts.

    Les secteurs déjà présents au CRM sont écartés par comparaison de mots
    significatifs, et les territoires déjà travaillés sont déprioritisés. Le
    type de source tourne pour ne pas dépendre d'une seule famille.
    """
    cov = coverage(records)
    seen_terms: set[str] = set()
    for sector in cov.sectors:
        seen_terms.update(w for w in sector.replace("—", " ").split() if len(w) > 4)
    if ledger is not None:
        seen_terms.update(ledger.examined_sector_terms())

    fresh_sectors = []
    for label, keywords in SECTOR_POOL:
        words = {w for w in _norm(label).replace("—", " ").split() if len(w) > 4}
        if words & seen_terms:
            continue
        fresh_sectors.append((label, keywords))
    if not fresh_sectors:
        fresh_sectors = list(SECTOR_POOL)

    untouched = [t for t in TERRITORY_POOL if t[0] not in cov.departments]
    territories = untouched or list(TERRITORY_POOL)

    specs: list[QuerySpec] = []
    for i in range(count):
        label, keywords = fresh_sectors[i % len(fresh_sectors)]
        dept, city = territories[i % len(territories)]
        source = SOURCE_CATALOGUE[i % len(SOURCE_CATALOGUE)]
        suffix = {
            "site_officiel": "site officiel contact",
            "annuaire_pro": "annuaire professionnel",
            "registre_public": "siret adresse entreprise",
            "page_professionnelle": "page professionnelle",
            "presse_locale": "article presse locale entreprise",
            "appel_projet": "appel à projets demande de prestation",
            "autre": "catalogue tarifs",
        }[source.type]
        specs.append(QuerySpec(label, keywords, dept, city, source.type,
                               f"{keywords} {city} {suffix}"))
    return specs


class ExplorationLedger:
    """Registre persistant des entreprises examinées, retenues ou écartées."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or EXPLORATION_PATH
        self.entries: list[dict[str, Any]] = []
        self.updated_at = ""
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = raw.get("entries", [])
            self.updated_at = raw.get("updated_at", "")

    def seen(self, key: str) -> bool:
        k = _norm(key)
        return any(_norm(e.get("domain", "")) == k or _norm(e.get("company", "")) == k
                   for e in self.entries)

    def record(self, company: str, domain: str = "", department: str = "",
               sector: str = "", decision: str = "écartée", reason: str = "",
               source_type: str = "site_officiel", source_url: str = "",
               lot: str = "") -> dict[str, Any]:
        entry = {"company": company, "domain": domain, "department": department,
                 "sector": sector, "decision": decision, "reason": reason,
                 "source_type": source_type, "source_url": source_url, "lot": lot,
                 "examined_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        self.entries.append(entry)
        return entry

    def examined_sector_terms(self) -> set[str]:
        terms: set[str] = set()
        for e in self.entries:
            terms.update(w for w in _norm(e.get("sector", "")).replace("—", " ").split()
                         if len(w) > 4)
        return terms

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.path.write_text(json.dumps(
            {"updated_at": self.updated_at, "count": len(self.entries), "entries": self.entries},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def stats(self) -> dict[str, Any]:
        by_decision: dict[str, int] = {}
        by_source: dict[str, int] = {}
        for e in self.entries:
            by_decision[e.get("decision", "?")] = by_decision.get(e.get("decision", "?"), 0) + 1
            by_source[e.get("source_type", "?")] = by_source.get(e.get("source_type", "?"), 0) + 1
        return {"examined": len(self.entries), "by_decision": by_decision,
                "by_source_type": by_source,
                "departments": sorted({e.get("department", "") for e in self.entries if e.get("department")})}
