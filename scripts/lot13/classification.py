"""Classification qualitative A/B/C/D du Lot 13.

POURQUOI UN MODULE SÉPARÉ
-------------------------
La classification répond à « quelle est la nature de la preuve du besoin ? ».
La priorité commerciale du CRM répond à « faut-il contacter maintenant, et dans
quel ordre ? ». Ce sont deux questions différentes : une entreprise peut être
catégorie A (besoin exprimé) et priorité moyenne (consultation déjà close, donc
accessibilité douteuse). Confondre les deux produirait exactement l'erreur du
Lot 11, où un bandeau « DISPONIBLE POUR DE NOUVEAUX PROJETS » avait été typé
`public_need` et faisait monter une fiche à 92.

RÈGLES
------
A — besoin explicite : l'entreprise demande publiquement une prestation qui
    relève de l'offre Prospecto, ET son identité est établie, ET le signal a
    été lu sur une page accessible, ET il est encore pertinent.
B — opportunité observée : un processus ou un défaut concret est observé sur
    une source officielle, mais l'entreprise ne demande rien publiquement.
C — hypothèse : les éléments sont insuffisants (identité masquée, rattachement
    non établi, page non lue, signal vu seulement en résultat de recherche).
D — non pertinente : aucun besoin crédible, ou contre-signal disqualifiant
    (signal expiré, vendeur de solution, prestataire déjà en place, hors cible).

D est prioritaire sur tout : un contre-signal disqualifiant ne se compense pas
par une preuve forte. C'est ce qui empêche de requalifier en A un appel d'offres
pourtant explicite mais clos depuis un an.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CATEGORY_A = "A"
CATEGORY_B = "B"
CATEGORY_C = "C"
CATEGORY_D = "D"
CATEGORIES = (CATEGORY_A, CATEGORY_B, CATEGORY_C, CATEGORY_D)

LABELS = {
    CATEGORY_A: "Besoin explicite",
    CATEGORY_B: "Opportunité observée",
    CATEGORY_C: "Hypothèse",
    CATEGORY_D: "Non pertinente",
}

# Motifs de disqualification. Chacun est un fait vérifiable, pas une opinion.
DISQUALIFIERS = (
    "signal_expire",
    "vendeur_de_solution",
    "prestataire_deja_en_place",
    "hors_cible_taille",
    "hors_cible_statut",
    "hors_territoire",
    "agregateur",
    "reseau_decision_mutualisee",
    "attribution_deja_prononcee",
)


@dataclass
class Signal:
    """Un signal commercial candidat, avant décision."""

    company: str
    # Le besoin est-il demandé par l'entreprise elle-même ?
    expressed: bool = False
    # L'entreprise est-elle identifiée sans ambiguïté (nom + site ou adresse) ?
    identity_established: bool = False
    # La page portant le signal a-t-elle été réellement récupérée et lue ?
    page_read: bool = False
    # Le signal est-il encore actionnable à la date de la session ?
    still_relevant: bool = True
    # Un processus ou un défaut a-t-il été observé sur une source officielle ?
    observed: bool = False
    # Motifs de disqualification, choisis dans DISQUALIFIERS.
    disqualifiers: list[str] = field(default_factory=list)
    # Lien entre le signal et l'entreprise : établi, ou seulement probable ?
    attachment_established: bool = True

    def validate(self) -> list[str]:
        errors = []
        if not self.company.strip():
            errors.append("entreprise vide")
        for d in self.disqualifiers:
            if d not in DISQUALIFIERS:
                errors.append(f"motif de disqualification inconnu : {d}")
        if self.expressed and not self.page_read:
            errors.append("un besoin exprimé doit être lu, pas seulement vu en recherche")
        if self.observed and not self.page_read:
            errors.append("une opportunité observée suppose une page lue")
        return errors


def classify(signal: Signal) -> tuple[str, list[str]]:
    """Retourne (catégorie, motifs). Ne lève pas : `validate()` précède."""
    reasons: list[str] = []

    if signal.disqualifiers:
        reasons.append("contre-signal disqualifiant : " + ", ".join(signal.disqualifiers))
        return CATEGORY_D, reasons

    if not signal.still_relevant:
        reasons.append("signal non pertinent à la date de la session")
        return CATEGORY_D, reasons

    if not signal.identity_established:
        reasons.append("identité de l'entreprise non établie : aucune fiche possible")
        return CATEGORY_C, reasons

    if not signal.attachment_established:
        reasons.append("rattachement du signal à cette entreprise non établi")
        return CATEGORY_C, reasons

    if not signal.page_read:
        reasons.append("aucune page lue : le signal reste non vérifié")
        return CATEGORY_C, reasons

    if signal.expressed:
        reasons.append("besoin demandé publiquement par l'entreprise, lu et encore pertinent")
        return CATEGORY_A, reasons

    if signal.observed:
        reasons.append("processus ou défaut observé sur source officielle, sans demande publique")
        return CATEGORY_B, reasons

    reasons.append("éléments insuffisants pour établir un besoin")
    return CATEGORY_C, reasons


def importable(category: str) -> bool:
    """Seules A et B peuvent produire une fiche CRM.

    C est conservé au journal comme piste à approfondir, jamais importé : une
    hypothèse ne doit pas occuper le CRM comme une opportunité. D est un rejet.
    """
    return category in (CATEGORY_A, CATEGORY_B)
