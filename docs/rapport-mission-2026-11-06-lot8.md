# Mission du 6 novembre 2026 — Audit Gmail, conversations commerciales, lot 8

**Auteur :** Martin BOURASSEAU — outillage Prospecto
**Branche :** `arena/7ed6352a-agent-prosect1`
**Périmètre :** audit de la boîte Gmail, traitement des conversations commerciales,
recherche et qualification d'un huitième lot de prospects.
**Aucun e-mail n'a été envoyé pendant cette mission.** Le dernier message sorti de
la boîte reste celui du 5 novembre à 14:34:37 (`1a1abeb27153577d`).

---

## Synthèse en une page

| Volet | Résultat |
|---|---|
| **A — Audit Gmail** | 0 nouvelle réponse humaine. 1 challenge de délivrance découvert (Alpha Mécanique). Écart 48 / 38 **entièrement expliqué et corrigé**. |
| **B — Lot 8** | 5 fiches qualifiées, **4 brouillons** sous `Prospection/2026-11-06-lot8`, 1 prospect conservé sans message faute d'adresse publique. |
| **C — Conversations commerciales** | **Aucune conversation commerciale à traiter.** Aucune réponse envoyée, aucun brouillon de réponse. |
| **Sécurité** | Pré-vol toujours bloqué. 2 oppositions respectées. Uzès toujours suspendue. B3R / Gallia non contactés. |
| **Code** | 5 défauts réels corrigés. **291 tests passent** (238 + 53 nouveaux). |

---

# A. Audit de la boîte Gmail

## A.1 Méthode et complétude

Gmail a été interrogé directement, **spam et corbeille inclus**
(`include_spam_trash=true`). Toutes les requêtes citées ci-dessous ont renvoyé
`search_scope.complete: true`, ce qui signifie l'absence de résultat et non une
recherche partielle.

| Requête | Portée | Résultat |
|---|---|---|
| `from:` — 20 adresses du premier groupe de contactés | complète | **0** |
| `from:` — 20 adresses du second groupe de contactés | complète | **0** |
| `-from:me from:` — 20 domaines d'entreprise contactés | complète | **0** |
| Expéditeurs automatiques (`mailer-daemon`, `postmaster`, `mail delivery`, `no-reply`) sur 3 jours | 29 messages, **tronqué** | 0 nouveau rebond |
| Balayage large sur 4 jours | 10 messages | 1 nouveauté : challenge Mailinblack |
| `"ne pas me relancer" -in:sent -in:drafts` | complète | 1 (opposition déjà traitée) |

La recherche par **domaine** en plus de l'adresse exacte est volontaire : une
réponse peut partir d'une autre boîte que celle qui a été contactée.

## A.2 Réponses humaines — état exhaustif

**Une seule réponse humaine existe à ce jour, et c'est une opposition.**

| Entreprise | Interlocuteur | Date | Message | Origine | Contenu | Intention | Intérêt | Action |
|---|---|---|---|---|---|---|---|---|
| Le Charme de l'Être Renarde | **Nicolas Smets** | 5 nov. 22:39 | `1a1ada77bcf46db9` | envoi `1a1a873377151814`, fil `1a1a8095e0a13794` | demande de ne plus être relancé | **opposition** | nul | **Traitée** : CRM `opposition` + liste de suppression. Aucune réponse commerciale. |

Classement demandé, appliqué à l'ensemble de la boîte :

| Catégorie | Nombre |
|---|---|
| Intérêt commercial | **0** |
| Demande d'information | **0** |
| Demande de devis | **0** |
| Demande de rendez-vous | **0** |
| Neutre | **0** |
| Refus | **0** |
| Opposition | **1** |

## A.3 Événements automatiques

| Type | Entreprise | Message | Lecture |
|---|---|---|---|
| Accusé automatique | BSP Auto | `1a1a8773ff8d4b90` | délivrance confirmée, **pas** un intérêt |
| Accusé automatique | B3R | `1a1abeb70f5e925c` | délivrance confirmée, **pas** un intérêt |
| Rebond dur | Séverine Lesourd | `1a1a87452d7ca7c0` | domaine inexistant, adresse en liste de suppression |
| **Challenge de délivrance** | **Alpha Mécanique** | **`1a1abeb8ee41cbb7`** | **délivrance NON acquise** |

