# Phase 10 — rapport final (seconde passe)

**Date :** 2026-11-07 · **Branche :** `arena/7ed6352a-agent-prosect1`
**Périmètre :** finalisation de la Phase 10. **Le Lot 11 n'est pas lancé.**
**Aucun email envoyé pendant cette passe.** `enabled=false`, `dry_run=true`, pré-vol bloquant.

---

## 1. Calibration de la priorité commerciale

### Le problème
La v8 confondait deux choses différentes : la **force d'un signal** et son
**autorité**. Un besoin *déduit* d'une lacune technique plafonnait à 34, mais
l'ampleur du constat pouvait le hisser à 98 — au-dessus d'un besoin *exprimé*
par l'entreprise elle-même. La hiérarchie commerciale était inversée.

### La méthode retenue
Les trois scores v8 (`site_web`, `refonte`, `ia_automatisation`) sont
**conservés à l'identique, non fusionnés, non modifiés** : 87/87 fiches restent
en `engine_version: v8`, et la migration a touché **0 axe**.

Une **quatrième grandeur, transversale et distincte**, est ajoutée dans
`prospecto/priority.py` (`v9-priority`) :

```
valeur = base(classe_du_signal) × facteur(pertinence_offre)
       + min(42, arrondi(meilleur_axe × 0,42))
```

Six classes, par ordre d'autorité décroissante :

| Classe | Base | Ce qu'elle veut dire |
|---|---:|---|
| `exprime_verifie` | 58 | L'entreprise le dit, source officielle datée |
| `exprime_non_verifie` | 44 | L'entreprise le dit, source non recoupée |
| `observe` | 34 | Constat direct sur le site, sans demande |
| `indirect` | 18 | Signal déduit d'un indice |
| `hypothetique` | 8 | Supposition |
| `exprime_hors_offre` | 18 | Demande réelle, mais hors de nos 3 services |

Trois garde-fous répondent aux exigences posées :

- **Pas de pénalité pour un site techniquement correct.** La pertinence se
  juge sur l'adéquation à l'offre, jamais sur la qualité du site. Un besoin
  exprimé et vérifié pertinent a un **plancher de 70**, quel que soit son score
  technique.
- **Pas de maximum automatique.** Une demande exprimée hors offre
  (externalisation de force de vente, lead-gen) est plafonnée en `basse` avec
  une magnitude nulle.
- **Écart constant, pas plafond.** L'écart `exprimé vérifié − observé` vaut
  **+24 de 0 à 100** (invariant testé). Une première calibration par plafond de
  magnitude a été **rejetée** : base 40 + plafond 28 donnait un maximum de 68,
  sous le seuil de 70, rendant la classe `haute` mécaniquement inaccessible
  (11 → 2). Le détail du rejet est dans `docs/calibration-priorite-v9.md`.

### Avant / après, sur les 83 fiches existantes

| Priorité | v8 | v9 |
|---|---:|---:|
| haute | 11 | 8 |
| moyenne | 31 | 48 |
| basse | 26 | 13 |
| à approfondir | 15 | 14 |

**27 priorités modifiées / 83 · 0 axe modifié · double comptage : 0.**
Médiane des exprimés **72** contre **58** pour les observés : la hiérarchie est
rétablie. 14 remontées, 1 rétrogradation.

Faux positifs corrigés : **iTelecom** (demande d'externalisation de force de
vente, hors offre) → `basse, 5`. **Charme de l'Hêtre** → `18, basse`.
Faux négatifs corrigés : **R Premium** `basse → 70 haute`, **Secteur 72**
`basse → 74 haute`.
Quatre constats *observés* restent `haute` par leur seule ampleur, ce qui est
voulu : Atelier du Bourrelier 98→75, Kévin Jenback 94→73, O Lames Déchues 89→71,
SARL Joly Location 88→71.

