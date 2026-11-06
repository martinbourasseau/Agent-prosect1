# Mission du 6 novembre 2026 — Gestion des réponses & lot 6

**Compte :** martin.bourasseau4@gmail.com · **Branche :** `arena/7ed6352a-agent-prosect1`
**Périmètre :** audit complet de la boîte + nouveau lot de prospection France entière.

> **Découverte structurante.** Les 15 brouillons des lots 4 et 5 ont été **envoyés manuellement
> depuis Gmail le 5 novembre 2026 entre 14:33:59 et 14:34:37**, hors agent. Le CRM et la file les
> croyaient encore « brouillon créé ». Le nombre réel d'envois de prospection est donc de **38**,
> et non 23. Tout a été réconcilié avant l'audit des réponses.

---

# A. GESTION DES RÉPONSES

## A.1 — Envois examinés

| Lot | Envois constatés | Date | Label Gmail |
|---|---|---|---|
| Historique antérieur à l'agent | 2 | 3 nov. 09:16–09:17 | — |
| Lots 1 à 3 | 21 | 3–4 nov. 22:21–22:26 | `Label_1` (lot 3) |
| **Lot 4** | **8** | **5 nov. 14:33:59–14:34:20** | `Label_2` |
| **Lot 5** | **7** | **5 nov. 14:34:22–14:34:37** | `Label_3` |
| **Total** | **38** | | |

Réconciliation opérée par `reconcile-sent --apply` : **15 éléments alignés, 0 non rapprochés,
0 doublon**. Chaque transition est tracée dans l'historique de l'élément avec l'identifiant du
message Gmail comme preuve ; aucun historique n'a été écrasé.

## A.2 — Méthode d'audit (exhaustivité démontrée)

La boîte contient **29 383 messages** : un balayage général est inutilisable. Trois requêtes
ciblées, toutes retournées `complete: true`, spam et corbeille inclus :

1. `from:(18 adresses exactes)` — destinataires sur fournisseurs gratuits (Gmail, Orange, Yahoo, Wanadoo).
2. `from:(19 domaines d'entreprise)` — capture aussi les réponses émises depuis une **autre adresse** du même domaine.
3. `from:(mailer-daemon OR postmaster) newer_than:5d` — rebonds.

