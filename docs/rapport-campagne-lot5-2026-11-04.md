# Rapport de campagne — Lot 5
**Date : 4 novembre 2026 · Branche : `arena/7ed6352a-agent-prosect1` · Expéditeur : Martin BOURASSEAU**

> **Aucun email n'a été envoyé pendant ce lot.** Les 7 messages existent uniquement à l'état de
> brouillons Gmail labellisés `Prospection/2026-11-04-lot5`. Le pré-vol reste bloqué par trois
> verrous indépendants (§8).
>
> **Correction importante apportée aux rapports précédents :** les lots 1 à 4 annonçaient
> « 0 réponse, 0 rebond ». C'était **faux**. L'audit de la boîte a retrouvé **1 rebond dur** et
> **1 accusé de réception automatique** que l'ancienne méthode de détection ne pouvait pas voir.
> La cause est identifiée, corrigée et testée (§5 et §13).

---

## 1. Entreprises examinées

| Élément | Volume |
|---|---|
| Entreprises ou structures examinées (recherche + tri) | **≈ 60** |
| Pages officielles réellement ouvertes et vérifiées | **20** |
| Recherches web ciblées | **13** |
| Secteurs nouveaux couverts par le lot | **6** |

Secteurs explorés : organismes de formation continue, propreté industrielle et services aux
entreprises, usinage / sous-traitance industrielle, blanchisserie industrielle, cavistes et
ateliers d'œnologie, transport sanitaire, self-stockage, contrôle technique, pépinières et
paysagistes, torréfacteurs, contrôle réglementaire, hébergement touristique, artisans du bâtiment.

Couverture géographique du lot : **95, 39, 75, 76, 69, 87, 28** — sept départements, dont
cinq jamais touchés par les lots précédents (95, 39, 76, 87, 28).

**Candidats écartés et pourquoi** (le tri fait partie du travail) :

| Écarté | Motif |
|---|---|
| Pépinières Mainaud (01) | Site récent, e-shop, outils de reconnaissance de plantes et formulaire de devis : déjà équipé, aucune lacune réelle |
| Akromeca (92), STMB Rosse | Création de devis en ligne avec dépôt de plans : processus déjà outillé |
| GREM (78) | Site moderne, filiale d'un groupe, certification ISO : la refonte n'est pas un besoin |
| Les Comptoirs du Café (84) | Boutique en ligne avec panier fonctionnel |
| La Brûlerie Nantes, Pépinières Français, Penthièvre | E-commerce / portail B2B déjà en place |
| Contrôle technique Briec, Autosur, Dekra | Réseaux nationaux : le décideur du site n'est pas local |
| Costockage, Bluespace, Box à la Carte | Réservation en ligne mature |
| PLB, Capgemini Institut, FC ENPC, CECA | Grands comptes, organismes publics ou associations |
| Chambres d'hôtes Bienvenue (48) | Site entièrement en erreur 404 : coordonnées non revérifiables sur une page vivante, donc **non contactée** |
| PFI SAT (77) | Besoin réel (planification des vérifications par téléphone/email) mais adresse email masquée par JavaScript : **non contactée** |
| Conteneur Montage Rapide | Société belge, hors périmètre France |

Aucun besoin n'a été déduit du seul secteur d'activité : chaque prospect retenu porte au moins
une preuve citée avec son URL et sa date d'observation.

## 2. Prospects ajoutés au CRM

**7 nouveaux prospects**, CRM porté de **50 → 57 fiches**. Fichier source :
`data/prospects/campagne-2026-11-04-lot5.json`.