**Traçabilité :** `data/history/priorite-commerciale-v8-vers-v9.json` contient
les 83 fiches scannées, les 27 changements en `before`/`after` avec le calcul
détaillé, et **une copie intégrale du CRM avant migration**. Chaque fiche porte
une entrée `history[]` datée. Simulation en lecture seule conservée dans
`data/history/simulation-calibration-v9.json`.

**Anomalie signalée, non corrigée :** *Beaujolais Réception* possède une preuve
typée `public_need`/`exprime` dont la citation est « Directeur de la publication :
Kevin CANARD, Gérant » — une ligne de mentions légales mal typée. Elle est
classée `incertaine` et ne bénéficie pas du plancher. Le typage d'origine n'a
pas été réécrit.

---

## 2. Les 5 brouillons du Lot 10

**5 créés, 0 non créé.** Label `Prospection/2026-11-07-lot10` = **`Label_8`**.
`check_email_v4` exécuté **avant chaque création** : **5/5 conformes**.
Contrôle anti-doublon préalable (`in:drafts` par destinataire) : **0, `complete:true`**.

| Entreprise | Brouillon | Mots |
|---|---|---:|
| O Lames Déchues | `r-5364782935530613267` | 137 |
| Zicplace | `r8291386275938075826` | 129 |
| Atelier du Bourrelier | `r-4868647836702402127` | 128 |
| Alain Louis | `r-3698618390914515863` | 125 |
| Étanchéité Nantaise | `r5641186055023628194` | 124 |

Chaque message cite un constat **relayé sur le site du destinataire** (marqueur
de gabarit publié, 2 000 réparations uniquement au comptoir, page contact
absente du menu, liens nommés « Button », formulaire sans qualification de
toiture). Signature exacte appliquée. **Aucune référence commerciale citée** :
la bibliothèque ne contient pas de description vérifiée de `groupebourasseau.com`
ni `synatrap.com`, donc en citer une aurait été inventer une réalisation.

**Les 5 anciens brouillons sont intacts** (Caléo, Cordes et Âme, Froger, Canfora
sur `Label_7` ; Ripaud sur `Label_6`), revérifiés dans cette passe. Aucun envoi.
File de validation : 68 → **73**.

---

## 3. Les structures restantes — **20 examinées sur 47 visées**

**Objectif non atteint, et il est déclaré comme tel** dans
`data/history/lot10-suite-exploration-2026-11-07.json` (`objective_reached:false`).
Les 13 recherches déjà faites n'ont **pas** été refaites. Aucune fiche n'a été
créée pour remplir un quota.

**2 qualifiées et importées :**

- **Ouest Affûtage** (22, Trégueux) — `saintbrieuc@ouestaffutage.com` publié en
  clair. Défaut vérifiable : le lien e-mail du pied de page utilise le schéma
  **`email:` au lieu de `mailto:`**, donc il ne fonctionne pas. Le secteur Nantes
  publie le téléphone de Saint-Brieuc ; quatre adresses sur trois domaines.
  11 salariés, service de tournées. → `refonte 89`, **haute 71**.
- **Sellerie Industrielle de l'Est** (57, Grosbliederstroff) — `sie2@wanadoo.fr`
  publié en clair. Le formulaire distingue l'objet mais ne demande aucune
  caractéristique du projet. → **moyenne 50**.

**6 écartées, 7 à approfondir, 5 non retenues.** Les rejets les plus instructifs
sont des **contre-signaux** : *L'Atelier du Marin* qualifie déjà le type de
sellerie **et** le type de bateau ; *AtelierD* a un parcours de réparation en
ligne avec paiement ; *Valcreuse* et *Totem Bau* ont déjà la réservation en
ligne. C'était exactement la prestation à proposer : pas d'opportunité.

