# Calibration commerciale v9 — priorité transversale

**Date : 2026-11-07** · Archive : `data/history/priorite-commerciale-v8-vers-v9.json`
· Simulation : `data/history/simulation-calibration-v9.json`

## Le problème

En v8, la priorité commerciale était `max(score des trois axes)`. Les trois axes
mesurent des choses différentes — absence de site, défauts d'un site existant,
charge manuelle — et **leurs barèmes ne sont pas commensurables**. Prendre leur
maximum comparait des grandeurs sans unité commune.

Conséquence mesurée : un besoin **exprimé par l'entreprise** plafonnait à **34**
sur l'axe qu'il désignait, tandis qu'une lacune **déduite par l'agent** atteignait
**98** en refonte. Une entreprise qui écrit « nous cherchons à automatiser nos
devis » passait derrière une entreprise dont on avait seulement inféré un site
vieillissant.

## Ce qui n'a pas été fait

**Les trois scores restent indépendants et strictement inchangés.** Aucune
fusion, aucune normalisation commune, aucun recalcul. Le contrôle est fait fiche
par fiche à la migration : `axes_modified = 0`.

La priorité v8 est conservée en place dans `scores.priority`, et le CRM complet
d'avant migration est archivé. Chaque fiche porte une entrée `history`
`calibration_priorite_commerciale_v9` avec l'avant et l'après.

## La méthode

Une quatrième lecture, transversale, qui répond à une autre question que les
axes : **« à quel point vaut-il la peine d'engager une conversation ? »**

Elle combine quatre critères explicables.

### 1. Classe de signal — critère dominant

| Classe | Base | Ce qui la caractérise |
|---|---|---|
| Besoin **exprimé et vérifié** | **58** | L'entreprise le dit elle-même, sur son propre site, extrait relu |
| Besoin **exprimé non vérifié** | 44 | Annonce rapportée par un tiers ou fiabilité moyenne |
| Problème **directement observé** | 34 | Constaté sur la source |
| Signal **indirect** | 18 | Indice à combiner |
| Opportunité **hypothétique** | 8 | Supposition du chercheur |
| Besoin exprimé **hors offre** | 18 | Réel, mais nous ne le servons pas |

### 2. Pertinence par rapport à l'offre

Une demande exprimée n'est pas automatiquement une priorité. Le module compare
la formulation au périmètre réel des prestations (création, refonte, IA et
automatisation) et détecte les demandes hors offre : logo, charte graphique,
application mobile, Google Ads, community management, maintenance informatique,
**externalisation de la force de vente**.

| Pertinence | Facteur | Effet |
|---|---|---|
| Proposé | ×1,00 | normal |
| Incertaine | ×0,65 | prudent |
| Hors offre | ×0,30 | magnitude annulée, priorité plafonnée à « basse » |

Une demande **mixte** (« un logo et un site ») reste dans l'offre : la partie qui
nous concerne est réelle, et les termes hors offre sont signalés.

### 3. Vérification — et un piège du modèle

`Evidence.__post_init__` remplit `verified_at` avec `observed_at` dès qu'il est
vide. **Un test « `verified_at` non vide » est donc toujours vrai** et ne
distingue rien. La première version de ce module tombait dans ce piège.

La vérification repose désormais sur l'**autorité de la source** :
`source_type == "site_officiel"`, `reliability == "haute"`, `observed == True`,
avec URL et date. Une annonce vue sur une page professionnelle tierce reste
« exprimé non vérifié ».

### 4. Magnitude bornée

`magnitude = min(42, arrondi(meilleur axe × 0,42))`. Elle apporte de la
différenciation **sans pouvoir écraser la classe de signal**.

## Deux calibrations, dont une rejetée par la simulation

**Première tentative — rejetée.** Base « observé » 40 et plafond de magnitude 28
donnaient un maximum de **68** à tout problème seulement observé. Aucun ne
pouvait donc atteindre « haute » (seuil 70), et la catégorie s'effondrait de
**11 fiches à 2**. Le plafond ne traduisait pas un jugement commercial : il
interdisait mécaniquement une classe entière.

