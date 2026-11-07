# Phase 10 — Audit initial et audit intelligent du portefeuille

**Date :** 7 novembre 2026
**Branche :** `arena/7ed6352a-agent-prosect1` — commit de départ `0a4b0d7`
**Périmètre de ce document :** sections **A** (état réel) et **B** (audit des 78 fiches).
**Diagnostic en lecture seule : aucun score, aucune fiche, aucun brouillon modifié.**

---

## A. État réel du projet

### A.1 Une premise à corriger : il n'y a pas de base SQLite

Vous demandez de contrôler « l'intégrité de la base SQLite ». **Cette base
n'existe pas.** Vérification faite :

- `find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3"` → aucun résultat ;
- aucun `import sqlite3` dans les 26 modules du projet.

Le CRM est **un fichier JSON unique** : `data/crm/prospects.json`
(610 Ko, clés `updated_at` / `count` / `prospects`). Il n'y a donc pas
d'intégrité transactionnelle à vérifier, mais une **intégrité de parsing et de
cohérence interne**, que j'ai contrôlée à la place : **47 fichiers JSON de
données, 0 corrompu**, et `count` déclaré = nombre réel de fiches.

Cela a une conséquence pratique pour la suite : sans transactions, toute
écriture est un remplacement de fichier complet. La sauvegarde préalable n'est
pas une précaution optionnelle, c'est le seul filet.

### A.2 Points vérifiés

| Point annoncé | Constat | |
|---|---|---|
| Branche `arena/7ed6352a-agent-prosect1` | conforme | ✅ |
| Commit `0a4b0d7` | conforme, arbre propre | ✅ |
| 350 tests | **350 au vert** | ✅ |
| 78 fiches | **78**, `count` cohérent | ✅ |
| Dashboard port 8787 | répond (302 vers login), `/api/metrics` cohérent | ✅ |
| Trois scores indépendants | présents sur **78/78**, tous en `v7.1` | ✅ |
| Pré-vol bloqué | **`(False, 3 blocages)`** | ✅ |
| Aucune fusion automatique | aucun merge, branche unique | ✅ |
| Base SQLite | **inexistante** — CRM en JSON | ❌ premise à corriger |

### A.3 Brouillons Gmail