### Résultat méthodologique important
**Les requêtes de « besoin exprimé » restent improductives même corrigées.**
La requête retravaillée sur Niort/Alençon/Chambéry a renvoyé **4 vendeurs et
0 entreprise exprimant un besoin**. Cause identifiée : les agences rédigent
leur argumentaire **en citant les mots du prospect** (« votre site ne vous
ramène aucun client »), donc les motifs côté client les capturent aussi. Les
exclusions lexicales `NEED_QUERY_EXCLUSIONS` **ne peuvent pas corriger cela**.
Ce canal doit passer par des plateformes d'appels d'offres, pas par la recherche
web générale. À l'inverse, les 3 recherches sectorielles sur sites officiels ont
donné 2 qualifiées et 6 pistes à approfondir.

---

## 4. Les 38 « fiches » non réexaminées

**Correction factuelle : ce ne sont pas des fiches CRM.** Ce sont **38 entrées
du registre d'exploration** jamais promues en prospects — **0 sur 38** présentes
au CRM, y compris par recherche de nom approché. Elles n'ont donc ni score, ni
priorité, ni coordonnées, ni statut Gmail à auditer. L'audit a porté sur ce qui
est réellement auditable (`data/history/audit-38-fiches-2026-11-07.json`) :

| Catégorie de rejet initial | Nombre |
|---|---:|
| annuaire seul, identité à établir | 14 |
| rejet à revalider sur source officielle | 13 |
| déjà outillée | 9 |
| concurrent / vendeur de la prestation | 2 |

**Décisions : 11 à clore** (hors cible structurelle : déjà outillé ou
concurrent), **27 maintenues en attente**. Doublons : **0**. Oppositions : **0**.
Promotions parallèles au CRM : **0**. Dérive de score : sans objet.
**Aucun besoin déclaré obsolète** sans relecture de source, et **aucune donnée
historique modifiée**.

---

## 5. Les 8 pistes — **2 qualifiées, pas 8 prospects**

Chaque piste a reçu **uniquement la vérification manquante**, sur source
directe, et une décision justifiée (`approfondissement-8-pistes-2026-11-07.json`).

| Piste | Décision | Preuve décisive |
|---|---|---|
| **Fermetures Leichnam** (02) | **qualifiée** | Email en clair ×2 ; **formulaire Typeform FERMÉ**, remplacé par la publicité de l'éditeur. Parcours de devis mort. → `refonte 81`, moyenne 68 |
| **Forages Berenguer** (34) | **qualifiée** | `forageberenguer@orange.fr` en clair ; formulaire sans champ de qualification ; suivi administratif manuel → moyenne 50 |
| Rhonalpe Étanchéité (01) | approfondir | **Énigme des 2 adresses résolue** : SIREN 751732702, établissement rue René Nicod **fermé le 31/01/2025**, siège actif 1 rue Grandes Roches. Email vu **seulement sur un annuaire tiers** → non retenu |
| SET AZUR (83) | annuaire seul, **identité levée** | **SIREN 983435405, La Seyne-sur-Mer**, distinct des 4 homonymes. Aucun site officiel |
| Atelier de Lutherie Cassat & Wellmer (78) | écartée | Accueil **et** `/contact` lus : **aucune adresse publiée**. Celle vue sur Facebook n'est pas confirmée |
| Abc Forage 34 (34) | écartée — **déjà outillée** | Devis déjà qualifié (objet, adresse, « accès difficile ? OUI/NON »). Aucune adresse publiée |
| Régis de Izarra (80) | écartée | 2 pages lues, 2 téléphones, **aucun email** |
| Bossard Philippe (94) | approfondir | Accueil lu sans email ; page Contact **non lue** → vérification déclarée **incomplète**, pas de conclusion |

Principe appliqué sans exception : **une adresse ne se devine pas**, et un
extrait de recherche, un JSON-LD seul, une page Facebook ou un annuaire tiers
**ne valent pas publication vérifiée**.

---

## 6. Gmail

Nouvel audit ciblé (`data/history/audit-gmail-seconde-passe-2026-11-07.json`).

**Piège rencontré et documenté :** une première requête large sur
« ne pas me relancer » a renvoyé **nos propres messages** — chaque email de
prospection contient cette formule d'opposition. Toute requête d'opposition
doit exclure l'expéditeur, sinon elle s'auto-déclenche.

