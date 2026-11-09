# Lot 11 — rapport final de la campagne de découverte

**Date de référence : 9 novembre 2026.** Recherche réellement exécutée : 21 requêtes
web, 32 lectures de pages, 82 structures examinées. Aucun envoi. Pré-vol toujours
bloqué sur ses trois motifs.

---

## A. Ce qui a été examiné

| Mesure | Valeur |
|---|---|
| Structures examinées | **82** (objectif 60-80 : atteint) |
| Requêtes `web_search` | 21 |
| Lectures de pages `fetch_page` | 37 tentatives, **33 réussies** |
| Départements couverts | **30** |
| Secteurs distincts | **19** |
| Retenues après lecture | **16** |
| À approfondir (lecture échouée ou preuve insuffisante) | 15 |
| Écartées sur contre-signal | 37 |
| Référencement d'annuaire seul | 14 |
| Doublons d'entreprise détectés | 3 |

Archive intégrale : `data/history/lot11-recherches-2026-11-09.json` — pour chaque
structure : nom, domaine, ville, département, secteur, type de source, URL,
décision et constat rédigé.

### Répartition départementale des 82 examinées

24 (8) · 41 (6) · 47 (6) · 32 (5) · 58 (5) · 56 (4) · 05, 12, 21, 26, 36, 42, 46,
51, 81, 89 (3 chacun) · 13, 15, 18, 43 (2) · 04, 07, 33, 40, 52, 53, 64, 77, 84,
86 (1).

Le portefeuille couvrait déjà 66 départements et 13 régions : **la nouveauté de ce
lot vient du secteur, pas du territoire.** Les 19 secteurs explorés étaient
inexplorés : ferronnerie d'art, géomètre-topographe, imprimerie-façonnage, contrôle
technique poids lourds, ramonage-fumisterie, prototypage 3D, vitrerie-miroiterie,
isolation par soufflage, signalétique, bureau d'études structure, levage-manutention,
entreposage frigorifique, gravure, domotique, contrôle d'accès, conserverie à façon,
pneumatique agricole/TP, moulistes-plasturgie, photovoltaïque.

---

## B. Fiches ajoutées au CRM

**CRM : 92 → 108 fiches. 16 créations, 0 collision, 0 écrasement.**

