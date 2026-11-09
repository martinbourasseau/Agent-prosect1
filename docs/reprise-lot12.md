# Reprise — Lot 12

**Lot :** `2026-11-03-lot12` · **Date de session :** 2026-11-03 · **Branche :** `arena/7ed6352a-agent-prosect1`
**CRM :** 108 → **120 fiches** · **Registre d'exploration :** 213 → **385 entrées**
**Tests :** 703 → **743, tous verts** · **Brouillons créés : 0** · **Envois : 0**

> **Convention de lecture.** Chaque affirmation est étiquetée **[Fait]** (observé
> dans une page récupérée ou dans un fichier du dépôt), **[Hypothèse]**
> (interprétation commerciale) ou **[Non vérifié]** (pas de page lue).
> Une information vue uniquement dans un résultat de moteur de recherche n'est
> jamais une preuve et n'a jamais produit de coordonnée importée.

---

## 1. Requêtes exécutées

**[Fait] 34 requêtes** `web_search` (depth 2), réparties sur les cinq familles
demandées — aucune famille n'a été traitée comme critère de qualification :

| Famille | Requêtes |
|---|---|
| Services (conseil, formation, BET, maintenance, nettoyage, recrutement) | 12 |
| Industrie / artisanat | 6 |
| Tourisme / loisirs | 6 |
| Commerce / distribution | 5 |
| Numérique / professionnel | 5 |

Liste complète, avec département visé et rendement observé, dans
`data/history/lot12-recherches-2026-11-03.json` → `requetes`.

**[Fait] Deux pièges de requête identifiés et documentés :**
- « métier + ville » renvoie massivement des **annuaires et des réseaux SEO à
  pages-villes**, pas des entreprises indépendantes (confirmé sur 34 requêtes).
- « solution » (GED, dématérialisation) ne renvoie que des **vendeurs** de
  solutions, jamais des acheteurs. Les 4 résultats de la requête
  « dématérialisation Territoire de Belfort » (Reproland, Deltic, DIMO, Numeria)
  ont été écartés avec ce motif explicite.

## 2. Pages lues

**[Fait] 46 tentatives de lecture ⇒ 39 réussies / 7 échouées.**
**22 sites officiels distincts lus en profondeur**, souvent sur 2 ou 3 pages
(accueil + contact + page métier).

Détail des 7 échecs — **aucun n'a produit de preuve** :

| Entreprise | URL | Cause |
|---|---|---|
| Assainissement Argentanais | `assainissement-argentanais-orne.fr` | page non récupérée |
| BKCS | `bkcs.fr` | page non récupérée |
| E.S.S. 37 | `ess37.fr/contact` | `AccessDenied` |
| Alcamparol | `alcamparol.com/contact/` (×2) | page non récupérée |
| — | 3 URL de proxy mal formées | erreur de l'agent, pas du site |

**[Fait]** Une URL de contact **devinée** (`alcamparol.com/contact-2/`) a renvoyé
404 : elle est comptée comme lue mais **ne prouve rien** et n'a servi à aucun
constat. Aucun CAPTCHA ni protection anti-robots n'a été contourné ; les
`AccessDenied` ont été acceptés comme tels.

## 3. Entreprises examinées

**[Fait] 173 entités examinées, dont 134 entreprises** (39 annuaires et
plateformes exclus du décompte) — **objectif indicatif 80-100 dépassé**.

| Décision de recherche | Nombre |
|---|---|
| Retenue et importée | **12** |
| Écartée avec motif | 118 |
| À approfondir | 2 |
| Non vérifiée (page non lue) | 2 |
| Annuaire / plateforme | 39 |