### Le cas Alpha Mécanique, à décider

Le 5 novembre à 13:35, `alpha_mecanique@invitations.mailinblack.com` a renvoyé une
invitation dont l'objet est `Re: Alpha Mécanique : vos demandes de devis sur plans` :

> « Un clic pour délivrer votre email ! […] je demande à tout nouvel expéditeur de
> confirmer qu'il est bien humain. »

Trois conséquences, toutes enregistrées :

1. Ce n'est **ni une réponse humaine, ni un accusé de réception, ni un rebond**.
   Le message est retenu en quarantaine chez le destinataire.
2. Alpha Mécanique est donc classé **délivrance non confirmée**, et surtout pas
   « délivré ». Une nouvelle intention `challenge_delivrance` a été créée pour ne
   plus confondre les cas.
3. **Le challenge n'a pas été validé.** Le valider reviendrait à faire aboutir un
   envoi de prospection, ce qui reste interdit tant que le pré-vol est bloqué.
   La décision vous appartient.

## A.4 Réconciliation des envois manuels — l'écart 48 / 38 est clos

Le journal de l'agent comptait 38 envois là où Gmail en montrait 48. Décomposition
vérifiée message par message :

| Poste | Nombre |
|---|---|
| Journal avant correction | 38 |
| Envois réels du 3 novembre **absents du journal** | **+ 8** |
| Rebond enregistré séparément | = 46 messages sortis |
| Auto-envois de test vers votre propre adresse (2 nov.) | **+ 2** |
| **Total Gmail** | **48** |

Les 8 envois retrouvés : Akla Architectes, The Architectes, Quattro Architectes,
L'Établi du Menuisier, Superchi Architectes, Le Serrurier d'à Côté, Garage Villedieu
Automobiles, Multitech Assistance.

**Cause racine.** Ces envois précèdent l'agent et n'ont donc **aucun élément dans
la file de validation**. L'ancien `reconcile_sent` ne savait traiter que les
éléments de file : il classait ces messages « non rapprochés » et ne les
enregistrait nulle part. L'écart était structurel et se serait reproduit.

**Correction.** Un envoi constaté dans Gmail sans élément de file est désormais
journalisé et répercuté au CRM, avec une entrée d'historique
`reconciled_sent_without_queue`. Aucune donnée n'est supprimée, aucun statut plus
avancé n'est rétrogradé, et un destinataire inconnu du CRM reste signalé.

Les 2 auto-envois du 2 novembre (émetteur « Martin Borrasso », objet
« [REDIRIGE vers…] ») sont **exclus du comptage commercial** et listés comme tels
dans `data/inbox/envois-observes-2026-11-07.json`.

## A.5 Deux anomalies de file découvertes et neutralisées

