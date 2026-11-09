"""Fiche du Lot 13 — besoins exprimés, preuves lues, aucune écriture.

Le Lot 13 ne produit qu'une seule fiche. C'est le résultat du pilote, pas un
objectif : sur 63 entités examinées, une seule réunit un besoin exprimé lu, une
identité établie, un signal encore pertinent et des coordonnées publiées.

Règles conservées des lots précédents :
* contre-signaux typés `maturite_existante` pour être réellement lus par
  `counter_signals.collect()` et peser sur la priorité ;
* axe IA alimenté uniquement par un processus publié et cité ;
* aucune coordonnée déduite d'un motif de domaine.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from prospecto.models import Evidence, Prospect
from prospecto.scoring import score_prospect
from prospecto.priority import ENGINE_VERSION, assess

TODAY = date(2026, 11, 3)
D = "2026-11-03"
LOT = "2026-11-03-lot13"
ROOT = Path(__file__).resolve().parents[2]
DNS_PATH = ROOT / "data/history/lot13-dns-2026-11-03.json"


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


DNS = {_norm(k): v["status"] for k, v in
       json.loads(DNS_PATH.read_text(encoding="utf-8")).items() if v.get("email")}


def ev(kind, url, quote, detail, *, level=None, source="site_officiel",
       reliability="haute", observed=True):
    e = {"kind": kind, "source_url": url, "quote": quote, "detail": detail,
         "source_type": source, "reliability": reliability,
         "observed_at": D, "verified_at": D, "observed": observed}
    if level:
        e["signal_level"] = level
    return e


PROJET = ("https://www.codeur.com/projects/"
          "489291-finalisation-et-optimisation-du-site-vitrine-styl-home")

FICHES = [
    {
        "company": "Styl'Home", "domain": "stylhome.fr",
        "website": "https://stylhome.fr/",
        "sector": "Rénovation intérieure, peinture en bâtiment et finitions décoratives",
        "city": "Lille", "department": "59",
        "address": "Lille et alentours (Nord) — adresse postale complète non publiée",
        "email": "contact@stylhome.fr", "phone": "",
        "contact_name": "", "contact_role": "",
        "qualification_category": "A",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux reprendre le site existant sans repartir de zéro : remplacer les visuels provisoires par vos vraies photos de chantier et rendre le parcours de devis plus direct",
        "observation": "votre consultation du 6 septembre demande de rendre le site « plus humain » et relève le manque de vraies photos ; la photo des deux gérants est encore un visuel provisoire « Soon.. »",
        "demo_detail": "la page d'accueil avec une vraie photo des deux gérants à la place du visuel provisoire, et un bouton de devis visible sans défilement",
        "custom_subject": "Styl'Home : la photo des gérants est encore un visuel provisoire",
        "custom_hook": "Vous écriviez le 6 septembre vouloir « davantage de vraies réalisations » et de « vraies photos de chantier ».",
        "notes": "Besoin exprimé publiquement le 06/09/2026 sur une plateforme de projets, "
                 "lu intégralement. L'entreprise y nomme elle-même son site stylhome.fr, "
                 "ce qui établit le rattachement sans lever l'anonymat du profil client. "
                 "Consultation close après 122 offres : un prestataire a peut-être été "
                 "retenu, ce n'est pas vérifié. Aucun téléphone publié sur les deux pages "
                 "lues ; l'adresse e-mail est publiée en clair sur la page contact.",
        "evidence": [
            ev("public_need", PROJET,
               "Je recherche un freelance pour reprendre, corriger et finaliser mon site "
               "vitrine existant : stylhome.fr, pour mon entreprise artisanale Styl’Home.",
               "L'entreprise demande explicitement une prestation de correction et de "
               "finalisation de son site, en nommant son domaine. Elle précise ne pas "
               "vouloir repartir de zéro. Publication du 06/09/2026, budget annoncé "
               "1 000 à 10 000 €. Le besoin relève directement de l'offre Prospecto "
               "(refonte ciblée). La page du projet est publique ; seul le profil du "
               "client est réservé aux abonnés, et il n'a pas été consulté.",
               source="appel_projet"),
            ev("public_need", PROJET,
               "– manque de vraies photos et d’éléments humains ;",
               "L'entreprise liste elle-même les défauts relevés par des retours "
               "extérieurs : manque de vraies photos, footer trop chargé sur mobile, "
               "problèmes responsive à certaines largeurs, formulaire de contact "
               "parfois lent à l'envoi, téléphone et e-mail à rendre cliquables. "
               "Ces points sont déclarés par l'entreprise, non mesurés par l'agent : "
               "aucun test de performance ni de rendu mobile n'a été exécuté.",
               source="appel_projet"),
            ev("website_gap", "https://stylhome.fr/",
               "![Photo des deux gérants de l'entreprise, père et fils](https://placehold.co/400x400?text=Soon..)",
               "Constat indépendant sur le site officiel, le 2026-11-03 : l'image "
               "annoncée comme « Photo des deux gérants de l'entreprise, père et fils » "
               "est servie depuis placehold.co avec le texte « Soon.. ». Ce n'est pas un "
               "artefact de lecture sans JavaScript : l'URL du visuel provisoire est "
               "écrite en dur dans la page. Ce constat corrobore le besoin exprimé "
               "deux mois plus tôt et indique qu'il n'est pas encore satisfait.",
               reliability="haute"),
            ev("website_gap", "https://stylhome.fr/",
               "Depuis plus de 4 ans, nous mettons nos 34 ans d'experience dans la "
               "peinture en batiment, l'enduit, la pose de sol et les finitions décoratives",
               "La phrase d'accueil juxtapose deux anciennetés sans les articuler "
               "(« plus de 4 ans » et « 34 ans d'experience ») et comporte deux accents "
               "manquants (« experience », « batiment »). Sur une page dont l'entreprise "
               "dit vouloir renforcer la confiance, cette première phrase est le premier "
               "élément de réassurance lu par un visiteur venant de Google Ads."),
            ev("parcours_incomplet", "https://stylhome.fr/contact",
               "Ou contactez-nous à [contact@stylhome.fr](mailto:contact@stylhome.fr)",
               "La page contact publie une adresse e-mail cliquable et un formulaire "
               "(Nom, Prénom, Email, Numéro de téléphone, Objet, Détaillez votre demande). "
               "En revanche aucun numéro de téléphone n'est affiché sur cette page ni sur "
               "l'accueil, alors que la consultation demande explicitement de rendre le "
               "téléphone « parfaitement accessible et cliquable » et de transformer les "
               "visiteurs « en appels et demandes de devis ». Le canal téléphonique "
               "annoncé comme objectif n'est pas proposé au visiteur."),
        ],
        "contre_signaux": [
            {"source_url": PROJET,
             "quote": "Fermé",
             "detail": "La consultation est close après 122 offres reçues. La sélection "
                       "d'un prestataire web est possible mais non vérifiée : ce "
                       "contre-signal réduit l'accessibilité commerciale sans établir "
                       "que le besoin a été satisfait. Les défauts, eux, sont toujours "
                       "observables sur le site le 2026-11-03."},
            {"source_url": "https://stylhome.fr/",
             "quote": "De la planification et de la préparation du chantier jusqu'à la "
                      "réalisation et aux finitions, découvrez un aperçu de nos travaux à "
                      "Lille, Bondues ou Verlinghem, ainsi que du résultat attendu.",
             "detail": "Contre-signal de maturité lu sur le site officiel le 2026-11-03 : "
                       "le site est structuré et récent (Next.js, pages Services et "
                       "Réalisations dédiées, galerie avant/après avec de vraies photos "
                       "de chantier hébergées, formulaire de devis). La création n'est "
                       "donc pas le besoin et la refonte pertinente est partielle. "
                       "L'entreprise déclare par ailleurs piloter Google Ads et "
                       "Analytics dans sa consultation : un outillage marketing est "
                       "déjà en place. Ces deux éléments délimitent le besoin sans "
                       "l'annuler — le visuel des gérants reste provisoire."},
        ],
    },
]


def build(fiche: dict) -> dict:
    raw = list(fiche["evidence"])
    for cs in fiche.get("contre_signaux", []):
        raw.append(ev("maturite_existante", cs["source_url"], cs["quote"],
                      cs["detail"], level="observe",
                      source="appel_projet" if cs["source_url"] == PROJET else "site_officiel"))
    evs = [Evidence(**e) for e in raw]
    for e in evs:
        errors = e.validate()
        assert not errors, (fiche["company"], e.kind, errors)
    p = Prospect(
        company=fiche["company"], domain=fiche["domain"],
        contact_email=fiche["email"], sector=fiche["sector"],
        needs=fiche["needs"], evidences=evs, website=fiche["website"],
        process_hint=fiche["process_hint"], demo_detail=fiche["demo_detail"],
        custom_hook=fiche["custom_hook"], custom_subject=fiche["custom_subject"],
        city=fiche["city"], department=fiche["department"], phone=fiche["phone"],
        contact_name=fiche["contact_name"], contact_role=fiche["contact_role"],
        recommended_service=fiche["recommended_service"],
        observation=fiche.get("observation", ""),
        source="appel_projet", lot=LOT, discovered_at=D,
        email_verification="verified" if fiche["email"] else "none",
        email_dns_status=DNS.get(_norm(fiche["company"]), "") if fiche["email"] else "",
        notes=fiche.get("notes", ""),
    )
    scores = score_prospect(p, today=TODAY)
    assessment = assess(p, scores, today=TODAY)
    return {"fiche": fiche, "prospect": p, "scores": scores, "assessment": assessment}


if __name__ == "__main__":
    for r in [build(f) for f in FICHES]:
        f, s, a = r["fiche"], r["scores"], r["assessment"]
        print(f"{f['company']} — catégorie {f['qualification_category']}")
        print(f"  création {s['site_web']['score']} | refonte {s['refonte']['score']} "
              f"| IA {s['ia_automatisation']['score']}")
        print(f"  priorité {a.value} ({a.tier}) | pénalité contre-signaux "
              f"{a.counter_signal_penalty} | joignable {a.contactable}")
        print(f"  confiance refonte : {s['refonte']['confidence']}")
        for reason in a.reasons:
            print("   -", reason)
    print("\nMoteur :", ENGINE_VERSION, "| Fiches :", len(FICHES))
