"""Personnalisation v5 — structure commerciale en 5 temps et diversité de lot.

Objectif du lot 7 : qu'un message ne soit plus reconnaissable comme « un email
de prospection standard ». Trois défauts du moteur v4 y empêchaient :

1. toutes les propositions commençaient par « Je peux vous proposer » ;
2. toutes les démonstrations commençaient par la même phrase de 20 mots ;
3. rien n'empêchait deux entreprises d'un même lot de recevoir la même trame.

Ce module apporte :

* des **familles de solution** explicites — on ne propose plus un agent IA par
  défaut, on choisit la réponse adaptée au besoin observé ;
* une **rotation déterministe** des amorces de proposition, de démonstration et
  des appels à l'action (même entreprise -> même formulation, donc reproductible) ;
* un segment **observation** distinct de l'accroche : l'accroche énonce le fait
  vérifiable, l'observation en tire la conséquence pour l'entreprise ;
* un **contrôle de diversité** à l'échelle d'un lot, et la détection des
  présentations de services génériques.

Aucune donnée n'est inventée ici : les amorces ne font qu'habiller des contenus
observés et sourcés fournis par le prospect.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Familles de solution. Le besoin observé décide, jamais le secteur d'activité.
# ---------------------------------------------------------------------------
SOLUTION_CREATION = "creation_site"
SOLUTION_REFONTE = "refonte_site"
SOLUTION_FORMULAIRE = "formulaire_intelligent"
SOLUTION_RESERVATION = "reservation_en_ligne"
SOLUTION_COMMANDE = "commande_en_ligne"
SOLUTION_DEVIS = "devis_automatise"
SOLUTION_AGENT_IA = "agent_ia"
SOLUTION_ADMIN = "automatisation_admin"

SOLUTION_TYPES: dict[str, str] = {
    SOLUTION_CREATION: "création de site",
    SOLUTION_REFONTE: "refonte de site",
    SOLUTION_FORMULAIRE: "formulaire intelligent",
    SOLUTION_RESERVATION: "réservation en ligne",
    SOLUTION_COMMANDE: "commande en ligne",
    SOLUTION_DEVIS: "automatisation des devis",
    SOLUTION_AGENT_IA: "agent IA de réponse",
    SOLUTION_ADMIN: "automatisation administrative",
}

# Une seule famille est « IA ». Les sept autres sont des solutions web ou
# d'automatisation classiques : le moteur ne doit pas pousser l'IA par défaut.
IA_SOLUTIONS = frozenset({SOLUTION_AGENT_IA})


# ---------------------------------------------------------------------------
# Amorces en rotation. Toutes acceptent un syntagme nominal en minuscule
# (« un formulaire… », « une demande de location… »).
# ---------------------------------------------------------------------------
PROPOSITION_OPENERS: tuple[str, ...] = (
    "Je peux vous proposer ",
    "Concrètement, je pourrais mettre en place ",
    "Mon idée : ",
    "Je vous suggère ",
    "Il serait assez simple d'ajouter ",
    "Ce que je pourrais prendre en charge : ",
)

# Chaque amorce contient les trois mentions exigées par check_email_v4 :
# une démonstration ou maquette, la gratuité, l'absence d'engagement.
# Elles sont volontairement plus courtes que l'amorce v4 (20 mots) pour laisser
# de la place au segment « observation » sans allonger le message.
DEMO_OPENERS: tuple[str, ...] = (
    "Je vous montre gratuitement, sans engagement, une démonstration : ",
    "Sans engagement, je vous prépare gratuitement une démonstration : ",
    "Je peux vous en faire une démonstration gratuite, sans engagement : ",
    "Sur demande, je vous envoie gratuitement une démonstration, sans engagement : ",
    "Je vous prépare une première maquette gratuite, sans engagement : ",
)

CTA_VARIANTS: tuple[str, ...] = (
    "Cela vous dirait de la découvrir ?",
    "Souhaitez-vous que je vous montre cela sur un cas concret de votre activité ?",
    "Un échange de quinze minutes vous conviendrait-il pour voir à quoi cela ressemblerait ?",
    "Dites-moi si le sujet mérite qu'on en parle.",
    "Est-ce un point qui vous occupe en ce moment ?",
    "Si vous êtes curieux, je vous montre — sinon, aucun souci.",
    "Vous préférez recevoir la démonstration, ou qu'on en parle d'abord ?",
)

# Formulations interdites : présentation de services générique, flatterie
# artificielle, fausse urgence, promesse de travail déjà réalisé.
GENERIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"je suis tomb[ée]+ sur votre (entreprise|site|profil)", "accroche générique « je suis tombé sur »"),
    (r"je (voulais|souhaitais) vous proposer mes services", "présentation de services générique"),
    (r"je me permets de vous contacter", "ouverture passe-partout"),
    (r"n'h[ée]sitez pas [àa] me contacter pour (tout|plus)", "formule de politesse commerciale creuse"),
    (r"dans le cadre du d[ée]veloppement de votre (activit[ée]|entreprise)", "formulation commerciale creuse"),
    (r"offre (exceptionnelle|limit[ée]e)|derni[èe]re chance|plus que quelques", "fausse urgence"),
    (r"je (vous garantis|vous assure) (un|résultat|des r[ée]sultats)", "promesse de résultat irréaliste"),
    (r"votre (magnifique|superbe|excellent) (site|entreprise|travail)", "compliment artificiel"),
    (r"j'ai (d[ée]j[àa] )?(r[ée]alis[ée]|cr[ée][ée]|d[ée]velopp[ée]) (pour vous|votre)",
     "prétend à une réalisation déjà effectuée"),
)

# Trames de présentation héritées de la v3/v4 : à ne plus utiliser dès qu'une
# prestation sur mesure a été recherchée pour l'entreprise.
LEGACY_SERVICE_LINES: tuple[str, ...] = (
    "Je crée des sites web professionnels qui valorisent votre activité",
    "Je modernise les sites web pour les rendre plus clairs",
    "Je conçois des agents IA qui traitent automatiquement vos demandes",
    "Je mets en place des automatisations qui vous font gagner du temps sur les tâches répétitives",
)


def _index(key: str, size: int, salt: int = 0) -> int:
    """Index stable dérivé du nom d'entreprise (reproductible, sans hasard)."""
    if size <= 0:
        return 0
    return (sum(ord(c) * (i + 1) for i, c in enumerate(key)) + salt) % size


