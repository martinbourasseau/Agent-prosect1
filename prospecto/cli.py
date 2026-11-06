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
from .crm import CRM
from .config import CAMPAIGNS_DIR, QUEUE_PATH, TIER_HAUTE, TIER_MOYENNE
from .messaging import compose_email, check_email_v4, select_variant
from .references import load_references, select_reference
from .deliverability import analyze_sender, provider_daily_limit
from .sender import Sender, load_settings, save_settings
from .suppression import SuppressionList
from .replies import ReplyHandler
from .metrics import compute_metrics


def _load_prospects(path: Path) -> list[Prospect]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("prospects", raw) if isinstance(raw, dict) else raw
    return [Prospect.from_dict(e) for e in entries]


def cmd_qualify(args: argparse.Namespace) -> int:
    prospects = _load_prospects(Path(args.prospects))
    results = qualify_batch(prospects)
    for res in results:
        print(f"[{res.tier:>14}] {res.score:>3}  {res.prospect.company} <{res.prospect.contact_email}>")
        for reason in res.reasons:
            print(f"               - {reason}")
    haute = [r for r in results if r.tier == TIER_HAUTE]
    moyenne = [r for r in results if r.tier == TIER_MOYENNE]
    print(f"\n{len(haute)} priorité haute, {len(moyenne)} moyenne, {len(results)} au total.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    prospects = _load_prospects(Path(args.prospects))
    results = qualify_batch(prospects)
    queue = ValidationQueue(Path(args.queue) if args.queue else None)
    crm = CRM()
    wanted = {TIER_HAUTE, TIER_MOYENNE} if args.include_moyenne else {TIER_HAUTE}
    generated = []
    for res in results:
        # Enregistrer dans le CRM (sans écraser), quel que soit le niveau.
        rec, created = crm.import_prospect(res.prospect, res)
        if res.tier not in wanted:
            print(f"CRM {'+' if created else '='} {res.prospect.company} [{res.tier}] (pas d'email)")
            continue
        try:
            email = generate_email(res.prospect)
        except GenerationError as exc:
            print(f"ÉCHEC génération {res.prospect.company} : {exc}")
            continue
        if args.dry_run:
            print(f"--- {res.prospect.company} [{res.tier}] ---\nObjet : {email.subject}\n{email.body}")
            continue
        try:
            item = queue.add(email, campaign=args.campaign)
        except ValueError as exc:
            print(f"déjà en file : {exc}")
            continue
        rec["status"] = "email_préparé"
        rec["proposed_email"] = {"subject": email.subject, "body": email.body, "queue_id": item.id}
        generated.append({"queue_id": item.id, **email.to_dict(), "score": res.score, "tier": res.tier})
        print(f"en file : {item.id} [{res.tier}] → {email.to} | {email.subject}")

    crm.save()
    if generated and not args.dry_run:
        CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
        out = CAMPAIGNS_DIR / f"{args.campaign}.json"
        payload = {
            "campaign": args.campaign,
            "strategy": "v3 — hook percutant + démo gratuite (docs/strategie-commerciale-v3.md)",
            "generated_count": len(generated),
            "emails": generated,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nCampagne écrite : {out}")
    return 0


def cmd_crm(args: argparse.Namespace) -> int:
    crm = CRM()
    if args.action == "import":
        prospects = _load_prospects(Path(args.prospects))
        results = qualify_batch(prospects)
        created = 0
        for res in results:
            _, was_created = crm.import_prospect(res.prospect, res)
            created += 1 if was_created else 0
            print(f"{'+' if was_created else '='} {res.prospect.company} [{res.tier}]")
        crm.save()
        print(f"\n{created} nouveaux, {len(results) - created} fusionnés. Total CRM : {len(crm.records)}")
    elif args.action == "init-history":
        n = crm.mark_history_contacted()
        crm.save()
        print(f"{n} entreprises de l'historique marquées contactées. Total CRM : {len(crm.records)}")
    elif args.action == "list":
        for r in crm.records:
            if args.tier and r.get("tier") != args.tier:
                continue
            print(f"[{r.get('tier', '?'):>14}] {r.get('company')} <{r.get('email', '')}> — {r.get('need', '')} ({r.get('status', '')})")
    elif args.action == "stats":
        print(json.dumps(crm.stats(), ensure_ascii=False, indent=2))
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


def cmd_generate_v4(args: argparse.Namespace) -> int:
    """Génère des emails v4 (variantes + références) et les met en file."""
    prospects = _load_prospects(Path(args.prospects))
    results = qualify_batch(prospects)
    queue = ValidationQueue(Path(args.queue) if args.queue else None)
    crm = CRM()
    wanted = {TIER_HAUTE, TIER_MOYENNE} if args.include_moyenne else {TIER_HAUTE}
    generated = []
    for res in results:
        rec, created = crm.import_prospect(res.prospect, res)
        if res.tier not in wanted:
            print(f"CRM {'+' if created else '='} {res.prospect.company} [{res.tier}] (pas d'email)")
            continue
        try:
            email = compose_email(res.prospect, variant=args.variant or "")
            problems = check_email_v4(email, res.prospect)
            if problems:
                raise GenerationError(" ; ".join(problems))
        except (GenerationError, ValueError) as exc:
            print(f"ÉCHEC génération {res.prospect.company} : {exc}")
            continue
        if args.dry_run:
            print(f"--- {res.prospect.company} [{res.tier}] variante={email.variant} réf={email.reference_id or '—'} ---")
            print(f"Objet : {email.subject}\n{email.body}")
            continue
        try:
            item = queue.add(email, campaign=args.campaign)
        except ValueError as exc:
            print(f"déjà en file : {exc}")
            continue
        rec["status"] = "email_préparé"
        rec["campaign"] = args.campaign
        rec["variant"] = email.variant
        rec["reference_id"] = email.reference_id
        rec["message_version"] = "v4"
        rec["proposed_email"] = {"subject": email.subject, "body": email.body, "queue_id": item.id}
        generated.append({"queue_id": item.id, **email.to_dict(), "score": res.score, "tier": res.tier})
        print(f"en file : {item.id} [{res.tier}] v={email.variant} → {email.to} | {email.subject}")
    crm.save()
    if generated and not args.dry_run:
        CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
        out = CAMPAIGNS_DIR / f"{args.campaign}.json"
        out.write_text(json.dumps({
            "campaign": args.campaign, "strategy": "v4 — variantes + références + démo gratuite",
            "generated_count": len(generated), "emails": generated,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nCampagne écrite : {out}")
    return 0


def cmd_references(args: argparse.Namespace) -> int:
    refs = load_references()
    if args.action == "list":
        for r in refs:
            print(f"[{'x' if r.enabled else ' '}] {r.id} — {r.name} ({r.kind}) → {r.url}")
            print(f"    besoins: {', '.join(r.need_tags)} | secteurs: {', '.join(r.sector_tags)}")
            print(f"    paternité: {r.authorship_status}")
    elif args.action == "select":
        prospects = _load_prospects(Path(args.prospects))
        for p in prospects:
            ref = select_reference(p, refs)
            print(f"{p.company} [{p.primary_need}] → {ref.id if ref else 'aucune'}")
    return 0


def cmd_deliverability(args: argparse.Namespace) -> int:
    settings = load_settings()
    email = args.email or settings.get("sender", {}).get("email", "")
    rep = analyze_sender(email)
    print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    print("\nLimite fournisseur indicative :", json.dumps(provider_daily_limit(rep.domain), ensure_ascii=False))
    return 0


def cmd_campaign(args: argparse.Namespace) -> int:
    sender = Sender()
    s = sender.settings
    if args.action == "status":
        print(json.dumps({
            "enabled": s.get("enabled"), "dry_run": s.get("dry_run"),
            "transport": s.get("transport"), "limits": s.get("limits"),
            "stop_conditions": s.get("stop_conditions"),
            "last_deliverability": s.get("deliverability", {}).get("last_result", {}),
        }, ensure_ascii=False, indent=2))
    elif args.action == "preflight":
        ok, issues = sender.preflight()
        print("PRÉ-VOL :", "OK ✅" if ok else "BLOQUÉ ❌")
        for i in issues:
            print("  -", i)
        return 0 if ok else 1
    elif args.action == "activate":
        ok, issues = sender.preflight()
        if not ok and not args.force:
            print("Activation refusée — contrôles non passés :")
            for i in issues:
                print("  -", i)
            print("Corrigez ces points, ou utilisez --force (déconseillé) après revue humaine.")
            return 1
        s["enabled"] = True
        s["dry_run"] = not args.live
        s["activated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")
        s["activated_by"] = args.by or "Martin"
        save_settings(s)
        print(f"Campagne activée (dry_run={s['dry_run']}, transport={s.get('transport')}).")
        if s["dry_run"]:
            print("Mode simulation. Pour un envoi réel : campaign activate --live (après revue).")
    elif args.action == "pause":
        s["enabled"] = False
        save_settings(s)
        print("Campagne mise en pause (enabled=false).")
    elif args.action == "run":
        if not s.get("enabled"):
            print("Campagne non activée. Utilisez 'campaign activate' d'abord.")
            return 1
        ok, issues = sender.preflight()
        if not ok and not s.get("dry_run", True):
            print("Envoi réel bloqué — pré-vol échoué :")
            for i in issues:
                print("  -", i)
            return 1
        crm = CRM()
        queue = ValidationQueue()
        candidates = sender.select_candidates(crm.records, [i.to_dict() for i in queue.items])
        plan = sender.build_plan(candidates)
        print(f"{len(candidates)} candidats qualifiés, {len(plan)} dans le plan (limites/ramp-up).")
        results = sender.execute(plan, transport=args.transport)
        for r in results:
            print(f"  [{r.get('status')}] {r.get('to', '')} {r.get('subject', '')}")
            if r.get("error"):
                print("      erreur :", r["error"])
        # Met à jour la file / le CRM pour les envois réels.
        for r in results:
            if r.get("status") == "sent" and r.get("queue_id"):
                try:
                    queue.mark_sent(r["queue_id"], r.get("message_id", ""))
                except (KeyError, ValueError):
                    pass
        print("Terminé.")
    return 0


def cmd_replies(args: argparse.Namespace) -> int:
    crm = CRM()
    handler = ReplyHandler(crm)
    if args.action == "process":
        raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
        messages = raw.get("messages", raw) if isinstance(raw, dict) else raw
        for m in messages:
            res = handler.process_reply(
                from_email=m.get("from", ""), text=m.get("text", m.get("body", "")),
                subject=m.get("subject", ""), message_id=m.get("message_id", ""),
                thread_id=m.get("thread_id", ""),
            )
            print(f"[{res.intent}] {res.email} ({res.company}) → {res.crm_status} | {res.next_action}")
            if res.suppressed:
                print("    → ajouté à la liste de suppression")
    elif args.action == "list":
        for rp in handler.replies:
            print(f"[{rp.get('intent')}] {rp.get('from')} → {rp.get('crm_status')}")
    elif args.action == "classify":
        from .replies import classify_intent
        print(classify_intent(args.text or ""))
    return 0


def cmd_suppression(args: argparse.Namespace) -> int:
    sl = SuppressionList()
    if args.action == "add":
        ok = sl.add(email=args.email or "", domain=args.domain or "", reason=args.reason or "manuel")
        print("ajouté" if ok else "déjà présent / rien à ajouter")
    elif args.action == "remove":
        print("retiré" if sl.remove(args.email or "") else "introuvable")
    elif args.action == "list":
        for e in sl.entries:
            print(f"{e.get('email') or e.get('domain')} — {e.get('reason')} ({e.get('added_at')})")
        print(f"\nTotal : {sl.count()}")
    elif args.action == "check":
        print("SUPPRIMÉ" if sl.is_suppressed(args.email or "") else "non supprimé")
    return 0


def cmd_reconcile_sent(args: argparse.Namespace) -> int:
    """Aligne file / CRM / journal sur les envois constatés dans Gmail (aucun envoi)."""
    from .reconcile import reconcile_sent
    from .sender import SendLog

    raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
    observed = raw.get("observed", raw) if isinstance(raw, dict) else raw
    crm, queue = CRM(), ValidationQueue()
    log = SendLog() if args.apply else None
    if not args.apply:
        print("(lecture seule : --apply pour enregistrer)")
        for obs in observed:
            hit = [i for i in queue.items if i.to.lower() == (obs.get("to") or "").lower()
                   and i.subject == obs.get("subject")]
            print(f"  {obs.get('to'):<42} {'→ ' + hit[0].id + ' [' + hit[0].status + ']' if hit else 'NON RAPPROCHÉ'}")
        return 0
    res = reconcile_sent(observed, crm, queue, log, observed_at=raw.get("observed_at", ""))
    print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
    print(f"\n{res.matched} éléments alignés sur « sent », {res.already_sent} déjà à jour, "
          f"{len(res.unmatched)} non rapprochés")
    return 0


def cmd_verify_emails(args: argparse.Namespace) -> int:
    """Contrôle DNS (MX) des adresses du CRM — aucune connexion SMTP, aucun envoi."""
    from .email_verify import verify_records, verify_email, DomainCache

    if args.email:
        print(json.dumps(verify_email(args.email), ensure_ascii=False, indent=2))
        return 0
    crm = CRM()
    summary = verify_records(crm.records, cache=DomainCache(), refresh=args.refresh)
    if args.apply:
        crm.save()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n{summary['checked']} adresses contrôlées — "
          f"{summary['deliverable']} routables, {summary['risky']} à risque, "
          f"{summary['blocking']} non délivrables")
    if not args.apply:
        print("(lecture seule : utiliser --apply pour enregistrer dans le CRM)")
    return 1 if summary["blocking"] else 0


def cmd_audit_inbox(args: argparse.Namespace) -> int:
    """Audit de la boîte : rebonds, accusés automatiques, réponses humaines."""
    from .inbox_audit import audit_inbox, apply_findings, save_audit
    from .sender import SendLog

    raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
    messages = raw.get("messages", raw) if isinstance(raw, dict) else raw
    crm = CRM()
    queue = ValidationQueue()
    findings = audit_inbox(messages, crm.records, queue.items)
    for f in findings:
        tag = f"{f.intent}/{f.severity}" if f.severity else f.intent
        print(f"[{tag}] {f.company or 'NON RATTACHÉ'} ← {f.from_email} "
              f"(destinataire réel : {f.recipient or '?'}, via {f.matched_by})")
        print(f"    {f.subject}")
    if args.apply:
        report = apply_findings(findings, crm, SuppressionList(), SendLog(), queue)
        save_audit(findings)
        print("\n" + json.dumps(report, ensure_ascii=False, indent=2))
    else:
        save_audit(findings)
        print("\n(constats enregistrés ; CRM non modifié — utiliser --apply)")
    return 0


def cmd_scores(args: argparse.Namespace) -> int:
    """(Re)calcule les trois scores indépendants et la priorité commerciale."""
    from .scoring import scores_from_record, AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA

    crm = CRM()
    touched = 0
    for rec in crm.records:
        if args.lot and (rec.get("lot") or "") != args.lot:
            continue
        scores = scores_from_record(rec)
        rec["scores"] = scores
        rec["commercial_priority"] = scores["priority"]
        touched += 1
        if args.verbose:
            print(f"\n{rec.get('company')} — priorité {scores['priority']}")
            for axis in (AXIS_SITE_WEB, AXIS_REFONTE, AXIS_IA):
                data = scores[axis]
                print(f"  {axis:<18} {data['score']:>3}/100 ({data['level']})")
                for reason in data["reasons"]:
                    print(f"      · {reason}")
    if args.apply:
        crm.save()
    print(f"\n{touched} fiches scorées" + ("" if args.apply else " (lecture seule, --apply pour enregistrer)"))
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    print(json.dumps(compute_metrics(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prospecto", description="Moteur de prospection Prospecto (v4)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("qualify", help="qualifier des prospects (score + preuves + niveau)")
    p.add_argument("prospects", help="fichier JSON des prospects")
    p.set_defaults(func=cmd_qualify)

    p = sub.add_parser("generate", help="générer les emails (haute, +moyenne si demandé) et les mettre en file")
    p.add_argument("prospects", help="fichier JSON des prospects")
    p.add_argument("--campaign", required=True, help="nom de campagne (ex. 2026-11-03-v3)")
    p.add_argument("--queue", help="chemin de la file (défaut : data/queue/validation_queue.json)")
    p.add_argument("--dry-run", action="store_true", help="afficher sans mettre en file")
    p.add_argument("--include-moyenne", action="store_true", help="inclure les prospects de priorité moyenne")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("crm", help="base de prospects enrichie (import, list, stats, init-history)")
    p.add_argument("action", choices=["import", "list", "stats", "init-history"])
    p.add_argument("prospects", nargs="?", help="fichier JSON à importer (action import)")
    p.add_argument("--tier", choices=["haute", "moyenne", "a_approfondir"], help="filtre (list)")
    p.set_defaults(func=cmd_crm)

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

    # ---- v4 ----
    p = sub.add_parser("generate-v4", help="générer des emails v4 (variantes + références) en file")
    p.add_argument("prospects"); p.add_argument("--campaign", required=True)
    p.add_argument("--queue"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--include-moyenne", action="store_true")
    p.add_argument("--variant", help="variante forcée (sinon sélection auto)")
    p.set_defaults(func=cmd_generate_v4)

    p = sub.add_parser("references", help="bibliothèque de références commerciales")
    p.add_argument("action", choices=["list", "select"])
    p.add_argument("prospects", nargs="?")
    p.set_defaults(func=cmd_references)

    p = sub.add_parser("deliverability", help="contrôles SPF/DKIM/DMARC du domaine expéditeur")
    p.add_argument("--email", help="email expéditeur (défaut : paramètres campagne)")
    p.set_defaults(func=cmd_deliverability)

    p = sub.add_parser("campaign", help="campagne d'envoi automatisé sous contrôles")
    p.add_argument("action", choices=["status", "preflight", "activate", "pause", "run"])
    p.add_argument("--live", action="store_true", help="désactive dry_run (envoi réel)")
    p.add_argument("--force", action="store_true", help="active malgré pré-vol (déconseillé)")
    p.add_argument("--by", help="qui active")
    p.add_argument("--transport", choices=["dry_run", "smtp", "gmail_connector"])
    p.set_defaults(func=cmd_campaign)

    p = sub.add_parser("replies", help="réception / interprétation des réponses")
    p.add_argument("action", choices=["process", "list", "classify"])
    p.add_argument("--file", help="JSON des messages reçus (process)")
    p.add_argument("--text", help="texte à classifier (classify)")
    p.set_defaults(func=cmd_replies)

    p = sub.add_parser("suppression", help="liste de suppression centralisée")
    p.add_argument("action", choices=["add", "remove", "list", "check"])
    p.add_argument("--email"); p.add_argument("--domain"); p.add_argument("--reason")
    p.set_defaults(func=cmd_suppression)

    p = sub.add_parser("metrics", help="métriques agrégées (CRM, envois, réponses, performance)")
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("reconcile-sent", help="constater les envois faits hors agent et aligner file/CRM/journal")
    p.add_argument("--file", required=True, help="JSON des messages relevés dans « Envoyés »")
    p.add_argument("--apply", action="store_true", help="enregistrer la réconciliation")
    p.set_defaults(func=cmd_reconcile_sent)

    p = sub.add_parser("verify-emails", help="contrôle DNS/MX des adresses (aucun envoi, aucune connexion SMTP)")
    p.add_argument("--email", help="vérifier une adresse isolée")
    p.add_argument("--apply", action="store_true", help="enregistrer le résultat dans le CRM")
    p.add_argument("--refresh", action="store_true", help="ignorer le cache DNS")
    p.set_defaults(func=cmd_verify_emails)

    p = sub.add_parser("audit-inbox", help="audit fiable des rebonds / accusés / réponses")
    p.add_argument("--file", required=True, help="JSON des messages Gmail récupérés")
    p.add_argument("--apply", action="store_true", help="appliquer au CRM, suppression, journal, file")
    p.set_defaults(func=cmd_audit_inbox)

    p = sub.add_parser("scores", help="trois scores indépendants (site, refonte, IA) + priorité")
    p.add_argument("--lot", help="limiter à un lot")
    p.add_argument("--apply", action="store_true", help="enregistrer dans le CRM")
    p.add_argument("--verbose", action="store_true", help="afficher les justifications")
    p.set_defaults(func=cmd_scores)

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
