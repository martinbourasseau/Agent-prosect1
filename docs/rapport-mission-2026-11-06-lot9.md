# Rapport de mission — Évolution de l'agent, lot 9 et audit Gmail

**Date :** 6 novembre 2026
**Dépôt :** `martinbourasseau/Agent-prosect1`
**Branche :** `arena/7ed6352a-agent-prosect1`
**Lot livré :** `2026-11-06-lot9` — label Gmail `Prospection/2026-11-06-lot9` (`Label_7`)
**Moteur :** v7 → **v7.1**

> **Aucun email de prospection n'a été envoyé pendant cette mission.**
> Le pré-vol reste bloqué sur trois points. Les quatre messages du lot 9 sont
> des **brouillons Gmail en attente de validation humaine**.

---

## 0. Sauvegarde et périmètre

Travail effectué **sur le projet existant** : aucun second agent, aucune
reconstruction de l'application. Avant toute modification, sauvegarde complète
dans `data/backups/2026-11-06-avant-lot9/` (38 fichiers, 916 K).

**Aucune suppression** de données, d'historique, de fiche ou de brouillon. Les
items de file neutralisés au lot 8 restent en place avec le statut `obsolete`.

---

## 1. Évolution réelle de l'agent

### 1.1 Ce qui a changé, et pourquoi

L'évolution n'est pas cosmétique : chaque ajout répond à un défaut **constaté
sur des données réelles**, pas à une idée d'amélioration.

| Capacité | Fichier | Défaut corrigé |
|---|---|---|
| Détection d'opportunités par processus | `prospecto/opportunity.py` | Le score dépendait du secteur, pas de ce que l'entreprise publie. |
| Trois scores indépendants avec preuves et confiance | `prospecto/scoring.py` | Un score « fort » pouvait reposer sur une seule affirmation du chercheur. |
| Catalogue de sources et mémoire d'exploration | `prospecto/sources.py` *(nouveau)* | La recherche retombait sur les mêmes secteurs et réexaminait des entreprises déjà écartées. |
| Preuves typées, datées, hiérarchisées | `prospecto/models.py` | Impossible de distinguer un fait observé d'une hypothèse, ni un site officiel d'un annuaire. |
| Références commerciales pertinentes | `prospecto/references.py`, `messaging.py` | Tout besoin « automatisation » attirait une plateforme d'agents IA, sans rapport. |
| Garde-fous d'envoi | `prospecto/sender.py` | `_is_blocked()` répondait `False` pour une entreprise déjà contactée. |
| Catégories réelles du tableau de bord | `prospecto/metrics.py`, `queue.py`, `dashboard.html` | Les brouillons étaient invisibles ; dix lignes de catégories étaient calculées puis jetées. |

### 1.2 Deux nouveaux types de preuve

Le modèle ne savait exprimer que des **manques**. Une entreprise déjà outillée
ne pouvait donc pas être créditée de ce qui fonctionne.

- `maturite_existante` — ce qui est **déjà en place** (contre-signal) ;
- `signal_confiance` — identité, accréditation, antériorité.

Ces deux types sont **exclus de la détection de besoin** (`NON_GAP_KINDS`).
Sans cette exclusion, une preuve de maturité contenant « demande de devis »
créait un besoin de devis : le contre-signal nourrissait le besoin qu'il est
censé réduire.

Chaque preuve porte désormais : `source_url`, `source_type`, `reliability`,
`verified_at`, `observed_at`, `observed`.

### 1.3 Le score IA ne dépend plus du métier

Le secteur n'est **pas un paramètre** de `analyze()`. Seuls les processus
publiés comptent. Vérifié sur le CRM : deux entreprises du même secteur
obtiennent des scores différents selon leurs processus, et changer uniquement
le secteur ne change rien au score (test `test_le_metier_n_influence_pas_le_score_ia`).

Pondérations : fiabilité `haute 1,0 / moyenne 0,75 / faible 0,45`, hypothèse
`× 0,5`, contre-signal `× 0,8`. Chaque motif cite **l'extrait réel**, le motif
de détection et **l'URL source**.

### 1.4 v7.1 — quatre trous de détection trouvés sur les pages du lot 9

