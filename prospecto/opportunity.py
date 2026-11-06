"""Détection d'opportunités opérationnelles à partir de faits observés (v7).

Problème résolu
---------------
Jusqu'au lot 8, le score « agent IA / automatisation » reposait sur le *type*
de preuve (`processus_manuel` = +60) et sur un champ libre `process_hint`. Deux
entreprises du même métier avec une seule preuve chacun recevaient donc le même
score, alors que leurs processus peuvent être opposés : l'une prend ses
réservations par téléphone, l'autre a un tunnel de réservation en ligne.

Ce module analyse le **contenu** des preuves (citation + reformulation) pour y
reconnaître des signaux opérationnels nommés, et des contre-signaux de maturité
qui réduisent le besoin. Le secteur d'activité n'est jamais une entrée.

Distinction fait / hypothèse
----------------------------
Chaque signal est rattaché à la preuve dont il est issu. Si cette preuve est
marquée `observed=False` (opportunité supposée et non fait constaté), le signal
est marqué hypothétique : il compte moins et dégrade la confiance. Un signal
n'est jamais inventé à partir du métier.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Normalisation : les sites utilisent des apostrophes typographiques, des
# espaces insécables et des accents. Sans normalisation, « téléphone » et
# « téléphone » ne se ressemblent pas pour un moteur de motifs.
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("\u2019", "'").replace("\u00a0", " ").replace("\u202f", " ")
    return re.sub(r"\s+", " ", text.lower()).strip()


@dataclass(frozen=True)
class Signal:
    """Un motif opérationnel reconnaissable dans une publication."""

    id: str
    label: str
    weight: int
    patterns: tuple[str, ...]
    axis: str


@dataclass
class Detection:
    """Un signal effectivement trouvé, et la preuve qui le porte."""

    signal: Signal
    matched_pattern: str
    evidence_index: int
    source_url: str
    quote: str
    observed: bool
    reliability: str

    @property
    def hypothetical(self) -> bool:
        return not self.observed

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal.id,
            "label": self.signal.label,
            "weight": self.signal.weight,
            "matched_pattern": self.matched_pattern,
            "evidence_index": self.evidence_index,
            "source_url": self.source_url,
            "quote": self.quote,
            "observed": self.observed,
            "hypothetical": self.hypothetical,
            "reliability": self.reliability,
        }


AXIS_IA = "ia_automatisation"
AXIS_REFONTE = "refonte"
AXIS_SITE = "site_web"

# ---------------------------------------------------------------------------
# Signaux d'automatisation. Le poids traduit l'ampleur de la tâche manuelle
# réellement décrite, pas l'intérêt commercial supposé du secteur.
# ---------------------------------------------------------------------------
AUTOMATION_SIGNALS: tuple[Signal, ...] = (
    Signal("devis_manuel", "Devis établi ou transmis à la main", 26, (
        "devis par e-mail", "devis par email", "devis par telephone",
        "envoyer votre commande", "envoyez-nous vos specifications",
        "nous vous envoyons un devis", "preparer et transmettre les devis",
        "demande de devis par", "devis personnalise", "etablir un devis",
        "devis sur demande", "recevoir un devis", "demande de prix",
    ), AXIS_IA),
    Signal("reservation_telephone", "Réservation ou commande par téléphone", 26, (
        "reservation par telephone", "reserver par telephone", "appelez-nous pour reserver",
        "merci d'appeler", "appeler obligatoirement", "par telephone uniquement",
        "commande par telephone", "reservation uniquement", "nous contacter par telephone pour",
    ), AXIS_IA),
    Signal("collecte_pieces", "Pièces ou justificatifs à collecter", 20, (
        "extrait k-bis", "extrait kbis", "k-bis", "kbis", "fiche d'ouverture de compte",
        "ouverture de compte", "justificatif", "piece jointe", "pieces jointes",
        "joindre votre", "merci de nous adresser votre", "dossier complet",
        "formulaire a completer", "fiche de renseignements",
    ), AXIS_IA),
    Signal("planification_manuelle", "Planification calée à la main", 22, (
        "fixer ensemble les dates", "pour fixer les dates", "nous vous contactons pour fixer",
        "convenir d'un rendez-vous", "convenir ensemble", "caler un creneau",
        "fixer un rendez-vous", "nous revenons vers vous pour", "dates disponibles sur demande",
        "planning sur demande",
    ), AXIS_IA),
    Signal("relance_client", "Relance laissée à la charge du client", 24, (
        "si vous n'avez pas recu", "merci de me rappeler", "merci de me contacter au",
        "sans reponse de notre part", "n'hesitez pas a relancer", "merci de relancer",
        "si vous ne recevez pas", "pensez a verifier vos spams", "peut se trouver dans les spams",
    ), AXIS_IA),
    Signal("tri_manuel", "Qualification ou vérification manuelle des demandes", 18, (
        "nous verifions", "nous verifierons", "nous etudions votre demande",
        "verifier la disponibilite", "nous echangeons sur", "adapter a votre profil",
        "adapte a votre profil", "selon votre profil", "nous selectionnons",
        "traitement de votre demande", "etude de votre demande",
        "impose au secretariat", "de verifier", "valider manuellement",
        "validation manuelle", "verifie manuellement", "puis de valider",
    ), AXIS_IA),
    Signal("ressaisie", "Ressaisie ou reformulation des demandes", 22, (
        "recopier", "recopie", "ressaisir", "ressaisie", "saisir a nouveau",
        "reporter les informations", "recopiees a la main", "saisie manuelle",
        "bon de commande", "en precisant le nom", "preciser le nom",
    ), AXIS_IA),
    Signal("info_sur_demande", "Information non publiée, à demander à chaque fois", 20, (
        "n'est pas publie", "ne sont pas publies", "pas publie", "sur demande",
        "afin de les connaitre", "pour les connaitre", "doit le demander",
        "doivent etre demandes", "consultable sur demande", "prendre contact afin",
        "dates disponibles sur demande",
    ), AXIS_IA),
    Signal("qualification_absente", "Demandes arrivant sans information de qualification", 22, (
        "aucun champ de qualification", "aucun champ", "champ libre", "pas de champ",
        "doivent etre obtenus", "doit etre obtenu", "par retour d'e-mail",
        "par retour d'email", "ne demande pas la localisation", "sans type de projet",
        "formulaire a champ libre",
    ), AXIS_IA),
    Signal("regles_manuelles", "Règles de gestion suivies à la main", 18, (
        "regles de gestion", "s'appliquent a chaque", "suivi de son cycle",
        "suivi manuel", "gere manuellement", "geres manuellement",
        "tenu manuellement", "tenus manuellement", "suivies manuellement",
        "suivi manuellement",
    ), AXIS_IA),
    Signal("canal_multiple", "Demande acceptée sur plusieurs canaux à retraiter", 16, (
        "par e-mail ou par telephone", "par telephone ou par e-mail",
        "soit en ligne, par telephone", "par courrier", "adressez nous un mail",
        "adressez-nous un mail", "envoyez-nous un mail", "en mentionnant vos",
    ), AXIS_IA),
    Signal("demandes_repetitives", "Demandes entrantes répétitives", 14, (
        "questions frequentes", "les memes questions", "demandes recurrentes",
        "nous recevons souvent", "souvent sollicite", "nombreuses demandes",
        "demandes de renseignement",
    ), AXIS_IA),
    Signal("delai_reponse", "Délai de réponse annoncé, tenu à la main", 12, (
        "reponse sous 48", "repondons sous 48", "sous 48 h", "sous 48h",
        "sous 24 h ouvr", "sous 24h", "reponse sous", "delai de reponse",
        "nous vous repondrons", "nous revenons vers vous",
    ), AXIS_IA),
)

# ---------------------------------------------------------------------------
# Contre-signaux : ce qui est DÉJÀ automatisé réduit le besoin. Sans eux, une
# entreprise très outillée obtenait le même score qu'une entrepriseartisanale.
# ---------------------------------------------------------------------------
MATURITY_SIGNALS: tuple[Signal, ...] = (
    Signal("reservation_en_ligne", "Réservation déjà en ligne", 30, (
        "reservation en ligne", "reserver en ligne", "reservez en ligne",
        "prise de rendez-vous en ligne", "rendez-vous en ligne", "booking",
        "calendrier de reservation", "disponibilites en ligne",
    ), AXIS_IA),
    Signal("paiement_en_ligne", "Paiement en ligne en place", 24, (
        "paiement en ligne", "paiement securise", "3d secure", "payer en ligne",
        "reglement en ligne", "carte bancaire en ligne", "boutique en ligne",
        "commander en ligne", "panier", "paiement carte bleue", "paiement par carte",
        "prise en compte immediate", "envoi programme", "sont automatise",
    ), AXIS_IA),
    Signal("espace_client", "Compte ou espace client existant", 22, (
        "espace client", "compte client", "mon compte", "espace professionnel",
        "espace pro", "votre espace personnel", "extranet",
    ), AXIS_IA),
    Signal("devis_en_ligne", "Demande de devis déjà structurée en ligne", 20, (
        "devis en ligne", "devis instantane", "devis immediat", "simulateur de devis",
        "obtenir un devis en ligne", "formulaire de devis",
    ), AXIS_IA),
    Signal("reponse_automatique", "Réponse ou confirmation automatique", 20, (
        "confirmation automatique", "accuse de reception automatique",
        "vous recevrez automatiquement", "e-mail automatique", "email automatique",
        "notification automatique", "reponse automatique",
    ), AXIS_IA),
    Signal("tarifs_publics", "Tarifs publics et à jour", 12, (
        "nos tarifs", "grille tarifaire", "tarifs en ligne", "prix affiches",
        "catalogue avec prix", "tarifs consultables",
    ), AXIS_IA),
)

# ---------------------------------------------------------------------------
# Signaux de refonte, distincts des signaux d'automatisation.
# ---------------------------------------------------------------------------
REFONTE_SIGNALS: tuple[Signal, ...] = (
    Signal("contact_incoherent", "Coordonnées incohérentes ou erronées", 34, (
        "tel:0663026447", "autre numero", "numero different", "adresse obsolete",
        "informations incoherentes", "ancien domaine", "site non publie",
        "page d'hebergement suspendu", "hebergement suspendu",
    ), AXIS_REFONTE),
    Signal("contact_pauvre", "Contact réduit à un lien mailto ou une carte", 26, (
        "mailto:", "lien mailto", "carte google", "aucun formulaire",
        "sans formulaire", "pas de formulaire", "formulaire absent",
    ), AXIS_REFONTE),
    Signal("parcours_incomplet", "Parcours de demande incomplet", 24, (
        "ne propose pas la creation de comptes", "aucun compte client",
        "liste deroulante", "champ service", "catalogue sans prix",
        "sans-prix.pdf", "pdf sans tarif",
    ), AXIS_REFONTE),
    Signal("mobile_degrade", "Usage mobile manifestement dégradé", 30, (
        "non responsive", "pas adapte au mobile", "illisible sur mobile",
        "affichage mobile degrade", "site fixe en largeur",
    ), AXIS_REFONTE),
    Signal("contenu_obsolete", "Contenu daté ou abandonné", 22, (
        "derniere mise a jour", "copyright 20", "mentions legales en cours",
        "site en construction", "prochainement", "page en travaux",
    ), AXIS_REFONTE),
)

# ---------------------------------------------------------------------------
# Signaux de présence en ligne, pour l'axe création.
# ---------------------------------------------------------------------------
PRESENCE_SIGNALS: tuple[Signal, ...] = (
    Signal("aucun_site", "Aucun site officiel identifiable", 40, (
        "aucun site", "pas de site", "sans site internet", "site inexistant",
        "aucun site officiel",
    ), AXIS_SITE),
    Signal("annuaire_seul", "Présence limitée à un annuaire ou un réseau social", 30, (
        "uniquement sur pagesjaunes", "seulement sur facebook", "page facebook uniquement",
        "present uniquement sur", "annuaire uniquement", "profil google uniquement",
    ), AXIS_SITE),
    Signal("prestations_floues", "Prestations mal présentées", 18, (
        "prestations non detaillees", "aucune presentation des services",
        "services non decrits", "activite peu claire",
    ), AXIS_SITE),
)

ALL_SIGNALS = AUTOMATION_SIGNALS + MATURITY_SIGNALS + REFONTE_SIGNALS + PRESENCE_SIGNALS


def _evidence_text(ev: Any) -> str:
    if isinstance(ev, dict):
        parts = (ev.get("quote", ""), ev.get("detail", ""), ev.get("source_url", ""))
    else:
        parts = (getattr(ev, "quote", ""), getattr(ev, "detail", ""),
                 getattr(ev, "source_url", ""))
    return normalize(" ".join(str(p or "") for p in parts))


def _ev_field(ev: Any, name: str, default: Any = "") -> Any:
    if isinstance(ev, dict):
        return ev.get(name, default)
    return getattr(ev, name, default)


def detect_signals(evidences: Iterable[Any], axis: str,
                   extra_text: str = "") -> list[Detection]:
    """Détecte les signaux d'un axe dans les preuves fournies.

    `extra_text` (typiquement process_hint) n'est utilisé que s'il existe au
    moins une preuve : un champ libre seul ne crée jamais de signal.
    """
    evs = list(evidences)
    # Les contre-signaux de maturité partagent l'axe IA mais ne doivent JAMAIS
    # être comptés comme un besoin : ils sont traités par detect_maturity().
    maturity_ids = {s.id for s in MATURITY_SIGNALS}
    catalogue = [s for s in ALL_SIGNALS if s.axis == axis and s.id not in maturity_ids]
    found: list[Detection] = []
    seen: set[str] = set()
    for idx, ev in enumerate(evs):
        text = _evidence_text(ev)
        if idx == 0 and extra_text:
            text += " " + normalize(extra_text)
        for sig in catalogue:
            if sig.id in seen:
                continue
            for pattern in sig.patterns:
                if pattern in text:
                    found.append(Detection(
                        signal=sig, matched_pattern=pattern, evidence_index=idx,
                        source_url=str(_ev_field(ev, "source_url")),
                        quote=str(_ev_field(ev, "quote"))[:200],
                        observed=bool(_ev_field(ev, "observed", True)),
                        reliability=str(_ev_field(ev, "reliability", "moyenne")),
                    ))
                    seen.add(sig.id)
                    break
    return found


def detect_maturity(evidences: Iterable[Any], extra_text: str = "") -> list[Detection]:
    """Contre-signaux de maturité, tous axes confondus (ils réduisent le besoin IA)."""
    evs = list(evidences)
    found: list[Detection] = []
    seen: set[str] = set()
    for idx, ev in enumerate(evs):
        text = _evidence_text(ev)
        if idx == 0 and extra_text:
            text += " " + normalize(extra_text)
        for sig in MATURITY_SIGNALS:
            if sig.id in seen:
                continue
            for pattern in sig.patterns:
                if pattern in text:
                    found.append(Detection(
                        signal=sig, matched_pattern=pattern, evidence_index=idx,
                        source_url=str(_ev_field(ev, "source_url")),
                        quote=str(_ev_field(ev, "quote"))[:200],
                        observed=bool(_ev_field(ev, "observed", True)),
                        reliability=str(_ev_field(ev, "reliability", "moyenne")),
                    ))
                    seen.add(sig.id)
                    break
    return found


@dataclass
class OpportunityReport:
    """Ce qui a été observé, ce qui est supposé, et ce qui manque."""

    automation: list[Detection] = field(default_factory=list)
    maturity: list[Detection] = field(default_factory=list)
    refonte: list[Detection] = field(default_factory=list)
    presence: list[Detection] = field(default_factory=list)

    def distinct_sources(self, detections: list[Detection]) -> int:
        return len({d.source_url for d in detections if d.source_url})

    def to_dict(self) -> dict[str, Any]:
        return {
            "automation": [d.to_dict() for d in self.automation],
            "maturity": [d.to_dict() for d in self.maturity],
            "refonte": [d.to_dict() for d in self.refonte],
            "presence": [d.to_dict() for d in self.presence],
        }


def analyze(evidences: Iterable[Any], process_hint: str = "") -> OpportunityReport:
    """Analyse complète. Le secteur n'est volontairement pas un paramètre."""
    evs = list(evidences)
    return OpportunityReport(
        automation=detect_signals(evs, AXIS_IA, process_hint),
        maturity=detect_maturity(evs, process_hint),
        refonte=detect_signals(evs, AXIS_REFONTE, process_hint),
        presence=detect_signals(evs, AXIS_SITE, process_hint),
    )
