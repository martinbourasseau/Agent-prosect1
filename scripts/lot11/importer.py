"""Import du Lot 11 — simulation par défaut, --applique pour écrire.

Règles tenues :
  * dédoublonnage sur domaine, e-mail ET nom normalisé avant toute création ;
  * aucune fiche existante n'est écrasée : si une collision est détectée, la
    fiche est laissée intacte et la collision est journalisée ;
  * les trois axes v8 et la priorité v10 sont ceux calculés par le moteur du
    dépôt, sans retouche manuelle ;
  * chaque fiche porte son historique de création et la provenance de l'adresse.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from prospecto.crm import CRM
from prospecto.config import SUPPRESSION_PATH
from prospecto.priority import ENGINE_VERSION
from prospecto.sources import ExplorationLedger
from prospecto.scoring import AXES
from fiches import FICHES, build, D, LOT

ARCHIVE = Path("data/history/lot11-recherches-2026-11-09.json")


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--applique", action="store_true")
    args = ap.parse_args()

    crm = CRM()
    before = len(crm.records)
    # Empreintes des fiches existantes : aucun écrasement autorisé.
    existing_domains = {(r.get("domain") or "").lower() for r in crm.records if r.get("domain")}
    existing_emails = {(r.get("email") or "").lower() for r in crm.records if r.get("email")}
    existing_names = {norm(r.get("company", "")) for r in crm.records}
    frozen = {r.get("id"): json.dumps(r, ensure_ascii=False, sort_keys=True) for r in crm.records}

    sup = json.loads(SUPPRESSION_PATH.read_text(encoding="utf-8"))
    sup_emails = {e["email"].lower() for e in sup.get("entries", [])}
    sup_domains = {e["domain"].lower() for e in sup.get("entries", []) if e.get("domain_wide")}

    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    # Domaines alternatifs observés : ils ne doivent pas créer de fiche séparée.
    alias = {"multi-pneus-36.fr": "multipneus36.fr", "multi-pneus.fr": "multipneus36.fr",
             "cs-depannages-reims.com": "cs-depannages.com"}

    rows, collisions, blocked = [], [], []
    for fiche in FICHES:
        r = build(fiche)
        p, scores, a = r["prospect"], r["scores"], r["assessment"]
        domain = fiche["domain"].lower()
        email = (fiche["email"] or "").lower()
        why = []
        if domain in existing_domains or domain in alias:
            why.append("domaine déjà présent")
        if email and email in existing_emails:
            why.append("adresse déjà présente")
        if norm(fiche["company"]) in existing_names:
            why.append("nom déjà présent")
        if why:
            collisions.append({"company": fiche["company"], "motifs": why})
            continue
        if email and (email in sup_emails or domain in sup_domains):
            blocked.append({"company": fiche["company"], "motif": "liste de suppression"})
            continue

        driving = a.best_axis
        conf = (scores.get(driving) or {}).get("confidence", "")
        # Règle de brouillon, uniforme et announced : joignable, priorité haute,
        # et confiance non faible sur l'axe qui porte la proposition.
        draft = bool(a.contactable and a.tier == "haute" and conf != "faible")

        record = {
            "company": fiche["company"], "website": fiche["website"], "domain": domain,
            "sector": fiche["sector"], "city": fiche["city"], "department": fiche["department"],
            "address": fiche["address"],
            "contact_name": fiche["contact_name"], "contact_role": fiche["contact_role"],
            "email": email, "phone": fiche["phone"], "source": "site_officiel",
            "evidence": [asdict(e) for e in p.evidences],
            "publication_date": "", "need": fiche["need"], "needs": fiche["needs"],
            "recommended_service": fiche["recommended_service"],
            "email_verification": p.email_verification,
            "email_verification_basis": (
                f"adresse lue directement sur une page officielle le {D} ; "
                "MX du domaine vérifié le même jour (le MX ne prouve pas l'existence de la boîte)"
                if email else "aucune adresse professionnelle publiée sur les pages lues"),
            "email_provenance": "publiee" if email else "",
            "email_dns_status": p.email_dns_status,
            "email_dns_checked_at": D if email else "",
            "process_hint": fiche["process_hint"], "demo_detail": fiche["demo_detail"],
            "custom_hook": fiche["custom_hook"], "custom_subject": fiche["custom_subject"],
            "notes": fiche["notes"], "lot": LOT, "discovered_at": D,
            "email_status": "non_contacté", "next_action": "",
            "scores": scores, "scoring_version": "v8",
            "commercial_priority": a.tier, "commercial_value": a.value,
            "commercial": asdict(a), "priority_engine_version": ENGINE_VERSION,
            "status": "nouveau", "status_crm": "qualified", "tier": a.tier,
            "score": max(int(scores[x]["score"]) for x in AXES),
            "justification": " ; ".join(a.reasons),
            "brouillon_autorise_lot11": draft,
            "brouillon_motif": (
                "joignable, priorité haute, confiance suffisante sur l'axe porteur"
                if draft else
                ("aucune adresse publiée" if not email else
                 f"priorité {a.tier}" if a.tier != "haute" else
                 f"confiance {conf} sur l'axe {driving} : vérifier avant contact")),
            "history": [{
                "at": D, "action": "fiche_creee_lot11",
                "reason": "Structure examinée sur sources publiques ; preuves citées et datées ; "
                          "trois axes v8 et priorité v10 calculés par le moteur du dépôt.",
                "source": fiche["website"],
            }],
        }
        rows.append({"record": record, "fiche": fiche, "assessment": a, "draft": draft})

    print(f"CRM avant : {before} fiches")
    print(f"Collisions (fiches existantes NON touchées) : {len(collisions)}")
    for c in collisions:
        print("   ", c["company"], "—", ", ".join(c["motifs"]))
    print(f"Bloquées par suppression : {len(blocked)}")
    print(f"Nouvelles fiches à créer : {len(rows)}")
    print(f"Brouillons autorisés par la règle : {sum(1 for r in rows if r['draft'])}")
    print()
    for r in rows:
        rec = r["record"]
        print(f"  {rec['company'][:36]:36} {rec['department']}  prio {rec['commercial_value']:3} "
              f"{rec['commercial_priority']:14} brouillon={'OUI' if r['draft'] else 'non'}")

    if not args.applique:
        print("\nSIMULATION — aucune écriture. Relancer avec --applique.")
        return 0

    # --- Écriture -----------------------------------------------------------
    created = 0
    for r in rows:
        rec, was_created = crm.upsert(r["record"])
        assert was_created, f"écrasement inattendu : {rec['company']}"
        created += 1
    # Vérification : aucune fiche antérieure modifiée.
    after_by_id = {x.get("id"): x for x in crm.records}
    for rid, blob in frozen.items():
        now = json.dumps(after_by_id[rid], ensure_ascii=False, sort_keys=True)
        assert now == blob, f"fiche antérieure modifiée : {rid}"
    crm.save()

    ledger = ExplorationLedger()
    led_before = len(ledger.entries)
    known = {norm(e.get("company", "")) for e in ledger.entries}
    added = 0
    for entry in archive["examined"]:
        if norm(entry["company"]) in known:
            continue
        ledger.record(
            company=entry["company"], domain=entry.get("domain", ""),
            department=entry.get("department", ""), sector=entry.get("sector", ""),
            decision=entry["decision"], reason=entry.get("note", "")[:400],
            source_type=entry.get("source_type", "site_officiel"),
            source_url=entry.get("url", ""), lot=LOT)
        known.add(norm(entry["company"]))
        added += 1
    ledger.save()

    report = {
        "lot": LOT, "date": D,
        "crm_avant": before, "crm_apres": len(crm.records), "fiches_creees": created,
        "collisions": collisions, "bloquees_suppression": blocked,
        "registre_avant": led_before, "registre_apres": len(ledger.entries),
        "registre_ajouts": added,
        "brouillons_autorises": [r["record"]["company"] for r in rows if r["draft"]],
        "fiches": [{"company": r["record"]["company"], "department": r["record"]["department"],
                    "axes": {a: r["record"]["scores"][a]["score"] for a in AXES},
                    "priorite": r["record"]["commercial_value"],
                    "palier": r["record"]["commercial_priority"],
                    "penalite_contre_signaux": r["assessment"].counter_signal_penalty,
                    "email": r["record"]["email"], "brouillon": r["draft"],
                    "brouillon_motif": r["record"]["brouillon_motif"]} for r in rows],
        "fiches_anterieures_inchangees": len(frozen),
    }
    Path("data/history/lot11-import-2026-11-09.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nÉCRIT : CRM {before} → {len(crm.records)} ; registre {led_before} → {len(ledger.entries)}")
    print(f"{len(frozen)} fiches antérieures vérifiées inchangées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