**[Fait]** Seulement **24 entités** ont fait l'objet d'une lecture officielle ;
**110 ont été vues en recherche seule**. Elles sont comptées comme *examinées*
(décision d'écarter prise et motivée) mais **aucune n'a produit de fiche**.

## 4. Départements et secteurs

**[Fait] 29 départements** parcourus : 02, 08, 09, 10, 11, 14, 16, 17, 19, 23, 25,
28, 37, 43, 48, 55, 61, 65, 66, 71, 73, 74, 75, 76, 80, 82, 85, 87, 90.
**11 départements** dans les fiches importées : 08, 09, 10, 16, 28, 55, 61, 65, 66, 71, 87.

**[Fait]** Aucun département ne dépasse le quart des entités examinées
(invariant vérifié par test). Secteurs importés : génie climatique, négoce de
bois, assainissement, hébergement insolite, parc de loisirs, traitement de
surface, équipement de boulangerie, expertise comptable, métallerie, nettoyage
professionnel, ébénisterie, bureau d'études structure.

## 5. Fiches importées

**[Fait] 12 fiches créées**, CRM **108 → 120**. Les **108 fiches antérieures ont
été vérifiées bit-à-bit inchangées** par assertion dans l'importeur.

| Entreprise | Dép. | Créa. | Refonte | IA | Prio. | Palier | Email |
|---|---|---|---|---|---|---|---|
| Laizeau Génie Climatique | 28 | 5 | 81 | 34 | 57 | à approfondir | non publié |
| Ajzenstein Louis et Associés | 08 | 5 | 73 | 0 | 65 | à approfondir | non publié |
| Alcamparol | 09 | 5 | 73 | 34 | 65 | à approfondir | non lu |
| L.C. Bois | 16 | 5 | 65 | 29 | 61 | moyenne | **oui, MX ok** |
| Kap'oupa Kap | 66 | 5 | 65 | 36 | 61 | à approfondir | non publié |
| Blanchefleur | 55 | 5 | 65 | 34 | 61 | à approfondir | non publié |
| TAM NET 87 | 87 | 5 | 65 | 12 | 61 | à approfondir | non publié |
| Tortora | 10 | 5 | 57 | 0 | 58 | à approfondir | publié, non importé |
| BETEP | 65 | 5 | 47 | 0 | 54 | moyenne | **oui, MX ok** |
| A.C.P.T. | 61 | 5 | 31 | 12 | 47 | à approfondir | non publié |
| MFMG | 08 | 5 | 57 | 0 | 34 | basse | **oui, MX ok** |
| Les Ateliers Genetier | 71 | 5 | 57 | 0 | 34 | basse | non confirmé |

**[Fait]** Aucune fiche n'atteint le palier **haute**. Ce n'est pas un réglage :
les défauts réellement observés sont ponctuels (liens cassés, bandeaux de
consentement en anglais, incohérences éditoriales) et non structurels.
**[Hypothèse]** Le rendement commercial de ce lot est faible ; il est reporté
tel quel plutôt que gonflé par des scores de complaisance.

## 6. Doublons

**[Fait] 1 doublon inter-lots détecté et non réinscrit : BET Sodeba**, déjà
écartée au lot 11 (`2026-11-09-lot11`). Le registre est passé de 213 à 385
(**+172** pour 173 entités), ce qui confirme le dédoublonnage par nom.

**[Fait] 1 doublon probable non résolu, volontairement non fusionné : FICOM /
HMC Conseil** — même adresse et même téléphone relevés en recherche. Règle
appliquée : *ne jamais fusionner sur la seule adresse* (précédents Multi Pneus 36
et CS Dépannages). Les deux sont écartées, aucune fiche créée.

**[Fait] Alias de domaines gérés sans créer de fiche séparée :** `mfmg.eu`
(site) / `mfmg.fr` (messagerie) ; `lc-bois.fr` (site) / `lcbois.fr` (messagerie).

**[Fait] Idempotence vérifiée :** une seconde exécution détecte **12 collisions**
et crée **0 fiche**. Aucune fusion, aucune suppression, aucun écrasement.

## 7. Besoins exprimés

**[Fait] 0 besoin exprimé.** Aucune des 22 entreprises lues ne demande
publiquement une prestation web, de refonte ou d'automatisation. Aucune preuve
`public_need` n'a été créée — un test l'impose sur tout le lot.

**[Fait]** Deux distinctions appliquées pour ne pas fabriquer de besoin :
- **HMC Conseil** vend de la « tenue, saisie et bilan comptable » : c'est une
  **prestation vendue**, pas un processus interne → écartée.
- **LGC** mentionne « deux assistantes administratives » : c'est un
  **effectif**, pas un processus documenté → aucun `processus_manuel` créé.

## 8. Opportunités probables

**[Fait] 12 opportunités directement observées** (une par fiche), toutes
adossées à une citation datée. Les plus solides :

- **LGC (28)** — site entièrement en images GIF et tableaux ; la page contact
  n'offre **ni formulaire ni e-mail**, seulement courrier, téléphone et fax,
  alors que l'entreprise vend des contrats d'entretien.
- **A.C.P.T. (61)** — « Après chaque intervention, nous établissons… un
  bordereau de suivi de déchets et une facture détaillée » : **processus
  documentaire répétitif publié**. **[Non vérifié]** : l'outil qui produit ces
  documents n'a pas été observé.
- **Alcamparol (09)** — « pour les réservations de groupe, merci de me contacter
  directement par mail pour recevoir les conditions… du contrat de location » :
  parcours manuel publié ; en plus, un lien public pointe vers
  `wp-admin/post.php?action=edit`.
- **L.C. Bois (16)** — les 4 raccourcis services de l'accueil pointent **tous
  vers la page d'accueil**.
- **Kap'oupa Kap (66)** — le Deval'Mountain est en « réservation uniquement par
  téléphone » alors que les autres activités ont une billetterie en ligne.

## 9. Répartition des trois scores

**[Fait]** Scores calculés par le moteur du dépôt (`v8`), **jamais retouchés**.
Les trois axes sont indépendants.

| Axe | min | max | moyenne | distribution |
|---|---|---|---|---|
| Création (`site_web`) | 5 | 5 | **5,0** | 5 × 12 |
| Refonte | 31 | 81 | **61,3** | 31×1, 47×1, 57×3, 65×4, 73×2, 81×1 |
| IA / automatisation | 0 | 36 | **15,9** | 0×5, 12×2, 29×1, 34×3, 36×1 |

**[Fait]** Création = 5 partout : **les 12 entreprises ont déjà un site**.
**[Fait]** IA > 0 sur **7 fiches seulement**, chacune adossée à une preuve
`processus_manuel` ou `parcours_incomplet` citée. Un test vérifie que deux
entreprises du même secteur (Blanchefleur 34 / Genetier 0) obtiennent des scores
différents **parce que leurs preuves diffèrent**, pas parce que leur secteur
diffère. **Le secteur n'entre nulle part dans le calcul.**

## 10. Priorité commerciale

**[Fait]** Moteur `v10-priority`, distinct des trois axes.
Valeurs **34 à 65**, moyenne **54,8**. Paliers : **haute 0 / moyenne 2 /
à approfondir 8 / basse 2**.

**[Fait]** Deux mécanismes de plafonnement ont joué :
- **9 fiches sans adresse exploitable** sont plafonnées à « à approfondir » :
  la valeur commerciale est conservée, mais l'entreprise n'est pas joignable.
- **3 fiches pénalisées par leurs contre-signaux** : MFMG −24, Genetier −24,
  LGC −11. Les deux premières passent en **basse** : leur défaut est cosmétique
  et leur parcours de devis fonctionne déjà.

**[Fait]** Portefeuille complet après import : 120 fiches, `priority_value`
moyenne 54,8, médiane 58 ; paliers haute 15 / moyenne 60 / à approfondir 25 /
basse 20 ; **41 fiches portent un contre-signal, 16 sont pénalisées**.

## 11. Emails vérifiés

**[Fait] 8 adresses publiées lues sur page officielle, 8/8 `mx_ok`**
(`data/history/lot12-dns-2026-11-03.json`) : `contact@mfmg.fr`,
`contact@hmcconseil.fr`, `contact@lcbois.fr`,
`contact@azur-nettoyage-limoges.fr`, `betep@betep.fr`,
`fred.tortora@tortora.fr`, `damianialpmetal@gmail.com`, `lordi@lordi.info`.

**[Fait] Seulement 3 sont importées** (MFMG, L.C. Bois, BETEP) : les 5 autres
appartiennent à des entreprises **écartées** ou à un cas litigieux.

**[Fait] Tortora : adresse publiée mais volontairement non importée.**
`fred.tortora@tortora.fr` est en ligne, mais l'accueil annonce une transmission
en 2021 à Frank Douet et Franck Pavie tandis que la page contact invite à joindre
« le dirigeant… Frédéric Tortora ». **[Non vérifié]** : le titulaire réel de la
boîte. Écrire à une personne qui a peut-être quitté l'entreprise n'est pas
justifiable ; la fiche est importée sans canal électronique.

**[Fait] Aucune adresse déduite d'un motif de domaine.** 9 fiches sur 12 n'ont
**aucune adresse publiée** ; ce manque est enregistré comme tel
(`email_verification="none"`), jamais comblé. **10 téléphones** publiés importés.
**[Fait]** Le MX prouve que le domaine accepte du courrier, **pas** que la boîte
existe : la mention figure dans chaque fiche (`email_verification_basis`).

## 12. Brouillons

**[Fait] 0 brouillon créé pour le Lot 12.** La règle est appliquée sans
exception : *pertinent + priorité haute + confiance suffisante + adresse
exploitable + pas de doublon + pas d'opposition*. **Aucune fiche n'atteint
« haute »** (§10), donc aucune ne franchit la première condition.

Motif enregistré fiche par fiche dans `brouillon_motif` :
- 9 × « aucune adresse publiée sur les pages lues » ;
- L.C. Bois et BETEP : « priorité moyenne, en dessous du seuil haute » ;
- MFMG : « priorité basse ».

**[Fait] Les 4 brouillons du Lot 11 sont intacts et non recréés** (`Label_9`,
file `pending`, campagne `2026-11-09-lot11`), vérifié par test. Les 2 brouillons
antérieurs (Caléo, Ripaud) sont également conservés. **Aucun envoi**, ni agent ni
Gmail : `send-log.json` inchangé (60 entrées, MD5 identique).

## 13. Entreprises prioritaires et justification

**[Fait] Aucune entreprise n'est prioritaire au sens du moteur.** Les trois
approches les plus défendables, si l'on devait approfondir :

1. **L.C. Bois (16)** — seule fiche du lot à cumuler *adresse publiée MX ok +
   confiance haute + défaut non cosmétique* (4 liens de service qui ne mènent
   nulle part). Valeur 61. **Action : relire une seconde page du parcours devis**
   pour confirmer l'ampleur avant tout contact.
2. **Alcamparol (09)** — valeur 65, processus de réservation de groupe
   explicitement manuel et lien d'administration exposé. **Blocage : aucune
   coordonnée électronique lue** (page contact inaccessible deux fois).
3. **A.C.P.T. (61)** — seul processus administratif répétitif réellement publié
   du lot (bordereau + facture après chaque intervention). **Blocage : ni
   e-mail ni téléphone publiés**, et mode de production non vérifié.

## 14. Rejets et motifs

**[Fait] 118 rejets motivés**, aucun rejet silencieux :

| Motif | Nombre |
|---|---|
| Annuaire seul, site officiel non lu | 32 |
| Réseau / chaîne / franchise (décision mutualisée) | 21 |
| Autre / non localisé dans le département visé | 18 |
| Association, organisme public, hors B2B | 12 |
| Réservation ou commande en ligne aboutie | 7 |
| Non approfondi (temps / priorité) | 6 |
| Gabarit SEO à pages-villes | 5 |
| Taille ou maturité hors cible TPE | 5 |
| Site déjà correct, aucun défaut exploitable | 4 |
| Vendeur de solution et non acheteur | 4 |
| Prestataire du même métier (pertinence offre faible) | 2 |
| Doublon probable non résolu | 1 |
| Source professionnelle seule, non vérifiée | 1 |

**[Fait] 4 faux défauts évités**, qui auraient produit des fiches injustifiées :
compteurs à 0 sur E.S.S. 37, Azur et VT Prévention (**artefact de lecture sans
JavaScript**), placeholders `{vendor_count}` / `{title}` du gestionnaire de
consentement, et tarif périmé dans l'index de Kap'oupa Kap (38 € vs 42 € partout
ailleurs). **Aucun n'a été retenu comme preuve.**

## 15. Meilleures sources

**[Fait] Rendement sur les 385 entrées du registre** (qualifiées / examinées) :

| Source | Examinées | Qualifiées | Taux brut |
|---|---|---|---|
| **site_officiel** | 142 | 30 | **21,1 %** |
| registre_public | 2 | 0 | 0 % |
| page_professionnelle | 15 | 0 | 0 % |
| annuaire_pro | 97 | 0 | 0 % |
| autre | 129 | 0 | 0 % |

**[Fait] Le site officiel est la seule source à rendement non nul**, confirmé
sur trois lots consécutifs. **[Hypothèse]** Les requêtes orientées « métier +
ville » devraient être abandonnées au profit d'un accès direct aux sites
d'entreprises déjà identifiées, ou de registres publics.

## 16. Bugs trouvés et corrections

**[Fait] 6 corrections, toutes couvertes par un test de régression :**

1. **Alias de domaine bloquant la fiche canonique** — `domain in alias` rejetait
   MFMG et L.C. Bois dès la première simulation alors qu'**aucun doublon
   n'existait**. Corrigé : l'alias ne sert qu'à *ramener* un domaine secondaire
   à son canonique pour le comparer à l'existant.
2. **Statut MX perdu par la casse** — le relevé DNS portait « L.C. BOIS », la
   fiche « L.C. Bois » : la clé ne correspondait pas, le statut MX était vide et
   la priorité plafonnée à tort. Corrigé par normalisation des deux côtés.
3. **Caractère CJK parasite** dans une preuve (« captcha图像 ») et deux coquilles
   de rédaction. Nettoyés ; un test interdit désormais tout caractère CJK.
4. **Vocabulaire de décision scindé dans le dashboard** — le lot écrivait
   `ecartee` / `importee` là où le registre utilisait `écartée` / `retenue`,
   produisant **7 catégories au lieu de 4** (« écartée 93 » + « ecartee 117 »).
   Corrigé par table de traduction à l'import ; les **172 entrées du lot 12**
   ont été normalisées, les **213 antérieures vérifiées intactes**.
5. **Deux tests du Lot 11 figeaient des compteurs cumulatifs** (`registre_apres
   == 213`, `len(anciennes) == 92`) et cassaient dès le lot suivant. Réécrits sur
   des **invariants** : le lot 11 est présent en entier, le total n'a pas
   régressé, et **toutes** les fiches du portefeuille restent en axes `v8`.
6. **Nom de méthode de test invalide** (espace dans `def`) : erreur de syntaxe
   corrigée avant exécution.

**[Fait] Incohérence préexistante signalée, non corrigée :** les lots 1 à 11
portent des dates du 2026-11-03 au 2026-11-09, postérieures ou égales à la date
de session. Ces fiches étant protégées, **aucune n'a été modifiée** ; le Lot 12
est daté du 2026-11-03, date de la session courante.

## 17. Tests

**[Fait] 743 tests, tous verts** (`python3 -m unittest discover tests -q`, ~4 s),
contre 703 avant le lot : **+40 tests** dans `tests/test_lot12.py`, 5 classes.

Couverture ajoutée : exhaustivité et honnêteté du journal de recherche ;
validation, datation et sourçage de chaque preuve ; contre-signaux typés pour
être **réellement lus** par le moteur et **réellement pénaliser** ; interdiction
d'un score IA sans processus publié ; interdiction d'un besoin exprimé fabriqué ;
interdiction d'une adresse déduite ; limite de 70 caractères sur les sujets ;
dédoublonnage et alias ; intégrité des données protégées.

**[Fait] Aucun compteur de portefeuille n'est figé** dans les nouveaux tests :
les effectifs sont recalculés, seules les règles sont assertions.

## 18. Tableau de bord

**[Fait]** Serveur arrêté puis relancé pour charger le code et les données
courants (`python3 -m prospecto.server`, port 8787), puis vérifié par `curl`
authentifié (`POST /login` form-urlencoded) :

- **Portefeuille : 120** fiches · qualifiés 29 · emails vérifiés 78 · téléphones 40
- **Exploration : 385** — écartée 210 / annuaire_seul 79 / retenue 45 / approfondir 51
- **Lot 12 :** 12 prospects, haute 0, moyenne 2, à approfondir 8, 3 emails
  vérifiés, **0 brouillon, 0 envoyé, 0 rebond**
- **Lot 11 :** 16 prospects, haute 7, **4 brouillons**, 0 envoyé — *inchangé*
- **Pipeline :** brouillons 6 / en attente 1 / **envoyés 68**
- **Campagne :** `enabled=false`, `dry_run=true`

**[Fait]** Les trois compteurs restent **strictement séparés** : envois hors
agent (8, statut `contacté`), envois agent (60 journalisés) et brouillons (6) ne
sont jamais additionnés. Aucun taux n'est calculé à partir d'un champ absent.

## 19. Journaux, sauvegardes et pré-vol

**[Fait] Sauvegarde vérifiable prise AVANT toute écriture :**
`/tmp/sauvegarde_lot12/data/` (272 fichiers), `/tmp/crm_avant_lot12.json`,
empreintes `/tmp/protected_lot12.md5` (7 fichiers).

**[Fait] Contrôle avant/après — les 5 fichiers sensibles sont intacts :**

| Fichier | Avant | Après |
|---|---|---|
| `data/history/send-log.json` | `96d33afc…` | **identique** |
| `data/history/reconciliations.json` | `ee0b74c4…` | **identique** |
| `data/campaigns/v4-settings.json` | `040b96bc…` | **identique** |
| `data/suppression.json` | `3e03b578…` | **identique** |
| `data/queue/validation_queue.json` | `c1c30e7e…` | **identique** |
| `data/crm/prospects.json` | `4f4fe3b1…` | modifié (12 créations, attendu) |
| `data/history/exploration-ledger.json` | `6f92254b…` | modifié (+172, attendu) |

**[Fait] Pré-vol exécuté sur une copie isolée** (`tempfile`), jamais sur la
configuration de production, car `Sender.preflight()` persiste
`dns.last_checked_at`. Résultat **`(False, 3 motifs)`**, inchangé :
1. « Campagne non activée (enabled=false). Activation explicite requise. »
2. « DKIM non détecté pour le domaine expéditeur. »
3. « Domaine expéditeur gratuit (Gmail (gratuit)) : prospection de masse
   déconseillée/interdite par les CGU. »

**[Fait]** La configuration réelle a été comparée octet à octet après le
pré-vol : **inchangée**. Le 3ᵉ motif reste le blocage de fond ; il n'a été
contourné d'aucune manière.

**[Fait] Oppositions respectées :** `celarenarde@gmail.com` (Nicolas Smets) et
`contact@severine-lesourd.com` (rebond dur) toujours dans la liste de
suppression, vérifié par test. Aucune des 12 fiches n'y figure.

**[Fait] Aucun envoi réel, aucun Gmail, aucun SMTP, aucun achat, aucun
abonnement, aucune modification DNS, aucune suppression de journal, aucun
contournement de challenge anti-bot.**

**Journaux produits :**
- `data/history/lot12-recherches-2026-11-03.json` — 34 requêtes, 46 lectures, 173 entités
- `data/history/lot12-dns-2026-11-03.json` — 8 vérifications MX
- `data/history/lot12-import-2026-11-03.json` — 12 créations, collisions, doublons
- `scripts/lot12/{journal,fiches,importer}.py` — reproductibles, simulation par défaut

**[Fait]** Une coquille vide créée en début de session
(`lot12-recherches-partiel-2026-11-03.json`, deux clés `note` et `date`, aucun
constat) a été retirée : elle est remplacée par le journal complet ci-dessus.
**Aucun journal de production n'a été supprimé.**

---

## Ce qu'il reste à faire

**[Fait]** 2 fiches « à approfondir » (ATS 55, MG02) : sites corrects, aucune
adresse publiée, processus non documenté.
**[Fait]** 2 entités « non vérifiées » (Assainissement Argentanais, BKCS) :
page non récupérée, à relire.
**[Hypothèse]** Pour obtenir des opportunités « haute », il faut changer de
méthode de sourcing : les requêtes « métier + ville » ont un rendement nul en
entreprises indépendantes. Les 32 « annuaire seul » de ce lot sont des pistes
reprenables **à condition de lire le site officiel** — jamais d'importer
l'annuaire comme preuve.
