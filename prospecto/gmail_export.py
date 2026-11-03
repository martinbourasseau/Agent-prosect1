"""Export de la file vers des brouillons Gmail.

Deux sorties :
1. JSON « prêt connecteur » : consommé par l'agent pour créer les brouillons
   via le connecteur Gmail sécurisé (aucun token dans ce dépôt).
2. Fichiers .eml (fallback local) : importables dans un client mail.

Règle absolue : n'exporter que des emails APPROVED (validés humainement),
sauf demande explicite d'export de prévisualisation. Jamais d'envoi.
"""
from __future__ import annotations

import json
from email.message import EmailMessage
from pathlib import Path

from .config import SENDER_NAME, SENDER_EMAIL, DATA_DIR
from .queue import ValidationQueue, APPROVED


def export_for_gmail(
    queue: ValidationQueue,
    out_path: Path | None = None,
    status: str = APPROVED,
) -> Path:
    """Export JSON des emails validés, prêt pour création de brouillons Gmail."""
    items = queue.list(status=status)
    payload = {
        "purpose": "Création de BROUILLONS Gmail (jamais d'envoi automatique)",
        "from": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "status_filter": status,
        "count": len(items),
        "drafts": [
            {
                "queue_id": i.id,
                "to": [i.to],
                "subject": i.subject,
                "body_text": i.body,
                "company": i.company,
                "campaign": i.campaign,
                "evidence_sources": i.evidence_sources,
            }
            for i in items
        ],
    }
    out_path = out_path or (DATA_DIR / "queue" / "gmail_drafts_export.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out_path


def export_eml(queue: ValidationQueue, out_dir: Path, status: str = APPROVED) -> list[Path]:
    """Fallback : un fichier .eml par email validé (brouillon importable)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for item in queue.list(status=status):
        msg = EmailMessage()
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = item.to
        msg["Subject"] = item.subject
        msg.set_content(item.body)
        path = out_dir / f"{item.id}.eml"
        path.write_bytes(bytes(msg))
        paths.append(path)
    return paths
