# Rapport — Mise à jour commerciale Prospecto v2 + première campagne (3 novembre 2026)

## 1. Modifications réalisées

- **Stratégie commerciale v2** (`docs/strategie-commerciale.md`) : message de référence
  « Une idée pour [Entreprise] ? », personnalisation pilotée par le besoin, démonstration
  gratuite limitée comme argument central, règles anti-invention.
- **Analyse des 8 emails du matin** (`docs/analyse-emails-2026-11-03.md`) : style factuel,
  constats sourcés, opt-out, brièveté — conservés dans la v2. Historique de dédoublonnage versionné.
- **Moteur Python** (`prospecto/`, sans dépendance externe) :
  - `strategy.py` : objets, ouvertures selon preuve, démos par besoin, réalisations par secteur ;
  - `generator.py` : emails courts + garde-fous (anti-invention, promesses interdites, opt-out,
    signature portfolio, longueur) ;
  - `qualification.py` : score fondé preuves + dédoublonnage sur l'historique ;
  - `research.py` : audit factuel de sites (HTTPS / formulaire / CTA) ;
  - `queue.py` + `gmail_export.py` : file de validation `pending → approved/rejected → sent`,
    export **brouillons Gmail uniquement** ;
  - `cli.py` : `qualify`, `generate`, `queue`, `export`, `audit`.
- **Démo personnalisable par prospect** (`demo_detail`), avec garde-fou anti-réalisation complète.

## 2. Tests effectués

- **53 tests unitaires, tous verts** (`python -m unittest discover -s tests`).
- Couverture : stratégie (démos, objets, ouvertures, élision), générateur (conformité v2,
  garde-fous, anti-invention), qualification (barème, dédoublonnage), audit site, file de
  validation (transitions, persistance), export Gmail (brouillons only).
- Test de bout en bout CLI : qualification → génération → mise en file → export.

## 3. Prospects qualifiés : 2

| Prospect | Secteur | Besoin | Preuve | Score |
|---|---|---|---|---|
| R Premium (Clichy, 92) | Bâtiment / rénovation | Refonte / SEO WordPress | Annonce Codeur.com ouverte (besoin public) | 60 |
| Secteur 72 (Montval-sur-Loir, 72) | Loisirs / lancement | Automatisation réservations | Annonce Codeur.com du 03/11 + presse actu.fr + site | 75 |

Leads examinés puis **écartés honnêtement** (détail dans `data/prospects/campagne-2026-11-03.json`) :
Gaboriau Ebénisterie & Jobard Energies (sites inaccessibles, lacunes non vérifiables) ;
LBLF, Boodbois, Pierre & Jardin, Hoose Bois Design (sites déjà bons, aucun problème à inventer) ;
Matabiau Locker Hub (besoin public réel mais pas de contact public) ; HOSSEA (projet fermé ancien).

## 4. Emails préparés : 2 (en attente de validation, aucun envoi)

| File | Destinataire | Objet | Brouillon Gmail |
|---|---|---|---|
| 2026-11-03-v2-001 | contact@renovationpremium.com | Une idée pour le site de R Premium ? | `r-7104264166518428447` |
| 2026-11-03-v2-002 | secteur72fr@gmail.com | Une idée pour gagner du temps chez Secteur 72 ? | `r7603863657574249798` |

Chaque email : première phrase au besoin public réel + source, une seule prestation, démo
gratuite limitée au centre, opt-out, signature v2 avec portfolio. Statut `pending`.

**Pour valider** : relire les brouillons dans Gmail, puis envoyer manuellement (ou demander
l'envoi). Commandes file : `python -m prospecto.cli queue approve <id>` / `reject <id>`.

## 5. Commits créés (branche `arena/7ed6352a-agent-prosect1`)

1. `506bbec` — docs : stratégie v2 + analyse des 8 emails + fondations
2. `445ac71` — feat : moteur v2 (personnalisation, démo, qualification, file)
3. `a638c9d` — feat : démo personnalisable par prospect
4. `a6515b8` — data : première campagne (2 prospects, preuves, emails en file)
5. `b701161` — data : brouillons Gmail créés (validation en attente)
6. (ce rapport)

## 6. Statut de synchronisation GitHub

- Tous les commits poussés sur `origin/arena/7ed6352a-agent-prosect1`.
- SHA local == SHA distant vérifié après chaque push (`gh api`).
- Dépôt : `martinbourasseau/Agent-prosect1`. Aucun secret versionné (`.env` ignoré).

## 7. Points bloquants / remarques

- **Volume volontairement limité à 2 prospects** : priorité aux besoins publics vérifiés avec
  contact exploitable. Plusieurs pistes écartées faute de preuve honnête (cf. §3). Le pipeline
  est prêt à être élargi (plus de recherches, ou assouplissement ciblé du ciblage).
- **Codeur.com** masque le contact des porteurs de projet : seules les entreprises nommées
  avec contact public sont prospectables par email. Les projets anonymes restent des leads
  à traiter via la plateforme.
- **Aucun envoi automatique** : les 2 emails sont des brouillons en attente de validation humaine.
- Le projet SYNATRAPE n'a pas été modifié. Aucun déploiement effectué.
