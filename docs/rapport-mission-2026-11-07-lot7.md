# Rapport de mission — 7 novembre 2026
## Lot 7 (5 nouveaux prospects) + révision des 6 brouillons du lot 6

**Aucun email envoyé.** Les 11 messages sont des brouillons Gmail en attente de votre validation.
Pré-vol toujours **BLOQUÉ** : campagne non activée, DKIM absent, domaine expéditeur gratuit.

---

## 1. Bilan de la révision des 6 brouillons du lot 6

Chaque brouillon a été contrôlé sur six axes : entreprise et activité, preuve de l'accroche,
pertinence du problème, adéquation de la solution, coordonnées et signature, caractère non générique.

| Brouillon | Entreprise | Défaut constaté en v4 | Correction apportée |
|---|---|---|---|
| -001 | Celtuce Traiteur | Accroche juste, mais solution survolée | Ajout de l'observation « plateaux-repas déjà en boutique en ligne, seuls les buffets restent manuels » ; proposition centrée sur les 5 informations réellement demandées |
| -002 | Mamie Cuisine | Problème implicite | Observation explicite : le client ne découvre le délai de 72 h et le forfait de zone qu'après avoir écrit |
| -003 | Baptiste Break | Conséquence non formulée | Observation : demandes reçues pour des semaines déjà pleines + suivi d'acompte manuel |
| -004 | SARL Joly Location | **Accroche trop faible** (site « à moderniser ») et **deux prestations** mélangées | Nouvelle accroche vérifiée : la fiche Pages Jaunes pointe vers `jolylocation-echafaudage.fr` qui affiche « This site is not published ». Une seule proposition : la redirection de l'ancien domaine |
| -005 | SARL Uzès Location | Adresse e-mail non confirmée | Corps réécrit, **fiche suspendue** (voir point 11) |
| -006 | Techniques Piscine | **Trame de service générique** héritée de la v3 (« Je mets en place des automatisations… ») | Trame supprimée, remplacée par une proposition précise : trier construction / rénovation / entretien et situer le chantier avant le premier appel |

**Historique conservé.** Les 6 brouillons ont été modifiés **en place** (`update_draft`) :
mêmes `draft_id`, mêmes `thread_id`, aucun brouillon supprimé ni recréé.
Les 6 versions v4 sont archivées dans `data/history/message-versions-lot6.json`.

Vérification Gmail après réécriture : **6 brouillons, label `Prospection/2026-11-06-lot6` réappliqué, 0 envoi.**
Le label ayant été détaché par la mise à jour, il a été remis sur les 6 messages.

---

## 2. Nombre d'entreprises examinées

- **≈ 44 structures repérées** par recherche, France entière, secteurs et départements élargis
  (formation, transport/logistique, distribution B2B, bien-être, immobilier, imprimerie, tourisme).
- **9 vérifiées par lecture directe de leur site** (pas seulement par extrait de moteur).
- **5 retenues.**

Écartées après vérification, avec la raison :

| Structure | Raison de l'exclusion |
|---|---|
| Imprimerie Graphitti (31) | Formulaire actuel **déjà qualifié** (prestation, objet, société, ville, échéance). La FAQ « BAT » vue en extrait n'est plus publiée |
| KDC Distribution (83) | Site en maintenance, aucune observation possible |
| Agence Normande Immobilière (76) | Estimation en ligne en 3 étapes avec dépôt de photos : déjà équipée |
| C&R Formation (75) | Redondance secteur + département avec France-PNL |
| Camping Le Lac (31) | Municipal |
| Toltek (63), 123Imprim, Veoprint, Imprimerie Market | Validation ou commande déjà automatisée |
| Transports Florczak (32), Guy Hoquet Dol, Propriétés de Normandie | Réseau, franchise ou groupe |
| Bpifrance, CNED, CCI | Organismes publics |

Deux pistes explorées se sont révélées **sans rendement** : traduction assermentée et diagnostics
immobiliers (annuaires générateurs de leads ou sites déjà outillés).

---

## 3. Nombre de nouveaux prospects