Le premier passage en v7 a produit des scores manifestement faux. Plutôt que
d'ajuster les chiffres, j'ai corrigé le moteur :

| Signal ajouté | Poids | Cas réel qui l'a révélé |
|---|---|---|
| `capacite_reponse_limitee` | 28 | **Cordes et Âme** publie « il peut être compliqué de répondre aux appels » et « Nous relevons les messages une fois par jour ». Score IA **0** avant correction. |
| `depot_via_messagerie` | 24 | **Caléo** : « Le bouton ci-dessous ouvre votre messagerie avec la demande pré-remplie ». Le point de rupture n'était pas reconnu. |
| `deplacement_obligatoire` | 22 | **Canfora** : « Venez nous rencontrer en magasin […] pour établir un devis personnalisé ! » |
| `echeances_recurrentes` | 18 | **Froger** : contrats annuels avec compte-rendu détaillé. |

`tri_manuel` a été étendu (« nous vous recontactons pour », « avant de chiffrer »,
« confirmer la faisabilité »).

**Autre correction :** la confiance comptait les sources des *détections*, pas
celles des *preuves*. Le catalogue dédoublonnant par signal, deux pages
décrivant le même processus ne comptaient que pour une. Canfora restait en
confiance « moyenne » alors que bourrellerie **et** sellerie établissent le
même fait. Confiance désormais **haute**.

**Impact mesuré** (`data/history/scores-v7-vers-v71.json`, 78 fiches balayées,
12 changements) :

| Entreprise | IA v7 | IA v7.1 |
|---|---:|---:|
| Caléo Tests & Services | 32 | **74** |
| Cordonnerie Canfora David | 38 | **60** |
| Froger Étanchéité | 38 | **56** |
| Cordes et Âme | 0 | **43** |

Les huit autres changements sont des fiches de l'historique Gmail antérieur qui
n'avaient **aucun score** : elles reçoivent un score explicite et prudent
(5 / 5 / 0). **Aucun score des lots 1 à 8 n'a bougé.**

### 1.5 Diversification des sources et mémoire d'exploration

`prospecto/sources.py` fournit :

- **7 familles de sources** typées (site officiel, annuaire pro, registre public,
  page professionnelle, presse locale, appel à projets, autre), chacune avec sa
  fiabilité par défaut et **ses conditions d'accès** — le catalogue mentionne
  explicitement robots.txt, les CGU et l'interdiction de contourner un CAPTCHA ;
- **50 secteurs** et **61 territoires** de travail ;
- `coverage()` et `plan_queries()`, qui proposent des départements **non
  couverts** et font tourner les types de sources ;
- `ExplorationLedger`, registre persistant où **toute structure examinée est
  inscrite, y compris écartée, avec son motif**. Elle ne sera pas réexaminée.

Deuxième bug réel corrigé ici : `examined_sector_terms()` ne découpait pas les
slugs. `etalonnage_metrologie` restait un token unique qui ne matchait aucun
terme du pool — le planificateur reproposait donc un secteur déjà traité.

### 1.6 Références commerciales

Une référence n'est insérée que si elle éclaire la solution retenue
(`REFERENCE_RELEVANT_SOLUTIONS`). Formulations neutralisées :

- « Vous pouvez découvrir cet exemple de site : Groupe Bourasseau — {url} »
- « SYNATRAP est un projet autour des agents IA, si le sujet vous parle : {url} »

**Résultat sur le lot 9 : aucune référence dans les quatre messages.** Aucune
des quatre fiches ne relève de la création ou de la refonte d'un site
institutionnel, ni d'un agent IA. Forcer un lien aurait été hors sujet.

### 1.7 Limites assumées

- **Le mobile n'est pas vérifié.** Les pages sont lues en texte : aucun rendu
  mobile n'est observé. Les trois scores « refonte » portent explicitement la
  mention « comportement sur mobile non vérifié ».
- **Une seule consultation par page.** Pas de suivi dans le temps, donc pas de
  détection d'évolution.
- **Les processus internes ne sont pas observables.** Ce qui n'est pas publié
  reste une hypothèse, marquée comme telle et pondérée à la moitié.
- **24 structures sur 55 n'ont qu'une présence d'annuaire.** C'est un constat
  exploitable (absence de site) mais sans adresse publique vérifiée, aucune
  fiche contactable n'a pu être créée.

