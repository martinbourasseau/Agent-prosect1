# Rapport de mission — phase 10

**Branche** `arena/7ed6352a-agent-prosect1` · **Date** 2026-11-07 · **Aucun e-mail envoyé**

> **Ce que cette phase a produit.** Un moteur de scoring refondu en trois axes
> indépendants, un planificateur de recherche qui apprend de son rendement, un
> module de qualification qui refuse de deviner, quatre faux négatifs récupérés,
> une cinquième fiche neuve, un tableau de bord qui dit enfin ce qui bloque — et
> **473 tests**. Elle a aussi produit deux échecs qu'il faut lire comme tels :
> le lot 10 s'arrête à **13 structures examinées sur ~60**, et **aucun brouillon
> n'a été créé** cette fois. Les deux sont documentés plus bas, pas contournés.

---

## 1. Audit du portefeuille — les 78 fiches

### Ce qui a été fait

Les 78 fiches ont été passées au crible, puis **41 constats** ont été consignés
dans `docs/audit-phase10-portefeuille.md` et
`data/history/audit-portefeuille-phase10.json`.

| Constat | Nombre |
|---|---|
| Insuffisamment qualifié | 15 |
| À approprier (opportunité réelle, angle à reprendre) | 12 |
| **Faux négatif** | 12 |
| **Faux positif** | 3 |
| Preuve mal typée | 1 |

**Huit rejets étaient justes et ont été maintenus** : Styl'escalier, Top Cheval,
Cavaland, L'Artisan Affûteur, Livio Baldelli, Azur Toiture, Dose Paris, Caféophil.
Tous déjà outillés. Les réintégrer aurait gonflé le portefeuille sans créer
d'opportunité.

### Faux positifs corrigés

Le cas net est **Charme de l'Hêtre** : score de création **40 → 0**. Sa vraie
preuve est `site_absent` — il n'y a pas de site à refondre, et le moteur
confondait les deux axes. Trois signaux mal typés ont été corrigés dans la
foulée.

### Faux négatifs : deux registres bien distincts

**Onze faux négatifs de scoring.** Des opportunités réelles notées zéro parce que
le moteur ne savait pas lire la preuve :

| Entreprise | Axe remonté | Avant → après |
|---|---|---|
| Brasserie VDL | IA | 0 → **46** |
| SAM 31 | IA | 0 → **44** |
| Dance Center | IA | 0 → **39** |
| Base nautique Picquigny | IA | 0 → **39** |
| Goudale Orchies | IA | 0 → **26** |
| La Bruchoise · Le Canotier | IA | 0 → **24** |
| Fromagerie et Baratte | IA | 0 → **22** |
| Celtuce | refonte / IA | **5 / 61 / 31** |
| Domaine Courbin | refonte / IA | **5 / 31 / 31** |
| Séverine Lesourd | refonte / IA | **5 / 31 / 22** |

**Dix besoins exprimés sous-évalués**, remontés de la fourchette 10-25 vers
34-60. Le plus parlant : *Restaurant quais de Quimper*, dont le besoin
d'automatisation est **écrit noir sur blanc** par l'entreprise, passait à 10.
Il est à **60**.

**Deux faux négatifs de rejet**, et c'est la vraie récupération de la phase :
**Zicplace** et **O Lames Déchues** avaient été écartées à tort. Toutes deux ont
été levées par relecture directe de la source (§3).

### Opportunités retrouvées et à approfondir

**4 fiches récupérées et qualifiables**, **6 pistes à approfondir** avec l'étape
manquante écrite, **3 rejets maintenus**. Sur les 51 fiches en attente du lot 9,
**13 ont été réellement réexaminées**. Les **38 autres sont marquées « non
réexaminé »** : leur motif initial n'est pas revalidé et ne doit pas être présenté
comme acquis.

---

## 2. Évolution de l'agent

### Trois scores indépendants, et quatre bugs de fond

Le moteur v8 sépare **création**, **refonte** et **IA/automatisation**. Le score
d'IA ne dépend plus du métier : il dépend de ce qui est observé.

