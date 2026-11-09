# Phase 10 bis — rapport final

**Date :** 2026-11-07 · **Branche :** `arena/7ed6352a-agent-prosect1`
**Aucun envoi par l'agent.** `enabled=false`, `dry_run=true`, pré-vol bloqué.
**Aucune modification DNS, aucun achat, aucune souscription, aucune suppression.**

---

## À lire en premier : deux prémisses du brief étaient fausses

### 1. Il ne restait pas 10 brouillons — 8 avaient été envoyés

Le brief annonçait « 10 brouillons en attente ». La vérification réelle montre
que **8 de ces brouillons ont été envoyés depuis Gmail le 9 novembre 2026,
entre 12:22:30 et 12:23:17** : les 5 du lot 10 (`Label_8`) et 3 du lot 9
(`Label_7`). Ils portent aujourd'hui le libellé `SENT`.

**Ces envois ne sont pas le fait de l'agent.** `enabled=false` et `dry_run=true`
sont restés actifs, et le journal de production compte toujours 60 entrées.
Il s'agit d'une action côté utilisateur, réconciliée additivement.

**Il reste 2 brouillons** : Caléo (`Label_7`) et Pépinières Ripaud (`Label_6`).

**Comment je l'ai établi, et le piège évité.** Deux requêtes ont renvoyé **0
avec `complete:true`** alors que les messages existaient :
`label:Prospection/2026-11-07-lot10` (nom imbriqué) et le filtre
`label_ids=["Label_8"]` combiné à `in:drafts`. Conclure « les brouillons ont
disparu » aurait été une erreur grave. La vérité est venue de `in:anywhere`
sur les destinataires, qui a montré les 8 messages en `SENT`.
**Un zéro sur une requête filtrée ne prouve jamais une absence.**

### 2. `Label_8` était le bon libellé — il n'y avait rien à corriger

Le brief demandait de vérifier l'écart entre `Label_8` et
`Prospection/2026-11-07-lot10`. **Il n'y a pas d'écart.** `list_labels` renvoie
`Label_8` → nom `Prospection/2026-11-07-lot10`. Gmail attribue des identifiants
opaques ; `Label_8` **est** le libellé attendu. Aucun reclassement n'a été
effectué, aucun brouillon recréé.

---

## 1. Recherches

### Périmètre de recherche : objectif atteint

**29 structures examinées** là où il en restait 27 à traiter. Aucune des
recherches des passes précédentes n'a été rejouée.

| Décision | Nombre |
|---|---:|
| Retenues et importées | **4** |
| Écartées | **6** |
| À approfondir | **19** |

**11 sites réellement ouverts et lus**, dont 5 avec assez de matière pour
importer. Les 19 « à approfondir » portent chacune l'étape manquante précise.

**5 fiches importées au total** (4 du périmètre + ERM 27 de la section C) :

| Entreprise | Dépt | Scores (site/refonte/IA) | Priorité v9 |
|---|---|---|---:|
| Scierie Labrue | 19 | 5 / 89 / 12 | haute 71 |
| Menuiserie Mirolo | 02 | 5 / 89 / 0 | haute 71 |
| D2Bois | 02 | 5 / 81 / 12 | moyenne 68 |
| ERM 27 | 27 | 5 / 89 / 0 | haute 71 ⚠ |
| Delahautemaison | 84 | 5 / 47 / 0 | moyenne 54 ⚠ |

⚠ = contre-signaux dominants, marquée « revue humaine requise » (voir §6).

**Preuves les plus nettes :** D2Bois publie encore une **icône Google+**,
service fermé en avril 2019. La Scierie Labrue affiche un panneau de
consentement **entièrement en anglais** qui prétend n'utiliser aucun cookie
soumis à consentement tout en listant Google Analytics.

**Les 6 rejets sont des contre-signaux, pas des absences de signal :** Lanoy
Couverture (formulaire qualifiant déjà adresse + 15 prestations), LOC'B,
Hublo (application mobile et créneaux en ligne), Easypro (e-commerce complet),
Blanc Comme Neige (commande en ligne), Proesa (cabinet de recrutement, client
non identifiable). Une entreprise bien outillée n'est pas un prospect.