| Contrôle | Portée | Résultat |
|---|---|---|
| Rebonds | **exhaustive** (`complete:true`) | **1**, le nxdomain connu. Aucun nouveau |
| Oppositions | **exhaustive** (`complete:true`) | **1**, Renarde / Nicolas Smets. Aucune nouvelle |
| Brouillons | échantillon 30 | **10** prospection, les 5 anciens intacts |
| Boîte de réception | échantillon 40 | Aucune réponse de prospect, aucune demande commerciale |

**0 nouvelle réponse humaine, 0 automatique, 0 rebond, 0 opposition, 0 challenge,
0 demande de devis.** Aucun brouillon de réponse n'était donc nécessaire.

**Protections maintenues :** opposition Renarde définitive (statut + liste de
suppression, 2 entrées) ; **challenge Mailinblack NON validé** ; aucun envoi.
Réconciliation sans écrasement : les 4 entrées et les 60 envois journalisés sont
inchangés, **MD5 4/4 vérifiés après la suite de tests**.

*Limite honnête :* les deux requêtes décisives sont exhaustives ; les deux
autres sont paginées et établissent l'absence de nouveauté sur l'échantillon
récent, pas sur toute la boîte.

---

## 7. Tests et intégrité

**508 tests, tous verts** (`python3 -m unittest discover tests -q`), contre 473
au début de la passe. Ajouts : 25 tests de priorité v9 + 10 tests de livraison
de la seconde passe.

Contrôles 1 à 10 :

| # | Contrôle | Résultat |
|---|---|---|
| 1 | Trois scores indépendants, non fusionnés | **87/87 en v8, 0 axe modifié** |
| 2 | Priorité transversale distincte | **87/87 en `v9-priority`** |
| 3 | Fiches intactes, aucune suppression | 83 → **87** (+4), 0 supprimée |
| 4 | Brouillons Lot 10 | **5/5** `["DRAFT","Label_8"]` |
| 5 | Anciens brouillons | **5/5 intacts** |
| 6 | Doublons / oppositions | **0 doublon**, 1 opposition + liste de 2 |
| 7 | Gmail / CRM réconciliés | sans écrasement |
| 8 | Journaux non pollués | **MD5 4/4 OK après les tests** |
| 9 | Dashboard | **HTTP 302 + API 87 fiches / 16 qualifiables / v9** |
| 10 | Pré-vol bloquant | **`(False, 3)`** |

**257 fichiers JSON, 0 invalide.** Aucune base SQLite dans ce dépôt : le CRM est
`data/crm/prospects.json`.

Deux invariants de test ont été **corrigés car trop forts**, non assouplis pour
masquer un défaut : une fiche créée *après* la migration v9 n'a pas d'entrée de
migration (elle est évaluée directement en v9) — elle doit porter une trace de
création datée, ce qui a été ajouté aux 4 nouvelles fiches.

---

## 8. Git et rapports

Chaîne de la seconde passe, sur `arena/7ed6352a-agent-prosect1` :
`52c48a4` (fin 1re passe) → `c09d425` (calibration v9) → `713680f` (5 brouillons)
→ commits de cette passe (pistes F, lot 10 suite, audit E, audit Gmail, tests,
rapport). **Aucune fusion automatique.** Aucun secret commité.

Rapports et archives produits :
`docs/calibration-priorite-v9.md`, `docs/rapport-final-phase10-2026-11-07.md`,
`data/history/priorite-commerciale-v8-vers-v9.json`,
`simulation-calibration-v9.json`, `approfondissement-8-pistes-2026-11-07.json`,
`lot10-suite-exploration-2026-11-07.json`, `audit-38-fiches-2026-11-07.json`,
`audit-gmail-seconde-passe-2026-11-07.json`,
`data/messages/brouillons-2026-11-07-lot10.json`.

---