Les 92 fiches antérieures ont été vérifiées **octet par octet** après chaque
écriture (sérialisation JSON triée comparée à l'état initial) : aucune modification
de score, de statut, de preuve ou d'historique.

| Priorité | Entreprise | Dép. | Secteur |
|---|---|---|---|
| **92** haute | Bureau Bois Concept | 05 | Bureau d'études structure bois |
| **77** haute | Miditraçage Esvia | 84 | Signalisation routière et marquage |
| **75** haute | SAS Adrien Fernandes D&S | 89 | Menuiserie, automatismes, domotique |
| **75** haute | Plast e-Concept | 56 | Injection plastique, outillages |
| **75** haute | FMESURE | 26 | Géomètre-expert, topographie |
| **71** haute | Métallerie des Alpilles | 13 | Ferronnerie d'art, menuiseries acier |
| **71** haute | ETS Frézouls | 81 | Électricité, alarmes, contrôle d'accès |
| **71** à approfondir | 3DM Impression | 40 | Impression 3D à façon |
| **68** moyenne | CS Dépannages | 51 | Vitrerie, serrurerie, dépannage |
| **68** à approfondir | Occibox | 12 | Location de box de stockage |
| **68** à approfondir | Léonard & Parmentier | 42 | Chaudronnerie, tôlerie, serrurerie |
| **60** moyenne | Multi Pneus 36 | 36 | Pneumatique et mécanique |
| **60** moyenne | L'Océane des Plastics | 56 | Rotomoulage, plasturgie |
| **50** moyenne | La Conserverie des Producteurs | 32 | Conserverie à façon |
| **48** moyenne | Transports Francis Valette | 12 | Transport, entreposage, logistique |
| **44** basse | Transports Bonnevialle | 12 | Transport sous température dirigée |

Paliers : **7 haute · 5 moyenne · 3 à approfondir · 1 basse.** Aucun quota de
qualifiés n'a été appliqué : le palier est celui calculé par le moteur v10.

### Dédoublonnage

Trois domaines désignaient des entreprises déjà retenues ; **une seule fiche par
entreprise**, les domaines alternatifs étant conservés en preuve et en note :

- `multi-pneus-36.fr` et `multi-pneus.fr` → **Multi Pneus 36** (même adresse
  103 avenue d'Argenton, même téléphone 02 54 27 37 67) ;
- `cs-depannages-reims.com` → **CS Dépannages** (même téléphone 07 83 30 73 70).

Le script d'import est idempotent : relancé après import, il détecte **16 collisions
et crée 0 fiche**.

---

## C. Les trois scores, indépendants

Chaque axe est calculé par `score_prospect` (moteur d'axes **v8**) à partir des
preuves citées ; aucun score n'a été saisi à la main.

| Axe | Min | Max | Moyenne | Fiches ≥ 45 |
|---|---|---|---|---|
| Création de site | 5 | 5 | 5,0 | **0** |
| Refonte | 15 | 98 | 77,9 | **14** |
| IA / automatisation | 0 | 46 | 13,7 | **1** |

**L'axe création est à 5 partout, et c'est le résultat attendu** : les 16 entreprises
ont toutes un site en ligne. Aucune n'a été créditée d'un besoin de création.
Ce lot est un lot de refonte et, marginalement, d'automatisation.

Chaque preuve porte son type, son URL, sa citation, sa date d'observation **et** de
vérification (09/11), son type de source et sa fiabilité. Deux types de preuve
invalides rencontrés en cours de route ont été corrigés avant import (voir §F).

### Besoins exprimés vs opportunités probables

- **3 besoins exprimés publiquement** par l'entreprise elle-même :
  - **Miditraçage Esvia** — offre d'emploi du 29/04/2026 : « Saisie et envoie des
    devis demandés », « Suivi des relances factures clients », « Classement et
    archivage ». C'est le besoin le plus solide du lot.
  - **Bureau Bois Concept** — « DISPONIBLE POUR DE NOUVEAUX PROJETS » en accueil.
  - **Transports Francis Valette** — « nous vous proposerons bientôt un tout nouveau
    service … les litiges disponibles à la vente » : projet web annoncé, non réalisé.
- **13 opportunités probables**, fondées sur des défauts **observés** (parcours
  incomplet, marqueurs de gabarit publiés, incohérence de domaine), jamais sur une
  déduction sectorielle.

Une offre d'emploi reste un besoin exprimé **sur le processus**, pas une intention
d'achat : `proves_purchase_intent` demeure `False` (test dédié).

### Contre-signaux pris en compte

13 fiches sur 16 portent au moins un contre-signal explicite. Effets réels :

| Entreprise | Contre-signal | Force | Pénalité | Priorité |
|---|---|---|---|---|
| Transports Bonnevialle | système **EDI déjà exploité** | fort | −24 | 68 → **44 basse** |
| Multi Pneus 36 | « SANS RENDEZ-VOUS » revendiqué | modéré | −11 | 71 → **60** |
| L'Océane des Plastics | formulaire avec pièce jointe + BE intégré | modéré | −11 | 71 → **60** |
| Transports F. Valette | suivi déjà externalisé (Station Chargeur) | modéré | −11 | 59 → **48** |

Les 9 autres contre-signaux sont **faibles (0 point)** : ils délimitent le périmètre
sans annuler le besoin. C'est la calibration v10 acceptée, non retouchée.

**37 entreprises ont été écartées sur contre-signal**, dont : Sebatelec (refonte
récente), Tecni-Services (chatbot déjà déployé), Atelier 42 (prestataire « EB
Création »), Devevey (« Vinium »), Modern Signalisation (« agence Achroma »),
BET Chaumont (« le site fait peau neuve »), 3D'Clypse (devis en 2 h), ATS Électronique,
Conserverie du Moulin (WooCommerce), J2L Textiles (BAT 24 h), Andikado, MPAP,
Calypso Plasse, Bosse & Frères, et les réseaux de contrôle technique (réservation
déjà en place). Signaux Girod Cahors : 0 salarié.

---

## D. Coordonnées et brouillons

**13 adresses professionnelles publiées et contrôlées**, 3 entreprises sans adresse
publiée. Le contrôle est un **contrôle MX du domaine** : il prouve que le domaine
sait recevoir, **pas que la boîte existe**. Cette limite est écrite dans chaque fiche.

Aucune adresse n'a été devinée. Cas de la **Métallerie des Alpilles** : le texte
affiché est inversé, mais l'adresse a été **lue en clair dans le lien mailto** de
l'icône Email — elle est donc publiée, non reconstituée.

### Règle de brouillon, appliquée uniformément

> adresse joignable (MX ok) **et** priorité haute **et** confiance non faible sur
> l'axe qui porte la proposition.

**4 brouillons créés** — dans la file de validation **et** dans Gmail, libellé
`Prospection/2026-11-09-lot11` (`Label_9`) :

| Entreprise | Destinataire | Mots | Brouillon Gmail |
|---|---|---|---|
| Miditraçage Esvia | `contactweb@miditracage.com` | 157 | `1a1c2638fdfbe9c8` |
| Métallerie des Alpilles | `contact@metalleriedesalpilles.fr` | 135 | `1a1c2639c4412b5b` |
| Bureau Bois Concept | `contact@etudebbc.fr` | 142 | `1a1c263ab077a895` |
| ETS Frézouls | `contact@frezouls.fr` | 140 | `1a1c263b80ce4a95` |

Les 4 passent `check_email_v4` **sans réserve**, ≤ 167 mots, sujet ≤ 70 caractères,
signature officielle exacte (**Martin BOURASSEAU / Création de sites web · Refonte ·
Agents IA · Automatisation / https://prospecto.website**), ligne d'opposition
présente. Aucune référence commerciale n'a été insérée faute de pertinence.

**12 fiches n'ont volontairement pas de brouillon :**

- **3 sans adresse publiée** : 3DM Impression, Occibox, Léonard & Parmentier ;
- **3 en priorité haute mais confiance faible** sur l'axe porteur : FMESURE,
  Plast e-Concept, SAS Adrien Fernandes D&S — à vérifier avant contact ;
- **6 en priorité moyenne ou basse** : CS Dépannages, Multi Pneus 36, L'Océane des
  Plastics, La Conserverie des Producteurs, Transports F. Valette, Transports
  Bonnevialle.

Aucun brouillon n'a été créé pour les 8 entreprises contactées le 09/11, ni pour une
adresse de la liste de suppression. Les 2 brouillons antérieurs (Caléo, Ripaud) sont
**conservés sans modification**.

**Aucun envoi : 0 appel à `send_draft` ou `send_message`.**

---

## E. Sources les plus performantes

Rendement brut recalculé sur le registre complet (**213 structures**) :

| Type de source | Examinées | Qualifiées | Taux brut |
|---|---|---|---|
| **Site officiel** | 118 | 30 | **25,4 %** |
| Registre public | 2 | 0 | 0 % |
| Page professionnelle | 15 | 0 | 0 % |
| Autre | 20 | 0 | 0 % |
| **Annuaire pro** | **58** | **0** | **0 %** |

La décision prise en début de lot — **écarter les requêtes d'annuaire** — est
confirmée par les faits : 58 structures vues en annuaire, **aucune** qualifiée. Le
site officiel reste la seule source qui produit des fiches. Les offres d'emploi
publiées **sur le site de l'entreprise** ont produit le meilleur besoin du lot.

---

## F. Erreurs rencontrées et corrigées

Rien n'a été masqué ; chaque erreur a été corrigée avant import.

1. **Quatre constats faux, corrigés après relecture** :
   - **MPO** — j'avais écrit « aucun formulaire de dépôt de cahier des charges ».
     La page contact porte en réalité un formulaire complet **avec dépôt de
     fichiers** et un rappel web. Constat corrigé, entreprise **rétrogradée** en
     « à approfondir » et **non importée**.
   - **La Conserverie des Producteurs** — les prix des bocaux **sont** publiés
     (0,39 € à 1,15 €). Le manque porte sur la demande de prestation, pas sur la
     transparence tarifaire.
   - **Bureau Bois Concept** — un formulaire existe ; le vrai défaut est le titre
     de page « Contacter Le GIE Tétraèdre », une autre entité.
   - **Plast e-Concept** — code postal écrit « 561900 Arzal » (six chiffres).
2. **Deux types de preuve invalides** (`besoin_exprime`, `manque_site`) n'existaient
   pas dans le modèle : ils étaient **ignorés en silence** par le moteur, ce qui
   faisait sortir Miditraçage en priorité **23 basse**. Corrigés en `public_need` et
   `website_gap`, validation systématique ajoutée → Miditraçage **77 haute**.
3. **Contre-signaux inertes** : ils étaient stockés dans une liste que le moteur ne
   lit pas. Convertis en preuves `maturite_existante` → pénalités réelles.
4. **`email_dns_status` non renseigné** alors que le DNS avait été mesuré : toutes
   les fiches sortaient « à approfondir ». Renseigné depuis les mesures réelles.
5. **Sujet de Bureau Bois Concept à 82 caractères** : il retombait silencieusement
   sur « Une idée pour votre entreprise ? ». Raccourci à 56.
6. **`gmail_draft_id` absent de la file** : les 4 brouillons étaient comptés « en
   attente » au lieu de « brouillons ». Renseigné → 6 brouillons / 1 en attente.
7. **Pré-vol exécuté sur la configuration réelle** : `Sender()` sans argument a
   persisté l'horodatage DNS dans `v4-settings.json`. Fichier **restauré depuis la
   sauvegarde**, contrôle relancé sur une copie isolée (`settings_path`). MD5 4/4.
8. **Lectures échouées, non insistées** : `3domega.fr`,
   `bernardforestier-ramonage-auch32.fr`, `maxelec89.fr` (2 échecs). Ces entreprises
   sont classées « à approfondir », **non importées**. Un échec de lecture ne prouve
   pas un site mort.
9. **Piège d'homonymie évité** : « BET Chaumont » est un nom de famille, l'entreprise
   est à **Laval (53)**, pas à Chaumont (52).

### 7 tests figeaient l'état du portefeuille

L'ajout des 16 fiches a fait échouer 7 tests qui assertaient des instantanés
(92 fiches, contre-signaux 2/8/7, rendement « 24 % », 2 brouillons, date du
07/11). Ils ont été convertis en **invariants recalculés depuis la source de
vérité**, sans rien retirer de ce qu'ils protégeaient :

- la trace de calibration v10 ne concerne que la **cohorte migrée**, pas une fiche
  née sous v10 ;
- `priority_value.n` est relu depuis le CRM ;
- les contre-signaux sont recomptés depuis les fiches ;
- le taux de rendement affiché était **déjà** comparé au taux recalculé : la ligne
  figée doublonnait ;
- brouillons et attente sont recomptés depuis la file, avec contrôle de la somme ;
- une évaluation doit être **datée et non future**, pas datée d'un jour précis.

---

## G. État final

| Élément | État |
|---|---|
| CRM | **108 fiches** (92 + 16), 92 antérieures inchangées |
| Registre d'exploration | **131 → 213** structures |
| File de validation | **73 → 77** (6 brouillons, 1 en attente, 60 envoyés) |
| Journal d'envois | **60**, inchangé (MD5) |
| Rapprochements | **5**, inchangés (MD5) |
| Suppression | **2**, inchangée (MD5) |
| Axes | **v8** sur les 108 fiches |
| Priorité | **v10-priority** sur les 108 fiches |
| `priority_value` | n 108, moyenne **54,8**, médiane 58, min 5, max 95 |
| Tests | **703 verts / 24 fichiers** (670 + 33 nouveaux) |
| MD5 protégés | **4/4** |
| Dashboard | redémarré, port 8787, `/api/metrics` et `/api/campaign` **200** |

Le tableau de bord affiche le lot 11 : **16 prospects, 7 haute, 13 adresses
vérifiées, 4 brouillons, 0 envoyé, 0 rebond, 0 réponse.**

### Pré-vol — toujours bloqué

```
(False, 3 motifs)
1. Campagne non activée (enabled=false). Activation explicite requise.
2. DKIM non détecté pour le domaine expéditeur.
3. Domaine expéditeur gratuit (Gmail (gratuit)) : prospection de masse
   déconseillée/interdite par les CGU.
```

`enabled=false` · `dry_run=true` · transport `gmail_connector` · SPF oui · DKIM non.
**Le 3e motif est le blocage de fond** : il ne se contourne pas par un réglage.

### Sécurité — aucune action interdite

Aucun envoi · `enabled` non modifié · aucun DNS modifié · aucun achat ni souscription ·
aucun challenge anti-bot validé · aucune donnée ni historique supprimé · aucun score
d'ancienne fiche modifié. Le bloc `securite` de l'archive est à `false` sur ses 7
clés, et un test le vérifie.

---

## H. Meilleures opportunités, par ordre d'appel

1. **Bureau Bois Concept (05) — 92.** Cherche publiquement des projets, mais son
   formulaire ne demande ni l'ouvrage ni la mission. Brouillon prêt.
2. **Miditraçage Esvia (84) — 77.** Seul besoin exprimé sur un processus complet
   (devis, relances, dossiers de chantier). Site récent : **automatisation, pas
   refonte**. Brouillon prêt.
3. **Métallerie des Alpilles (13) — 71.** Adresse e-mail affichée inversée, deux
   numéros contradictoires, « Created with Sketch. » publié. Brouillon prêt.
4. **ETS Frézouls (81) — 71.** Liens internes en http sur un site https, ressources
   de 2018. Brouillon prêt.
5. **3DM Impression (40) — 71.** Les boutons boutique envoient le visiteur vers le
   domaine de préproduction de l'hébergeur. Défaut net, mais **pas d'adresse
   publiée** : approche à trouver.
6. **Multi Pneus 36 (36) — 60.** Compteurs « -125+ ans d'expérience » et
   « -1250% sans rendez-vous » en accueil, trois domaines dispersés.

---

## I. Fichiers produits

- `data/history/lot11-recherches-2026-11-09.json` — les 82 examinées, doublons,
  constats, bloc sécurité ;
- `data/history/lot11-import-2026-11-09.json` — résultat d'import, collisions,
  axes et priorités fiche par fiche ;
- `data/history/lot11-brouillons-2026-11-09.json` — les 4 brouillons, corps exacts,
  identifiants Gmail et de file ;
- `data/history/lot11-dns-2026-11-09.json` — contrôles MX datés ;
- `scripts/lot11/fiches.py` — définitions sourcées des 16 fiches ;
- `scripts/lot11/importer.py` — import idempotent, simulation par défaut ;
- `tests/test_lot11.py` — **33 tests** de garanties.

**Le lot 11 est exécuté, pas planifié.** Prochaine action humaine : valider ou
rejeter les 4 brouillons. Aucun envoi n'est possible tant que les trois motifs du
pré-vol subsistent.