**2 erreurs de département corrigées**, preuves à l'appui : Menuiserie Mirolo
`68 → 02` (Saint-Quentin), AZ Menuiseries `68 → 60` (Sempigny).

### Registre d'exploration : 27 entrées ouvertes reprises

Travail effectué sur les entrées les plus tractables, avec vérification et non
supposition :

- **D2Bois (02)** : site officiel trouvé et lu, adresse vérifiée → **qualifiée**.
- **Menuiserie Mirolo (02)** : idem → **qualifiée**, département corrigé.
- **AZ Menuiseries (60)** : site lu, département corrigé, défauts forts relevés
  → **reste ouverte**, adresse non lue.
- **Travaux Obat** : **clôturée avec preuve** — Obat est un éditeur de logiciel
  SaaS de devis/facturation (21 000 clients, offre « Studio : site internet »,
  devis vocaux par IA). **Concurrent direct**, pas un prospect.

Les entrées restantes conservent leur étape manquante. **Aucune n'a été
transformée en fiche CRM par défaut** : le registre (131 entrées) et le
portefeuille (92 fiches) restent deux objets distincts, avec un test qui
verrouille cette séparation.

---

## 2. Les deux opportunités prioritaires

### La Châtaigneraie de Bel Air (23) — approfondir, pas de brouillon

**Identité :** LA CHATAIGNERAIE DE BEL AIR, 7 Le Theilloux, 23230
Bord-Saint-Georges, 06 19 55 23 67. Deux pages lues directement.

**L'avis est bien réel, mais il n'est pas daté.** « Un peu déçu que sa répond
pas au téléphone quand on appelle » figure dans un carrousel d'avis Google
(Trustindex) **sur le site de l'établissement**, au milieu de 8 avis très
positifs. **Aucune date n'est affichée.** Conformément à votre avertissement,
un avis non daté ne prouve pas une difficulté actuelle : ce signal est
consigné comme **témoignage client non daté**, pas comme problème courant.

**Le signal solide est ailleurs, dans le parcours.** Le formulaire de la page
Contact & réservation est destiné à « toute demande de réservation » mais ne
demande que **Nom, Téléphone, Email, Message** : ni dates de séjour, ni nombre
de chiens, ni gabarit, ni vaccination. L'accueil confirme que la réservation
« peut se faire par téléphone ou e-mail ». Chaque réservation exige donc un
échange manuel de cadrage.

**Analyse de la solution :** un **formulaire de réservation qualifié** est la
réponse la plus directe et la moins coûteuse. Un **agent IA n'aurait de sens
qu'après** ce formulaire — automatiser un cadrage inexistant n'apporte rien.
Un accusé de réception automatique traiterait le symptôme « on n'arrive pas à
vous joindre ».

**Pourquoi aucun brouillon :** l'adresse `contact@lachataigneraiedebelair.fr`
apparaît dans l'index de recherche de la page officielle, mais **elle est
absente de mes deux lectures directes**. Non confirmée ⇒ pas de contact.
L'étape suivante est écrite : relire la page dans un navigateur complet.

### ERM 27 (27) — qualifiée, mais besoin modeste et pas de brouillon

**Identité complète vérifiée :** ERM27, **SIRET 33215991200085**, 38 rue du
Coudray, 27240 Sylvains-les-Moulins, 02 59 43 12 33, `erm27@erm27.fr` **lu en
clair**. Trois pages lues.

**Le besoin est faible, et je le dis.** Le seul défaut directement constaté
est un bandeau de **consentement implicite** (« nous supposerons que vous en
êtes satisfait ») et des mentions légales citant la directive 95/46/CE,
abrogée. À l'inverse : contenu technique riche et à jour, et **un prestataire
web déjà crédité** (My Market Office) dans les mentions légales.

**Les horaires contradictoires** évoqués au lot précédent **n'ont pas été
retrouvés** dans les pages lues : signal **abandonné**, pas reporté.

**Décision :** fiche conservée, **aucun brouillon**. Ni refonte ni agent IA ne
sont justifiés par les preuves actuelles. La fiche est marquée « revue humaine
requise » car son score est surévalué (§6).

---

## 3. Découverte commerciale : changement de méthode

### Le diagnostic, et pourquoi plus de mots-clés n'y changent rien