**5 brouillons**, tous vérifiés par `in:drafts` **et** label (un label seul ne
prouve pas l'existence du brouillon) :

| Entreprise | Message | Label |
|---|---|---|
| Caléo Tests & Services | `1a1b672541671292` | `Label_7` (lot 9) |
| Cordonnerie Canfora David | `1a1b1b9735345222` | `Label_7` |
| Froger Étanchéité | `1a1b1b98459979b3` | `Label_7` |
| Cordes et Âme | `1a1b1b991300c965` | `Label_7` |
| Pépinières Ripaud | `1a1b16dee5899e57` | `Label_6` (lot 8) |

**0 réponse** de ces cinq destinataires, spam et corbeille inclus
(`search_scope.complete: true`). Cohérence CRM ↔ Gmail ↔ dashboard : **exacte**.

> Piège rencontré : `label:Prospection` renvoie 0 brouillon. Les labels sont
> imbriqués (`Prospection/2026-11-06-lot9`) et Gmail ne fait pas correspondre le
> parent. Il faut interroger chaque label feuille.

### A.4 Cohérence des compteurs

- Portefeuille : partition **exclusive**, total 78, contrôle `cohérent`.
- Délivrance : 3 confirmées + 55 non confirmées + 1 rebond + 1 challenge = **60**, contrôle `cohérent`.
- File : 68 items — `sent` 52, `draft` 4, `pending` 2, `obsolete` 10.
- Suppression : **2** entrées. Registre d'exploration : **55** structures.

### A.5 Sauvegarde

`data/backups/2026-11-07-avant-phase10/` — **41 fichiers, 1,3 Mo**, créée avant
toute opération. Aucune suppression d'historique, de fiche ou de brouillon.

---

## B. Audit intelligent des 78 fiches

**41 fiches présentent au moins un constat.** Détail machine-readable :
`data/history/audit-portefeuille-phase10.json`.

| Catégorie demandée | Fiches |
|---|---:|
| 1. Intéressants insuffisamment qualifiés | **15** |
| 2. Faux positifs | **3** |
| 3. Faux négatifs | **12** |
| 4. À approfondir | **12** |
| 5. Déjà suffisamment équipées (écartées à juste titre) | **8** |
| Constat annexe : preuve mal typée | 1 |

### B.1 LE défaut structurel : la hiérarchie des signaux est inversée

C'est la conclusion la plus importante de cet audit, et elle rejoint exactement
votre priorité de la section C.

**15 fiches contiennent un besoin exprimé publiquement par une entreprise, avec
un budget déclaré.** Elles viennent d'annonces Codeur.com. Exemples textuels :

> « Je dirige un organisme de formation… les relances correspondantes doivent se
> déclencher automatiquement… sans intervention manuelle de ma part »
> — budget 500–1 000 €

> « Nous ouvrons un restaurant traditionnel sur les Quais de Quimper, nous
> aurions besoin d'un site internet… avec un module de réservation intégré »
> — budget 500–1 000 €, 164 offres déjà reçues

> « Je travaille dans la vente d'espaces publicitaires audiovisuels… une grande
> partie de l'activité repose sur des offres à durée limitée, reçues chaque
> semaine » — outil IA de centralisation, budget 1 000–10 000 €

**Ces fiches sont scorées 10 à 25/100.** Pendant ce temps, une entreprise dont on
a simplement déduit que le site mérite une refonte obtient **65/100**.

Autrement dit : *une entreprise qui dit chercher un prestataire et chiffre son
budget vaut moins, dans le modèle actuel, qu'une entreprise dont on suppose
qu'un rafraîchissement lui serait utile.* C'est l'inverse de ce que vous demandez.

La cause n'est pas un bug de calcul, c'est un **choix de pondération** :
`public_need` pèse 10 points sur l'axe refonte et **rien** sur l'axe IA, alors
que `website_gap` en pèse 30 et `site_obsolete` 50.

**Pourquoi ces fiches n'ont-elles pas été contactées ?** Le porteur de l'annonce
est masqué par la plateforme : ni raison sociale, ni adresse. Le blocage est
réel — mais ce n'est pas une raison de les sous-scorer. Ce sont deux problèmes
distincts : **force du signal** et **contactabilité**. Le modèle actuel les
confond.

### B.2 Faux positifs — 3 fiches

Le score repose uniquement sur une preuve `sector_opportunity`, qui est une
déduction ou un fait de presse, pas un besoin observé :

| Fiche | Score | Preuve unique |
|---|---:|---|
| **Charme de l'Hêtre** | création **40** | « Depuis le 1er juillet, Chloé Poupinet a créé sa société » |
| **CERF Athletic Training** | refonte 5 | « l'objectif de la première année serait d'atteindre une centaine d'adhérents » |
| **Carot's** | 0 | « ont créé la société Carot's spécialisée dans… objets personnalisés » |

Une création d'entreprise est un **événement**, pas une opportunité commerciale.
Charme de l'Hêtre obtient 40/100 en création de site sur cette seule base : ce
n'est pas défendable devant le dirigeant.

### B.3 Faux négatifs — 12 fiches, et la cause est identifiable

Ce sont les fiches les plus intéressantes commercialement, et elles sont
**sous-évaluées sur le mauvais axe**. Leurs preuves sont réelles et bien
observées — le problème est leur **typage**.

| Fiche | Refonte | IA | Ce que dit la preuve |
|---|---:|---:|---|
| **Brasserie VDL** | 65 | **0** | « Commande uniquement par téléphone ! » |
| **Dance Center** | 65 | **0** | Inscriptions sur place, PDF à remplir, 3 chèques trimestriels |
| **SAM31** | 65 | **0** | Processus manuel équivalent |
| **La Bruchoise / Casa Blu** | 65 | **0** | idem |
| **Fromagerie et Baratte** | 65 | **0** | idem |
| **Base nautique de Picquigny** | 65 | 26 | Devis groupes par e-mail, paiements virement/chèque |
| **Restaurant Le Canotier** | 65 | 2 | idem |
| **Restaurant Goudale Orchies** | 65 | 2 | idem |
| **L'Occidentale** | 65 | 26 | idem |
| **Celtuce Traiteur** | 71 | 12 | idem |
| **SAS Maire** | 100 | 26 | idem |
| Centre Équestre de la Renarde | 35 | 0 | ⚠️ **en opposition — ne jamais recontacter** |

**Diagnostic technique.** Ces preuves sont typées `website_gap`. Elles
alimentent donc l'axe refonte à plein poids, et l'axe IA seulement via la
détection de motifs dans le texte. Or j'ai vérifié que le texte ne déclenche
rien :

```
Brasserie VDL   « commande uniquement par telephone »  → AUCUN signal
Dance Center    « les inscriptions ont lieu au … »     → AUCUN signal
Dance Center    « les 3 cheques correspondant aux … »  → AUCUN signal
Base nautique   « veuillez nous contacter … par email » → AUCUN signal
```

Le catalogue contient `commande par telephone` et `par telephone uniquement`,
mais **pas** `commande uniquement par telephone` : l'insertion de l'adverbe
casse la correspondance. Même fragilité sur les inscriptions sur place et le
règlement par chèques — que votre section C cite explicitement comme signaux
faibles à détecter.

**Ce ne sont donc pas des entreprises sans besoin : ce sont des besoins que
l'agent ne sait pas lire.** Une commande exclusivement téléphonique est un
besoin d'automatisation, pas un besoin de refonte graphique.

### B.4 À approfondir — 12 fiches

- **8 fiches de l'historique Gmail antérieur, 0 preuve** : Multitech Assistance,
  Garage Villedieu Automobiles, Le Serrurier d'A Cote, Superchi Architectes,
  L'Etabli du Menuisier, Quattro Architectes, The Architectes, Akla Architectes.
  Toutes scorées 5/5/0 en confiance **faible** — le modèle est honnête, mais ces
  fiches ne sont pas qualifiées. Elles sont déjà contactées : l'enjeu n'est pas
  de les relancer, il est de savoir s'il y a une suite commerciale.
- **SAS Maire** : refonte 100 mais domaine de l'adresse en `nxdomain`. Le score
  est élevé, l'adresse est morte. À vérifier avant toute décision.
- **Carot's**, **Beaujolais Réception** : pas d'adresse publique. Suivi
  téléphonique possible, pas de brouillon.

### B.5 Déjà suffisamment équipées — 8, écartées à juste titre

Styl'escalier (configurateur + devis en ligne), Top Cheval (boutique
opérationnelle), Cavaland (réservation en place), **L'Artisan Affûteur**
(Calendly temps réel, formulaire de tournée structuré, bon postal, tarifs
publiés), Livio Baldelli (réservation + paiement), Azur Toiture, Dose Paris
(compte pro structuré, 200+ clients pro), Caféophil.

