# Rapport de campagne — Mission v3 (3 novembre 2026)

> Élargissement massif de la prospection + rattachement de l'outil au site
> **prospecto.website**. Aucun email envoyé. Tout passe par la file de validation.

## 1. Chiffres clés

| Indicateur | Valeur |
|---|---|
| **Total fiches CRM** | **16** |
| Prospects déjà présents avant la mission | 10 (2 actifs v2 + 8 déjà contactées) |
| **Nouveaux prospects découverts (v3)** | **6** |
| Besoins **exprimés publiquement** (preuve + URL) | 5 |
| Opportunités **probables** (priorité moyenne) | 2 (+ 1 à approfondir) |
| **Coordonnées email vérifiées récupérées (v3)** | **3** (+ téléphones) |
| Prospects **qualifiés** (haute + moyenne, email prêt) | 5 |
| **Emails préparés v3** | **5** |
| Brouillons v2 conservés | 2 |
| **Total en attente de validation** | **7** |
| Emails envoyés | **0** |
| Tests unitaires | **64 verts** |
| Commits sur la branche | 11 (poussés + vérifiés sur GitHub) |

### Répartition du pipeline actif (8)
- **Priorité haute (3)** : R Premium, Secteur 72, BSP Auto — besoin exprimé + contact exploitable.
- **Priorité moyenne (2)** : CERF Athletic Training, Charme de l'Hêtre — besoin fortement probable + éléments concrets.
- **À approfondir (3)** : Carot's, Matabiau Locker Hub, GELA — conservés, contact à récupérer (aucun rejet).
- **Déjà contactées (8, exclues du pipeline)** : Multitech Assistance, Garage Villedieu Automobiles, Le Serrurier d'A Cote, Superchi Architectes, L'Etabli du Menuisier, Quattro Architectes, The Architectes, Akla Architectes.

## 2. Nouveaux prospects découverts (v3)

| Entreprise | Lieu | Niveau | Besoin | Contact vérifié | Source / preuve |
|---|---|---|---|---|---|
| **BSP Auto** | Paris (75) | haute | Automatisation newsletter | support@bsp-auto.com | Codeur.com (projet 492305) |
| **CERF Athletic Training** | Mouzillon (44) | moyenne | Automatisation inscriptions/suivi | contact@cerf-athletic-training.fr | actu.fr (12/08/2026) + site |
| **Charme de l'Hêtre** | La Chapelle-Urée (50) | moyenne | Création site vitrine | charmedelhetre50@gmail.com | actu.fr (18/08/2026) |
| **Carot's** | Manneville-sur-Risle (27) | à approfondir | Création boutique en ligne | à rechercher | presse (mai 2026) |
| **Matabiau Locker Hub** | Toulouse (31) | à approfondir | One-page multilingue | masqué (Codeur) | Codeur.com (projet 492083) |
| **GELA** | — | à approfondir | Automatisation réseaux sociaux | masqué (Codeur) | Codeur.com (projet 492271) |

Chaque fiche conserve : nom, site, secteur, ville/département, contact, email pro public,
téléphone, source de découverte, URL de preuve, date de publication, besoin, prestation
recommandée, score + justification, et email proposé le cas échéant. **Aucune coordonnée
fabriquée** ; les contacts masqués (Codeur) ne sont pas inventés.

## 3. Emails préparés (file de validation, aucun envoi)

**Campagne v3 (`2026-11-03-v3`) — 5 emails**, hook dès la 1re phrase, une seule prestation,
démo gratuite limitée au centre, objet court naturel, CTA simple, opt-out, signature portfolio :

| ID | Entreprise | Objet | Niveau |
|---|---|---|---|
| v3-001 | R Premium | Votre annonce WordPress + référencement | haute |
| v3-002 | Secteur 72 | Secteur 72 : automatiser avant l'ouverture ? | haute |
| v3-003 | BSP Auto | Votre newsletter mensuelle, en pilote automatique ? | haute |
| v3-004 | CERF Athletic Training | CERF : automatiser le suivi de vos adhérents ? | moyenne |
| v3-005 | Charme de l'Hêtre | Charme de l'Hêtre : être trouvé sur Google ? | moyenne |

**Brouillons v2 conservés** (R Premium, Secteur 72) : les 2 brouillons Gmail restent en place
(`r-7104264166518428447`, `r7603863657574249798`) et dans la file. Les nouvelles versions v3
sont ajoutées **sans écraser** les anciennes : Martin choisit laquelle valider.

### Exemple — Secteur 72 (v3)
> **Objet :** Secteur 72 : automatiser avant l'ouverture ?
>
> Bonjour Marc,
>
> J'ai suivi le lancement de Secteur 72 : vous préparez l'ouverture de votre terrain d'airsoft et le développement de la boutique.
>
> Je mets en place des automatisations qui font gagner du temps sur les tâches répétitives.
>
> Je peux vous préparer gratuitement une première démonstration personnalisée, sans engagement : un exemple de parcours de réservation automatisé avec rappels avant chaque session.
>
> Seriez-vous intéressé pour la découvrir ?
>
> Si le sujet ne vous concerne pas, répondez « ne pas me relancer » : je le note et je ne vous écrirai plus.
>
> Bonne journée,
> Martin BOURASSEAU
> Création web · Agents IA · Automatisation
> https://prospecto.website

## 4. Réalisations / exemples (en attente des URLs de Martin)

- Whitelist officielle `data/realisations.json` créée, **vide** pour l'instant
  (`status: en_attente_des_urls_de_martin`).
- **Aucun lien d'exemple n'est inséré** tant que les URLs ne sont pas transmises et whitelistées
  (garde-fou anti-mensonge : le générateur refuse tout lien hors whitelist).