| # | Entreprise | Ville (dpt) | Secteur | Responsable public |
|---|---|---|---|---|
| 001 | ATOMER | Groslay (95) | Formation continue chimie / analyses R&D | Laurent CANCOUËT, Directeur Général |
| 002 | NETTOYAGE INDUSTRIEL | Lons-le-Saunier (39) | Propreté industrielle B2B | Michael Rigaud |
| 003 | Vignerons et Caviste | Paris (75) | Caviste + cours d'œnologie | Stéphane (accueil) |
| 004 | La Caviste | Le Havre (76) | Caviste indépendant | Frédérique Lecaudé, Maître Caviste |
| 005 | ALPHA MECANIQUE | Vénissieux (69) | Usinage de précision | aucun nom publié |
| 006 | SARL Ambulances Sainte-Marie | Couzeix (87) | Transport sanitaire | Christophe Duprat, fondateur |
| 007 | Blanchisserie des 3 Régions | Cherisy (28) | Blanchisserie industrielle | aucun nom publié |

Quand aucun nom n'est publié, la salutation reste « Bonjour, » : aucun prénom n'a été inventé
à partir d'une adresse email.

## 3. Doublons évités

- Les **50 fiches existantes** ont été relues avant toute recherche.
- Chaque candidat a été contrôlé sur **le domaine puis l'adresse email** : **7 contrôles négatifs
  sur 7**, donc **0 doublon créé**.
- Plusieurs candidats ont été écartés en amont parce qu'ils étaient déjà traités ou déjà exclus
  (Blondeau Déménagement, écarté au lot 4, est réapparu dans les résultats self-stockage).
- Le rattachement par lot a été reconstitué pour les 50 fiches antérieures à partir de la file de
  validation et des fichiers de campagne — **aucune donnée n'a été écrasée**, seuls des champs
  vides ont été comblés.

## 4. Prospects qualifiés

**7 sur 7 qualifiés et contactables**, donc 7 brouillons.

| Entreprise | Niveau CRM | Preuve décisive |
|---|---|---|
| ATOMER | haute | CGV officielles : « Les inscriptions doivent être confirmées par écrit à l'aide d'un bulletin d'inscription […] renvoyé par e-mail ou par courrier » |
| NETTOYAGE INDUSTRIEL | haute | Formulaire de contact limité à « Nom, Adresse email, Message » + captcha, sans qualification du besoin |
| ALPHA MECANIQUE | haute | « Dès réception de vos plans, nous analysons les dimensions, les tolérances, la matière […] » puis devis sous 24 à 48 h |
| Ambulances Sainte-Marie | haute | « Gestion des demandes d'entente au préalable », tiers payant, 12 véhicules |
| Blanchisserie des 3 Régions | haute | « This site is currently suspended » — site entier hors ligne, constaté le 04/11/2026 |
| Vignerons et Caviste | moyenne | « Avant toute réservation en ligne, merci de nous écrire un mail […] pour s'assurer des disponibilités » |
| La Caviste | moyenne | « Nous donnons très peu de renseignements par téléphone » + aucune commande en ligne |

## 5. Répartition haute / moyenne / faible

**Lot 5** : **5 haute / 2 moyenne / 0 faible / 0 à approfondir**.
Priorité commerciale (besoin × contactabilité) : **6 haute / 1 moyenne**.