Contrôle croisé : `-in:sent -in:drafts "ne pas me relancer"` (toute réponse citant notre ligne
d'opposition) → 1 résultat, cohérent.

## A.3 — Réponses humaines trouvées : 1

| Prospect | Contenu exact | Analyse | Décision |
|---|---|---|---|
| **Centre Équestre de la Renarde** — Smets Nicolas, Brignoles (83) | « **Ne pas me relancer** » + signature complète | Opposition explicite. Réponse humaine, mais **sans aucun intérêt commercial** : ni question, ni demande de renseignement, ni proposition de rendez-vous. | **Aucune réponse envoyée.** Opposition enregistrée, adresse ajoutée à la liste de suppression, statut CRM `opposition`, `opposed: true`, prochain contact interdit. |

Message `1a1ada77bcf46db9`, fil d'origine `1a1a8095e0a13794`, reçu le 5 nov. à 22:39:45,
rattaché au prospect par correspondance exacte d'adresse (élément de file `2026-11-04-lot2-001`).

## A.4 — Réponses commerciales à traiter : 0

**Aucune demande de renseignements, aucune demande de devis, aucune proposition de rendez-vous,
aucune réponse positive, aucun refus argumenté** n'a été trouvé sur les 38 envois.

En conséquence :

- **Réponses effectivement envoyées : 0.**
- **Brouillons de réponse à valider : 0.**

Il n'y avait rien à quoi répondre. Répondre à l'opposition aurait contrevenu à la fois à la
consigne « jamais de réponse aux messages sans intérêt commercial » et au respect dû à une
désinscription. Aucune réponse n'a été inventée pour remplir un quota.

## A.5 — Accusés automatiques : 2

| Émetteur | Contenu | Traitement |
|---|---|---|
| **BSP Auto** `resa@bsp-auto.com` | « Ticket Reçu — Votre demande a bien été prise en compte par nos services. » | Accusé de billetterie. Aucune réponse. Statut `auto_reply`, délivrance confirmée. |
| **B3R** `contact@blanchisseriedes3regions.fr` | « Cette adresse va bientot disparaitre, la Blanchisserie des 3 régions a été **rachetée par Gallia**. Pour toute demande ou prise de contact, merci désormais d'utiliser l'adresse suivante : **b3r@gallia28.fr** » — signé Stéphanie | Accusé automatique, **aucune réponse**. Information commerciale de valeur extraite et conservée : `redirect_address = b3r@gallia28.fr`. |

**Suite à donner à B3R (décision utilisateur requise).** L'entreprise a été rachetée : l'accroche
envoyée (« votre site affiche une page d'hébergement suspendu ») est probablement obsolète, et
l'adresse actuelle va disparaître. La fiche porte désormais la mention « vérifier et requalifier
avant toute décision ». **Aucun contact automatique n'a été effectué vers `b3r@gallia28.fr`** :
ce serait un nouvel envoi de prospection, non autorisé.

## A.6 — Rebonds : 1 (aucun nouveau)

`contact@severine-lesourd.com` — domaine `severine-lesourd.com` inexistant (NXDOMAIN), rebond dur
du 4 nov. Déjà en suppression. **Les 15 envois du 5 novembre n'ont produit aucun rebond.**
Taux de rebond dur : **1 / 38 = 2,6 %**.

## A.7 — Conversations sans réponse

**35 des 38 envois** n'ont reçu ni réponse, ni accusé, ni rebond. Attention : l'absence de rebond
ne prouve pas la remise en boîte du destinataire. Seuls 2 envois ont une délivrance confirmée
(par accusé automatique).

## A.8 — Liste de suppression

| Adresse | Motif | Date |
|---|---|---|
| `contact@severine-lesourd.com` | Rebond dur — domaine inexistant | 4 nov. |
| `celarenarde@gmail.com` | **Opposition explicite** | **6 nov. (appliquée immédiatement)** |

---

# B. NOUVELLE PROSPECTION — LOT `2026-11-06-lot6`

## B.1 — Volumétrie

| Indicateur | Valeur |
|---|---|
| Structures repérées (recherche France entière) | **29** |
| Vérifiées par consultation directe des pages officielles | **8** |
| Ajoutées au CRM | **7** |
| Doublons évités | **0 collision** sur 64 fiches (contrôle automatique à l'import) |
| Qualifiées « besoin réel » (priorité haute) | **4** |
| Qualifiées « opportunité probable » (priorité moyenne) | **3** |
| Emails vérifiés à la source officielle | **6** |
| Email public non vérifié | **1** (Uzès Location) |
| Adresses MX valides | **6 / 7** |
| **Adresse non délivrable détectée** | **1** (SAS Maire) |
| Téléphones professionnels publics | **7 / 7** |
| Responsables identifiés (publics et fiables) | **3** |
| **Brouillons Gmail créés** | **6** |
| **Envois de prospection** | **0** |

**Nouveaux départements couverts :** 30, 44, 55, 62, 78 (plus 38 et 76 déjà connus).
**Nouveaux secteurs :** traiteur d'entreprise, pâtisserie sur commande, location de matériel BTP
et d'échafaudages, travaux publics avec location d'engins, pisciniste.

## B.2 — Les 7 entreprises ajoutées, avec le besoin observé

Scores **indépendants** : création / refonte / agent IA-automatisation, sur 100.
Aucun score IA n'est déduit du secteur : chacun repose sur une preuve citée et une URL.

| # | Entreprise | Dept. | Créa. | Refonte | IA | Priorité | Besoin observé (vérifiable) |
|---|---|---|---:|---:|---:|---|---|
| 1 | **Celtuce Traiteur** — Rezé | 44 | 5 | 45 | **90** | haute | La page devis exige 5 informations précises et fournit un **modèle d'e-mail à trous** (`mailto` pré-rempli) au lieu d'un formulaire. Les plateaux-repas ont déjà une boutique en ligne ; les devis buffets restent manuels. |
| 2 | **Mamie Cuisine Traiteur** — St-Quentin-Fallavier | 38 | 5 | 45 | **90** | haute | « Les plateaux-repas se commandent en ligne » mais « pour les buffets ou petit-déjeuners, **uniquement par mail au minimum 72h à l'avance** ». Forfait de livraison « calculé selon votre zone », non exposé au client. |
| 3 | **Baptiste Break Pâtisserie Traiteur** — Sartrouville | 78 | 5 | 5 | **100** | haute | CGV : commande par mail ou téléphone, « **devis par mail sous un maximum de 72h** ». Page commande : nombre de commandes limité par semaine, « certaines dates peuvent être complètes plusieurs semaines à l'avance », créneau réservé à réception de l'acompte. Ni créneaux, ni devis, ni suivi d'acompte en ligne. |
| 4 | **SARL Joly Location** — Sangatte | 62 | **90** | 25 | **70** | haute | Le second domaine `jolylocation-echafaudage.fr`, **encore déclaré sur sa fiche Pages Jaunes**, affiche « This site is not published ». Le site actif est `joly-location.fr`. Parc de 35 000 m² d'échafaudages, devis « personnalisés » sur simple demande, sans disponibilité en ligne. |
| 5 | **SARL Uzès Location** — Uzès | 30 | 5 | **75** | 30 | moyenne | Le site invite à « réserver » mais le formulaire ne demande que nom, téléphone, e-mail et message libre : ni matériel, ni dates, ni durée. Aucun calendrier de disponibilité. |
| 6 | **SAS Maire** — Senon | 55 | 5 | **75** | 30 | **à approfondir** | Une vingtaine d'engins nommément listés (PC 09 à PC 290, chargeurs, PW), location « avec et sans conducteur », mais la page se termine par « contactez nous par téléphone / par e-mail ». **Aucun brouillon : adresse non délivrable (voir B.4).** |
| 7 | **Techniques Piscine** — Le Havre | 76 | 5 | **75** | 30 | haute | Formulaire réduit à nom / e-mail / téléphone / message, sans type de projet ni localisation, alors que l'entreprise annonce 4 prestations et intervient sur 3 départements. |

**Responsables publics retenus** (uniquement sources fiables) : Yoann Marty, chef traiteur (site
officiel Celtuce) ; Baptiste Bresser, dirigeant (CGV officielles, SIRET 82139868200020) ;
Robert Joly, gérant (annuaire officiel de la mairie de Sangatte). Les 4 autres fiches n'ont
**aucun nom inventé**.

## B.3 — Ce qui a été écarté, et pourquoi

- **Auto-école Defrance (94)** — vérifiée puis écartée : site réalisé par la plateforme
  Vroomvroom, formulaire de contact déjà structuré (formation souhaitée, coordonnées, consentement).
  Aucune lacune démontrée.
- **Réseaux et franchises** — Irripiscine, Piscines HydroSud, PLS Location (multi-agences),
  Celtic School Rennes (prise de rendez-vous en ligne déjà en place).
- **Faux site** — `artisan.goldwizard.fr` : téléphone `06 12 34 56 78`, e-mail masqué,
  « 850 projets » invérifiables. Site de démonstration, pas une entreprise.
- **Emails obfusqués** — AD Conduite, L'Atelier Ferronnerie : adresse non reconstructible de façon fiable.
- **Pistes conservées sans vérification** — TP Services, Lapierre Traiteur, Hervé Hayraud,
  les 4 cabinets de géomètres, Menuiserie Deschenes, Le Menuisier Nantais, Atelier de la Croisière,
  Piscine & Spas Avelin, Atlante Piscine : repérés mais **non consultés directement**, donc non
  qualifiés. Aucun n'a été ajouté sur la seule base d'un extrait de recherche.

## B.4 — Anomalie de coordonnées détectée : SAS Maire

L'adresse publiée **sur leur propre site** est `info@sas-maire.fr`. Contrôle DNS du 6 novembre :

```
sas-maire.fr    MX = NXDOMAIN   A = NXDOMAIN   NS = NXDOMAIN
maire-sas.fr    MX = 0 mail.maire-sas.fr.   A = 109.234.166.92   NS = o2switch
```

Le domaine de l'adresse e-mail **n'existe pas**, tandis que celui du site est parfaitement
configuré : inversion probable du nom de domaine dans l'adresse publiée. L'entreprise ne peut
recevoir aucun e-mail à cette adresse.

**Décision :** entreprise conservée au CRM (interessante, preuves solides), statut
`à approfondir`, **aucun brouillon créé**. Seul canal connu : 03 29 85 99 15. Une adresse sur
`maire-sas.fr` reste à confirmer publiquement — elle n'a pas été devinée.

## B.5 — Les 6 brouillons Gmail

Label **`Prospection/2026-11-06-lot6`** (`Label_4`), appliqué aux 6 messages (vérifié : 6/6
portent `DRAFT` + `Label_4`). **Aucun n'est envoyé.**

| ID file | Entreprise | Objet | Variante | Référence | Mots | ID brouillon |
|---|---|---|---|---|---:|---|
| lot6-001 | Celtuce Traiteur | Celtuce : vos devis buffets recopiés à la main ? | `automation_ia` | synatrap.com | 149 | `r4668255302629793023` |
| lot6-002 | Mamie Cuisine Traiteur | Mamie Cuisine : la règle des 72 h, appliquée automatiquement ? | `refonte` | groupebourasseau.com | 146 | `r7069133405038258003` |
| lot6-003 | Baptiste Break | Baptiste Break : vos semaines complètes visibles avant la demande ? | `synatrap_ia` | synatrap.com | 145 | `r-2074566668747048619` |
| lot6-004 | SARL Joly Location | Joly Location : votre ancien domaine renvoie « site non publié » | `with_example` | groupebourasseau.com | 148 | `r7248452827625200722` |
| lot6-005 | SARL Uzès Location | Uzès Location : matériel, dates, durée — demandés dès le formulaire ? | `demo_site` | synatrap.com | 144 | `r8584317365937954867` |
| lot6-006 | Techniques Piscine | Techniques Piscine : qualifier le projet avant le premier appel ? | `short_hook` | — | 126 | `r-1290563027882505100` |

**Contrôles avant création :** `check_email_v4` sur les 6 → **0 violation**. 6 objets distincts,
**6 variantes distinctes**, 3 formulations d'appel à l'action, 2 références réparties selon la
pertinence réelle (site institutionnel pour un problème de domaine, plateforme IA pour un
processus à automatiser). Signature exacte **Martin BOURASSEAU** + `https://prospecto.website`
vérifiée sur les 6. Ligne d'opposition présente sur les 6. Aucun destinataire en liste de suppression.

## B.6 — Blocage d'envoi, inchangé

**PRÉ-VOL : BLOQUÉ ❌** — trois motifs, tous indépendants de cette mission :

1. `campaigns.enabled = false` — activation des campagnes non validée par l'utilisateur.
2. **DKIM absent** sur le compte d'envoi (`dkim_present: false`).
3. Domaine d'envoi `gmail.com`, fournisseur gratuit : `ok_for_bulk: false`. SPF présent,
   DMARC présent mais `p=none`.

L'autorisation de répondre aux conversations humaines **n'a pas activé les campagnes**. Aucun
e-mail n'a été envoyé à une nouvelle entreprise. Aucune modification DNS, aucun service payant,
aucun contournement de verrou, aucune modification de SYNATRAP / SYNATRAPE.

---

# C. CUMUL GLOBAL DEPUIS LE LANCEMENT

| Indicateur | Avant cette mission | Après |
|---|---:|---:|
| Fiches CRM | 57 | **64** |
| Emails renseignés | 45 | **52** |
| dont vérifiés à la source | 33 | **38** |
| Téléphones | 37 | **44** |
| Envois de prospection constatés | 23 *(sous-évalué)* | **38** *(réel, réconcilié)* |
| Brouillons en attente | 15 *(en réalité envoyés)* | **6** |
| Rebonds durs | 1 | 1 |
| Accusés automatiques | 1 | **2** |
| Réponses humaines | 0 *(non détectées)* | **1** (opposition) |
| Désinscriptions / oppositions | 0 | **1** |
| Liste de suppression | 1 | **2** |
| Fiches scorées (3 axes) | 7 | **14** |
| Lots distincts suivis | 8 | **9** |

---

# D. TESTS, CORRECTIONS ET FICHIERS

## D.1 — Tests

**177 tests, tous réussis** (`python3 -m unittest discover tests -q`), dont **33 nouveaux**
dans `tests/test_lot6.py`, sans aucun accès réseau :

- 8 tests d'extraction d'adresse de remplacement (français, anglais, expéditeur, adresses de rôle).
- 2 tests de classification (opposition vs vraie réponse humaine).
- 10 tests de réconciliation : idempotence, preuve conservée, historique non écrasé,
  **statut avancé jamais rétrogradé**, destinataire inconnu signalé, insensibilité à la casse.
- 3 tests de personnalisation des démonstrations.
- 5 tests de rotation des appels à l'action (stabilité, jeu autorisé, diversité).
- 5 tests de fusion des réponses entrantes (pas de double compte).
- 1 test d'identité d'expéditeur sur les 6 variantes.

## D.2 — Quatre défauts réels corrigés

1. **`demo_detail` ignoré pour les prospects « automatisation ».** Le moteur remplaçait la
   démonstration patiemment recherchée par une phrase générique identique pour tous. Les 6
   messages du lot auraient été standardisés. Le détail personnalisé prime désormais sur tous les axes.
2. **Appel à l'action unique.** Tous les messages se terminaient par la même phrase. Trois
   formulations sont maintenant en rotation déterministe (reproductible).
3. **Métriques aveugles à l'audit de boîte.** Le bloc `replies` affichait 0 opposition alors que
   l'opposition était déjà comptée dans `deliverability`. Fusion par identifiant de message,
   sans double compte. Vérifié : `replies.total = 4` (1 rebond, 2 accusés, 1 opposition).
4. **Aucun outil pour constater les envois faits hors agent.** Nouveau module `reconcile.py` +
   commande `reconcile-sent`, qui aligne file, CRM et journal sur la réalité de Gmail sans jamais
   écraser l'historique ni rétrograder un statut.

## D.3 — Anomalies constatées

| Anomalie | Gravité | Traitement |
|---|---|---|
| 15 brouillons envoyés hors agent, non reflétés dans le CRM | **haute** | Réconcilié (15/15), module dédié + 10 tests |
| `info@sas-maire.fr` non délivrable (domaine NXDOMAIN) | moyenne | Entreprise conservée, aucun brouillon, canal téléphone seul |
| Ancien domaine Joly Location non publié mais encore référencé | moyenne | Preuve retenue comme accroche vérifiable |
| B3R rachetée par Gallia, adresse en cours de disparition | moyenne | Adresse de remplacement conservée, requalification soumise à l'utilisateur |
| Métriques `replies` à zéro malgré une opposition | moyenne | Fusion audit + journal, 5 tests |
| `demo_detail` et CTA non personnalisés | moyenne | Corrigés, 8 tests |
| 1 accroche dépassait la limite de 150 mots | faible | Resserrée à 149 mots, contrôle repassé à 0 violation |

## D.4 — Fichiers modifiés ou créés (19 entrées)

**Code (5)** — `prospecto/reconcile.py` *(nouveau)*, `prospecto/cli.py`,
`prospecto/inbox_audit.py`, `prospecto/messaging.py`, `prospecto/metrics.py`.

**Tests (1)** — `tests/test_lot6.py` *(nouveau, 33 tests)*.

**Données (6 modifiés)** — `data/crm/prospects.json`, `data/queue/validation_queue.json`,
`data/history/send-log.json`, `data/history/inbox_audit.json`, `data/history/domain_checks.json`,
`data/suppression.json`.

**Données (6 nouveaux)** — `data/prospects/campagne-2026-11-06-lot6.json`,
`data/prospects/campagne-2026-11-06-lot6-contactables.json`, `data/campaigns/2026-11-06-lot6.json`,
`data/inbox/audit-2026-11-06.json`, `data/inbox/sent-observed-2026-11-05.json`,
`data/history/reconciliations.json`.

**Sauvegarde** — `data/backups/2026-11-06-avant-lot6/` : 24 fichiers, état complet avant toute modification.

**Rapport** — `docs/rapport-mission-2026-11-06.md` *(ce document)*.

## D.5 — Tableau de bord

Redémarré pour charger les modules Python corrigés (process `tableau-de-bord-prospecto-22cf97ff`,
port 8787). Vérifié après authentification : CRM 64, file 17 en attente / 38 envoyés,
`replies` = 1 rebond + 2 accusés + 1 opposition, 9 lots, lot 6 = 7 prospects / 6 brouillons / 0 envoi.

---

# E. CE QUI ATTEND L'UTILISATEUR

1. **Valider les 6 brouillons du lot 6** (label `Prospection/2026-11-06-lot6`) — ou demander des retouches.
2. **Trancher pour B3R** : l'entreprise est rachetée par Gallia ; faut-il requalifier la fiche
   vers `b3r@gallia28.fr`, ou la classer sans suite ?
3. **Confirmer l'adresse d'Uzès Location** avant envoi : `uzeslocation.30700@gmail.com` provient
   d'un extrait indexé et n'apparaît plus sur la page contact actuelle.
4. **Lever les trois blocages d'envoi** (activation, DKIM, domaine propre) pour toute campagne
   future. En l'état, aucun envoi de prospection n'est possible ni autorisé.

**Aucune relance ne sera adressée au Centre Équestre de la Renarde.**