**Calibration retenue.** L'avantage de l'exprimé est un **écart de base à
magnitude égale** (+24 sur l'observé), pas un plafond imposé à l'observé. Un
problème massif directement constaté peut donc rester « haute ».

**Invariant vérifié par test :** pour toute valeur d'axe `v`,
`valeur(exprimé vérifié, v) − valeur(observé, v) = 24`, constant de 0 à 100.

### Plancher explicite

Un besoin **exprimé, vérifié et pertinent** est remonté à 70 s'il est en dessous.
C'est le cas que la v8 pénalisait : un site techniquement correct ne doit pas
enterrer une demande explicite. Le plancher n'est **pas** accordé à toute demande
exprimée — il exige la vérification **et** l'adéquation à l'offre.

### Contactabilité

Question séparée, comme en v8. Sans adresse joignable, la priorité est plafonnée
à « à approfondir » mais **la valeur commerciale est conservée** : une belle
opportunité sans adresse est une recherche de coordonnées, pas un non-intérêt.

## Résultats sur les 83 fiches

| Priorité | v8 | v9 |
|---|---|---|
| Haute | 11 | **8** |
| Moyenne | 31 | **48** |
| Basse | 26 | **13** |
| À approfondir | 15 | **14** |

**27 priorités modifiées, 56 inchangées, 0 score d'axe modifié.**

| Classe retenue | Fiches |
|---|---|
| Problème observé | 53 |
| Besoin exprimé et vérifié | 17 |
| Hypothétique | 8 |
| Indirect | 4 |
| Exprimé hors offre | 1 |

**Le test décisif** — médiane des exprimés **72**, médiane des observés **58**.
Plancher d'un exprimé vérifié pertinent : **70**. Quatre problèmes observés
restent « haute » par leur ampleur : Atelier du Bourrelier (axe 98 → 75),
Kévin Jenback (94 → 73), SARL Joly Location (88 → 71), O Lames Déchues (89 → 71).

### Faux positifs et faux négatifs corrigés

- **R Premium** — besoin exprimé et vérifié, axes (5, 25, 0). En v8 : **basse**.
  Le site est correct, donc l'entreprise était enterrée alors qu'elle demandait
  explicitement une prestation. V9 : **70, haute** (plancher appliqué).
- **Secteur 72** — **basse → 74, haute**.
- **iTelecom** — demande « prendre des rendez-vous qualifiés entre notre dirigeant
  et des décideurs d'entreprise ». C'est de l'**externalisation commerciale**,
  pas un système que nous construisons. V9 : **hors offre, 5, basse**.
- **Charme de l'Hêtre** — **moyenne → 18, basse** : signal seulement indirect.
- **14 remontées** de basse vers moyenne, **1 rétrogradation** vers basse.

### Contrôles

- Une preuve citée deux fois dans un même axe : **0**.
- Scores d'axe modifiés par la calibration : **0**.
- Demande hors offre classée « haute » : **0**.
- **498 tests** au vert, dont 25 nouveaux pour la priorité transversale.

## Une anomalie de données découverte, non corrigée silencieusement

La fiche **Beaujolais Réception** porte une preuve de type `public_need` au
niveau `exprime` dont l'extrait est :

> « Directeur de la publication : Kevin CANARD, Gérant »

Ce n'est **pas un besoin** : c'est une ligne de mentions légales mal typée. Le
filtre de pertinence la classe « incertaine » (×0,65), ce qui limite le dégât,
mais la preuve devrait être retypée. Elle est signalée pour l'audit des 38 fiches
et **n'a pas été réécrite** : corriger une preuve historique demande une
relecture de la source, pas une édition de confort.

## Limites restantes

- **La magnitude utilise encore le meilleur axe**, toutes classes confondues. Un
  besoin exprimé sur l'IA accompagné d'un site très dégradé profite de la
  magnitude de la refonte. C'est défendable — l'ampleur du problème est réelle —
  mais cela mélange les axes dans un seul terme.
- **Le périmètre de l'offre est une liste de mots-clés.** Il couvre les cas
  observés, pas les formulations nouvelles. Une demande hors offre inédite
  passera pour « incertaine » (×0,65) plutôt que pour « hors offre ».
- **La priorité ne filtre pas le statut.** Une entreprise déjà contactée peut
  afficher « haute » : la valeur commerciale et le droit de contacter restent
  deux questions distinctes. La liste d'appel doit filtrer sur le statut, ce que
  fait le dossier de qualification.
- **Les seuils 70 / 45 / 25 sont des choix**, pas des mesures. Ils sont
  adossés à la distribution observée sur 83 fiches et devront être revus quand
  le portefeuille aura doublé.