**Ces rejets sont corrects et doivent être préservés.** Ils prouvent que le
filtre « déjà outillé » fonctionne. Aucune raison commerciale crédible de leur
vendre une prestation.

### B.6 Deux rejets potentiellement levables

| Fiche | Motif du rejet | Ce qui le lèverait |
|---|---|---|
| **Zicplace** (93) | « adresse e-mail non vérifiée sur les pages consultées » | 2 000 réparations/an, diagnostic en magasin seul. Vérifier l'adresse sur la page contact. |
| **O Lames Déchues** (95) | idem, + site en chantier | Gabarit non rempli, logos génériques. Vérifier l'adresse. |

Leur rejet tenait à une **limite de ma consultation**, pas à une absence
d'opportunité. Ce sont de faux négatifs du registre d'exploration.

### B.7 Preuve mal typée — 1 fiche

**Beaujolais Réception** : « Directeur de la publication : Kevin CANARD, Gérant »
est enregistré comme `public_need`. C'est une **identité de dirigeant**, donc un
`signal_confiance` — type qui n'existait pas au moment de la saisie (lot 8).
Cette erreur gonfle artificiellement le compte des besoins exprimés.

---

## Synthèse : ce que l'audit impose de corriger

Trois défauts, par ordre d'impact commercial décroissant :

1. **La hiérarchie des signaux est inversée.** Un besoin exprimé avec budget
   vaut 10 ; une lacune de site supposée vaut 65. Le modèle doit distinguer
   quatre niveaux — *exprimé*, *observé*, *indirect*, *hypothétique* — et les
   pondérer dans cet ordre. Il doit aussi séparer **force du signal** et
   **contactabilité**, aujourd'hui confondues.
2. **Le typage des preuves détermine l'axe, et il est faux sur 12 fiches.** Un
   processus manuel rangé en `website_gap` produit un besoin de refonte là où
   il y a un besoin d'automatisation.
3. **La détection par motifs est trop littérale.** Un adverbe inséré
   (« uniquement ») suffit à perdre le signal. Les signaux faibles que vous
   listez en section C — inscriptions manuelles, paiements par chèques, devis
   par e-mail — ne sont pas couverts.

Aucun score historique n'a été modifié. Les corrections seront tracées comme
une nouvelle évaluation, avec conservation des valeurs v7.1.

---

## État d'avancement de la Phase 10

| Section | État |
|---|---|
| A — Audit initial | **terminé** (ce document) |
| B — Audit des 78 fiches | **terminé** (ce document + JSON) |
| C — Intelligence de découverte | à faire |
| D — Moteur de scoring | **spécification reçue incomplète** |
| E et suivantes — lot 10, sécurité, livraison | **non reçues** |

Votre message s'interrompt à « *Score 1 : création de site web — Évalue
notamment :* ». Les critères des trois axes et les sections suivantes n'ont pas
été transmis. Je m'arrête ici plutôt que d'inventer vos critères de notation.

**Contraintes maintenues pendant tout l'audit :** pré-vol bloqué, aucun envoi,
aucune suppression, aucune fusion, sauvegarde préalable effectuée.