class LotRotation:
    """Répartition garantie des amorces à l'échelle d'un lot.

    Le hachage seul produit des collisions : sur cinq entreprises, trois
    recevaient la même amorce. En connaissant la composition du lot, on
    distribue les amorces en ordre décalé : tant que le lot ne dépasse pas le
    nombre de formulations disponibles, aucune n'est répétée. L'ordre est trié,
    donc la régénération d'un message reste reproductible.
    """

    _SIZES = {"proposition": len(PROPOSITION_OPENERS),
              "demo": len(DEMO_OPENERS),
              "cta": len(CTA_VARIANTS)}
    _SALTS = {"proposition": 0, "demo": 2, "cta": 4}

    def __init__(self, companies: Iterable[str]):
        self.companies = sorted({c for c in companies if c})

    def index(self, company: str, kind: str = "proposition") -> int:
        size = self._SIZES.get(kind, 1)
        if company in self.companies:
            pos = self.companies.index(company)
        else:
            pos = _index(company, max(1, len(self.companies)))
        return (pos + self._SALTS.get(kind, 0)) % size


def pick_opener(company: str, kind: str = "proposition",
                rotation: "LotRotation | None" = None) -> str:
    """Amorce stable pour cette entreprise, différente selon le segment."""
    choices = {"demo": DEMO_OPENERS, "cta": CTA_VARIANTS}.get(kind, PROPOSITION_OPENERS)
    if rotation is not None:
        return choices[rotation.index(company, kind)]
    salt = {"demo": 7, "cta": 13}.get(kind, 0)
    return choices[_index(company, len(choices), salt=salt)]


def build_proposition(service: str, company: str, fallback: str = "",
                      rotation: "LotRotation | None" = None) -> str:
    """Habille la prestation observée d'une amorce variée.

    Si aucune prestation sur mesure n'a été recherchée, on retombe sur la trame
    générique — mais ``check_email_v4`` la signalera comme point à améliorer.
    """
    service = (service or "").strip()
    if not service:
        return fallback
    if service[0].isupper():
        # Phrase déjà complète : on ne la dénature pas.
        return service if service[-1] in ".!?" else service + "."
    opener = pick_opener(company, "proposition", rotation)
    sentence = opener + service
    return sentence if sentence[-1] in ".!?" else sentence + "."