**5**, tous créés dans le CRM : `data/prospects/campagne-2026-11-07-lot7.json`.
CRM : **64 → 69 fiches**.

Chaque fiche porte : activité et localisation vérifiées, 2 à 3 preuves citées avec URL et date
d'observation (2026-11-07), coordonnées professionnelles publiques, niveau de vérification,
observation, famille de solution, message personnalisé, statut du brouillon et campagne.

---

## 4. Doublons évités

- Contrôle anti-doublon sur les **64 fiches existantes** : **0 collision** (entreprise, domaine, e-mail).
- Contrôle de la liste de suppression (2 entrées) : **aucun contact interdit**.
- **1 écartée pour redondance** : C&R Formation, même secteur et même département que France-PNL,
  afin de ne pas envoyer deux approches voisines.
- Import CRM : **5 créations, 0 fusion**.

---

## 5. Prospects qualifiés par priorité

**4 priorité haute, 1 priorité moyenne.**

| Priorité | Entreprise | Dép. | Ville | Secteur |
|---|---|---|---|---|
| Haute | France-Hypnose-Formation / France-PNL | 75 | Paris | Formation professionnelle |
| Haute | Atoutransport | 89 | Perceneige | Transport, groupage de déménagement |
| Haute | Bonbon Foliz | 78 | Le Perray-en-Yvelines | Distribution confiserie B2B |
| Haute | Bulles & Détente | 25 | Serre-les-Sapins | Spa / bien-être |
| Moyenne | L'Ô de Claise | 36 | Saint-Michel-en-Brenne | Hébergement et spa |

---

## 6. Emails vérifiés et non vérifiés

**Lot 7 : 5 adresses sur 5 vérifiées**, toutes relevées telles quelles sur une page publique.
**Aucune adresse construite à partir d'un nom de domaine.**

Contrôle DNS du domaine **de l'adresse** (et non celui du site) : MX publiés pour les 5.
Téléphone professionnel relevé et vérifié pour les 5.

État global du CRM après contrôle : **57 adresses** — 55 routables, 2 non délivrables ;
niveau de preuve : **43 vérifiées**, **14 publiques non confirmées**.

Cas particuliers conservés sans envoi possible :
- **SARL Uzès Location** — adresse publique non confirmée → suspendue, brouillon conservé.
- **SAS Maire (55)** — domaine de l'adresse en NXDOMAIN → 7ᵉ fiche du lot 6, **aucun brouillon**.

---

## 7. Les trois scores de chaque nouveau prospect

Scores indépendants : création de site / refonte / agent IA-automatisation.

| Entreprise | Création | Refonte | Agent IA | Axe dominant |
|---|---|---|---|---|
| France-Hypnose-Formation / France-PNL | 5 | 45 | **100** | Automatisation |
| Atoutransport | 5 | 45 | **90** | Automatisation |
| Bonbon Foliz | 5 | 5 | **100** | Automatisation |
| L'Ô de Claise | 5 | **75** | 30 | Refonte / parcours |
| Bulles & Détente | 5 | 35 | **70** | Automatisation |

Le score « création » est volontairement bas partout : les cinq ont déjà un site en ligne.
Chaque score est justifié dans le CRM par les preuves citées et leur URL.

---

## 8. Nombre de nouveaux brouillons

**5 brouillons créés**, label `Prospection/2026-11-07-lot7` (`Label_5`).
**Total en attente : 11 brouillons** (6 lot 6 + 5 lot 7), **0 envoi**.

| Brouillon | Destinataire | Objet | Mots |
|---|---|---|---|
| -001 | contact@france-pnl.com | Inscriptions France-PNL : quatre canaux, une seule validation ? | 149 |
| -002 | demenagement@atoutransport.com | Atoutransport : vos dates de groupage consultables en ligne ? | 118 |
| -003 | contact@bonbon-foliz.com | Bonbon Foliz : vos ouvertures de compte pro par e-mail ? | 164 |
| -004 | reservation@odeclaise.fr | Ô de Claise : vos cartes cadeau réservables en ligne ? | 165 |
| -005 | contact@bulles-et-detente.fr | Bulles & Détente : le suivi de vos bons cadeaux automatisé ? | 161 |