Quatre défauts ont été trouvés **en testant**, pas en relisant le code :

1. **La maturité lisait la recommandation du chercheur.** Un champ `detail`
   disant « il faudrait un module de réservation » était compté comme une
   réservation existante. Le détecteur ne lit plus que `Evidence.quote`.
2. **Les signaux s'empilaient sur la preuve 0.** Dédoublonner par `signal.id` dès
   la première preuve récompensait dix fois le même extrait. Tous les couples
   sont désormais collectés, puis les plus forts affectés aux preuves non
   encore récompensées.
3. **La négation n'existait pas.** « Pas de réservation en ligne » créait un
   besoin de réservation *et* un signal de maturité.
4. **`process_hint` était cité comme preuve.** C'est une note de chercheur, pas
   un extrait vérifiable. Il ne produit plus de citation.

S'y ajoutent quatre niveaux de preuve (**exprimé 1,0 / observé 0,85 / indirect
0,45 / hypothétique 0,25**), une base de **34** pour un besoin exprimé sur l'axe
désigné, une preuve qui ne paie qu'une fois, la contactabilité sortie du score,
et une **date d'évaluation par axe**. **65 des 78 scores ont changé** ; la
baseline v7.1 intégrale est archivée dans
`data/history/scores-v71-vers-v8.json`.

### Planificateur de recherche

`prospecto/planner.py` mémorise secteurs et départements, dédoublonne par
empreinte de requête, et **priorise les sources qui ont produit des qualifiés**.
Le rendement est lissé par un prior de 8 observations à 15 % — sans quoi un seul
coup de chance décidait de la stratégie. Mesuré sur les données réelles :

| Source | Examinées | Qualifiées | Rendement lissé |
|---|---|---|---|
| **Site officiel** | 21 | **9** | **0,352** |
| Autre | 6 | 0 | 0,086 |
| Page professionnelle | 12 | 0 | 0,060 |
| **Annuaire pro** | 33 | **0** | **0,029** |
| Sources jamais essayées | 0 | — | 0,150 |

L'annuaire professionnel a consommé **33 examinations pour zéro qualification**.
Une source neuve reste préférée à cette source mauvaise prouvée : c'est le
comportement voulu.

**Un défaut trouvé par l'usage.** Les requêtes « besoin exprimé » ne ramenaient
que des **agences web qui vendent la prestation** — en Corse, trois agences et
zéro prospect. Le bruit est structurel : les agences optimisent précisément ces
formulations. Les motifs ont été reformulés du côté client (`"notre site est
obsolète"`, `"nous n'avons pas de site"`) et des exclusions ajoutées
(`-agence -freelance -prestataire …`).

### Qualification : refuser de deviner

`prospecto/dossier.py` construit le dossier complet et **bloque** au lieu de
combler un trou. La vérification d'une adresse repose sur
`email_publication_evidence()` : l'adresse doit être **citée dans une preuve
datée d'une source officielle**. Un MX prouve seulement que le domaine route.

Trois pages ont été relues pour lever ce blocage proprement (Canfora, Cordes et
Âme, Froger) et archivées dans
`data/history/confirmations-coordonnees-2026-11-07.json`. Résultat :
**0 adresse décodée non confirmée** dans tout le portefeuille.

### Limites restantes — à lire avant de faire confiance aux scores

**La limite principale est structurelle et n'est pas corrigée.** Un besoin
**exprimé** plafonne à **34** sur son axe désigné, alors qu'une lacune de site
**déduite** atteint **57** en refonte, et jusqu'à **98** avec trois preuves. La
hiérarchie a été corrigée *à l'intérieur* d'un axe, **pas entre les axes**. Une
entreprise qui écrit « nous cherchons à automatiser » peut donc rester derrière
une entreprise dont on a seulement inféré un site vieillissant. Corriger cela
demande une échelle commune aux trois axes, ce qui est un changement de
calibrage, pas un patch.

Autres limites assumées :

- **Le contre-signal n'est pas soustrait, il est seulement affiché.** Une
  entreprise qui publie une grille tarifaire complète et un parcours en quatre
  étapes garde un score de refonte élevé si son site a par ailleurs des défauts.