Les agences rédigent leur argumentaire **en citant les mots du prospect**
(« votre site ne vous ramène aucun client »). Un motif lexical côté client
capture donc la page du vendeur. **Le texte fautif est une citation, pas une
erreur de requête** : aucune exclusion ne peut le corriger.

### Le déplacement : classer l'auteur, pas le vocabulaire

Nouveau module **`prospecto/discovery.py`**, avec **25 tests** dont deux
régressions construites sur les pages d'agences réelles qui avaient fait
échouer la méthode (Expressweb, Structolabs). Six classes :

`demande_directe_entreprise` · `probleme_directement_observe` ·
`temoignage_client_publie` · `signal_indirect` ·
`argumentaire_commercial_tiers` · `hypothese_non_verifiee`

**Le statut de vendeur est évalué en premier et il est éliminatoire.** Seule
une `demande_directe` peut porter un besoin « exprimé ». Un témoignage client
prouve une friction, **pas une intention d'achat**.

Le module détecte aussi 9 familles de problèmes opérationnels : formulaire
fermé, demande sans qualification, réservation téléphonique seule,
coordonnées incohérentes, lien `email:` au lieu de `mailto:`, adresse inversée,
consentement implicite. **Aucune ne marque `proves_purchase_intent`** : un
problème observé n'est pas une intention d'achat.

### Rendement : la définition exacte, avant toute comparaison

**Vous aviez raison de demander la vérification.** Les chiffres « 0,352 » et
« 0,029 » **ne sont pas des taux de qualification** : ce sont les `yield_score`
de `planner.py`, des **moyennes a posteriori** :

```
yield_score = (qualifiés + 8 × 0,15) / (examinés + 8)
```

Le lissage **écrase les grandes séries nulles** (34 examens, 0 qualifié donne
0,029 et non 0) et **remonte les petites séries**. Comparer ce nombre à un taux
brut, ou à un chiffre calculé sur un autre périmètre, est une erreur de
lecture. `SourceYield` porte désormais la méthode avec le nombre et
**refuse la comparaison** entre méthodes différentes.

**Rendement réel, même méthode de comptage pour toutes les sources :**

| Source | Examinées | Qualifiées | **Taux brut** | Taux lissé |
|---|---:|---:|---:|---:|
| **site_officiel** | 70 | 17 | **0,243** | 0,233 |
| autre | 13 | 0 | 0,000 | 0,057 |
| page_professionnelle | 14 | 0 | 0,000 | 0,055 |
| **annuaire_pro** | 34 | 0 | **0,000** | 0,029 |

**À conserver :** les sites officiels, seul canal à avoir produit des
prospects. **À abandonner :** la recherche lexicale de besoin exprimé
(2 tentatives, 0 prospect) et les annuaires seuls (34 examens, **0** qualifié).

**Limite honnête sur le canal recrutement :** testé dans cette passe, il
souffre du **même défaut d'auteur** quand il passe par des agrégateurs
(Indeed, Ouest-France emploi) ou des cabinets. Il n'est exploitable que si
l'entreprise publie elle-même — et il faut alors viser son site, pas la boîte
de recrutement nominative.

---

## 4. Gmail

| Mesure | État réel |
|---|---:|
| Brouillons restants | **2** (Caléo, Ripaud) |
| Brouillons envoyés hors agent le 09/11 | **8** |
| Réponses humaines nouvelles | **0** |
| Réponses automatiques nouvelles | 0 |
| Rebonds nouveaux | **0** |
| Oppositions nouvelles | **0** |
| Challenges nouveaux | 0 |

**Classement par lot vérifié :** `Label_8` = lot 10, `Label_7` = lot 9,
`Label_6` = lot 8. Correct, rien reclassé.

