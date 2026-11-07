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

# v8 — adverbes qui s'intercalent sans changer la nature du processus.
# « commande uniquement par téléphone » décrit le même besoin que
# « commande par téléphone ». Les retirer pour la SEULE comparaison évite de
# perdre le signal ; le texte affiché reste l'original normalisé.
_MATCH_FILLERS = (
    "uniquement", "seulement", "exclusivement", "directement", "eventuellement",
    "egalement", "aussi", "bien", "donc", "alors",
)


# Une occurrence précédée d'une négation n'affirme rien. La fenêtre est courte
# et placée AVANT le motif : « pas de paiement en ligne » est nié, « paiement en
# ligne, pas de frais » ne l'est pas.
_NEGATION_CUES = (
    "pas de ", "pas d'", "pas du ", "pas des ", "sans ", "aucun ", "aucune ",
    "ni ", "absence de ", "absence d'", "ne propose pas ", "ne proposons pas ",
    "n'y a pas ", "il n'y a pas ", "nous n'avons pas ", "non disponible",
    "pas encore ", "jamais de ", "plus de paiement", "defaut de ",
)


def _negated(text: str, position: int, window: int = 42) -> bool:
    """Vrai si l'occurrence en `position` est introduite par une négation."""
    before = text[max(0, position - window):position]
    return any(cue in before for cue in _NEGATION_CUES)


def _affirmed(text: str, pattern: str) -> bool:
    """Le motif apparaît-il au moins une fois SANS être nié ?"""
    start = 0
    while True:
        pos = text.find(pattern, start)
        if pos < 0:
            return False
        if not _negated(text, pos):
            return True
        start = pos + 1