- Les 5 emails v3 sont complets sans lien ; ils seront enrichis d'un exemple pertinent
  (un seul lien max, par secteur) dès que Martin fournira ses URLs.

## 5. Meilleures sources (rendement constaté)

1. **Codeur.com** (flux `/projects/c/web.rss` + pages projet) — meilleure source de **besoins
   exprimés** nommés, avec budget/date. Contacts porteurs masqués → contact pro retrouvé
   indépendamment sur le site de l'entreprise.
2. **Presse locale** (actu.fr, lamanchelibre.fr, ouest-france) — excellente pour **lancements
   d'activité nommés + contact public** (email/téléphone dans l'article).
3. **Sites d'entreprises** — vérification des coordonnées publiques (email, téléphone).
- Faible rendement : posts LinkedIn (articles marketing), recherches Google génériques
  (comparatifs de prestataires), sites anciens invérifiables. Pistes écartées sans invention.

## 6. Nouveau modèle d'email retenu (v3)

- **Hook dès la 1re phrase**, spécifique, crédible, vérifiable (annonce, projet, lancement,
  processus automatisable). Accroche sur mesure (`custom_hook`) prioritaire.
- **Une seule prestation** selon le besoin réel (web OU IA/automatisation), jamais le catalogue.
- **Démo gratuite limitée** = argument central (« Je peux vous préparer gratuitement une
  première démonstration personnalisée, sans engagement : … »).
- **Objet court, naturel, intrigant mais honnête** (≤ 70 caractères), jamais racoleur.
- **Très court** (40–150 mots), naturel, humain ; CTA simple ; opt-out ; signature portfolio.
- Garde-fous `check_email` : longueur, démo gratuite + sans engagement, opt-out, signature,
  anti-invention (hook ↔ preuve), promesses interdites, whitelist des liens.

## 7. Rattachement à prospecto.website (app + site)

- **Espace Prospecto construit** : `prospecto/server.py` (stdlib, bind `0.0.0.0`) +
  `prospecto/dashboard.html`. Interface **sombre assortie au site** (Archivo, abyss/glacier/tide).
  - **Connexion sécurisée** : mot de passe + cookie de session signé HMAC (HttpOnly, SameSite).
  - **API reliée** : `/api/stats`, `/api/prospects`, `/api/queue`, `/api/campaigns`,
    `POST /api/queue/{id}/approve|reject`.
  - **Aucun envoi d'email** depuis le dashboard (approuver ne change que le statut).
  - Onglets Prospects / Validation / Campagnes, cartes de stats, filtres, aperçu des emails.
- **Architecture étudiée avant modification** : site Next.js 16 (App Router), `X-Frame-Options
  SAMEORIGIN` → intégration par **lien** (pas iframe). Site marketing **non reconstruit**.
- **Patch nav prêt** (`integrations/prospecto-site/`) : lien « Espace Prospecto » desktop +
  mobile, réutilisant les classes du site. **Non appliqué / non poussé** sur `prospecto-site`.
- **Guide** : `docs/integration-site-prospecto.md` (déploiement sous-domaine `app.prospecto.website`
  ou chemin `/app`, DNS, HTTPS, durcissement). **Aucun déploiement automatique.**
- Preview live lancée (port 8787). Mot de passe dans `data/.dash_password` (gitignoré).

## 8. Tests & commits

- **64 tests unitaires verts** : stratégie, générateur (dont whitelist), qualification (tiers),
  CRM (fusion sans écrasement, dédoublonnage, stats), file de validation, recherche/audit.
- Correctifs v3 : salutation au prénom (naturel), dédoublonnage sans clé vide,
  `recommended_service` stocké correctement, stats excluant les contactées du pipeline.

### Commits (branche `arena/7ed6352a-agent-prosect1`, poussés + vérifiés)
| SHA | Objet |
|---|---|
| `d2428af` | Moteur v3 — hooks, prestation unique, CRM 3 niveaux, whitelist réalisations |
| `f34d939` | Lot v3 — 6 nouveaux prospects, 5 emails v3 en file |
| `ba76def` | Espace Prospecto — dashboard + API sécurisée, intégration site |
| *(rapport)* | Stats CRM + test + rapport final v3 |
- Rappel : sauvegarde CRM pré-migration `24ffbf8` (`data/backups/2026-11-03-avant-v3/`).

## 9. Sécurité & conformité (respectées)

- **Aucun email commercial envoyé** sans approbation explicite ; file `pending → approved/rejected → sent`.
- Aucun verrou de sécurité désactivé ; limites Gmail respectées.
- Aucune coordonnée fabriquée ; aucun problème inventé ; besoins publics référencés quand ils existent.
- Démo gratuite **limitée**, sans engagement ; pas de promesse de réalisation complète gratuite.
- Secrets jamais committés (`.gitignore` : `.env`, tokens, `data/.dash_password`, `data/.dash_secret`).
- Données CRM **non supprimées / non écrasées** ; sauvegarde avant migration ; fusion additive.
- RGPD : opt-out dans chaque email ; prospection professionnelle B2B ; CGU plateformes respectées
  (contacts masqués non extraits).
- Projet SYNATRAPE / SYNATRAP **non modifié**.

## 10. Prochaines étapes (à valider par Martin)

1. **Valider / rejeter** les 7 emails en file (dashboard ou CLI). Aucun envoi automatique.
2. **Transmettre les URLs de réalisations** → whitelist + enrichissement d'un exemple par email si pertinent.
3. **Choisir l'URL de déploiement** du dashboard, appliquer le patch nav dans `prospecto-site`,
   déployer en HTTPS avec mot de passe fort (voir guide).
4. Poursuivre l'élargissement (le moteur/CRM est prêt pour de nouveaux lots sans plafond).