**CRM complet (57 fiches)** : 12 haute · 25 moyenne · 12 à approfondir · 8 non scorées
(fiches issues de l'historique Gmail antérieur, sans preuve conservée).

## 6. Emails vérifiés / non vérifiés

| Niveau | Lot 5 | CRM total |
|---|---|---|
| `verified` (publié sur une page officielle ouverte) | **6** | 33 |
| `public_unverified` (publié mais non revérifiable) | **1** | 12 |
| Sans adresse | 0 | 12 |
| **Total adresses** | **7** | **45** |

**Nouveauté du lot : contrôle DNS systématique.** Les 45 adresses du CRM ont été vérifiées :
**44 domaines routables (MX présents), 1 domaine inexistant**. Aucune connexion SMTP n'a été
ouverte et aucun message de test n'a été envoyé : le contrôle est purement DNS.

Les 7 adresses du lot 5 ont des MX valides, y compris `blanchisseriedes3regions.fr` : son
hébergement web est suspendu, mais sa messagerie (Microsoft 365) est indépendante et fonctionne.
Son adresse reste classée `public_unverified` car elle provient du contenu indexé du site,
aujourd'hui inaccessible — elle n'est **pas** présentée comme vérifiée.

## 7. Téléphones vérifiés

**7 numéros sur 7 prospects** : 6 `verified` (relevés sur la page officielle ouverte) et
1 `public_unverified` (B3R). CRM total : **37 numéros**.

## 8. Sécurité d'envoi — état inchangé

```
PRÉ-VOL : BLOQUÉ ❌
  - Campagne non activée (enabled=false). Activation explicite requise.
  - DKIM non détecté pour le domaine expéditeur.
  - Domaine expéditeur gratuit (Gmail) : prospection de masse déconseillée/interdite par les CGU.
```

**0 envoi réel, 0 contournement.** Aucun réglage DNS, aucun abonnement, aucune activation.
Le fichier `data/campaigns/v4-settings.json` n'a changé que sur l'horodatage du dernier contrôle ;
`enabled` reste `false`. Les projets SYNATRAP et SYNATRAPE n'ont pas été modifiés.

## 9. Besoins de création de site

**1 besoin fort** : Blanchisserie des 3 Régions — score **90/100**. Le site institutionnel renvoie
la page de suspension de l'hébergeur sur la racine **et** sur une page intérieure. Une entreprise
B2B qui couvre trois régions n'a plus de vitrine accessible.

Les 6 autres ont un site en ligne : leur score de création est volontairement bas (5/100), avec
le motif explicite « un site est déjà en ligne : pas de création à proprement parler ».

## 10. Besoins de refonte

| Entreprise | Score | Motif sourcé |
|---|---|---|
| NETTOYAGE INDUSTRIEL | **85** | Site d'éditeur d'hébergeur, bascule manuelle « Affichage Web / Affichage Mobile », liens d'administration publics, formulaire non qualifié |
| Vignerons et Caviste | **75** | Parcours de réservation cassé : confirmation manuelle obligatoire avant achat, atelier vendu « en stock » sans date |
| La Caviste | **75** | Site vitrine sans panier ni click & collect, téléphone volontairement peu utilisé |
| ATOMER | **55** | Navigation en images GIF, mise en page en tableaux, HTTP, catalogues et programmes uniquement en PDF, copyright « 1997 - 2024 » |
| Ambulances Sainte-Marie | 35 | Formulaire libre avec question anti-spam, sans pré-qualification |
| Blanchisserie des 3 Régions | 35 | Vitrine à reconstruire (déjà comptée en création) |
| ALPHA MECANIQUE | 5 | Site correct : **aucune refonte proposée**, ce serait un argument faux |

## 11. Besoins d'agent IA / automatisation

| Entreprise | Score | Processus observé |
|---|---|---|
| ATOMER | **100** | Bulletin d'inscription PDF signé à renvoyer, dossiers incomplets mis en attente, puis conventions-convocations, factures, feuilles d'émargement et attestations envoyées par email |
| ALPHA MECANIQUE | **100** | Réception des plans par email, analyse manuelle des tolérances/matière/quantités, devis sous 24-48 h, commande par retour |
| Ambulances Sainte-Marie | **70** | Constitution des dossiers d'entente préalable et gestion du tiers payant pour 12 véhicules |
| NETTOYAGE INDUSTRIEL | 40 | Chantiers récurrents suivis par des responsables, demandes non qualifiées |
| Blanchisserie des 3 Régions | 40 | Devis et tournées de collecte (indice indirect) |
| Vignerons et Caviste | 30 | Vérification manuelle des disponibilités avant chaque réservation |
| La Caviste | 30 | Demandes spéciales traitées par email |

Les trois axes sont **indépendants** : ATOMER et ALPHA MECANIQUE ont un score IA de 100 et un
score de création de 5 ; B3R a un score de création de 90 et un score IA de 40. Chaque note est
accompagnée de ses motifs, avec l'extrait cité et l'URL.

## 12. Brouillons Gmail créés

**7 brouillons**, tous labellisés `Prospection/2026-11-04-lot5` (**Label_3**), tous vérifiés par
`check_email_v4` **avant** création : **0 anomalie**.

| File | Destinataire | Objet | Brouillon Gmail |
|---|---|---|---|
| lot5-001 | contact@atomer.fr | ATOMER : vos inscriptions encore par bulletin PDF ? | `r-3672069521747812245` |
| lot5-002 | nettoyage.industriel@wanadoo.fr | Nettoyage Industriel : qualifier vos demandes de devis | `r-2030763522328067709` |
| lot5-003 | vigneronsetcaviste@gmail.com | Vos cours d'œnologie : réserver sans appeler ? | `r-7012393960743457622` |
| lot5-004 | boutique@lacaviste.fr | La Caviste : vos commandes préparées sans emails | `r-3517500887937529637` |
| lot5-005 | contact@alphamecanique.fr | Alpha Mécanique : vos demandes de devis sur plans | `r9082772945695603666` |
| lot5-006 | ambulancestemarie@gmail.com | Ambulances Sainte-Marie : vos ententes préalables | `r-7886629766998266627` |
| lot5-007 | contact@blanchisseriedes3regions.fr | B3R : votre site affiche une page d'hébergement suspendu | `r1203180346807190290` |

Contrôles effectués sur les 7 : objets tous distincts et ≤ 70 caractères · **7 appels à l'action
différents** · corps de 123 à 142 mots · accroche appuyée sur une preuve citée · démo gratuite
« sans engagement » · opposition simple (« ne pas me relancer ») · signature officielle
**Martin BOURASSEAU / Création de sites web · Refonte · Agents IA · Automatisation** ·
référence choisie selon le besoin (synatrap.com pour l'IA, groupebourasseau.com pour le web).

La formulation de paternité a été adoucie sur ce lot : « voici le site institutionnel **de mon
groupe** » au lieu de « que j'ai conçu pour mon groupe ». Aucun contenu déjà correct des lots
précédents n'a été modifié.

**Vérification Gmail après création** : les 7 messages portent bien `["DRAFT", "Label_3"]`.
**Brouillons en attente, tous lots confondus : 15** (8 du lot 4 + 7 du lot 5).

## 13. Analyse de performance des lots 1 à 4

### Ce qui était faux

Les rapports annonçaient 23 envois, 0 réponse, 0 rebond. La détection interrogeait Gmail avec
`from:<adresse exacte du prospect>`. Cette méthode est structurellement incapable de voir :

- **un rebond**, qui arrive de `mailer-daemon@googlemail.com`, jamais du prospect ;
- **une réponse d'une autre adresse du même domaine**.

### Ce qui existe réellement

| Constat | Détail |
|---|---|
| **Rebond dur** | Message `1a1a87452d7ca7c0` — « Votre message n'est pas parvenu à **contact@severine-lesourd.com** […] DNS type 'mx' lookup […] NXDOMAIN ». Le site officiel est `severine-lesourd.**fr**` : l'adresse du lot 2 portait la mauvaise extension. |
| **Accusé automatique** | Message `1a1a8773ff8d4b90` de **resa@bsp-auto.com**, « Bsp-auto : Ticket Reçu ». Le CRM connaît `support@bsp-auto.com` : même domaine, autre boîte. C'est une **preuve de délivrance**, pas une marque d'intérêt. |
| **Réponse humaine** | **0**, confirmée par une recherche `in:anywhere` sur les 30 domaines prospectés, spam et corbeille inclus, sur 14 jours. |
| **Opposition** | **0**. |

Bilan de délivrabilité réel : **23 envoyés · 1 non délivré (4,3 %) · 1 accusé automatique ·
0 réponse humaine · 0 opposition · 21 délivrances non confirmées**.

### Diagnostic honnête

1. **La délivrabilité n'est pas démontrée.** La présence dans « Envoyés » ne prouve pas la remise.
   Avec SPF présent, **DKIM absent**, DMARC `p=none` et un domaine `gmail.com` gratuit, une part
   des messages a pu être classée en spam chez les destinataires sans générer le moindre rebond.
   Le taux de réponse de 0 % ne permet pas de conclure, dans un sens ni dans l'autre.
2. **La qualité des prospects était inégale.** Les lots 1 à 3 contiennent des fiches issues de
   petites annonces (Codeur.com) sans entreprise identifiable ni coordonnées : 12 fiches sont
   encore « à approfondir ». Le lot 5 corrige cela : 7 entreprises nommées, 7 sites vérifiés.
3. **La personnalisation était réelle mais l'offre trop large.** Les accroches citaient bien une
   preuve, mais plusieurs messages mélangeaient site, refonte et IA. Le lot 5 retient **un seul
   besoin dominant par message**, choisi par le score le plus élevé.
4. **Les objets étaient corrects** (courts, concrets, sans promesse). Rien à corriger.
5. **Les références étaient pertinentes**, mais la formulation de paternité était plus
   affirmative que nécessaire ; elle est adoucie sur le lot 5.
6. **Le volume est trop faible pour conclure.** 23 messages, dont 21 sans preuve de remise, ne
   constituent pas un échantillon permettant de juger une offre.

### Améliorations livrées dans ce lot (sans toucher aux emails déjà envoyés)

- **`prospecto/email_verify.py`** — contrôle MX avant préparation. Aurait bloqué le rebond :
  `severine-lesourd.com` → NXDOMAIN, `severine-lesourd.fr` → MX valide.
- **`prospecto/inbox_audit.py`** — détection par expéditeur démon + extraction du **destinataire
  réel** dans le corps, puis rattachement par email → domaine → `thread_id`. Le rebond n'est
  **jamais** attribué à l'adresse du démon.
- **`prospecto/scoring.py`** — trois scores indépendants et justifiés, au lieu d'un besoin déduit
  du secteur.
- **Métriques** — bloc `deliverability` qui sépare envoyé / délivré / rebondi, et ventilation
  par lot.

**Aucun email envoyé n'a été modifié. Aucune donnée, campagne ou historique n'a été supprimé.**

## 14. Conformité

- Coordonnées **publiées et vérifiables** uniquement ; chaque fiche porte l'URL source et la date.
- Trois niveaux distingués : `verified`, `public_unverified`, `none`. Une adresse supposée n'est
  jamais présentée comme vérifiée.
- Prospection B2B : message en lien direct avec l'activité professionnelle du destinataire,
  expéditeur clairement identifié, mention d'opposition simple et gratuite
  (« répondez ne pas me relancer »).
- **Liste de suppression respectée et alimentée** : `contact@severine-lesourd.com` y a été ajoutée
  pour rebond dur. Aucun recontact, aucune relance après opposition.
- Aucune donnée de santé collectée : pour le transporteur sanitaire, seules des informations
  publiques d'entreprise sont utilisées, et la démonstration proposée porte sur des exemples fictifs.
- CGU et limitations respectées : aucun contournement de CAPTCHA ni de dispositif anti-robot.
  Les pages protégées ou masquées (PFI SAT) ont été **écartées**, pas forcées.
- Aucun service payant, aucune modification DNS.

## 15. Tests

**144 tests, tous au vert** (110 existants + **34 nouveaux** dans `tests/test_lot5.py`).

```
python3 -m unittest discover tests -q
Ran 144 tests in 0.573s
OK
```

Couverture ajoutée : syntaxe et MX (résolveur simulé, aucun accès réseau) · NXDOMAIN bloquant ·
repli A · erreur DNS transitoire non concluant · cache · indépendance des trois scores · plafond
à deux preuves par axe · justification citant la source · priorité dégradée sans adresse joignable ·
extraction du destinataire d'un rebond Gmail FR et d'un DSN · non-attribution au démon ·
classification rebond / accusé / humain / opposition · rattachement par domaine et par thread ·
application bout-en-bout (CRM, suppression, journal, file) · idempotence de l'audit ·
persistance des nouveaux champs · délivrabilité « envoyé ≠ délivré » · signature officielle.

## 16. Fichiers créés ou modifiés

**Nouveaux modules**
- `prospecto/email_verify.py` — vérification DNS/MX + cache horodaté
- `prospecto/scoring.py` — trois scores indépendants + priorité commerciale
- `prospecto/inbox_audit.py` — détection et rattachement fiables des rebonds et réponses
- `tests/test_lot5.py` — 34 tests

**Nouvelles commandes**
- `prospecto verify-emails [--email X] [--apply] [--refresh]`
- `prospecto audit-inbox --file X.json [--apply]`
- `prospecto scores [--lot X] [--apply] [--verbose]`

**Modules enrichis** : `models.py` (5 types de preuve + 10 champs de suivi), `crm.py`,
`qualification.py`, `metrics.py` (délivrabilité, lots, scores), `cli.py`, `dashboard.html`
(onglet **Délivrabilité & Lots**, filtre par lot, colonne des trois scores, badge DNS,
prochaine action).

**Données** : `data/prospects/campagne-2026-11-04-lot5.json`,
`data/campaigns/2026-11-04-lot5.json`, `data/inbox/audit-2026-11-04.json`,
`data/history/inbox_audit.json`, `data/history/domain_checks.json`, mises à jour du CRM, de la
file, du journal d'envoi et de la liste de suppression.

**Sauvegarde préalable** : `data/backups/2026-11-04-avant-lot5/` — 20 fichiers copiés avant
toute modification.

**Tableau de bord** : `http://0.0.0.0:8787`, mot de passe dans `data/.dash_password`.

## 17. État Git et prochaines améliorations

### Cumul réel depuis le lancement

| Indicateur | Valeur |
|---|---|
| Fiches CRM | **57** |
| Adresses email | **45** (33 vérifiées, 12 publiques non vérifiées) |
| Téléphones | **37** |
| File de validation | **49** = 26 en attente + 23 envoyés |
| Brouillons Gmail en attente | **15** (lot 4 : 8 · lot 5 : 7) |
| Envois réels constatés | **23**, tous antérieurs à ce lot |
| Envois pendant le lot 5 | **0** |
| Rebonds durs | **1** |
| Accusés automatiques | **1** |
| Réponses humaines | **0** |
| Oppositions | **0** |
| Liste de suppression | **1** adresse |
| Tests | **144 OK** |

### Prochaines améliorations proposées

1. **Lever les trois verrous d'envoi**, dans cet ordre : domaine d'envoi dédié → SPF + DKIM +
   DMARC → activation explicite. Tant que ce n'est pas fait, aucune mesure de performance n'a
   de sens. *Aucune action DNS ne sera engagée sans votre accord.*
2. **Valider les 15 brouillons** en attente dans Gmail, puis envoyer par très petits paliers
   (5 à 10 par jour) une fois les verrous levés, pour observer la délivrabilité réelle.
3. **Corriger l'adresse de la Pension Séverine Lesourd** : le domaine `.fr` est valide. Elle reste
   en suppression tant qu'une vérification et une décision explicites n'ont pas eu lieu.
4. **Compléter les 12 fiches « à approfondir »** (petites annonces sans entreprise identifiable) :
   retrouver la société et une adresse publiée, ou les classer sans suite.
5. **Étendre le contrôle DNS en pré-vol obligatoire** : bloquer automatiquement toute préparation
   d'email dont le domaine est NXDOMAIN (aujourd'hui le contrôle annote et alerte).
6. **Automatiser l'audit de boîte** à chaque ouverture du tableau de bord, pour ne plus jamais
   manquer un rebond ou une réponse.
7. **Préparer les réponses personnalisées** dès qu'une réponse humaine arrivera : le moteur de
   classification est prêt et testé, mais il n'a encore jamais été déclenché sur un vrai message.

---

*Rapport généré le 4 novembre 2026. Toutes les valeurs sont calculées depuis le CRM, la file de
validation, le journal d'envoi et l'audit de boîte — aucune n'est estimée.*