- **10 éléments « en attente » visaient des prospects déjà contactés** (héritage
  des lots v3/v4 : Rénovation Premium, secteur72fr, BSP Auto, Cerf Athletic,
  Charme de l'Être). Ils sont passés en statut `obsolete` avec motif et historique.
  Sans cela, une validation de la file aurait produit des doubles contacts.
- **Les 5 brouillons du lot 7 étaient en statut `draft`, pas `pending`.** Le
  compteur de brouillons ne les voyait pas. Les deux statuts sont désormais
  reconnus comme « non envoyé ».

Un point reste ouvert : `campingmeretcamargue@orange.fr` a un e-mail préparé
(statut CRM `email_préparé`) **jamais transformé en brouillon Gmail**. Il apparaît
dans la catégorie « préparés sans brouillon ».

## A.6 Tableau de bord — les neuf catégories

| Catégorie | Valeur | Définition |
|---|---|---|
| Envoyés | **46** | messages sortis, rebonds compris |
| Délivrés confirmés | **3** | accusé ou réponse humaine rattachés à l'entreprise |
| Délivrance non confirmée | **41** | ni preuve, ni rebond, ni challenge |
| Rebonds | **1** | avis de non-remise |
| Réponses humaines | **1** | dont l'opposition |
| Réponses automatiques | **2** | accusés de réception |
| Oppositions | **1** | aussi comptée en réponse humaine |
| Brouillons | **14** | en file avec un brouillon Gmail |
| En attente | **1** | préparé sans brouillon |
| *Challenge de délivrance* | *1* | *catégorie ajoutée, remise non acquise* |
| *Suspendus* | *1* | *Uzès Location* |
| *File obsolète neutralisée* | *10* | *héritage v3/v4* |

Un contrôle d'exclusivité est affiché : **3 + 41 + 1 + 1 = 46**. Les catégories de
réponse se recouvrent volontairement et ne s'additionnent pas.

**« Envoyé » n'est jamais affiché comme « délivré ».** Sur 46 messages sortis,
3 seulement ont une preuve de remise.

---

# B. Lot 8 — cinq entreprises, quatre brouillons

## B.1 Ce qui a été cherché

Secteurs non explorés jusqu'ici : pépinière de production vendant aux professionnels,
formation CACES et habilitations, couverture-zinguerie-ramonage en artisan solo,
négoce de fournitures industrielles, location de matériel de réception.

**Environ 50 structures repérées, 16 pages vérifiées directement, 5 retenues.**
Le volume est volontairement faible : la consigne « qualité plutôt que volume
artificiel » a été appliquée, et les motifs d'exclusion sont documentés.

## B.2 Les cinq fiches

### 1. Pépinières Ripaud — La Tardière (85) → brouillon

- **Site :** ripaudpepinieres.com · **Courriel :** info@ripaudpepinieres.com · **Tél. :** 02 51 69 64 08
- **Preuve vérifiée** (`/content/17-la-pepiniere`) : « Si vous êtes un nouveau client,
  merci de nous adresser votre extrait k-bis et la fiche d'ouverture de compte
  complétée » puis « envoyer votre commande à info@… en précisant le nom des
  végétaux, le conditionnement, la taille et la quantité ». Le catalogue lié est
  `catalogue-ripaud-2026-2027-sans-prix.pdf`.
- **Opportunité :** le parcours **professionnel** est resté au courriel, alors que
  le côté particuliers est déjà outillé (paiement 3D Secure, retrait, franco).
  Solution proposée : `commande_en_ligne` — un espace pro qui collecte le K-bis et
  contrôle les lignes. **Pas de création de site.**
- **Interlocuteur :** la FAQ cite « Amandine et Damien » puis Marc-Henri Doyon
  (2022) **sans fonction explicite**. Aucun nom n'est utilisé : le message
  s'adresse à l'entreprise. Bénéfice orienté équipes de vente.
- Scores : site 5 · refonte 45 · automatisation 100.

### 2. Le Centre Formation — 4 centres (01 / 38 / 63 / 69) → brouillon

- **Site :** le-centre-formation.fr · **Courriel :** formation@lecentreformation.fr · **Tél. :** 04 78 90 60 22
- **Preuve vérifiée** (article du 19/12/2025) : « Nous vous envoyons un lien par
  e-mail, adapté à votre profil, pour créer votre dossier sur Mon Compte Formation »
  puis « Une fois votre dossier réceptionné, Le Centre Formation vous contacte
  pour fixer ensemble les dates ».
- **Opportunité :** qualification du profil, préparation du lien CPF, créneaux par
  centre. Solution `automatisation_admin`. **L'organisme a déjà un devis en ligne :
  aucun formulaire de devis n'est proposé.**
- **Interlocuteur :** l'auteur du billet est `l.cachat@…`, mais ni nom complet ni
  fonction ne sont publiés → message adressé à l'entreprise, bénéfice orienté
  gestion administrative des dossiers.
- **Deux points d'honnêteté :** le siège n'est pas publié, le département 38 est
  renseigné d'après le premier centre listé et rien n'est affirmé sur le siège ;
  le domaine du site diffère de celui des adresses, le contrôle MX porte bien sur
  `lecentreformation.fr`.
- Scores : site 5 · refonte 5 · automatisation 100.

### 3. Kévin Jenback, couvreur-zingueur-ramoneur — Saint-Germain-des-Prés (49) → brouillon

- **Site :** mrjenbackprotegevotrehabitat.com · **Courriel :** kjenback@gmail.com · **Tél. :** 06 16 12 55 42
- **Preuve vérifiée, et c'est la meilleure du lot :** sur la page devis, le bouton
  « Devis gratuit » pointe vers `tel:0663026447` — **le 06 63 02 64 47** — alors que
  l'en-tête, le pied de page et la clause de rappel affichent le 06 16 12 55 42.
- Deux autres constats : « Je réponds à votre devis sous 48h, si vous n'avez pas
  reçu ma réponse, merci de me contacter au 06 16 12 55 42 » (le suivi repose sur le
  client) ; le texte demande de choisir parmi **dix** prestations mais le champ
  « Service » n'en propose que **quatre**.
- **Interlocuteur vérifié :** « Je suis Kévin, artisan depuis 13 ans » → dirigeant
  seul. Le message l'appelle par son prénom et parle de demandes perdues et de
  temps passé à rappeler.
- Solution `formulaire_intelligent`. Aucun jugement porté sur l'origine de
  l'erreur de numéro : seule la différence est constatée.
- Scores : site 5 · refonte 75 · automatisation 90.

### 4. MSF PRO Industries — Bagnolet (93) → brouillon

- **Site :** msfpro-industries.com · **Courriel :** sales@msfpro-industries.com · pas de téléphone publié
- **Preuve vérifiée :** les deux boutons « Demander un devis » sont des liens
  `mailto:`, sans formulaire ; le parcours annoncé demande « une référence, une
  photo de plaque signalétique ou un cahier des charges » puis « nous échangeons
  sur les caractéristiques techniques, les quantités et les contraintes ».
- **Opportunité :** structurer l'entrée en relation devis. Un panier et un tunnel
  de commande existent déjà : **aucune refonte n'est proposée** (site récent,
  fichiers déposés en octobre 2026). Solution `devis_automatise`.