# Amorces qui n'ont de sens que pour un travail sur un site. Annoncer une
# « maquette » pour un formulaire de devis ou un parcours CPF serait inexact.
SITE_ONLY_DEMO_OPENERS = frozenset({
    i for i, o in enumerate(DEMO_OPENERS) if "maquette" in o.lower()
})
SITE_SOLUTIONS = frozenset({"creation_site", "refonte_site"})


def build_demo(detail: str, company: str, fallback: str = "",
               rotation: "LotRotation | None" = None,
               solution_type: str = "") -> str:
    """Démonstration spécifique, annoncée gratuite et sans engagement.

    v6 : les amorces réservées aux sites sont écartées quand la solution retenue
    n'est pas un site, pour ne pas promettre une maquette qui n'a pas de sujet.
    """
    detail = (detail or "").strip().rstrip(".")
    if not detail:
        return fallback
    opener = pick_opener(company, "demo", rotation)
    if solution_type and solution_type not in SITE_SOLUTIONS:
        pool = [o for i, o in enumerate(DEMO_OPENERS) if i not in SITE_ONLY_DEMO_OPENERS]
        if pool and any(opener == DEMO_OPENERS[i] for i in SITE_ONLY_DEMO_OPENERS):
            idx = rotation.index(company, "demo") if rotation else _index(company, len(pool))
            opener = pool[idx % len(pool)]
    sentence = opener + detail
    return sentence if sentence[-1] in ".!?" else sentence + "."


def generic_problems(text: str) -> list[str]:
    """Repère les tournures commerciales creuses ou les promesses interdites."""
    lowered = (text or "").lower()
    found: list[str] = []
    for pattern, label in GENERIC_PATTERNS:
        if re.search(pattern, lowered):
            found.append(label)
    return found


def uses_legacy_service_line(text: str) -> bool:
    return any(line.lower() in (text or "").lower() for line in LEGACY_SERVICE_LINES)


@dataclass
class DiversityReport:
    """Contrôle d'un lot : deux entreprises ne doivent pas recevoir la même trame."""

    size: int
    problems: list[str]
    distinct_subjects: int
    distinct_bodies: int
    distinct_proposition_openers: int
    distinct_demo_openers: int
    distinct_ctas: int

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "ok": self.ok,
            "problems": self.problems,
            "distinct_subjects": self.distinct_subjects,
            "distinct_bodies": self.distinct_bodies,
            "distinct_proposition_openers": self.distinct_proposition_openers,
            "distinct_demo_openers": self.distinct_demo_openers,
            "distinct_ctas": self.distinct_ctas,
        }


def _matched(text: str, choices: Iterable[str]) -> str:
    for choice in choices:
        if text.startswith(choice):
            return choice
    return ""