---

## 2. Lot 9 — recherche et qualification

### 2.1 Volumétrie

| Indicateur | Valeur |
|---|---:|
| Structures **examinées** | **55** |
| Retenues (fiches créées) | **4** |
| Écartées après examen, avec motif | 27 |
| Présence d'annuaire uniquement | 24 |
| Départements explorés | **23** |
| Types de sources utilisés | 3 (site officiel, annuaire pro, page professionnelle) |
| Fiches ajoutées au CRM | 4 → **78** |
| Emails professionnels vérifiés sur page | **4 / 4** |
| Téléphones professionnels vérifiés sur page | **4 / 4** |
| Brouillons Gmail créés | **4** |
| Messages envoyés | **0** |

**55 explorations pour 4 fiches est le résultat voulu**, pas un échec de
conversion : 27 structures ont été écartées *après* vérification, dont
certaines très bien placées sectoriellement mais déjà outillées.

Exemple notable : **L'Artisan Affûteur** (35) semblait être un excellent
candidat (affûtage itinérant, artisan solo, quatre canaux d'entrée). La lecture
de `lartisanaffuteur.fr/contact/` a montré une réservation Calendly avec
disponibilités en temps réel, un formulaire de tournée structuré avec
auto-complétion d'outils, un bon d'affûtage postal en ligne et des tarifs
publiés. **Écarté : aucune opportunité défendable.**

### 2.2 Secteurs et territoires neufs

Secteurs jamais traités : **étalonnage/métrologie**, **cordonnerie-bourrellerie**,
**étanchéité de toitures-terrasses**, **lutherie**.
Départements neufs au CRM : **03 (Allier)** et **35 (Ille-et-Vilaine)**.

### 2.3 Les quatre fiches

| Entreprise | Dept | Site | Refonte | IA | Confiance IA | Service recommandé |
|---|---|---|---:|---:|---|---|
| **Caléo Tests & Services** | 62 | caleo-ts.fr | 45 | **74** | moyenne | Automatisation administrative |
| **Cordonnerie Canfora David** | 03 | cordonnerie-canfora-moulins.fr | **71** | 60 | **haute** | Formulaire intelligent |
| **Froger Étanchéité** | 35 | froger-etancheite.fr | **71** | 56 | moyenne | Formulaire intelligent |
| **Cordes et Âme** | 75 | cordesetame.fr | 5 | **43** | moyenne | Automatisation administrative |

Score « création de site » = **5/100 pour les quatre** : elles ont toutes un
site en ligne. Vendre une création serait faux.

**Caléo Tests & Services** — Béthune, laboratoire indépendant depuis 2007,
COFRAC 2-5035, plus de 5 000 équipements vérifiés par an et 370 types
d'instruments. Le formulaire de devis est *bien construit*, champ par champ.
Le problème est ailleurs : il **se termine dans la messagerie du client**, et
les listes longues doivent arriver en tableur joint. Opportunité : dépôt côté
serveur et suivi de parc, pas réécriture du formulaire.
*Fait observé* : le bouton mailto, l'envoi en pièce jointe, les tarifs non
publiés. *Hypothèse* : la qualification ligne par ligne est humaine.

**Cordonnerie Canfora David** — Moulins, entrepreneur individuel, SIREN
482141652, APE 9523Z. Deux pages de service imposent le déplacement pour un
devis. Contact et fonction vérifiés dans les mentions légales
(« M. CANFORA DAVID », directeur de la publication). Opportunité : dépôt de
demande avec photos pour un premier chiffrage à distance.

**Froger Étanchéité** — Cesson-Sévigné, membre CSFE et FFB. **Le lien e-mail du
site est écrit à l'envers** : `mailto:moc.liamg%40etiehcnateregorf`. Un visiteur
qui clique sur « E-mail » n'écrit pas à l'entreprise. Défaut concret,
reproductible, avec perte de demandes à la clé.

> **Point de vigilance sur cette adresse.** `frogeretancheite@gmail.com` est le
> **décodage déterministe** de la chaîne publiée à l'envers, cohérent avec la
> raison sociale. Ce n'est **pas** une adresse déduite du nom de domaine. Cela
> reste une inférence de lecture : **à confirmer par téléphone (06 35 41 64 70)
> avant validation du brouillon.** C'est signalé dans la fiche.

**Cordes et Âme** — Paris, atelier depuis 1958, trois luthiers nommés.
L'entreprise **écrit elle-même sa difficulté** : appels difficiles à prendre,
messages relevés une fois par jour, préférence pour le mail. C'est un fait
observé, pas une déduction sectorielle. Une boutique avec panier existe déjà :
l'opportunité ne porte pas sur une création de site. Contact vérifié :
Jean-Baptiste Ferrier, maître luthier et chef d'atelier.

### 2.4 Anti-doublon et messages

Contrôle avant import sur **tout le CRM** : domaine, nom normalisé, email,
téléphone, liste d'opposition → **0 collision**. Aucun des quatre destinataires
n'apparaît dans la boîte Gmail, tous dossiers compris (`search_scope.complete:
true`, spam et corbeille inclus).

Quatre **variantes différentes** (`automation_ia`, `with_example`, `refonte`,
`short_hook`), objets personnalisés, **0 violation `check_email_v4`**, signature
exacte, mention d'opposition explicite dans chacun. Aucun prénom n'est utilisé
quand la fonction n'est pas vérifiée (Caléo, Froger).

---

## 3. Audit Gmail

### 3.1 Réconciliation des envois manuels

14 messages ont été envoyés manuellement le 6 novembre 2026 entre 16:39:36 et
16:40:29, **hors agent**. Ils sont réconciliés : **matched 14, unmatched 0**.

- lot 6 (`Label_4`) : 6 envois — Celtuce, Mamie Cuisine, Baptiste Break, Joly,
  Uzès, Techniques Piscine ;
- lot 7 (`Label_5`) : 5 envois — France-PNL, Atoutransport, Bonbon Foliz,
  L'Ô de Claise, Bulles & Détente ;
- lot 8 (`Label_6`) : 3 envois — Le Centre Formation, Jenback, MSF PRO.

**Ripaud est le seul brouillon des lots antérieurs restant**
(`1a1b16dee5899e57`). Les 11 brouillons des lots 6 et 7 et les 3 du lot 8 sont
`SENT` : la demande d'alignement de leur formulation sur celle du lot 8 est
**caduque** — `update_draft` est impossible sur un message envoyé. Aucune
tentative de modification.

### 3.2 Réponses, rebonds, oppositions

Six requêtes ciblées, toutes avec `search_scope.complete: true`, **spam et
corbeille inclus** :

| Catégorie | Sur les 14 envois |
|---|---:|
| Réponses humaines | **0** |
| Demandes d'information, devis, rendez-vous | **0** |
| Objections / refus | **0** |
| Oppositions nouvelles | **0** |
| Accusés de réception automatiques | **0** |
| Rebonds | **0** |
| Challenges de délivrance | **0** |

**Aucune réponse n'a été envoyée et aucun brouillon de réponse n'a été créé** :
il n'y avait rien à traiter.

Antérieurs, inchangés : opposition **Renarde** (`celarenarde@gmail.com`),
accusés automatiques BSP et B3R, rebond dur `contact@severine-lesourd.com`,
challenge Mailinblack **Alpha Mécanique — non validé**. Aucun rebond, accusé ou
challenge n'a reçu de réponse.

### 3.3 Écarts corrigés

- **Incident Uzès** : une entreprise `suspendu` a reçu un envoi manuel. Statut
  `suspendu` **conservé**, ajout de `sent_while_suspended: true`,
  `delivery_status: non_confirmee` et d'un champ `incident`. L'item de file
  passe à `sent` avec historique. L'historique n'est pas écrasé.
- **Journal d'envoi** : 46 → **60 entrées**, dont 37 marquées
  `gmail_manual_observed`. **0 entrée lot 9.**
- **« Accepté par Gmail » ≠ délivrance** : sur 60 messages sortis, **3 délivrances
  confirmées**, **55 non confirmées**, 1 rebond, 1 challenge. Les catégories
  sont exclusives et se somment exactement à 60.

---

## 4. Fiabilité

### 4.1 Tests

**350 tests, tous au vert** (292 existants + **58 nouveaux** dans
`tests/test_lot9.py`), en `python3 -m unittest discover tests -q`.

Les nouveaux tests couvrent : catalogue de sources et conditions d'accès,
planification hors territoires couverts, registre d'exploration (rechargement,
motif, termes de secteur), les quatre nouveaux signaux, l'exclusion des preuves
de maturité et de confiance, la confiance multi-pages, la pondération des
hypothèses et de la fiabilité, l'indépendance du score vis-à-vis du métier, la
pertinence des références, l'absence d'adresse, les statuts bloqués, les
oppositions, la partition exclusive du portefeuille, le comptage des
brouillons, et l'intégrité complète du lot livré.

Cinq échecs sont apparus à la première exécution. **Deux étaient des bugs
réels** (`examined_sector_terms`, `_is_blocked` sur « contacté »), un une marge
de longueur trop fine, deux des erreurs dans mes tests. Tous corrigés à la
source.

### 4.2 Fuite d'historique découverte et corrigée

En vérifiant l'arbre Git après commit, deux fichiers de données restaient
modifiés **à chaque exécution des tests**. Enquête faite, deux fuites réelles :

1. **`reconcile_sent()` écrivait toujours son historique dans le journal de
   production**, même quand l'appelant fournissait un CRM, une file et un
   journal en mémoire. Depuis le lot 8, chaque exécution de la suite ajoutait
   des rapprochements fictifs : **189 entrées de fixture sur 193** dans
   `data/history/reconciliations.json`. Il ne restait que **4 rapprochements
   réels**. Un paramètre `history_path` permet désormais d'isoler l'historique.
2. **`preflight()` persiste son résultat DNS** dans `data/campaigns/v4-settings.json`.
   Deux tests l'appelaient sur le fichier de production et réécrivaient
   `last_checked_at` à chaque run. Ils travaillent maintenant sur une copie.

**Aucune donnée n'a été détruite** : les 189 entrées parasites sont conservées
dans `data/history/reconciliations-pollution-tests-2026-11-06.json`, avec une
note expliquant leur origine. Le journal de production ne contient plus que les
4 rapprochements réels (15 envois du 5 nov, 8 sans file, 14 du 6 nov).

Trois tests de régression verrouillent les deux fuites, dont un qui compare le
contenu du journal de production avant/après un rapprochement isolé. Vérification
finale : **deux exécutions consécutives de la suite laissent les fichiers de
production bit pour bit identiques.**

C'est la raison pour laquelle « intégrité de l'historique » ne peut pas être
affirmée sur la seule lecture des fichiers : il faut vérifier que l'outillage
lui-même ne les abîme pas.

### 4.3 Pré-vol — toujours bloquant

```
(False, 3 issues)
  - Campagne non activée (enabled=false). Activation explicite requise.
  - DKIM non détecté pour le domaine expéditeur.
  - Domaine expéditeur gratuit (Gmail) : prospection de masse déconseillée/interdite par les CGU.
```

`ok_for_bulk: false`. **L'envoi manuel des 14 messages par l'utilisateur n'est
pas une autorisation d'envoyer** : le blocage est resté actif pendant toute la
mission. Aucune campagne activée, aucun contournement, aucun achat, aucune
modification DNS.

### 4.4 Tableau de bord (port 8787)

Trois défauts corrigés :

1. `ValidationQueue.counts()` n'énumérait que quatre statuts : les **4
   brouillons** du lot 9 et les **10 items obsolètes** étaient invisibles.
2. `renderPipeline()` construisait dix lignes de catégories **puis ne les
   renvoyait pas** : seul un résumé s'affichait.
3. Aucune catégorie ne couvrait l'amont du portefeuille ni l'exploration écartée.

État servi, calculé sur les données réelles :

**Portefeuille — partition exclusive, total 78, contrôle `cohérent`**

| Étape | Nombre |
|---|---:|
| Découverts | 13 |
| À investiguer | 1 |
| Brouillons en attente | 6 |
| Contactés | 55 |
| Rebonds | 1 |
| Oppositions | 1 |
| Suspendus | 1 |

Qualifiés (priorité haute ou moyenne) : **38** — lecture transversale,
explicitement marquée comme ne s'ajoutant pas aux étapes.

**Délivrance — contrôle `cohérent`** : 3 confirmées + 55 non confirmées + 1
rebond + 1 challenge = **60 envoyés**. Brouillons porteurs d'un draft Gmail :
**5** ; préparés sans brouillon : **1**.

**File** : total 68 — `sent` 52, `draft` 4, `pending` 2, `obsolete` 10, ouverts 6.

---

## 5. Git

| Élément | Valeur |
|---|---|
| Branche | `arena/7ed6352a-agent-prosect1` |
| Commit précédent | `9cae5b8` (évolution v7) |
| Commit de ce lot | `df49e42` — « Lot 9 : moteur v7.1, 55 explorations, 4 brouillons, catégories réelles » |
| Rapport | `docs/rapport-mission-2026-11-06-lot9.md` |

Fichiers principaux modifiés : `prospecto/{opportunity,scoring,models,sources,
references,messaging,sender,queue,metrics}.py`, `prospecto/dashboard.html`.
Ajouts : `tests/test_lot9.py`, `data/prospects/campagne-2026-11-06-lot9.json`,
`data/campaigns/campagne-2026-11-06-lot9.json`, `data/messages/messages-2026-11-06-lot9.json`,
`data/history/exploration-ledger.json`, `data/history/scores-v7-vers-v71.json`.

Aucun secret publié. Pas de fusion automatique.

---

## 6. Prochaine évolution — vers un fonctionnement quotidien autonome

L'agent ne peut pas tourner seul chaque jour en l'état. Voici ce qui manque,
par ordre de déblocage réel.

### 6.1 Bloquant — décision et dépense requises

**Un domaine d'envoi professionnel avec SPF, DKIM et DMARC.** Tant que
l'expéditeur est `martin.bourasseau4@gmail.com`, la prospection est contraire
aux CGU du fournisseur et le pré-vol bloque — à juste titre. Cela demande un
domaine, un service de messagerie ou un ESP, et un accès DNS. **Je m'arrête
ici : achat, abonnement et modification DNS ne relèvent pas de mon
autorisation.** Une fois en place, `enabled=true` devient une décision
commerciale explicite de votre part, pas une déduction.

### 6.2 Automatisable sans dépense

1. **Ordonnanceur quotidien** : `plan_queries()` sait déjà quoi chercher ensuite.
   Une tâche planifiée peut produire chaque matin un lot de requêtes non
   couvertes, en s'appuyant sur le registre pour ne rien réexaminer.
2. **Vérification mobile réelle** : les scores « refonte » plafonnent faute de
   rendu mobile. Un rendu headless lèverait le manque le plus fréquent.
3. **Re-vérification périodique des preuves** : `verified_at` est en place, la
   fraîcheur est déjà pondérée au-delà de 180 jours. Il manque le job qui
   reconsulte et signale ce qui a changé.
4. **Audit de boîte planifié** : les requêtes sont écrites et reproductibles ;
   elles peuvent tourner chaque jour et ne remonter que les nouveautés.
5. **Confirmation des adresses décodées** : cas Froger. Une règle « adresse
   obtenue par décodage → confirmation téléphonique avant brouillon » devrait
   être codée dans le pipeline plutôt que documentée dans une note.

### 6.3 Ce qui doit rester humain

La validation des brouillons, toute décision tarifaire ou commerciale, la
réponse à une négociation, et l'activation d'une campagne. Le moteur peut
préparer ; il ne doit pas décider d'engager.

---

## Annexe — artefacts

| Chemin | Contenu |
|---|---|
| `data/history/exploration-ledger.json` | 55 structures examinées, décision et motif |
| `data/history/scores-v7-vers-v71.json` | 12 changements de scores, avant/après |
| `data/history/scores-v6-vers-v7.json` | 66 changements du passage v6 → v7 |
| `data/prospects/campagne-2026-11-06-lot9.json` | 4 fiches, preuves complètes |
| `data/messages/messages-2026-11-06-lot9.json` | 4 messages, 0 violation |
| `data/campaigns/campagne-2026-11-06-lot9.json` | campagne désactivée, 4 brouillons |
| `data/backups/2026-11-06-avant-lot9/` | sauvegarde préalable, 38 fichiers |
| `data/history/reconciliations-pollution-tests-2026-11-06.json` | 189 entrées de test mises en quarantaine, conservées |