- **Interlocuteur :** la boîte est intitulée « CONTACT COMMERCIAL » sur le site →
  angle commercial (demandes qualifiées dès l'arrivée, sans relance manuelle).
  Aucun nom inventé.
- Scores : site 5 · refonte 45 · automatisation 90.

### 5. Beaujolais Réception — Saint-Étienne-des-Oullières (69) → **pas de brouillon**

- **Tél. :** 04 74 03 37 76 · **Dirigeant vérifié :** Kevin CANARD, gérant, cité
  comme directeur de la publication aux mentions légales.
- **Preuves vérifiées :** « Indiquez les quantités… Nous vérifions ensuite leur
  disponibilité » ; la politique de confidentialité décrit « vérifier la
  disponibilité du matériel… préparer et transmettre les devis » ; « ne propose
  pas la création de comptes clients ».
- **Pourquoi aucun message : aucune adresse courriel publique n'a été trouvée** sur
  le site refait, qui n'expose qu'un formulaire et un téléphone. Conformément à la
  règle, **aucune adresse n'a été déduite du nom de domaine**. La fiche est marquée
  `non_contactable` et bloquée à l'envoi.
- malgré un score d'automatisation de 100 : le score ne rend pas contactable.

## B.3 Structures écartées après vérification directe

| Structure | Motif |
|---|---|
| Tôlerie Générale (95) | déjà équipée : ERP + formulaire avec dépôt de plan 10 Mo |
| Pépinières Ramette (14/27) | déjà équipée : espace pro, devis et tarifs personnalisés 24 h/24 |
| CLS Chantilly (60) | formulaire de devis déjà qualifié ; plus aucune adresse publiée sur le site refait |
| Auto-école Faure (74) | `/contact` n'est qu'une carte Google intégrée, aucune coordonnée exploitable |
| Naden Industries (69) | boutique en ligne déjà annoncée, contenu générique |
| Kab Formation (94), Manuteo, CSF (45), TEMIS/BRINK'S | réseaux, lead-gen multi-domaines ou multi-centres |

**Aucune de ces structures n'a reçu de fiche CRM.**

## B.4 Personnalisation — moteur v6

Le moteur adapte désormais le message **à l'entreprise et à la personne** :

- `ROLE_FAMILIES` reconnaît cinq familles (dirigeant, commercial, administratif,
  exploitation, technique) **à partir de la fonction publiée uniquement**. Une
  fonction inconnue ne déclenche aucun angle : mieux vaut écrire à l'entreprise
  qu'inventer un rôle.
- Un bénéfice rédigé à la main pour l'entreprise prime toujours sur l'angle
  générique par rôle.
- **Aucun agent IA n'est proposé systématiquement.** Les cinq solutions du lot
  sont différentes : commande en ligne, automatisation administrative, formulaire
  intelligent, devis automatisé, réservation en ligne. `agent_ia` n'apparaît pas.
- Structure imposée : observation vérifiable → problème → solution → bénéfice
  professionnel → démonstration gratuite → appel à l'action.
- **Diversité contrôlée et mesurée :** 4 objets, 4 corps, 4 amorces de proposition,
  4 amorces de démonstration, 4 appels à l'action distincts. Zéro problème signalé
  par `check_lot_diversity`.
- Les 4 messages passent `check_email_v4` sans violation (153, 162, 166 et 141 mots
  pour un plafond de 170).
- Signature conforme sur les quatre : *Martin BOURASSEAU / Création de sites web ·
  Refonte · Agents IA · Automatisation / https://prospecto.website*.

## B.5 Deux défauts de rédaction corrigés à la relecture

1. **Une « maquette » était annoncée pour un formulaire de devis.** L'amorce de
   démonstration « Je vous prépare une première maquette gratuite » n'a de sens
   que pour un site. Elle est maintenant écartée quand la solution n'est pas un
   site, et un test balaie les six familles de solution concernées.
2. **La variante courte supprimait l'observation vérifiée** du message MSF PRO.
   La variante a été changée : chaque message du lot contient désormais son
   observation, ce qui est verrouillé par un test.

## B.6 Formulation des références — décision à confirmer

Les fiches de référence portaient `authorship_status: owner_declared` avec la note
« paternité déclarée par le propriétaire, non encore publiée juridiquement », mais
les phrases disaient « le site **que j'ai conçu** » et « la plateforme **que je
développe** ». Pour rester strictement dans ce qui est établi, les formulations du
lot 8 sont devenues :

- « À titre d'exemple, voici le site institutionnel **de mon groupe** : … »
- « Côté automatisation, voici SYNATRAP, la plateforme **de mon groupe** : … »

La propriété est annoncée, la conception n'est plus revendiquée. **Les 11
brouillons des lots 6 et 7 conservent l'ancienne formulation** : dites-moi si vous
souhaitez que je les aligne, je le ferai en place sans toucher aux labels.

## B.7 Traçabilité Gmail

- Label créé : **`Prospection/2026-11-06-lot8` → `Label_6`**
- 4 brouillons créés, label appliqué, revérifié par
  `in:drafts label:Prospection/2026-11-06-lot8` → **4 messages `DRAFT` + `Label_6`,
  recherche complète**.

| Entreprise | Destinataire | Brouillon | Message |
|---|---|---|---|
| Pépinières Ripaud | info@ripaudpepinieres.com | `r-5172376794852333002` | `1a1b16dee5899e57` |
| Le Centre Formation | formation@lecentreformation.fr | `r-3781413814320777965` | `1a1b16e00589e855` |
| Kévin Jenback | kjenback@gmail.com | `r-59861167252265867` | `1a1b16e0e43b02fa` |
| MSF PRO Industries | sales@msfpro-industries.com | `r4288620166161112368` | `1a1b16e1bd96c27c` |

---

# C. Conversations commerciales

**Il n'y en a aucune à traiter.** Les trois recherches ciblées (40 adresses et
20 domaines, spam et corbeille inclus) sont revenues vides et complètes. Personne
n'a demandé d'information, de devis ou de rendez-vous ; personne n'a manifesté
d'intérêt.