**Observation réelle et solution retenue pour chacun :**

1. **France-PNL** — la page d'inscription ouvre quatre canaux et précise que « seule l'inscription
   avec paiement carte bleue entraine une prise en compte immédiate ». Les autres demandes attendent
   une validation du secrétariat, pour des groupes de 15 maximum.
   → *Parcours d'inscription unique* qui vérifie les places et prépare la convention. Pas d'agent IA.
2. **Atoutransport** — « les dates de groupage sont connues plusieurs mois à l'avance, prenez contact
   afin de les connaître ». → *Calendrier de navettes consultable*, relié au devis.
3. **Bonbon Foliz** — l'espace revendeur demande d'envoyer le Kbis et les produits souhaités par e-mail
   « afin que nous puissions vous établir un bon de commande ».
   → *Formulaire d'ouverture de compte pro* avec dépôt de Kbis et bon de commande généré.
4. **L'Ô de Claise** — « si vous possédez une carte cadeau merci d'appeler obligatoirement » alors que
   la réservation en ligne existe déjà. → *Reconnaissance des bons cadeaux dans le module existant*.
5. **Bulles & Détente** — bons valables 6 mois, prolongation 10 €/mois, annulation 48 h à l'avance.
   La vente est automatisée, pas le suivi. → *Registre de bons cadeaux* avec échéances et prolongations.

Les deux entreprises de bien-être reçoivent des approches **différentes** : reconnaissance d'un bon
à la réservation pour l'une, registre de suivi des échéances pour l'autre.

Diversité mesurée : **5 amorces de proposition, 5 amorces de démonstration, 5 appels à l'action distincts**.
Sur le lot 6 : **6 / 5 / 6**. Aucun copier-coller entre entreprises.

---

## 9. Améliorations apportées au moteur

Nouvelle structure en cinq temps : **accroche vérifiable → observation → proposition → démonstration → appel à l'action**.

- **8 familles de solution** (`formulaire_intelligent`, `commande_en_ligne`, `reservation_en_ligne`,
  `devis_automatise`, `automatisation_admin`, `refonte_site`, `parcours_client`, `agent_ia`).
  **L'agent IA n'est proposé que lorsqu'il est le bon choix** — aucun des 5 messages du lot 7 n'en propose.
- **Segment observation** obligatoire : la conséquence concrète de ce qui a été constaté, sans critique gratuite.
- **Rotation par lot** (`LotRotation`) : amorces de proposition (6), de démonstration (5) et appels
  à l'action (7) attribués sans répétition tant que le lot ne dépasse pas la taille du jeu.
  Reproductible quel que soit l'ordre d'entrée. Une simple rotation par hachage produisait des collisions.
- **`check_lot_diversity`** : contrôle automatique de la diversité d'un lot entier.
- **9 tournures génériques interdites** + détection des trames de service héritées de la v3.
- **Cohérence de la référence** : la phrase « Côté agents IA » ne s'affiche plus devant un simple
  formulaire ; elle devient « Côté automatisation ». Une référence n'est citée que si elle est pertinente.
- **Bug corrigé** : `check_email_v4` était sensible à la casse et déclarait absente une phrase
  commençant par « Sans engagement, … ». Les contrôles se font désormais sur le texte replié en minuscules.
- **Plafond porté à 170 mots** (≈ 1 150 caractères), justifié par l'ajout du segment observation ;
  signature et clause de désinscription représentent ≈ 37 mots incompressibles.
- **Garde-fou d'envoi** : `select_candidates` exclut désormais explicitement les statuts bloqués
  (suspendu, opposition, désinscrit, rebond, plainte), y compris via la file de validation.
  Auparavant une fiche suspendue bien scorée aurait pu être sélectionnée.
- **Comptage des réponses humaines corrigé** : une opposition est écrite par une personne.
  Elle était comptée 0 en « réponses humaines » et 1 en « oppositions ».
- **Tableau de bord** : ajout des cartes « Brouillons en attente », « Suspendus (non envoyables) » et
  « Oppositions ». Les six catégories demandées sont distinguées : envoyés (38), brouillons (16 en file),
  réponses humaines (1), accusés automatiques (2), rebonds durs (1), oppositions (1).