- **La confiance ne mesure pas la fraîcheur.** Une preuve de 2019 et une preuve
  d'hier pèsent pareil.
- **Les compteurs à 0 % ne sont pas une preuve fiable.** Chez Atelier du
  Bourrelier, ils peuvent venir d'une animation JavaScript non déclenchée lors de la
  lecture de la page. Le constat est marqué sous réserve et n'a pas servi à scorer.
- **Le planificateur ne sait pas qu'une requête a échoué pour cause de bruit.**
  Il enregistre le rendement, pas la cause ; les motifs ont été corrigés à la
  main.
- **La Corse est couverte, mais par des recherches qui n'ont rien donné.** 13/13
  régions ne veut pas dire 13 régions productives.

---

## 3. Lot 10 — et les récupérations

### Le chiffre honnête

**13 structures examinées sur les ~60 visées.** L'objectif n'est **pas atteint**
et l'archive le dit (`objective_reached: false`, avec `gap_reason`). Le budget de
recherche est passé dans la vérification directe des sources de la section G —
un choix, pas un oubli. **Aucune fiche n'a été créée pour remplir un quota.**

### Cinq fiches neuves dans le CRM (78 → 83)

Quatre viennent de l'approfondissement du lot 9, une du lot 10 :

| Entreprise | Dépt | Création / Refonte / IA | Priorité |
|---|---|---|---|
| **Atelier du Bourrelier** | **45** | 5 / **98** / 12 | haute |
| **O Lames Déchues** | 95 | 5 / **89** / 27 | haute |
| **Zicplace** | 93 | 5 / **81** / 31 | haute |
| **Alain Louis — Naturaliste taxidermiste** | 78 | 5 / **81** / 12 | haute |
| Étanchéité Nantaise | 44 | 5 / 39 / 22 | basse |

**5 e-mails vérifiés, 5 téléphones vérifiés, 5/5 domaines routables (`mx_ok`),
0 doublon.** Les cinq qualifient au sens du dossier.

### Les meilleures opportunités, preuves à l'appui

**O Lames Déchues (95, Bréançon).** Écartée pour « site en chantier, adresse
invérifiable ». Le site est aujourd'hui complet et les coordonnées sont en clair.
Mais le gabarit n'est pas fini : la FAQ annonce « Retrouvez mon planning
hebdomadaire […] sur cette page **[ou section « Planning »]** » — le marqueur de
gabarit est **publié tel quel** et **aucune section planning n'existe**, alors
que toute l'activité itinérante en dépend. Les tournées professionnelles
récurrentes se calent à la main. Contre-signal noté : encaissement CB déjà
possible, donc pas de besoin de paiement en ligne.

**Zicplace (93, Montreuil).** Écartée car l'adresse n'était vue qu'en JSON-LD ;
elle est en réalité publiée **en clair, deux fois**. L'entreprise annonce
**+2 000 réparations par an** et n'offre qu'un point d'entrée : « Passez au
magasin avec votre matériel ». Aucun pré-diagnostic, aucune prise de dépôt en
ligne. La même page publie **deux horaires contradictoires** (Lun–Sam 10h–20h
dans le bloc dépôt, Mar–Sam 11h–19h30 en pied de page). Contre-signaux forts
notés : grille tarifaire complète et parcours en quatre étapes déjà publiés —
le besoin n'est pas la refonte du contenu.

**Atelier du Bourrelier (45, Dordives).** Le registre indiquait **91** : la
société est dans le **Loiret**. Aucune page contact ni devis dans la navigation ;
les coordonnées n'existent qu'en pied de page. Un encart annonce « Retrouvez-moi
sur ce salon » **sans nom, sans lieu, sans date**, avec un accord masculin qui ne
correspond pas à la dirigeante présentée sur la même page.

**Alain Louis (78, Gazeran).** Quatre visuels de galerie portent un lien nommé
**« Button »** renvoyant à la page courante. Le bouton « DEMANDER UN DEVIS »
renvoie à la page contact générique. « Appeler avant de venir » : premier contact
téléphonique, aucune description structurée de l'animal à naturaliser.

