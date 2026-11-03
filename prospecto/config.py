"""Configuration publique de l'expéditeur (aucun secret ici)."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
CAMPAIGNS_DIR = DATA_DIR / "campaigns"
QUEUE_PATH = DATA_DIR / "queue" / "validation_queue.json"

SENDER_NAME = os.environ.get("PROSPECTO_SENDER_NAME", "Martin BOURASSEAU")
SENDER_EMAIL = os.environ.get("PROSPECTO_SENDER_EMAIL", "martin.bourasseau4@gmail.com")
PORTFOLIO_URL = os.environ.get("PROSPECTO_PORTFOLIO_URL", "https://prospecto.website")

SIGNATURE_TAGLINE = "Création web · Agents IA · Automatisation"

# Garde-fous de génération (docs/strategie-commerciale.md §2)
MAX_BODY_WORDS = 170
MIN_BODY_WORDS = 60
MAX_SUBJECT_CHARS = 70
OPT_OUT_LINE = (
    "Si le sujet ne vous concerne pas, répondez « ne pas me relancer » : "
    "je le note et je ne vous écrirai plus."
)

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


def signature() -> str:
    return (
        f"Bonne journée,\n{SENDER_NAME}\n{SIGNATURE_TAGLINE}\n{PORTFOLIO_URL}"
    )