---

## 10. Tests et résultats

**238 tests, tous réussis** (`python3 -m unittest discover tests -q`).

Nouveaux tests du lot 7 : familles de solution, segment observation, amorces, `LotRotation`,
diversité de lot, garde-fous anti-générique, régression de casse, budget de mots, identité et signature,
**sécurité de la suspension** (7 tests), **comptage des réponses humaines** (5 tests),
cohérence de la référence (4 tests).

Contrôles sur les données réelles :
- `check_email_v4` sur les **11 messages : 0 problème**.
- `check_lot_diversity` : **conforme sur les deux lots**.
- Signature `Martin BOURASSEAU` + `https://prospecto.website` : **présente sur les 11**.
- Gmail : **11 brouillons** portant le bon label, **dernier envoi = 5 novembre** (hors agent).
- Pré-vol : **BLOQUÉ** — campagne non activée, DKIM absent, domaine gratuit.
- Uzès Location : **absente des candidats à l'envoi**, les 2 adresses en opposition exclues.
- Tableau de bord : redémarré, authentification testée, nouveaux compteurs vérifiés via l'API.

---

## 11. Problèmes rencontrés

1. **Un extrait de moteur n'est pas une preuve.** Trois accroches envisagées reposaient sur du texte
   absent du HTML réellement servi (FAQ « BAT » de Graphitti, « samedis par téléphone » de Bulles & Détente,
   « validation manuelle » de KDC). Graphitti et KDC ont été écartées ; l'accroche de Bulles & Détente
   a été reconstruite sur les conditions réellement publiées.
2. **Rendement faible de deux secteurs** : traduction assermentée et diagnostics immobiliers ne donnent
   que des annuaires générateurs de leads ou des sites déjà outillés.
3. **Budget de mots dépassé** au premier essai : les 5 messages faisaient 161 à 176 mots.
   Corrigé par le raccourcissement des amorces et de deux accroches, puis plafond fixé à 170.
4. **Bug de casse** dans le contrôle qualité, découvert à cette occasion (voir point 9).
5. **Collisions d'amorces** avec une rotation par hachage : 3 messages sur 5 commençaient leur
   proposition par « Je vous suggère ». Résolu par `LotRotation`.
6. **Label Gmail détaché par `update_draft`** : la mise à jour d'un brouillon ne conserve pas les
   labels personnalisés. Le label a été réappliqué aux 6 messages et les identifiants resynchronisés.
7. **Caractères non français** glissés dans des chaînes générées : reprise et contrôle systématique
   des fichiers écrits (aucun caractère parasite restant).
8. **Faille de sélection** : un statut « suspendu » n'était pas filtré par le moteur d'envoi.
   Corrigé et couvert par des tests.
9. **Sous-comptage des réponses humaines** : l'opposition de la Renarde n'apparaissait pas comme
   réponse humaine. Corrigé.

### Suspensions et interdictions actives

- **SARL Uzès Location** — `uzeslocation.30700@gmail.com` non confirmé.
  Fiche marquée `suspendu`, brouillon conservé mais **non envoyable**, exclusion testée.
- **SAS Maire (55)** — domaine de l'adresse en NXDOMAIN : aucun brouillon.
- **B3R / Gallia** — aucun contact vers `b3r@gallia28.fr` sans nouvelle qualification et autorisation explicite.
- **Liste de suppression (2)** : `celarenarde@gmail.com`, `contact@severine-lesourd.com`.
- **SYNATRAP / SYNATRAPE** : projets non touchés.
- **Aucun envoi, aucune modification DNS, aucun achat, aucune suppression de données.**

---

## Prochaine étape, de votre côté

Les 11 brouillons sont relisables dans Gmail sous `Prospection/2026-11-06-lot6` et
`Prospection/2026-11-07-lot7`, ou depuis le tableau de bord.
Aucun ne partira sans votre validation explicite — et l'envoi restera de toute façon bloqué
tant que le DKIM n'est pas configuré sur un domaine professionnel.