### Ce qui a été écarté, et pourquoi

**8 rejets motivés** : trois agences web, ALP Construction (**déjà outillée** :
devis en ligne, espace client, rappel programmé), deux plateformes de mise en
relation, un **belge hors périmètre**, un syndicat professionnel. **2 annuaires
seuls.** **2 à approfondir**, dont **Régis de Izarra (80)** : signaux manuels
forts — conseils de conservation donnés un par un, uniquement sur rendez-vous,
colis express 24 h, tannage 15 jours et séchage trois mois — mais **aucune adresse
e-mail publiée**. Non contactable en l'état, donc **aucune fiche**.

**Sept départements neufs** : 2A, 2B, 50, 58, 78, 80, 94. Les **13 régions
métropolitaines** sont désormais couvertes.

### Deux corrections de département

Atelier du Bourrelier **91 → 45**, Rhonalpe Étanchéité **69 → 01**. Fermetures
Leichnam était enregistré en **67** : la société est à Saint-Quentin, **02**.

### Le manque à signaler

**Aucun brouillon n'a été créé pour cette phase.** Le label
`Prospection/2026-11-07-lot10` n'a pas été créé. Les cinq fiches neuves sont
qualifiées et prêtes, mais la rédaction et le dépôt Gmail restent à faire. Les
anciens brouillons n'ont **pas** été modifiés.

---

## 4. Gmail — audit et réconciliation

**69 adresses interrogées** en quatre requêtes ciblées, spam et corbeille inclus,
en exigeant `search_scope.complete`. Une requête large sur une boîte de 29 000
messages renvoie du bruit tronqué et ne prouve rien.

| Catégorie | Trouvé | Nouveauté |
|---|---|---|
| Réponse humaine | **1** | 0 |
| Réponse automatique | 0 | 0 |
| Rebond | **1** | 0 |
| Challenge de sécurité | **1** | 0 |
| Demande d'info / devis / RDV | **0** | 0 |
| Opposition | **1** | 0 |

**La seule réponse humaine est une opposition.** Centre équestre de la Renarde,
5 novembre : « **Ne pas me relancer** ». Déjà réconciliée, statut `opposition`,
adresse en liste de suppression. **Aucune nouvelle approche, jamais.**

Le scoring v8 a remonté son score d'IA de 0 à 22. **Son statut n'a pas changé** et
le dossier la bloque explicitement. C'est le comportement voulu : la force d'une
opportunité et le droit de contacter sont deux questions distinctes.

**Le seul rebond** est celui de `contact@severine-lesourd.com`, domaine
introuvable, déjà connu. Aucun nouveau rebond sur les 14 envois réconciliés du
6 novembre.

**Le seul challenge** est un Mailinblack pour Alpha Mécanique : « Un clic pour
délivrer votre email ! ». **Laissé non validé**, conformément à la consigne de
sécurité. Il reste classé `challenge_en_attente` : ce n'est ni une réponse
humaine, ni une délivrance confirmée.

**Brouillons de réponse : zéro.** Aucune demande commerciale explicite n'a été
trouvée ; il n'y avait rien à quoi répondre. La règle qui autorise une réponse
simple ne s'applique pas faute d'objet.

**Rapprochements CRM : aucun nécessaire.** Les 14 envois hors agent du 6 novembre
l'étaient déjà (`matched 14, unmatched 0`). Les **5 brouillons** existants ont été
vérifiés **intacts**, aucun modifié.

Détail dans `docs/audit-gmail-phase10.md` et
`data/history/audit-gmail-phase10.json`.

> **Limite de l'audit.** Les requêtes couvrent les **adresses connues du CRM**.
> Une réponse émise depuis une autre adresse du même prospect — un collègue, une
> adresse de direction — leur échapperait. Ce cas demande une recherche par objet
> de conversation plutôt que par expéditeur.

---

## 5. Fiabilité

### Tests

**473 tests, tous au vert** (`python3 -m unittest discover tests -q`).
Répartition : 55 lot 9, 38 phase 10 v8, 26 planificateur, 30 dossier, **29
livraison phase 10**, plus les suites antérieures.