Par conséquent :

- **0 réponse envoyée** dans un fil d'origine ;
- **0 brouillon de réponse** créé ;
- la seule réponse humaine étant une opposition, elle n'appelait **aucune réponse
  commerciale** — elle a été traitée par la suppression et la mise à jour du CRM.

La règle de tri est en place pour la suite : réponse simple → envoi dans le fil
d'origine ; devis, tarif, négociation, contrat ou doute → brouillon ; opposition →
suppression et CRM, sans réponse.

---

# D. Sécurité et garde-fous

## D.1 Pré-vol — toujours bloqué

```
Campagne non activée (enabled=false). Activation explicite requise.
DKIM non détecté pour le domaine expéditeur.
Domaine expéditeur gratuit (Gmail) : prospection de masse déconseillée/interdite par les CGU.
```

**Aucun envoi, aucune modification DNS, aucun achat, aucun contournement.**

## D.2 Un trou de sécurité réel corrigé

`_is_blocked` ne bloquait pas une fiche **sans adresse courriel**. Beaujolais
Réception, scorée 100 en automatisation, aurait donc pu franchir les filtres de
sélection. Deux protections ajoutées :

- une fiche sans adresse est bloquée quel que soit son score ;
- `non_contactable`, `aucune_adresse_publique`, `non_trouve` et `inconnu` rejoignent
  les statuts bloqués.

