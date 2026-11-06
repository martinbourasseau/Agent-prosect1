"""Configuration publique de l'expéditeur (aucun secret ici). — v3"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
CAMPAIGNS_DIR = DATA_DIR / "campaigns"
QUEUE_PATH = DATA_DIR / "queue" / "validation_queue.json"
CRM_PATH = DATA_DIR / "crm" / "prospects.json"
REALISATIONS_PATH = DATA_DIR / "realisations.json"
REFERENCES_PATH = DATA_DIR / "references.json"
SUPPRESSION_PATH = DATA_DIR / "suppression.json"
CAMPAIGN_SETTINGS_PATH = DATA_DIR / "campaigns" / "v4-settings.json"
SEND_LOG_PATH = DATA_DIR / "history" / "send-log.json"
REPLIES_PATH = DATA_DIR / "history" / "replies.json"

SENDER_NAME = os.environ.get("PROSPECTO_SENDER_NAME", "Martin BOURASSEAU")
SENDER_EMAIL = os.environ.get("PROSPECTO_SENDER_EMAIL", "martin.bourasseau4@gmail.com")
PORTFOLIO_URL = os.environ.get("PROSPECTO_PORTFOLIO_URL", "https://prospecto.website")

SIGNATURE_TAGLINE = "Création de sites web · Refonte · Agents IA · Automatisation"

# Garde-fous de génération v3 (email très court, hook dès la 1re phrase).
# Lot 7 : la structure v5 ajoute un segment « observation » (conséquence du fait
# cité) aux quatre segments v4. Le plafond passe de 150 à 170 mots pour accueillir ce
# segment sans sacrifier l'accroche sourcée. 170 mots restent un e-mail court
# (~1 150 caractères, lecture inférieure à une minute) ; les amorces de
# démonstration ont été raccourcies pour compenser.
MAX_BODY_WORDS = 170
MIN_BODY_WORDS = 40
MAX_SUBJECT_CHARS = 70
OPT_OUT_LINE = (
    "Si le sujet ne vous concerne pas, répondez « ne pas me relancer » : "
    "je le note et je ne vous écrirai plus."
)
CTA_V3 = "Seriez-vous intéressé pour la découvrir ?"

# Promesses interdites : la démo gratuite est toujours limitée.
FORBIDDEN_PROMISES = [
    "site complet gratuit",
    "site entièrement gratuit",
    "refonte complète gratuite",
    "refonte entièrement gratuite",
    "agent complet gratuit",
    "automatisation complète gratuite",
    "réalisation complète gratuite",
    "tout gratuitement",
]

# Niveaux de priorité CRM (mission v3).
TIER_HAUTE = "haute"            # besoin explicitement exprimé + contact exploitable
TIER_MOYENNE = "moyenne"        # besoin fortement probable, éléments concrets
TIER_A_APPROFONDIR = "a_approfondir"  # opportunité intéressante, infos insuffisantes
TIERS = (TIER_HAUTE, TIER_MOYENNE, TIER_A_APPROFONDIR)


def signature() -> str:
    return f"Bonne journée,\n{SENDER_NAME}\n{SIGNATURE_TAGLINE}\n{PORTFOLIO_URL}"