def match_form(text: str) -> str:
    """Forme souple servant uniquement à la comparaison de motifs."""
    words = [w for w in normalize(text).split() if w not in _MATCH_FILLERS]
    return " ".join(words)


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
    signal_level: str = ""   # v8 : exprime / observe / indirect / hypothetique

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
# v7.1 — types de preuve qui ne décrivent pas un manque et ne doivent donc
# jamais déclencher un signal d'opportunité (voir detect_signals).
NON_GAP_KINDS = frozenset({"maturite_existante", "signal_confiance"})

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
        "rendez vous par sms", "prise de rendez vous par", "sur rendez vous par telephone", "appelez-nous pour reserver",
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
        # v7.1 — relevés sur la page devis de Caléo Tests & Services.
        "nous vous recontactons pour", "avant de chiffrer", "confirmer la faisabilite",
        "objet d'une analyse", "analyse rapide",
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
    # v7.1 — les quatre signaux ci-dessous ont été ajoutés après lecture des
    # pages du lot 9 : chacun correspond à une formulation réellement publiée
    # qu'aucun signal du catalogue ne reconnaissait.
    Signal("capacite_reponse_limitee", "Difficulté à répondre énoncée par l'entreprise", 28, (
        "complique de repondre", "difficile de repondre", "pas toujours en mesure de repondre",
        "relevons les messages", "messages une fois par jour", "de preference par mail",
        "privilegiez le mail", "nous ne pouvons pas repondre", "difficile de joindre",
    ), AXIS_IA),
    Signal("depot_via_messagerie", "Le formulaire se termine dans la messagerie du client", 24, (
        "ouvre votre messagerie", "ouvrir ma messagerie", "demande pre-remplie",
        "votre logiciel de messagerie", "envoyez-la plutot en piece jointe",
        "tableur excel", "export de votre logiciel de parc",
    ), AXIS_IA),
    Signal("deplacement_obligatoire", "Un déplacement est nécessaire pour être chiffré", 22, (
        "venez nous rencontrer", "venir nous rendre visite", "venir nous presenter",
        "venez nous presenter", "venez nous rendre visite", "venir en magasin",
        "venez avec votre", "passez au magasin", "en magasin pour",
        "venir a l'atelier avec", "sur place pour etablir",
    ), AXIS_IA),
    Signal("echeances_recurrentes", "Échéances récurrentes à suivre", 18, (
        "contrats annuels", "contrat annuel", "revision annuel", "entretien annuel",
        "compte-rendu detaille", "verification annuelle", "reetalonnage",
        "passage regulier",
    ), AXIS_IA),
    # v8 — signaux faibles listés explicitement au cahier des charges et
    # absents du catalogue. Chacun a été trouvé dans une fiche du portefeuille.
    Signal("commande_telephone_seulement", "Commande ou réservation téléphonique exclusive", 28, (
        "commande uniquement par telephone", "commandes uniquement par telephone",
        "reservation uniquement par telephone", "reservations par telephone uniquement",
        "commande par telephone uniquement", "prise de commande par telephone",
    ), AXIS_IA),
    Signal("inscription_manuelle", "Inscriptions ou adhésions traitées manuellement", 26, (
        "les inscriptions ont lieu", "inscription sur place", "inscriptions sur place",
        "bulletin d'inscription", "fiche d'inscription", "formulaire d'inscription a",
        "pre-adhesions", "preadhesions", "dossier d'inscription",
        "inscrire au secretariat", "inscription au comptoir",
        "fiches d'inscription", "inscription par courrier", "inscription par mail",
        "renvoyer la fiche", "fiche a telecharger",
    ), AXIS_IA),
    Signal("paiement_manuel", "Encaissement sans parcours en ligne", 20, (
        "par cheque", "par cheques", "cheques correspondant", "reglement par cheque",
        "virement - cheque", "modes de paiement : - virement",
        "especes ou cheque", "cheque de caution", "regler sur place",
        "regler un acompte", "verser un acompte", "acompte par cheque",
        "cheque au courrier", "virement bancaire apres reception",
    ), AXIS_IA),
    Signal("contact_direct_manuel", "Demande à adresser directement, sans parcours guidé", 22, (
        "veuillez nous contacter directement", "contactez-nous directement par",
        "nous contacter directement par email", "nous contacter directement par e-mail",
        "devis personnalise par email", "devis par email ou par telephone",
        "demande a nous adresser",
        "par mail direct", "par courriel direct", "par email direct",
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
    matches: dict[str, list[Detection]] = {}
    seen: set[int] = set()          # indices de preuve déjà récompensés
    for idx, ev in enumerate(evs):
        # v7.1 — « maturite_existante » décrit ce qui fonctionne déjà et
        # « signal_confiance » l'identité de l'entreprise. Aucune des deux
        # n'établit un manque : les scanner comme un besoin produisait des
        # faux positifs (une « boutique en ligne » citée comme contre-signal
        # pouvait contenir « demande de devis » et créer un besoin de devis).
        if str(_ev_field(ev, "kind", "")) in NON_GAP_KINDS:
            continue
        # v8 — seul l'extrait verbatim fait preuve. `detail` est notre
        # reformulation et contient souvent la solution PROPOSÉE : la lire
        # transformait « un paiement en ligne simplifierait… » en
        # « le paiement en ligne existe déjà ».
        text = match_form(str(_ev_field(ev, "quote", "")))
        for sig in catalogue:
            for pattern in sig.patterns:
                if _affirmed(text, match_form(pattern)):
                    matches.setdefault(sig.id, []).append(Detection(
                        signal=sig, matched_pattern=pattern, evidence_index=idx,
                        source_url=str(_ev_field(ev, "source_url")),
                        quote=str(_ev_field(ev, "quote"))[:200],
                        observed=bool(_ev_field(ev, "observed", True)),
                        reliability=str(_ev_field(ev, "reliability", "moyenne")),
                        signal_level=str(_ev_field(ev, "signal_level", "")),
                    ))
                    break

    # Le constat du chercheur est une source distincte, citée comme telle.
    # Indice -1 : il ne se confond avec aucune preuve publiée. Il n'est retenu
    # que s'il existe au moins une preuve réelle.
    if extra_text and evs:
        hint_text = match_form(extra_text)
        for sig in catalogue:
            for pattern in sig.patterns:
                if _affirmed(hint_text, match_form(pattern)):
                    matches.setdefault(sig.id, []).append(Detection(
                        signal=sig, matched_pattern=pattern, evidence_index=-1,
                        source_url="",
                        quote="Constat du chercheur : " + str(extra_text)[:180],
                        observed=True, reliability="moyenne",
                        signal_level="observe",   # constat direct du chercheur
                    ))
                    break

    # Chaque signal est affecté à une preuve qui l'établit et n'a pas encore
    # été récompensée. Les plus forts d'abord, pour ne pas gaspiller une preuve
    # solide sur un indice faible. Un signal sans preuve libre est abandonné :
    # il répéterait une preuve déjà payée.
    for sig_id in sorted(matches, key=lambda k: -matches[k][0].signal.weight):
        candidates = matches[sig_id]
        candidates.sort(key=lambda d: (d.evidence_index == -1, d.evidence_index))
        free = [d for d in candidates if d.evidence_index not in seen]
        if not free:
            continue
        pick = free[0]
        found.append(pick)
        seen.add(pick.evidence_index)
    found.sort(key=lambda d: d.evidence_index)
    return found


def detect_maturity(evidences: Iterable[Any], extra_text: str = "") -> list[Detection]:
    """Contre-signaux de maturité, tous axes confondus (ils réduisent le besoin IA)."""
    evs = list(evidences)
    found: list[Detection] = []
    seen: set[str] = set()
    for idx, ev in enumerate(evs):
        # Un contre-signal est un fait cité par l'entreprise. Notre résumé
        # (`extra_text`) n'est jamais une preuve : il contient trop souvent
        # « pas de réservation en ligne », qui affirmait l'inverse.
        text = match_form(str(_ev_field(ev, "quote", "")))
        for sig in MATURITY_SIGNALS:
            if sig.id in seen:
                continue
            for pattern in sig.patterns:
                if _affirmed(text, match_form(pattern)):
                    found.append(Detection(
                        signal=sig, matched_pattern=pattern, evidence_index=idx,
                        source_url=str(_ev_field(ev, "source_url")),
                        quote=str(_ev_field(ev, "quote"))[:200],
                        observed=bool(_ev_field(ev, "observed", True)),
                        reliability=str(_ev_field(ev, "reliability", "moyenne")),
                        signal_level=str(_ev_field(ev, "signal_level", "")),
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