## 9. Total de prospects qualifiés au CRM

**16 dossiers qualifiables sur 87 fiches (18 %)** — c'est-à-dire réunissant
identité, activité, localisation, adresse publiée vérifiée et routable, preuve
concrète datée, et aucun blocage de statut.

- **87 fiches**, 100 % scores v8 + priorité v9 · **45 départements**
- Priorités : **haute 9 · moyenne 51 · basse 13 · à approfondir 14**
- **55 adresses vérifiées**, 0 décodée-non-confirmée
- Statuts : contacté 53, nouveau 17, brouillon en attente 9, auto_reply 2,
  email_préparé 1, brouillon_créé 1, opposition 1, rebond 1, suspendu 1,
  à approfondir 1
- Registre d'exploration : **100 structures** (écartée 49, annuaire seul 26,
  retenue 13, approfondir 12) · **58 départements**, **13/13 régions**
- Pipeline : **60 envois**, **3 délivrances confirmées**, 56 non confirmées,
  1 rebond dur, 1 réponse humaine, 1 opposition · **10 brouillons en attente**

**Les 4 nouvelles qualifiées de cette passe** (Fermetures Leichnam, Forages
Berenguer, Ouest Affûtage, Sellerie Industrielle de l'Est) sont au statut
`nouveau`, **sans brouillon et sans envoi**.

Principal bloqueur, inchangé : **53 fiches déjà contactées**, auxquelles
s'ajoutent 16 localisations absentes et 15 adresses non recoupées.

---

## 10. Recommandation pour la suite

**Ne pas lancer le Lot 11 en l'état.** Trois raisons, par ordre d'importance :

1. **Le canal d'envoi est bloqué et non négociable par l'agent.** Le pré-vol
   échoue sur 3 points. Tant que SPF/DKIM/DMARC ne sont pas en place, tout envoi
   dégrade la réputation du domaine. **Toute modification DNS exige votre
   validation.** C'est le seul déblocage qui change réellement la donne : les
   10 brouillons en attente sont prêts et ne demandent qu'un canal.
2. **La délivrance n'est pas mesurée.** 3 confirms sur 60 envois : 56 envois
   sans preuve de remise. Avant d'envoyer davantage, il faut instrumenter la
   délivrance, sinon le rendement restera inconnu.
3. **Le vivier se tarit sur la méthode actuelle.** 100 structures examinées
   pour 13 retenues, et le rendement des annuaires est de **0,029** contre
   **0,352** pour les sites officiels. Les requêtes de besoin exprimé sont
   structurellement captées par les agences.

Séquence conseillée :

- **Étape 1 — votre décision :** valider les 10 brouillons en attente et
  arbitrer la configuration DNS. Rien n'est envoyé sans vous.
- **Étape 2 — sans coût :** approfondir les **12 pistes ouvertes** du registre
  et les 27 entrées maintenues de l'audit E. Ce sont des vérifications ciblées
  à rendement élevé, pas de la recherche large. Deux sont déjà très mûres :
  *La Châtaigneraie de Bel Air* (réservation par téléphone, avec un avis Google
  publié sur son propre site disant qu'elle ne répond pas au téléphone) et
  *ERM 27* (horaires contradictoires) — il ne manque que la page contact.
- **Étape 3 — changement de méthode :** pour trouver des besoins *exprimés*,
  passer par les plateformes d'appels d'offres et les marchés publics, seul
  canal où une entreprise publie une demande plutôt qu'un vendeur son
  argumentaire.
- **Étape 4 — nettoyage :** clore les 11 entrées hors cible de l'audit E, et
  corriger le typage de la preuve de *Beaujolais Réception*.

**Ce qui reste inachevé, explicitement :** 27 des 47 structures de la section D,
et 2 pistes sur 8 encore ouvertes (Rhonalpe, Bossard) plus SET AZUR sans site
officiel. L'avancement exact est consigné dans `docs/reprise-phase10.md` pour
être repris sans rien refaire.
