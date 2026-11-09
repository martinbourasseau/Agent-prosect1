# Lot 13 — Pilote stratégique de détection de besoins commerciaux réels

**Date de session déclarée :** 2026-11-03 · **Branche :** `arena/7ed6352a-agent-prosect1`
**Nature :** pilote de détection. Aucun envoi, aucun brouillon, aucune validation.

---

## 1. Résumé en une page

Le Lot 13 change de méthode : au lieu de chercher « métier + ville », il cherche
des **besoins que l'entreprise a elle-même rendus publics** — consultations,
appels d'offres, offres d'emploi décrivant un processus, annonces de
développement.

| Indicateur | Valeur |
|---|---|
| Requêtes exécutées | **17** |
| Appels de lecture | **22** (20 réussis, 2 échecs) |
| Pages distinctes lues | **18** dont 5 pour la revue des brouillons |
| Entreprises / structures examinées | **63** |
| Intermédiaires et agrégateurs écartés comme tels | **32** |
| Catégorie **A** — besoin explicite | **1** |
| Catégorie **B** — opportunité observée | **0** |
| Catégorie **C** — hypothèse | **19** |
| Catégorie **D** — non pertinente | **43** |
| Fiches importées | **1** (Styl'Home) |
| Brouillons créés | **0** |
| Envois | **0** |
| CRM | **120 → 121** |
| Registre d'exploration | **385 → 448** |
| Tests | **801 OK** (743 + 58 nouveaux) |

**Le résultat le plus important est négatif : une seule entreprise sur 63
réunit les conditions.** Ce n'est pas un échec de recherche, c'est la mesure du
rendement réel de cette stratégie. Aucun besoin n'a été fabriqué pour remplir un
quota. Le détail des 62 rejets est archivé et constitue le livrable principal.

**Second résultat, inattendu :** l'enquête sur l'anomalie de dates a **renversé
l'hypothèse de départ**. Les dates des lots 1-11 sont authentiques, corroborées
par Gmail côté serveur. Ce sont les lots **12 et 13** qui sont antidatés. Voir §12.

---

## 2. Recherche

### 2.1 Ce qui a été abandonné, et pourquoi

Les stratégies suivantes ont été explicitement écartées comme **preuve** :

- « métier + ville » et « secteur + département » → renvoient des annuaires et
  des pages-villes d'agences, jamais un besoin ;
- les annuaires → conservés uniquement comme découverte secondaire ;
- les requêtes contenant le vocabulaire d'une solution (« automatiser devis »)
  → ne renvoient que des **vendeurs** de cette solution.

### 2.2 Les cinq axes de recherche réellement utilisés

| Axe | Requêtes | Rendement observé |
|---|---|---|
| Besoin exprimé (consultations, projets publics) | 5 | **Le seul productif** : 1 fiche |
| Marchés publics | 5 | Acheteurs nommés, mais 9 avis expirés |
| Annonces de développement | 3 | Franchises et grands groupes uniquement |
| Processus publiés (offres d'emploi) | 2 | Employeur masqué derrière l'agence d'intérim |
| Automatisation | 2 | Vendeurs, ou projets clos et anonymes |

### 2.3 Les cinq pièges rencontrés, documentés pour ne pas être répétés

1. **Requête « solution » ⇒ vendeurs.** « nous souhaitons automatiser le
   traitement des devis » ne retourne que des prestataires qui vendent cette
   automatisation. Douze entités écartées à ce seul motif.

2. **Témoignages d'agences ⇒ clients déjà équipés.** La requête « refonte de
   notre site » semble prometteuse : elle contient les mots du besoin. En
   réalité elle retourne des pages d'agences où des clients **racontent la
   refonte déjà livrée** (Moulin de Radray, FSGT 61, Baert.fr, Future4care,
   Escarbille, Instant Mouvement…). Dix entités écartées : ce sont des
   **contre-signaux**, pas des prospects.

3. **Offres d'emploi ⇒ employeur invisible.** Sur les agrégateurs, l'employeur
   affiché est l'agence d'intérim (Adecco, Randstad, SIMON, Walters People…),
   qui recrute « pour un client » anonyme. Le processus décrit est réel, mais
   il n'est rattachable à aucune entreprise identifiée.

4. **Appels d'offres ⇒ dates cachées dans les extraits.** L'Office de Tourisme
   Bisca Grands Lacs publie un besoin remarquablement détaillé (refonte,
   réservation, RGAA, OPQUAST). L'extrait de recherche ne montre aucune date.
   **La lecture de la page révèle « avant le vendredi 31 octobre 2025 »** :
   expiré depuis plus d'un an. Sans lecture, cette fiche aurait été importée
   comme une opportunité majeure.

5. **Le mot « site » matche des sites de travaux.** Sur un agrégateur de
   marchés, la recherche « création site web » retourne un avis portant sur un
   « Site de Maintenance et de Remisage » ferroviaire. Faux positif de requête.

### 2.4 Accès payant : pas de contournement

Trois projets Codeur sont **ouverts et récents** (cave à vin à Toulouse le
21/10/2026, réseau de 5 boulangeries le 14/10/2026, fournisseur de fluides
frigorigènes le 13/10/2026). Le besoin y est explicite et bien décrit. Mais
« le profil du client est réservé aux prestataires abonnés ». **Aucun abonnement
n'a été pris, aucun accès contourné.** Ces trois pistes sont classées **C** et
conservées au journal.

---

## 3. Résultats commerciaux

### 3.1 La fiche importée : Styl'Home (catégorie A)

**Identité.** Styl'Home, rénovation intérieure et peinture en bâtiment, Lille et
alentours (Bondues, Verlinghem), département 59. Entreprise familiale « de père
en fils ». Site officiel : `https://stylhome.fr/`.

**Coordonnées.** `contact@stylhome.fr`, **publiée en clair** en lien `mailto` sur
`https://stylhome.fr/contact`. MX vérifié le jour même : `mx_ok`
(`mx1.hostinger.com`, `mx2.hostinger.com`). **Aucun téléphone n'a été importé** :
aucun numéro n'est affiché sur les deux pages lues. Aucun nom de titulaire n'a
été renseigné, faute de publication nominative.

**Le besoin, exprimé par l'entreprise.** Consultation publique du
**06/09/2026**, lue intégralement :

> « Je recherche un freelance pour reprendre, corriger et finaliser mon site
> vitrine existant : stylhome.fr, pour mon entreprise artisanale Styl'Home. »

L'entreprise nomme elle-même son domaine : **le rattachement est établi par la
source**, sans qu'il ait été nécessaire de lever l'anonymat du profil client.
Elle précise ne pas vouloir repartir de zéro, et liste les défauts qui lui ont
été rapportés : manque de vraies photos, footer trop chargé sur mobile,
problèmes responsive, formulaire parfois lent, téléphone et e-mail à rendre
cliquables.

**Corroboration indépendante sur le site officiel (2026-11-03).** Deux mois
après la consultation, les défauts sont toujours là :

- la photo annoncée comme « Photo des deux gérants de l'entreprise, père et
  fils » est servie depuis **`https://placehold.co/400x400?text=Soon..`**.
  Ce n'est pas un artefact de lecture sans JavaScript : l'URL du visuel
  provisoire est écrite en dur dans la page ;
- la phrase d'accueil juxtapose **« Depuis plus de 4 ans »** et
  **« nos 34 ans d'experience »**, avec deux accents manquants ;
- la page contact n'affiche **aucun numéro de téléphone**, alors que la
  consultation demande de transformer les visiteurs « en appels ».

**Scores (moteur du dépôt, non retouché).**

| Axe | Score | Confiance |
|---|---|---|
| Création de site | 39 | haute |
| **Refonte** | **100** | **haute** |
| Agent IA / automatisation | 12 | moyenne |

Priorité commerciale **86 / haute**, moteur `v10-priority`.

L'axe création reste à 39 : le moteur part de 5 (« un site est déjà en ligne »)
et n'ajoute que la contribution du besoin exprimé. **La création n'est pas le
bon service**, et le moteur le dit. L'axe IA reste à 12, plafond du type de
preuve : **aucun processus interne n'a été lu**, seulement un parcours de contact
incomplet. Ce 12 n'est pas un besoin d'automatisation.

**Contre-signaux réellement lus par le moteur.**

- La consultation est **close après 122 offres**. Un prestataire a peut-être été
  retenu — ce n'est pas vérifié. Le moteur classe ce contre-signal en force
  faible car la source n'est pas le site officiel de l'entreprise.
- Le site est **structuré et récent** (Next.js, pages Services et Réalisations,
  galerie avant/après avec de vraies photos hébergées, formulaire de devis).
  L'entreprise pilote déjà Google Ads et Analytics.

**Pénalité appliquée : 0.** Le moteur est resté prudent, faute de marqueur
explicite reconnu. **Ce point est signalé plutôt que contourné** : le texte des
contre-signaux n'a pas été réécrit pour arracher une pénalité, et aucun
coefficient n'a été modifié. La conséquence pratique est que **la priorité 86
surestime probablement l'accessibilité commerciale** de cette fiche, la
consultation étant close. C'est une limite à connaître avant toute décision.

**Brouillon : non.** Le pilote n'autorise aucun brouillon, quel que soit le
palier. Le champ `brouillon_autorise_lot13` est à `false` avec son motif.

### 3.2 Le cas Adastra : pourquoi ce n'est pas une fiche (catégorie C)

Un cahier des charges public très complet (v1.1, publié le 18/08/2026) demande
refonte, paiement Stripe et back-office, pour une entité nommée **Adastra**,
« cabinet proposant des services juridiques et de formalités d'entreprise en
ligne ». Il décrit un **processus manuel remarquable** : le client remplit un
formulaire → un document de synthèse est généré → envoyé à Adastra → « l'équipe
Adastra **reporte** ensuite ces informations sur le document officiel définitif »
déposé au greffe. C'est exactement le type de processus qui justifierait un agent.

`adastra-legal.fr` existe et concorde : activité de formalités juridiques,
adresse parisienne, SIREN 984085118 recoupé au BODACC. **Mais** l'URL du site et
le contact sont **masqués** dans le projet (« membres Pro », contact
« Djamil •••••••••• »), et **aucun « Djamil » n'apparaît** dans l'équipe publiée
(Anaïs SEGHIR, Président). Un homonyme a d'ailleurs été écarté
(`adastra-avocats.fr`, Lyon, SIREN différent).

**Décision : catégorie C, aucune fiche.** L'activité et l'adresse concordent,
mais cela ne suffit pas à établir que ce projet est celui de cette société. Le
processus manuel, aussi documenté soit-il, **provient d'une source non rattachée** :
il ne peut pas être compté comme un besoin exprimé par cette entreprise. De plus
le site ne publie **aucune adresse e-mail**. Importer aurait supposé deux choses
non établies.

### 3.3 Répartition des 43 rejets (catégorie D)

| Motif | Nombre |
|---|---|
| Vendeur de la solution | 12 |
| Prestataire déjà en place (témoignages d'agences) | 10 |
| Signal expiré | 9 |
| Hors cible par la taille | 6 |
| Attribution déjà prononcée | 2 |
| Réseau / décision mutualisée | 2 |
| Hors territoire | 1 |
| Faux positif de statut | 1 |

Un avis d'**attribution** n'est pas une opportunité : le marché est déjà conclu.
Une agence qui vend de la refonte n'est pas un acheteur de refonte. Ces deux
distinctions, à elles seules, éliminent 24 des 63 entités.

---

## 4. CRM et registre

### 4.1 État vérifié en début et fin de lot

| Élément | Avant | Après |
|---|---|---|
| Fiches CRM | 120 | **121** |
| Registre d'exploration | 385 | **448** |
| File de validation | 77 | 77 (inchangée) |
| Messages sortis | 60 production + 8 rapprochés = 68 | inchangé |
| Suppressions | 2 | 2 |
| `enabled` / `dry_run` | `false` / `true` | **`false` / `true`** |

**Il n'existe aucune base SQLite dans ce dépôt** (`find` sur `*.db` et
`*.sqlite*` : vide). Le CRM est le fichier `data/crm/prospects.json`. Toute
mention d'une base relationnelle serait inexacte.

### 4.2 Protection des 120 fiches antérieures

- Sauvegarde complète de `data/` avant toute écriture : **275 fichiers**.
- Empreintes MD5 des 7 fichiers sensibles prises avant, vérifiées après.
- Contrôle final par comparaison à `HEAD` : **0 suppression, 0 modification**
  des 120 fiches, **1 ajout** (Styl'Home).
- Les 5 fichiers que l'importeur ne doit pas toucher (`send-log`,
  `reconciliations`, `v4-settings`, `suppression`, `validation_queue`) :
  **empreintes identiques**.

### 4.3 Idempotence

L'import a été rejoué : **0 création**, collision détectée sur le domaine, l'adresse
et le nom. Le contenu des fiches et du registre est identique à la passe
 précédente ; seuls `created_at` / `updated_at` / `examined_at`, horodatés par la
machine, avancent. Aucune fiche écrasée.

**Incident réel survenu et corrigé pendant le lot.** Une première exécution a
écrit le CRM puis échoué sur le registre (`KeyError: 'écartée'` : le journal du
Lot 13 emploie le libellé déjà accentué du registre, absent de la table de
traduction héritée du Lot 12). L'état partiel a été **restauré depuis la
sauvegarde vérifiée** — empreintes revenues à 7/7 — puis l'import relancé en une
passe complète. Le rapport archivé décrit donc la passe réelle (120 → 121), et
non une reprise sans création.

### 4.4 Registre d'exploration : 63 ajouts

Décisions après import : écartée 253, annuaire_seul 79, retenue 46,
approfondir 70. Les 19 catégories C sont enregistrées en « approfondir » :
**une hypothèse reste une piste, elle n'occupe pas le CRM**.

Rendement par type de source, tous lots confondus : **site officiel 148 examinées
/ 34 qualifiées (23 %)**, toutes les autres sources à 0 %. Ce chiffre conforte le
choix de ne plus traiter les annuaires comme des preuves.

---

## 5. Revue des 4 brouillons du Lot 11

**Cadre respecté : lecture seule.** Les 4 brouillons ont été retrouvés dans
Gmail (`list_drafts`), leurs identifiants comparés à l'archive
`data/history/lot11-brouillons-2026-11-09.json` : **conformes**. Aucun n'a été
modifié, supprimé, envoyé ni validé. La décision finale appartient à
l'utilisateur.

**Contrôles transverses, effectués avant toute recommandation.**

- `list_messages` sur les 4 domaines, brouillons exclus, **corbeille et spam
  inclus** : **0 message**, `search_scope.complete = true`. Aucun contact
  antérieur, aucune réponse, aucune opposition.
- Messages sortants (`load_outbound`) : **0 message concerné**. Journal d'envoi :
  60 entrées, **0 concernée**. Liste de suppression : 2 entrées, aucune ne
  concerne ces entreprises.
- Les 4 adresses sont `mx_ok`.
- Chaque affirmation du corps des messages a été **revérifiée sur le site le
  2026-11-03** — c'est ce contrôle qui a fait changer un verdict.

### 5.1 Miditraçage Esvia — `contactweb@miditracage.com`

Brouillon `r4042321371979229617`, 157 mots. Priorité CRM 77.

**Vérifié.** L'offre d'emploi du 29/04/2026 est **toujours en ligne**. Toutes les
citations du message sont conformes : « Saisie et envoie des devis demandés »,
« Suivi des relances factures clients », DICT/DC4/PPSPS, « Classement et
archivage ». Le processus administratif est donc bien publié par l'entreprise.

**Réserves.** (a) L'offre a **six mois** : rien ne prouve que le recrutement soit
encore ouvert, et le message s'appuie dessus comme d'un fait actuel.
(b) Localisation : le titre dit « Avignon », le corps dit
**« Saint Saturnin les Avignon »**. (c) Le type de preuve `public_need` est
**mal choisi** : une offre d'emploi n'est pas une demande d'achat de prestation
web. Ce type alimente le bonus « besoin exprimé » et **gonfle la priorité**.

**Recommandation : À approfondir.** Confirmer que le poste est encore ouvert,
corriger la commune, et requalifier le type de preuve en processus observé. Le
fond du message est honnête ; c'est son actualité qui n'est pas établie.

### 5.2 Métallerie des Alpilles — `contact@metalleriedesalpilles.fr`

Brouillon `r2207186572977723131`, 135 mots. Priorité CRM 71.

**Le défaut principal a disparu.** Le message s'ouvrait sur une adresse e-mail
affichée à l'envers sur le site. **Relecture du 2026-11-03 : l'adresse est
désormais affichée à l'endroit** (`contact@metalleriedesalpilles.fr`), et la
chaîne inversée a disparu du code de la page. **L'accroche est devenue fausse.**

**Ce qui reste, vérifié.** La mention « Created with Sketch. » subsiste. Surtout,
une **incohérence téléphonique** demeure : le lien est `tel:0974991623` alors que
le texte affiché est « 06 98 56 65 16 ». Un visiteur qui clique n'appelle pas le
numéro qu'il lit.

**Recommandation : À rejeter en l'état.** Envoyer ce message affirmerait un
défaut corrigé depuis. Un **nouveau** message pourrait être rédigé sur
l'incohérence `tel:` — mais c'est une création, pas une correction, et la
décision appartient à l'utilisateur.

### 5.3 Bureau Bois Concept — `contact@etudebbc.fr`

Brouillon `r8619847980088428557`, 142 mots. Priorité CRM **92**.

**Vérifié et conforme.** La page `https://www.etudebbc.fr/contactus` porte
toujours le titre **« Contacter Le GIE Tétraèdre »** alors que l'entreprise est
l'« Eurl Bureau Bois Concept ». Le formulaire demande Nom, Téléphone, E-mail,
Société, **Sujet, Question** : aucun champ ne qualifie l'ouvrage (type de
structure, essence, portée), donc chaque demande arrive sans les informations
nécessaires à une étude bois.

**Réserve importante sur la priorité.** L'accueil affiche
**« DISPONIBLE POUR DE NOUVEAUX PROJETS »** suivi de « Contactez-nous ». C'est un
**bandeau de disponibilité commerciale de l'entreprise pour ses propres études
bois** — pas une demande d'achat de prestation web. Il a été typé `public_need`,
ce qui déclenche le bonus « besoin exprimé » et explique une **priorité de 92
gonflée**. C'est la même classe d'erreur que celle relevée sur Beaujolais
Réception.

**Recommandation : À valider pour son contenu**, les deux défauts cités étant
réels et confirmés. **Mais** un recalcul interne de la priorité est à
recommander après requalification de la preuve. **Aucune modification n'a été
faite** : ni la fiche, ni le score, ni le brouillon.

### 5.4 ETS Frézouls — `contact@frezouls.fr`

Brouillon `r-2619464416091008266`, 140 mots. Priorité CRM 71.

**Tout est confirmé.** Sur `https://www.frezouls.fr/controle-dacces/`, les liens
« En savoir + » vers interphone et digicode sont en **`http://`**
(`http://frezouls.fr/controle-dacces/interphone/`, `.../digicode/`), et les images
comme le logo sont servis depuis `wp-content/uploads/2018/12/` et `2018/04/`.

**Formulation.** Le message dit « dans leurs chemins d'accès » : c'est exact et
prudent. Une date dans un chemin d'upload **ne prouve pas** que la page n'a pas
été mise à jour depuis ; le message ne le prétend pas.

**Recommandation : À valider.** Preuves conformes, formulation honnête, aucun
contact antérieur, adresse joignable. L'envoi reste soumis à l'utilisateur et de
toute façon bloqué par le pré-vol (§7).

### 5.5 Synthèse

| # | Entreprise | Verdict | Motif décisif |
|---|---|---|---|
| 001 | Miditraçage Esvia | **À approfondir** | Offre de 6 mois, actualité non établie ; commune à corriger |
| 002 | Métallerie des Alpilles | **À rejeter en l'état** | Accroche devenue fausse : e-mail corrigé depuis |
| 003 | Bureau Bois Concept | **À valider (contenu)** | Défauts confirmés, mais priorité 92 gonflée par un type de preuve erroné |
| 004 | ETS Frézouls | **À valider** | Toutes les preuves confirmées, formulation exacte |

**Enseignement transversal.** Une preuve peut devenir fausse entre deux lots.
Le contrôle « le défaut est-il encore là ? » doit précéder toute validation, même
pour un message rédigé quelques jours plus tôt.

---

## 6. Classification A/B/C/D

La classification est **calculée**, jamais saisie : `scripts/lot13/classification.py`
produit la catégorie à partir d'un `Signal` décrivant des faits vérifiables
(besoin exprimé, identité établie, page lue, signal encore pertinent,
rattachement établi, disqualifiants).

| Catégorie | Signification | Importable |
|---|---|---|
| **A** | Besoin explicite lu, identité établie, encore pertinent | oui |
| **B** | Processus ou défaut observé, sans demande publique | oui |
| **C** | Hypothèse : identité masquée, rattachement non établi, page non lue | **non** |
| **D** | Non pertinente, ou contre-signal disqualifiant | non |

**Deux règles structurantes.**

1. **D prime sur tout.** Un contre-signal disqualifiant ne se compense pas par une
   preuve forte. C'est ce qui empêche de requalifier en A un appel d'offres
   pourtant explicite mais expiré depuis un an.
2. **La catégorie n'est pas la priorité.** Ce sont deux questions différentes :
   « quelle est la nature de la preuve ? » et « faut-il contacter maintenant ? ».
   Styl'Home est A **et** haute priorité ; une fiche A pourrait être priorité
   moyenne si son accessibilité est douteuse. Les paliers CRM
   (haute/moyenne/basse/à approfondir) sont inchangés.

**À ne pas confondre** avec les catégories A/B/C du moteur `public_tenders.py`,
qui classent des **avis de marché**, ni avec les 4 niveaux de signal du modèle
(`exprime`, `observe`, `indirect`, `hypothetique`), qui qualifient une **preuve**.

---

## 7. Sécurité et pré-vol

### 7.1 Pré-vol : toujours bloqué, sur copie isolée

Le pré-vol a été exécuté sur une **copie temporaire** des réglages, jamais sur la
configuration de production. Ce n'est pas une précaution théorique :
**`preflight()` écrit dans son fichier de réglages** (il y persiste
`deliverability.last_checked_at` et `last_result`). L'exécuter sur
`data/campaigns/v4-settings.json` aurait modifié la production. Vérification
faite : la copie a été modifiée, **l'original est resté identique** (MD5 conforme).

**Résultat : `False`, 3 motifs.**

1. « Campagne non activée (`enabled=false`). Activation explicite requise. »
2. « DKIM non détecté pour le domaine expéditeur. »
3. « Domaine expéditeur gratuit (Gmail (gratuit)) : prospection de masse
   déconseillée/interdite par les CGU. »

**Le troisième est le blocage de fond.** Activer la campagne et publier un DKIM
ne suffiraient pas : un domaine d'envoi dédié reste nécessaire.

**Actions requises, toutes réservées à l'utilisateur :** choisir et acquérir un
domaine d'envoi dédié ; publier SPF et DKIM chez l'hébergeur DNS ; configurer une
adresse sur ce domaine ; puis, seulement, activer `enabled` et lever `dry_run`.

**Aucune de ces actions n'a été effectuée.** Aucun achat, aucun abonnement, aucun
DNS modifié, `enabled` toujours à `false`, `dry_run` toujours à `true`.

### 7.2 Protections intactes

- Opposition **Renarde / Nicolas Smets** (`celarenarde@gmail.com`) : maintenue.
- Rebond dur `contact@severine-lesourd.com` : maintenu en suppression.
- Challenge anti-bot Mailinblack / Alpha Mécanique : **non validé**.
- Les **8 entreprises contactées hors agent le 09/11** ne sont pas recontactées.
- Aucun challenge anti-bot résolu, aucun accès payant contourné.

### 7.3 Délivrabilité : ce qui est mesuré, ce qui ne l'est pas

| Compteur | Valeur | Ce qu'il prouve |
|---|---|---|
| Brouillons Gmail en attente | 6 | un brouillon existe, rien n'est parti |
| Envois au journal de l'agent | 60 | message sorti |
| Envois manuels rapprochés | 8 | constatés dans Gmail |
| Total messages sortis | 68 | sortie, **pas remise** |
| Acceptés par le fournisseur | 68 | identifiant renvoyé, **pas remise** |
| **Délivrés confirmés** | **3** | accusé ou réponse humaine |
| Délivrance non confirmée | 63 | **statut inconnu** |
| Rebonds durs | 1 | échec |
| Challenges de délivrance | 1 | non résolu |

**63 messages sur 68 ont un statut de remise inconnu.** L'absence de rebond ne
prouve pas la délivrance. Aucune statistique n'a été inventée à partir de champs
inexistants.

---

## 8. Tableau de bord

Redémarré après import pour servir le code et les données à jour. `/healthz` :
**200**. Authentification : **302**. `/api/metrics` : **200**. Page : **200**,
36 471 octets. Syntaxe JavaScript vérifiée (`node --check`) : **OK**.

**Dix invariants de comptage contrôlés, tous vrais :** partition du portefeuille
exclusive et sommant au total ; pipeline exclusif ; envoyés = production +
rapprochements ; délivrance partitionnée sans double compte ; délivrés ≤ acceptés
≤ envoyés ; CRM = portefeuille ; brouillons Gmail ≤ fiches au statut brouillon ;
registre ≥ CRM.

**Un écart apparent, expliqué.** « Fiches au statut brouillon » affiche **7**
quand « Brouillons Gmail en attente » affiche **6**. Ce n'est pas une erreur :
une fiche ancienne (Camping Mer et Camargue) porte le statut `email_préparé`
**sans identifiant de brouillon Gmail**. Les deux compteurs mesurent des choses
différentes et sont libellés différemment. Ils ne sont pas additionnés.

Ces contrôles sont devenus **10 tests permanents** qui n'assertent aucune valeur
absolue : ils resteront vrais au prochain lot.

---

## 9. Anomalie de dates des lots 1-11 — note de suivi dédiée

Archive complète : **`data/history/suivi-dates-lots-1-a-11-2026-11-03.json`**.
**Aucune correction appliquée.**

### 9.1 Le constat initial, et son renversement

Le point de départ était : « les lots 1-11 portent des dates du 04/11 au 09/11,
postérieures à la date de session déclarée (03/11) ; elles sont probablement
erronées. »

**L'enquête aboutit à la conclusion inverse.** Deux sources indépendantes
corroborent ces dates :

- **Git.** Les commits de lot portent exactement ces dates : lot 1 `fb87665` le
  04/11, lot 6 `472abfc` le 06/11, lot 9 `df49e42` le 07/11, lot 10 `713680f` le
  08/11, lot 11 `7a31abe` le 09/11.
- **Gmail, horodatage serveur.** Le champ `internal_date` est produit par Google,
  pas par le dépôt. Relevé : les envois du lot 1 (L'Occidentale, La Bruchoise,
  SAM31, Dance Center) portent `1793827617000`, soit **2026-11-04T21:26:57Z**.
  Les 8 envois hors agent portent `1794223397000`, soit **2026-11-09T11:23:17Z**.
  Des envois du 03/11 existent aussi (`1793697455000`).

**Ces journées ont réellement existé côté Google.** La chronologie des lots 1-11
est authentique.

### 9.2 L'incohérence réelle est ailleurs

L'horloge de la sandbox indique **2026-11-09T23:35Z** pendant une session déclarée
au **2026-11-03** — six jours d'écart. Les scripts des lots 12 et 13 figent
`D = "2026-11-03"` d'après la date déclarée, tandis que `created_at` est horodaté
par la machine :

| Lot | `discovered_at` | `created_at` | Écart |
|---|---|---|---|
| lot 12 (12 fiches) | 2026-11-03 | 2026-11-09 | **6 jours** |
| lot 13 (1 fiche) | 2026-11-03 | 2026-11-09 | **6 jours** |
| lot 1 (5 fiches rattachées après coup) | 2026-11-04 | 2026-11-03 | −1 jour |
| lot 7 (5 fiches) | 2026-11-07 | 2026-11-06 | −1 jour |

**Ce sont donc les lots 12 et 13 qui sont antidatés**, et non les lots 1-11.

### 9.3 Champs porteurs de dates, recensés

**Horodatés par la machine** (`datetime.now(timezone.utc)` dans `crm.py:_now()`,
`queue.py:_now()`, `sources.py`) : `created_at`, `updated_at`, `history[].at`,
`examined_at`.

**Saisis par le chercheur** : `discovered_at`, `evidence[].observed_at`,
`evidence[].verified_at`, `email_dns_checked_at`, `lot`, `campaign`,
`publication_date`.

**Observés sur une source externe** : `sent_at`, `sent_observed_at`,
`last_inbound_at`, `last_reply_at`, `draft_created_at`, `draft_updated_at`.
**Ces derniers sont déjà authentiques** : les « corriger » falsifierait
l'historique d'envoi.

### 9.4 Impact sur le scoring : nul

`scoring.FRESHNESS_DAYS = 180`. Un écart de 6 jours est très inférieur au seuil :
**aucun score, palier ou pénalité de contre-signal n'est affecté**. Le risque est
documentaire — présenter une date comme preuve de récence — et non numérique.

**Consigne appliquée pendant tout le Lot 13 :** les dates des lots 1-11 n'ont
**pas** servi de preuve de récence. La récence a été établie par les dates de
publication des **sources externes** (consultation Styl'Home du 06/09/2026,
appel d'offres Bisca expiré le 31/10/2025, offre Miditraçage du 29/04/2026).

### 9.5 Méthode de correction proposée — non appliquée

1. Obtenir de l'utilisateur la **date civile de référence** de chaque session :
   le dépôt seul ne peut pas la déterminer.
2. Construire la table lot → date réelle à partir des dates de commit **et** des
   `internal_date` Gmail, en gardant les deux comme pièces.
3. Produire un script **en lecture seule** qui liste les champs à corriger, sans
   écrire.
4. Faire valider ce rapport **champ par champ, lot par lot**.
5. Sur autorisation explicite seulement : sauvegarde horodatée, puis correction
   **additive** — conserver la valeur d'origine dans un champ distinct
   (par ex. `date_originale_declaree`) et ajouter une entrée d'historique motivant
   chaque changement.
6. **Ne jamais réécrire** `sent_at`, `last_reply_at`, `draft_created_at`.
7. Réexécuter la suite et vérifier que les fiches antérieures restent identiques
   hors champs autorisés.
8. Ajouter un invariant : `created_at` et `discovered_at` d'une même fiche ne
   doivent pas diverger de plus d'un jour — **sans figer de date de lot**.

**Décisions attendues de l'utilisateur :** confirmer les dates civiles ; dire si
la correction doit porter sur les lots 12-13 (antidatés) plutôt que sur les lots
1-11 (corroborés) ; choisir l'alignement sur l'horodatage machine ou sur la date
civile déclarée.

---

## 10. Technique

### 10.1 Fichiers ajoutés

| Fichier | Rôle |
|---|---|
| `scripts/lot13/classification.py` | moteur A/B/C/D, `Signal`, `classify()`, `importable()` |
| `scripts/lot13/journal.py` | 17 requêtes, 22 lectures, 63 entités, 32 intermédiaires |
| `scripts/lot13/fiches.py` | 1 fiche, 7 preuves, construction et scoring |
| `scripts/lot13/importer.py` | simulation par défaut, `--applique`, idempotent |
| `tests/test_lot13.py` | **58 tests** en 6 classes |
| `data/history/lot13-recherches-2026-11-03.json` | journal complet |
| `data/history/lot13-import-2026-11-03.json` | rapport d'import |
| `data/history/lot13-dns-2026-11-03.json` | vérification MX |
| `data/history/lot13-preflight-2026-11-03.json` | pré-vol sur copie isolée |
| `data/history/suivi-dates-lots-1-a-11-2026-11-03.json` | note de suivi des dates |

### 10.2 Tests

**801 tests OK** (743 existants + 58 nouveaux), 26 fichiers. Aucune régression.

Les 6 classes : classification (13), journal (12), fiches (12), archives (6),
protections (5), cohérence du tableau de bord (10).

**Aucun compteur cumulatif figé.** Les tests vérifient des règles : « une
hypothèse n'est pas importable », « un signal expiré est rejeté même explicite »,
« un site en ligne ne crée pas un besoin de création », « l'axe IA reste plafonné
sans processus publié », « délivrés ≤ acceptés ≤ envoyés ». Le seul test de
volume vérifie un **plancher** (`≥ 40` entités), pas un total.

### 10.3 Trois erreurs réelles rencontrées et corrigées

1. **Collision de modules entre lots.** `scripts/lot12/` et `scripts/lot13/`
   nomment tous deux leurs modules `journal` et `fiches`. Un `sys.path.insert`
   dans `test_lot13.py` retournait les modules **déjà chargés** du Lot 12 :
   **355 erreurs** et des tests qui passaient sur les mauvaises données.
   Corrigé par chargement explicite sous noms uniques
   (`importlib.util.spec_from_file_location`), sans polluer `sys.modules`.

2. **`KeyError: 'écartée'`** dans la table de traduction héritée du Lot 12 :
   le journal du Lot 13 emploie déjà le libellé accentué du registre. État
   partiel restauré depuis la sauvegarde, puis import relancé (§4.3).

3. **Contre-signal mal attribué.** Une phrase de la consultation Codeur
   (« Je souhaite conserver l'univers actuel du site ») était citée avec
   l'URL du **site officiel** comme source. Relecture du site et remplacement
   par une citation réellement lue sur `stylhome.fr`. **Une preuve ne doit
   jamais citer une URL où elle n'a pas été lue.**

### 10.4 Ce qui n'a pas été modifié

Coefficients et règles de scoring ; les 3 axes et leur indépendance ; le moteur
de priorité `v10-priority` ; les 120 fiches antérieures ; les journaux d'envoi et
de réconciliation ; la file de validation ; la liste de suppression ; les
réglages de campagne ; les 4 brouillons du Lot 11 ; les dates des lots 1-11.

---

## 11. Limites assumées

1. **Une seule fiche importée.** Le pilote montre que la détection par besoin
   exprimé public a un rendement faible sur les sources accessibles sans
   abonnement. C'est un résultat, pas un quota manqué.
2. **63 entités examinées** pour une cible de 40 à 60 : léger dépassement, dû aux
   séries de rejets homogènes (témoignages d'agences, vendeurs) qu'il aurait été
   arbitraire de tronquer.
3. **57 des 63 entités ne l'ont été qu'en résultat de recherche**, sans lecture
   de page. Elles sont classées C ou D en conséquence, jamais importées.
4. **Aucun test de rendu mobile réel.** Les problèmes responsive de Styl'Home
   sont **déclarés par l'entreprise**, pas mesurés. Aucun défaut mobile n'est
   présenté comme confirmé par un test.
5. **Priorité 86 probablement surestimée** pour Styl'Home : la consultation est
   close et le moteur n'a pas pénalisé ce contre-signal (§3.1). Signalé, non
   contourné.
6. **Deux échecs de lecture** sur 22 appels, causés par une URL de proxy mal
   formée par l'agent. Aucune preuve ne cite une page non lue.
7. **Le rattachement d'Adastra reste non établi.** Une concordance d'activité et
   d'adresse ne suffit pas.
8. **La date civile réelle des sessions reste inconnue.** Seul l'utilisateur peut
   la fixer.
9. **63 des 68 messages sortis ont une remise non confirmée.** La délivrabilité
   n'est pas présentée comme fonctionnelle.

---

## 12. Décisions attendues de l'utilisateur

1. **Les 4 brouillons du Lot 11** : statuer sur chaque verdict (§5.5). Aucun n'a
   été touché.
2. **Styl'Home** : décider s'il faut préparer une approche, sachant que la
   consultation est close après 122 offres (§3.1).
3. **Anomalie de dates** : confirmer les dates civiles et autoriser ou refuser la
   correction, qui devrait viser les lots 12-13 (§9).
4. **Requalification de deux types de preuves** (`public_need` sur une offre
   d'emploi pour Miditraçage, sur un bandeau de disponibilité pour Bureau Bois
   Concept) : autoriser ou refuser le recalcul des priorités (§5).
5. **Domaine d'envoi dédié** : décision d'achat, préalable à toute levée du
   pré-vol (§7.1).
6. **Pistes C relisables** : 19 hypothèses conservées au registre, dont deux
   collectivités nommées dont l'avis primaire n'a pas été lu (Arvert, Gravelines).

---

## 13. Reprise rapide

```bash
cd /home/user/Agent-prosect1
python3 -m unittest discover tests -q          # 801 OK
PYTHONPATH=. python3 scripts/lot13/importer.py # simulation, idempotent
python3 -m prospecto.server                    # port 8787, bind 0.0.0.0
```

**Constantes utiles.** `MAX_BODY_WORDS=170` (viser ≤167), `MIN_BODY_WORDS=40`,
`MAX_SUBJECT_CHARS=70`, `PORTFOLIO_URL=https://prospecto.website`,
expéditeur `Martin BOURASSEAU` / `martin.bourasseau4@gmail.com`.
Labels Gmail : 6 = lot 8, 7 = lot 9, 8 = lot 10, **9 = lot 11**.

**API.** `metrics.compute_metrics()` ; `load_outbound()` → `.from_production`,
`.total`, `.messages` ; `counter_signals.collect()` → **liste** ;
`Evidence.validate()` → **liste**, ne lève pas ; `OutboundMessage` non
sérialisable → `asdict()` ; `Sender(settings_path=<copie>)` **impérativement**.