## D.3 Interdits respectés

| Contrainte | État |
|---|---|
| Liste de suppression | 2 adresses, intacte, testée |
| Uzès Location | toujours suspendue (CRM + file) |
| B3R / Gallia | aucun contact, absence vérifiée dans le lot 8 |
| SYNATRAP / SYNATRAPE | projets non touchés |
| Adresses déduites du domaine | aucune |
| Démonstration annoncée comme déjà faite | aucune |
| Suppression de données | aucune (statuts et historiques uniquement) |

---

# E. Livrables

| Fichier | Contenu |
|---|---|
| `data/prospects/campagne-2026-11-06-lot8.json` | 5 fiches, 16 preuves datées et sourcées |
| `data/campaigns/2026-11-06-lot8.json` | 4 messages v6, brouillons, diversité mesurée |
| `data/inbox/envois-observes-2026-11-07.json` | 8 envois réconciliés + 2 auto-envois exclus |
| `data/history/inbox_audit.json` | 5 constats, dont le challenge |
| `data/backups/2026-11-07-avant-lot8/` | 34 fichiers sauvegardés avant écriture |
| `tests/test_lot8.py` | **53 tests** de régression |
| `docs/rapport-mission-2026-11-06-lot8.md` | ce rapport |

**Modules modifiés :** `personalization.py` (v6 : rôles, bénéfices, amorces
contextuelles), `messaging.py`, `models.py`, `metrics.py` (9 catégories),
`dashboard.html`, `inbox_audit.py` (challenge), `reconcile.py` (envois sans file),
`sender.py` (blocage sans adresse), `data/references.json`.

**Tests : 291 passent.** Tableau de bord relancé sur le port 8787.

---

# F. Ce qui attend votre décision

1. **Valider ou non les 15 brouillons en attente** (11 des lots 6-7, 4 du lot 8).
   Rien ne partira sans votre accord, et le pré-vol reste bloqué de toute façon.
2. **Challenge Mailinblack d'Alpha Mécanique** : le laisser expirer, ou le valider
   pour que le message du 5 novembre soit remis. Je ne l'ai pas validé.
3. **Formulation des références** : aligner ou non les 11 brouillons plus anciens
   sur « de mon groupe » plutôt que « que j'ai conçu ».
4. **Beaujolais Réception** : une adresse professionnelle est-elle obtenable par
   téléphone, ou faut-il laisser la fiche en attente ?
5. **`campingmeretcamargue@orange.fr`** : l'e-mail préparé n'a jamais de brouillon.
   Faut-il le créer ou l'abandonner ?
6. **Déblocage du pré-vol** : il exige un domaine d'envoi propre avec DKIM. Aucune
   action DNS ou achat n'a été engagé.