Les onze contrôles demandés :

| # | Contrôle | État |
|---|---|---|
| 1 | Trois scores indépendants et reproductibles | ✅ 83/83 recalculés à l'identique |
| 2 | Anti-doublons sur tout le CRM | ✅ 0 collision, inter-lots vérifié |
| 3 | Oppositions et suspensions | ✅ jamais qualifiables, test explicite |
| 4 | Adresses absentes / non confirmées | ✅ **0 décodée non confirmée** |
| 5 | Réconciliation Gmail | ✅ 4 réconciliations réelles, rien à ajouter |
| 6 | Journaux sans pollution de fixtures | ✅ contrôle sur les entrées |
| 7 | Intégrité des données historiques | ✅ baseline v7.1 + 3 migrations archivées |
| 8 | Dashboard | ✅ partition exclusive **cohérente**, 83 fiches |
| 9 | Envois bloqués | ✅ pré-vol `(False, 3)` |
| 10 | Preuve datée obligatoire | ✅ 12/12 qualifiables en ont une |
| 11 | Décisions conservées | ✅ registre append-only, 2 décisions par fiche levée |

### Protections vérifiées intactes

```
enabled = False              dry_run = True
require_spf = True           require_dkim = True      require_dmarc = True
honor_suppression_list = True    include_opt_out = True
identify_sender = True       b2b_only = True
follow_up.enabled = False    stop_on_reply = True     stop_on_opt_out = True
```

**Pré-vol : `(False, 3 blocages)`** — campagne non activée, DKIM absent, domaine
expéditeur gratuit. Aucun DNS, SPF, DKIM, DMARC ni aucune protection modifiés.
**Aucun achat, aucun abonnement, aucun contournement.**

### Deux incidents évités, et un vrai piège

**`Sender().preflight()` écrit en production.** Un appel direct réécrit
l'horodatage `last_checked_at` de `data/campaigns/v4-settings.json`. Détecté par
comparaison MD5, annulé par `git checkout --`. Les tests travaillent sur une
copie depuis `0a4b0d7`, et un test vérifie maintenant que le pré-vol **ne touche
pas** le fichier de production.

**Un test interdisait le mot « fixture » à la note qui documente la
quarantaine.** Le contrôle a été déplacé sur les entrées : une note doit pouvoir
expliquer ce qu'elle a nettoyé.

**MD5 des quatre journaux de production : 4/4 OK** avant et après la suite
complète — `reconciliations.json`, `send-log.json`, `v4-settings.json`,
`suppression.json`.

### Deux bugs de mes propres patches, corrigés

Une apostrophe non échappée dans les motifs de requête a cassé l'import de
`planner.py` — **444 tests sont tombés à 419** le temps de le voir. Un test de
régression vérifie désormais que chaque motif se formate et que ses guillemets
sont équilibrés. Un test du lot 9 figeait `retenue == 4` ; le registre étant un
journal qui croît quand un rejet est levé, l'invariant a été reformulé.

---

## 6. Git

**Branche** `arena/7ed6352a-agent-prosect1` — aucune autre branche créée.

| Commit | Contenu |
|---|---|
| `811d9d1` | A + B — intégrité, pré-vol, audit des 78 fiches (41 constats) |
| `b3cda10` | D — scoring v8, trois axes, 65 scores migrés |
| `89346b8` | E — planificateur, rendement des sources, couverture |
| `3db140f` | F — dossier de qualification, vérification sur preuve |
| `283aea3` | G — approfondissement lot 9, 4 faux négatifs levés |
| `ada9f41` | I + J — audit Gmail par adresse, envois bloqués |
| `3baaf4b` | H + K + L — lot 10 partiel, dashboard pilotage, 473 tests |
| *(ce commit)* | M — rapport final |

Rapport : `docs/rapport-mission-2026-11-07-phase10.md`.
Reprise : `docs/reprise-phase10.md`.
**Aucune fusion automatique. Aucun secret commité.**

---