**`check_email_v4` exécuté sur les 5 messages du lot 10 : 5/5 conformes**
(124 à 137 mots, signature exacte, mention d'opposition présente dans chacun).
Contrôle a posteriori : ils ont été envoyés hors agent, **aucun n'a été
modifié**. Archive `audit-brouillons-contenu-2026-11-07.json`.

**Conversation des 8 destinataires :** requête `in:anywhere` incluant spam et
corbeille, `complete:true` → **aucune réponse, aucun rebond**. Le seul rebond
connu reste celui du 04/11 (`severine-lesourd.com`).

**Protections :** opposition **Nicolas Smets / Renarde maintenue** (statut +
liste de suppression, 2 entrées). **Challenge Mailinblack non validé.**
Aucune demande commerciale ⇒ aucun brouillon de réponse nécessaire.

**Délivrances :** 3 confirmées, **56 non confirmées** — et non 55 comme
indiqué au brief. Rappel : *non confirmée* ≠ *échec*.

---

## 5. Délivrabilité

Détail complet dans **`docs/delivrabilite-phase10bis.md`**. L'essentiel :

**Les 3 motifs réels du pré-vol**, reproduits sur une copie isolée :

1. Campagne non activée (`enabled=false`) — voulu.
2. **DKIM non détecté** pour le domaine expéditeur.
3. **Domaine expéditeur gratuit (Gmail)** : prospection de masse proscrite par
   les CGU.

**Le blocage de fond est le troisième.** L'envoi se fait depuis une adresse
`gmail.com` gratuite : les enregistrements SPF/DKIM/DMARC de ce domaine
appartiennent à Google, il est **impossible d'y aligner votre marque**. Un
domaine professionnel dédié n'est pas une optimisation, c'est un **prérequis**.
Et la restriction des CGU est légitime : **elle n'a pas été contournée**.

**Solution économique recommandée :** un domaine dédié (**~10–15 €/an**) +
un service d'envoi à offre gratuite type Brevo (~300 messages/jour).
**Coût récurrent d'envoi : 0 €.** Comparatif de 5 options dans le document,
avec Amazon SES (~0,10 $/1 000) moins cher au volume mais exigeant de
construire la gestion des rebonds.

**Second problème, distinct :** le dispositif **n'instrumente pas la
délivrance** — 3 confirmations sur 60. Corriger l'authentification sans
corriger la mesure, c'est envoyer mieux sans savoir si cela marche.

**Plan en 7 étapes** avec un **critère d'arrêt objectif** chacune
(en-têtes `spf/dkim/dmarc=pass` **lus**, webhook produisant une entrée
« délivré », pré-vol `(True, [])`, puis montée en charge 10–20/jour).
**Règle tenue : un domaine n'est jamais déclaré prêt sur sa configuration,
seulement sur des en-têtes lus et un cycle remise/rebond mesuré.**

---

## 6. Fiabilité

**557 tests, tous verts** (533 → 557, +24). 25 tests de découverte, 24 de
phase 10 bis, moins les ajustements d'invariants.

| # | Contrôle | Résultat |
|---|---|---|
| 1 | Scores v8 indépendants | **92/92 en v8** |
| 2 | Priorité v9 distincte | **92/92 en `v9-priority`** |
| 3 | Doublons | **0** (garde à l'import par domaine et adresse) |
| 4 | Adresses e-mail | 5/5 nouvelles lues directement, `mx_ok` |
| 5 | Oppositions / suspensions | 1 opposition, liste de 2, intactes |
| 6 | Brouillons | 2 restants + 8 envoyés réconciliés |
| 7 | Rapprochements Gmail | **4 → 5 entrées**, additif |
| 8 | Journaux de production | **3/4 MD5 identiques** ; `reconciliations.json` **+1 entrée par conception** |
| 9 | Intégrité SQLite | **sans objet : aucune base**, CRM en JSON |
| 10 | Dashboard | HTTP 302, API **92 fiches / 13 qualifiables / v9** |
| 11 | Envois bloqués | pré-vol `(False, 3)`, `enabled=false` |

### Défaut de scoring vérifié — mesuré, non corrigé

**`MATURITY_FACTOR = 0.8` est documenté mais ne s'applique qu'aux
automatisations détectées par le moteur.** Une preuve typée
`maturite_existante` écrite à la main **ne réduit aucun axe** et laisse
`counter_signals` vide.

Conséquence : **ERM 27 obtient `refonte 89 / haute 71`** alors que son seul
défaut est un bandeau de consentement et que son contenu est à jour avec un
prestataire web en place.

**16 fiches** portent un contre-signal explicite, dont **5 en priorité
haute** ; l'écart simulé atteint **18 points** sur un axe.

**Je n'ai pas recalibré.** Vous avez demandé de ne pas modifier les
coefficients arbitrairement, et une recalibration exige le protocole de la v9
(simulation, avant/après sur tout le portefeuille, revue des faux
positifs/négatifs, archive). J'ai donc : **mesuré en lecture seule**, archivé
(`simulation-contre-signaux-2026-11-07.json`), et **marqué 2 fiches « revue
humaine requise »** pour que la priorité ne soit pas consommée aveuglément.
**Aucun score modifié.**

### Trois invariants de test corrigés, pas assouplis

Trois tests affirmaient que des fiches étaient « qualifiables ». Or
`qualified` signifie **éligible à une nouvelle approche** : devenu faux à
juste titre après les envois du 09/11. Les tests vérifient désormais
l'invariant durable — **l'absence de blocage de qualité** — au lieu d'un état
courant appelé à changer.

### Limite du tableau de bord, à signaler

L'API affiche **60 envois** (journal de production). Les **8 envois hors agent**
sont au journal des rapprochements et **ne sont pas inclus** dans ce total.
**Total observé : 68.** Je n'ai pas modifié `send-log.json`, fichier protégé.
Le tableau de bord sous-estime donc les envois réels ; à corriger en lisant les
deux journaux.

---

## 7. Git

Branche `arena/7ed6352a-agent-prosect1`, depuis `e68eb8e`. Commits de cette
passe : découverte par auteur, recherches B1/B2/C, contre-signaux,
réconciliation des 8 envois, plan de délivrabilité, tests, rapport.
**Aucune fusion automatique. Aucun secret commité.**

Archives produites : `phase10bis-recherches-2026-11-07.json`,
`simulation-contre-signaux-2026-11-07.json`,
`audit-gmail-phase10bis-2026-11-07.json`,
`audit-brouillons-contenu-2026-11-07.json`.
Documents : `docs/delivrabilite-phase10bis.md`, ce rapport,
`docs/reprise-phase10.md` mis à jour.

---

## 8. Conclusion

**La Phase 10 est terminée sur son périmètre de recherche.** Objectif atteint
(29 ≥ 27), les deux opportunités prioritaires instruites avec une décision
motivée chacune, la méthode de découverte remplacée et testée, les brouillons
audités, la réconciliation faite, le plan de délivrabilité prêt.

**État final : CRM 92 fiches, 13 qualifiables, 47 départements, registre 131
entrées, 2 brouillons en attente, 557 tests verts, 0 envoi par l'agent.**

### Ce qui reste bloquant

1. **Le domaine d'envoi.** `gmail.com` gratuit ne peut pas porter de
   prospection authentifiée. Rien ne partira proprement avant sa création.
   **Décision et dépense : à vous.**
2. **La mesure de la délivrance.** 3 confirmations sur 60 : sans webhooks, le
   rendement restera inconnu même avec un domaine parfait.
3. **Le défaut des contre-signaux.** 5 fiches en priorité haute sont
   probablement surévaluées. Corriger demande une recalibration tracée et
   votre accord.

### Trois recommandations

**1 — Décidez du domaine, puis instrumentez avant d'envoyer.** Domaine +
offre gratuite (~10–15 €/an, 0 € d'envoi), quatre enregistrements DNS, puis les
webhooks. Ne validez les 2 brouillons restants qu'après un pré-vol
`(True, [])` **obtenu sur de vrais en-têtes**. C'est le seul chemin qui
débloque réellement.

**2 — Faites la recalibration des contre-signaux avant tout nouveau lot.**
La simulation est prête et l'écart est chiffré (18 points, 16 fiches, 5 en
haute). Sans elle, l'agent continuera à mettre en avant des entreprises bien
outillées — exactement l'inverse de l'objectif commercial.

**3 — Cherchez les demandes exprimées là où l'auteur est identifiable.**
Le canal recrutement testé ici échoue pour la même raison que la recherche
lexicale : l'auteur n'est pas l'entreprise. Les **appels d'offres et marchés
publics** sont le seul canal où une organisation publie une demande signée,
datée, avec un budget. C'est le prochain chantier de découverte, pas un
nouveau jeu de mots-clés.

**Le Lot 11 n'a pas été lancé.**