def check_lot_diversity(emails: list[Any]) -> DiversityReport:
    """Contrôle de diversité d'un lot de messages.

    Règles : aucun objet ni corps dupliqué ; aucune amorce de proposition, de
    démonstration ou d'appel à l'action ne doit couvrir plus de la moitié du lot
    dès quatre messages. En deçà, on exige seulement l'absence de doublon exact.
    """
    problems: list[str] = []
    subjects = [getattr(e, "subject", "") for e in emails]
    bodies = [getattr(e, "body", "") for e in emails]
    n = len(emails)

    if len(set(subjects)) < n:
        problems.append("objets dupliqués dans le lot")
    if len(set(bodies)) < n:
        problems.append("corps de message dupliqués dans le lot")

    prop_openers, demo_openers, ctas = [], [], []
    for email in emails:
        body = getattr(email, "body", "")
        prop_hit = ""
        for part in body.split("\n\n"):
            prop_hit = _matched(part, PROPOSITION_OPENERS)
            if prop_hit:
                break
        prop_openers.append(prop_hit)
        demo_hit = ""
        for part in body.split("\n\n"):
            demo_hit = _matched(part, DEMO_OPENERS)
            if demo_hit:
                break
        demo_openers.append(demo_hit)
        cta_hit = ""
        for part in body.split("\n\n"):
            if part.strip() in CTA_VARIANTS:
                cta_hit = part.strip()
                break
        ctas.append(cta_hit)

    if n >= 4:
        ceiling = max(1, n // 2)
        for label, values in (("amorce de proposition", prop_openers),
                              ("amorce de démonstration", demo_openers),
                              ("appel à l'action", ctas)):
            counts: dict[str, int] = {}
            for value in values:
                if value:
                    counts[value] = counts.get(value, 0) + 1
            for value, count in counts.items():
                if count > ceiling:
                    problems.append(
                        f"{label} identique pour {count}/{n} messages : « {value.strip()[:60]}… »")

    return DiversityReport(
        size=n,
        problems=problems,
        distinct_subjects=len(set(subjects)),
        distinct_bodies=len(set(bodies)),
        distinct_proposition_openers=len({v for v in prop_openers if v}),
        distinct_demo_openers=len({v for v in demo_openers if v}),
        distinct_ctas=len({v for v in ctas if v}),
    )


# ---------------------------------------------------------------------------
# v6 — adaptation à l'interlocuteur (lot 8)
# ---------------------------------------------------------------------------
# Un même problème ne se formule pas de la même façon selon la personne qui lit.
# Un gérant pense chiffre d'affaires et temps passé ; un responsable administratif
# pense pièces manquantes et ressaisie ; un responsable d'exploitation pense
# planning et terrain. On n'invente jamais la fonction : elle est relevée sur une
# source publique, stockée dans contact_role, et seule une fonction reconnue
# déclenche un angle. Sinon le message reste adressé à l'entreprise.

ROLE_FAMILIES: dict[str, tuple[str, ...]] = {
    "dirigeant": ("gérant", "gerant", "gérante", "gerante", "président", "president",
                  "directeur général", "directeur general", "dg", "fondateur",
                  "fondatrice", "dirigeant", "dirigeante", "co-dirigeant", "artisan",
                  "entrepreneur", "repreneur"),
    "commercial": ("responsable commercial", "directeur commercial", "commercial",
                   "chargé d'affaires", "charge d'affaires", "vente", "adv"),
    "administratif": ("responsable administratif", "secrétariat", "secretariat",
                      "secrétaire", "secretaire", "assistante", "assistant",
                      "gestionnaire", "comptable", "administratif"),
    "exploitation": ("responsable d'exploitation", "directeur d'exploitation",
                     "responsable de site", "chef d'atelier", "responsable logistique",
                     "responsable production", "exploitant"),
    "technique": ("directeur technique", "responsable technique", "bureau d'études",
                  "responsable méthodes", "informatique", "dsn", "rsi"),
}

# Angle de bénéfice par famille. Formulations courtes, sans promesse chiffrée.
ROLE_BENEFITS: dict[str, str] = {
    "dirigeant": "moins de temps passé en allers-retours, et des demandes qui aboutissent",
    "commercial": "des demandes entrantes qualifiées dès leur arrivée, sans relance manuelle",
    "administratif": "des dossiers complets du premier coup, sans ressaisie ni pièce manquante",
    "exploitation": "un planning lisible et moins d'appels pour caler une intervention",
    "technique": "des demandes exploitables directement, sans reprise manuelle en amont",
}


def detect_role_family(contact_role: str) -> str:
    """Renvoie la famille de rôle, ou '' si la fonction n'est pas reconnue.

    La comparaison se fait sur la fonction telle qu'elle est publiée. Une
    fonction absente ou exotique ne déclenche aucun angle : mieux vaut un
    message adressé à l'entreprise qu'un rôle inventé.
    """
    role = (contact_role or "").strip().lower()
    if not role:
        return ""
    for family, markers in ROLE_FAMILIES.items():
        if any(m in role for m in markers):
            return family
    return ""


def benefit_for(prospect) -> str:
    """Bénéfice professionnel adapté à l'interlocuteur.

    Un bénéfice explicite rédigé pour l'entreprise prime toujours sur l'angle
    générique par rôle : il est plus précis et a été vérifié à la main.
    """
    explicit = (getattr(prospect, "benefit", "") or "").strip()
    if explicit:
        return explicit
    family = detect_role_family(getattr(prospect, "contact_role", ""))
    return ROLE_BENEFITS.get(family, "")