## 7. Trois prochaines améliorations pour rendre Prospecto plus autonome

### 1. Une échelle commune aux trois axes

C'est la limite la plus coûteuse aujourd'hui. Un besoin **exprimé par
l'entreprise** plafonne à 34 pendant qu'une lacune **déduite par l'agent**
atteint 98. Tant que les axes ne partagent pas de référence, la priorité
commerciale reste biaisée en faveur de ce que l'agent sait observer plutôt que
de ce que le prospect dit vouloir.

**À faire :** calibrer les trois axes sur une même distribution, en utilisant
les 83 fiches déjà scorées comme jeu de référence, puis vérifier que les dix
besoins exprimés remontent au-dessus des lacunes seulement inférées. C'est un
travail de calibrage avec revue humaine, pas un patch.

### 2. Boucler la cause d'échec d'une requête, pas seulement son rendement

Le planificateur sait qu'une source a mal produit ; il ne sait pas **pourquoi**.
La recherche corse a échoué parce que les agences web capturent la formulation,
et il a fallu une intervention humaine pour reformuler les motifs.

**À faire :** classer automatiquement chaque résultat écarté (`agence`,
`plateforme`, `hors_périmètre`, `homonyme`, `annuaire_seul`), et quand une
requête dépasse un seuil de bruit structurel, la marquer comme **motif à
reformuler** plutôt que comme territoire épuisé. Aujourd'hui, un échec de
formulation ressemble à un territoire stérile — et la Corse risque d'être
abandonnée pour la mauvaise raison.

### 3. Rendre la vérification de coordonnées continue et vérifiable

La règle « adresse citée dans une preuve datée d'une source officielle » est
solide, mais elle est appliquée **à la main** : chaque confirmation a demandé une
relecture et un script. Résultat, 15 fiches restent bloquées sur « adresse
publiée mais non recoupée » et 13 sur « aucune adresse publiée ».

**À faire :** un vérificateur qui, pour chaque fiche bloquée, ouvre la page
contact et les mentions légales, cherche l'adresse en clair, et **écrit la
preuve datée** quand il la trouve — sans jamais valider de challenge, sans
jamais deviner, et en laissant la fiche bloquée quand la page ne dit rien. Une
passe périodique sur les seules fiches bloquées transformerait 28 blocages en
soit une qualification, soit une absence définitive et documentée.

---

## Annexe — chiffres de référence

**Portefeuille : 83 fiches** — 55 contactées, 18 découvertes, 6 brouillons en
attente, 1 à investiguer, 1 rebond, 1 opposition, 1 suspendue. Partition
exclusive **cohérente**.

**Qualification : 12 dossiers qualifiables sur 83 (14 %)**, **53 e-mails
vérifiés**, **31 téléphones vérifiés**, **0 adresse décodée non confirmée**.

**Blocages** : 53 déjà contactées, 16 localisation absente, 15 adresse non
recoupée, 13 sans adresse publiée, 8 activité non renseignée, 8 sans source
datée, 8 sans preuve concrète, 2 domaines non routables, 1 opposition, 1 rebond,
1 suspendue.

**Pipeline** : 60 envoyés, **3 délivrances confirmées**, **55 non confirmées**,
1 rebond, 1 challenge, 1 réponse humaine, 2 automatiques, 1 opposition,
5 brouillons, 10 obsolètes. Taux de rebond **1,7 %**.

> **Envoyé n'est pas délivré.** 55 messages sont sortis sans preuve de remise ni
> rebond : leur statut est **inconnu**, pas « délivré ».

**Exploration : 72 structures examinées** — 35 écartées, 26 annuaire seul,
9 retenues, 2 à approfondir. **49 départements, 13/13 régions.**

**Répartition des trois scores** (fort / moyen / faible) :
création **2 / 0 / 81** · refonte **6 / 25 / 52** · IA **1 / 18 / 64**.
Priorités : 11 haute, 31 moyenne, 26 basse, 15 à approfondir.

**File de validation : 68** — 52 envoyés, 10 obsolètes, 4 brouillons, 2 en attente.
**Suppression : 2 entrées.**