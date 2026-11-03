"""CLI Prospecto : qualification, génération, file de validation, export Gmail."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import Prospect
from .qualification import qualify_batch, QUALIFIED
from .generator import generate_email, GenerationError
from .queue import ValidationQueue, STATUSES
from .gmail_export import export_for_gmail, export_eml
from .research import audit_html
from .config import CAMPAIGNS_DIR, QUEUE_PATH


def _load_prospects(path: Path) -> list[Prospect]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("prospects", raw) if isinstance(raw, dict) else raw
    return [Prospect.from_dict(e) for e in entries]


def cmd_qualify(args: argparse.Namespace) -> int:
    prospects = _load_prospects(Path(args.prospects))
    results = qualify_batch(prospects)
    for res in results:
        print(f"[{res.status:>12}] {res.score:>3}  {res.prospect.company} <{res.prospect.contact_email}>")
        for reason in res.reasons:
            print(f"               - {reason}")
    qualified = [r for r in results if r.status == QUALIFIED]
    print(f"\n{len(qualified)}/{len(results)} prospects qualifiés.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    prospects = _load_prospects(Path(args.prospects))
    results = qualify_batch(prospects)
    queue = ValidationQueue(Path(args.queue) if args.queue else None)
    generated = []
    for res in results:
        if res.status != QUALIFIED:
            print(f"ignoré ({res.status}) : {res.prospect.company}")
            continue
        try:
            email = generate_email(res.prospect)
        except GenerationError as exc:
            print(f"ÉCHEC génération {res.prospect.company} : {exc}")
            continue
        if args.dry_run:
            print(f"--- {res.prospect.company} ---\nObjet : {email.subject}\n{email.body}")
            continue
        try:
            item = queue.add(email, campaign=args.campaign)
        except ValueError as exc:
            print(f"déjà en file : {exc}")
            continue
        generated.append({"queue_id": item.id, **email.to_dict(), "score": res.score})
        print(f"en file : {item.id} → {email.to} | {email.subject}")

    if generated and not args.dry_run:
        CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
        out = CAMPAIGNS_DIR / f"{args.campaign}.json"
        payload = {
            "campaign": args.campaign,
            "strategy": "v2 — démonstration gratuite personnalisée (docs/strategie-commerciale.md)",
            "generated_count": len(generated),
            "emails": generated,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nCampagne écrite : {out}")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    queue = ValidationQueue(Path(args.queue) if args.queue else None)
    if args.action == "list":
        items = queue.list(status=args.status, campaign=args.campaign)
        for item in items:
            print(f"{item.id}  [{item.status:>8}]  {item.company} <{item.to}>")
            print(f"    Objet : {item.subject}")
            if item.gmail_draft_id:
                print(f"    Brouillon Gmail : {item.gmail_draft_id}")
        counts = queue.counts()
        print("\nTotal : " + ", ".join(f"{s}={counts[s]}" for s in STATUSES))
    elif args.action == "show":
        item = queue.get(args.id)
        print(json.dumps(item.to_dict(), ensure_ascii=False, indent=2))
    elif args.action == "approve":
        item = queue.approve(args.id)
        print(f"approuvé : {item.id} ({item.company})")
    elif args.action == "reject":
        item = queue.reject(args.id, args.reason or "")
        print(f"rejeté : {item.id} ({item.company})")
    elif args.action == "attach-draft":
        item = queue.attach_draft(args.id, args.draft_id)
        print(f"brouillon attaché : {item.id} → {item.gmail_draft_id}")
    elif args.action == "mark-sent":
        item = queue.mark_sent(args.id, args.message_id or "")
        print(f"marqué envoyé : {item.id}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    queue = ValidationQueue(Path(args.queue) if args.queue else None)
    if args.format == "json":
        out = export_for_gmail(queue, Path(args.out) if args.out else None, status=args.status)
        print(f"export Gmail (brouillons uniquement) : {out}")
    else:
        paths = export_eml(queue, Path(args.out or "data/local_exports/eml"), status=args.status)
        for p in paths:
            print(f"écrit : {p}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    html = Path(args.html).read_text(encoding="utf-8", errors="replace")
    audit = audit_html(html, args.url)
    print(json.dumps({
        "url": audit.url,
        "https_ok": audit.https_ok,
        "has_contact_form": audit.has_contact_form,
        "has_mailto": audit.has_mailto,
        "has_tel_link": audit.has_tel_link,
        "has_visible_cta": audit.has_visible_cta,
        "gaps": audit.gaps,
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prospecto", description="Moteur de prospection Prospecto (v2)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("qualify", help="qualifier des prospects (score + preuves)")
    p.add_argument("prospects", help="fichier JSON des prospects")
    p.set_defaults(func=cmd_qualify)

    p = sub.add_parser("generate", help="générer les emails des prospects qualifiés et les mettre en file")
    p.add_argument("prospects", help="fichier JSON des prospects")
    p.add_argument("--campaign", required=True, help="nom de campagne (ex. 2026-11-03-v2)")
    p.add_argument("--queue", help="chemin de la file (défaut : data/queue/validation_queue.json)")
    p.add_argument("--dry-run", action="store_true", help="afficher sans mettre en file")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("queue", help="file de validation humaine")
    p.add_argument("action", choices=["list", "show", "approve", "reject", "attach-draft", "mark-sent"])
    p.add_argument("id", nargs="?", help="identifiant de l'élément")
    p.add_argument("--status", choices=list(STATUSES), help="filtre (list)")
    p.add_argument("--campaign", help="filtre (list)")
    p.add_argument("--reason", help="motif de rejet")
    p.add_argument("--draft-id", help="id du brouillon Gmail (attach-draft)")
    p.add_argument("--message-id", help="id du message envoyé (mark-sent)")
    p.add_argument("--queue", help="chemin de la file")
    p.set_defaults(func=cmd_queue)

    p = sub.add_parser("export", help="exporter pour brouillons Gmail (jamais d'envoi)")
    p.add_argument("--format", choices=["json", "eml"], default="json")
    p.add_argument("--status", default="approved", choices=list(STATUSES))
    p.add_argument("--out", help="chemin de sortie")
    p.add_argument("--queue", help="chemin de la file")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("audit", help="audit factuel d'une page HTML récupérée")
    p.add_argument("--html", required=True, help="fichier HTML local")
    p.add_argument("--url", required=True, help="URL d'origine (schéma https inclus)")
    p.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
