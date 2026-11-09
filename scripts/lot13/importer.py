"""Import du Lot 13 — simulation par défaut, --applique pour écrire.

Reprend les garde-fous du Lot 11 :
  * dédoublonnage sur domaine, e-mail ET nom normalisé avant toute création ;
  * aucune fiche existante écrasée : collision ⇒ fiche laissée intacte ;
  * assertion finale que les 120 fiches antérieures sont bit-à-bit identiques ;
  * scores et priorité produits par le moteur du dépôt, jamais retouchés ;
  * aucun envoi, aucun brouillon créé par ce script.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prospecto.crm import CRM
from prospecto.config import SUPPRESSION_PATH
from prospecto.priority import ENGINE_VERSION
from prospecto.sources import ExplorationLedger
from prospecto.scoring import AXES
from fiches import FICHES, build, D, LOT
from classification import importable, LABELS
import journal

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/history/lot13-recherches-2026-11-03.json"
IMPORT_REPORT = ROOT / "data/history/lot13-import-2026-11-03.json"

# Vocabulaire de décision déjà en place dans le registre d'exploration.
# Le journal de recherche garde des libellés techniques ; on les traduit à
# l'import pour que le tableau de bord ne scinde pas une même catégorie.
# « non_verifie » (page non lue) retombe sur « approfondir » : c'est bien
# l'action attendue, et le motif conserve la mention « page non récupérée ».
DECISION_VERS_REGISTRE = {
    "importee": "retenue",
    "ecartee": "écartée",
    # Le journal du Lot 13 emploie déjà le libellé accentué du registre.
    "écartée": "écartée",
    "approfondir": "approfondir",
    "annuaire_seul": "annuaire_seul",
    "non_verifie": "approfondir",
}


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--applique", action="store_true")
    args = ap.parse_args()

    journal.archiver(ARCHIVE)

    crm = CRM()
    before = len(crm.records)
    existing_domains = {(r.get("domain") or "").lower() for r in crm.records if r.get("domain")}
    existing_emails = {(r.get("email") or "").lower() for r in crm.records if r.get("email")}
    existing_names = {norm(r.get("company", "")) for r in crm.records}
    frozen = {r.get("id"): json.dumps(r, ensure_ascii=False, sort_keys=True) for r in crm.records}

    sup = json.loads(SUPPRESSION_PATH.read_text(encoding="utf-8"))
    sup_emails = {e["email"].lower() for e in sup.get("entries", [])}
    sup_domains = {e["domain"].lower() for e in sup.get("entries", []) if e.get("domain_wide")}

    # Domaines alternatifs observés pour une même entreprise. Aucun n'a été
    # constaté au Lot 13 : la table reste vide plutôt que d'hériter d'alias du
    # Lot 12 sans rapport avec les entreprises de ce lot.
    alias: dict[str, str] = {}

    rows, collisions, blocked = [], [], []
    for fiche in FICHES:
        assert importable(fiche["qualification_category"]), (
            f"{fiche['company']} : catégorie "
            f"{fiche['qualification_category']} non importable")
        r = build(fiche)
        p, scores, a = r["prospect"], r["scores"], r["assessment"]
        domain = fiche["domain"].lower()
        email = (fiche["email"] or "").lower()
        why = []
        # Un alias ne sert qu'à RAMENER un domaine secondaire à son domaine
        # canonique pour le comparer à l'existant. Il ne doit jamais bloquer la
        # fiche canonique elle-même (bug corrigé : `domain in alias` rejetait
        # MFMG et L.C. Bois dès la première exécution, sans aucun doublon réel).
        canonical = alias.get(domain, domain)
        if canonical in existing_domains:
            why.append("domaine déjà présent")
        if email:
            email_domain = email.split("@")[-1]
            if email in existing_emails or alias.get(email_domain, email_domain) in existing_domains:
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
        # Le Lot 13 est un pilote de DÉTECTION. Aucun brouillon n'est autorisé,
        # même lorsqu'une fiche atteint le palier haut : la décision de
        # contacter appartient à l'utilisateur. Le champ est conservé à false
        # avec son motif pour que le tableau de bord n'invente pas d'attente.
        draft = False
        motif = ("pilote de détection : rédaction et validation réservées à l'utilisateur"
                 f" (palier {a.tier}, confiance {conf or 'inconnue'} sur l'axe {driving})")

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
            "phone_provenance": "publie_sur_site_officiel" if fiche["phone"] else "",
            "process_hint": fiche["process_hint"], "demo_detail": fiche["demo_detail"],
            "custom_hook": fiche["custom_hook"], "custom_subject": fiche["custom_subject"],
            "notes": fiche["notes"], "lot": LOT, "discovered_at": D,
            "qualification_category": fiche["qualification_category"],
            "qualification_label": LABELS[fiche["qualification_category"]],
            "qualification_basis": next(
                (e["motif"] for e in journal.E if e["nom"] == fiche["company"]), ""),
            "email_status": "non_contacté", "next_action": "",
            "scores": scores, "scoring_version": "v8",
            "commercial_priority": a.tier, "commercial_value": a.value,
            "commercial": asdict(a), "priority_engine_version": ENGINE_VERSION,
            "status": "nouveau", "status_crm": "qualified", "tier": a.tier,
            "score": max(int(scores[x]["score"]) for x in AXES),
            "justification": " ; ".join(a.reasons),
            "brouillon_autorise_lot13": draft,
            "brouillon_motif": motif,
            "history": [{
                "at": D, "action": "fiche_creee_lot13",
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
        print(f"  {rec['company'][:34]:34} {rec['department']}  prio {rec['commercial_value']:3} "
              f"{rec['commercial_priority']:14} {rec['brouillon_motif']}")

    stats = journal.stats()
    if not args.applique:
        print("\nSIMULATION — aucune écriture. Relancer avec --applique.")
        print("Examinées :", stats["entites_examinees"],
              "| catégories :", stats["categories"],
              "| pages distinctes lues :", stats["pages_distinctes_lues"])
        return 0

    created = 0
    for r in rows:
        rec, was_created = crm.upsert(r["record"])
        assert was_created, f"écrasement inattendu : {rec['company']}"
        created += 1
    after_by_id = {x.get("id"): x for x in crm.records}
    for rid, blob in frozen.items():
        now = json.dumps(after_by_id[rid], ensure_ascii=False, sort_keys=True)
        assert now == blob, f"fiche antérieure modifiée : {rid}"
    crm.save()

    ledger = ExplorationLedger()
    led_before = len(ledger.entries)
    known = {norm(e.get("company", "")) for e in ledger.entries}
    added = 0
    for entry in journal.E:
        if norm(entry["nom"]) in known:
            continue
        # Le registre a déjà un vocabulaire de décision (« écartée »,
        # « retenue », « approfondir », « annuaire_seul »). Réutiliser
        # exactement ces libellés évite de scinder une même catégorie en deux
        # dans le tableau de bord (« écartée » 93 + « ecartee » 117).
        decision = DECISION_VERS_REGISTRE[entry["decision"]]
        st = ("annuaire_pro" if entry["lecture"] == "annuaire"
              else "site_officiel" if entry["lecture"] == "officielle"
              else "autre")
        ledger.record(
            company=entry["nom"], domain="", department=entry["departement"],
            sector=entry["secteur"], decision=decision,
            reason=entry["motif"][:400], source_type=st,
            source_url=entry["url"], lot=LOT)
        known.add(norm(entry["nom"]))
        added += 1
    ledger.save()

    report = {
        "lot": LOT, "date": D,
        "crm_avant": before, "crm_apres": len(crm.records), "fiches_creees": created,
        "collisions": collisions, "bloquees_suppression": blocked,
        "registre_avant": led_before, "registre_apres": len(ledger.entries),
        "registre_ajouts": added,
        "recherche": stats,
        "brouillons_autorises": [r["record"]["company"] for r in rows if r["draft"]],
        "fiches": [{"company": r["record"]["company"], "department": r["record"]["department"],
                    "axes": {a: r["record"]["scores"][a]["score"] for a in AXES},
                    "priorite": r["record"]["commercial_value"],
                    "palier": r["record"]["commercial_priority"],
                    "categorie": r["fiche"]["qualification_category"],
                    "penalite_contre_signaux": r["assessment"].counter_signal_penalty,
                    "email": r["record"]["email"], "brouillon": r["draft"],
                    "brouillon_motif": r["record"]["brouillon_motif"]} for r in rows],
        "fiches_anterieures_inchangees": len(frozen),
        "envoi_autorise": False,
    }
    IMPORT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"\nÉCRIT : CRM {before} → {len(crm.records)} ; registre {led_before} → {len(ledger.entries)}")
    print(f"{len(frozen)} fiches antérieures vérifiées inchangées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
