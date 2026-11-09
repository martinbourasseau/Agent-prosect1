# Phase 10 finale — rapport d'exécution

**Objet :** fiabilisation du CRM, du scoring, de la délivrabilité, et ouverture
d'un nouveau canal (marchés publics).
**Date de référence des données :** 9 novembre 2026.
**Branche :** `arena/7ed6352a-agent-prosect1`.

**Ce qui n'a pas été fait, et qui était interdit :** aucun e-mail de prospection
envoyé par l'agent, aucune campagne, aucun achat, aucune souscription, aucune
modification DNS, aucun challenge validé, aucune suppression de données, aucune
opposition ignorée, aucun faux prospect. `enabled=false` et `dry_run=true` sont
inchangés du début à la fin. **Le Lot 11 n'a pas été lancé.**

Les chiffres du brief ont été traités comme des références à vérifier. Trois
d'entre eux étaient faux ; les corrections sont signalées ci-dessous.

---

## 1. Tableau de bord et rapprochement de la production

### Totaux

| Mesure | Avant | Après | Origine du changement |
|---|---:|---:|---|
| Messages sortis | 60 | **68** | 8 messages partis de Gmail hors agent, rapprochés |
| Journal de production | 60 | **60** | **inchangé, MD5 identique** |
| Délivrances confirmées | 3 | **3** | aucune preuve nouvelle |
| Délivrance non confirmée | 56 | **63** | les 8 rapprochés sont sans preuve de remise |
| Doublons écartés | — | **37** | dédoublonnage par identifiant |
| Fiches CRM | 92 | **92** | aucun ajout |
| Tests | 557 | **670** | +113 |

**Correction du brief :** il annonçait 68 envois pour 55 délivrances non
confirmées. Le journal de production ne contient que **60** entrées. Les 68 ne
s'obtiennent qu'en ajoutant les 8 messages réellement partis de Gmail le 09/11
hors agent. **Aucune ligne n'a été ajoutée au journal pour atteindre 68** : la
consolidation lit deux sources et les garde distinctes.

### Les huit messages hors agent

Étanchéité Nantaise, Alain Louis, Atelier du Bourrelier, Zicplace, O Lames
Déchues, Cordes et Âme, Froger Étanchéité, Cordonnerie Canfora David — tous
`SENT` dans Gmail le 09/11, fiches CRM passées à `contacté`, identifiants de
message conservés dans `data/history/reconciliations.json`.

**Envoyé hors agent n'est pas envoyé par Prospecto.** Le tableau de bord affiche
la provenance : « 60 au journal de production, 8 constatés dans Gmail et
rapprochés ».

### Onze catégories, sans double compte

Préparés **73** · brouillons Gmail **2** · envoyés **68** · acceptés par le
fournisseur **68** · délivrées confirmées **3** · non confirmées **63** ·
rebonds **1** · challenges **1** · réponses humaines **1** · réponses
automatiques **2** · oppositions **1**.

Deux contrôles d'exclusivité sont affichés et vérifiés par les tests :
les étapes du portefeuille totalisent 92 fiches ; confirmés + non confirmée +
rebonds + challenges = 68. **Les catégories de réponse se recouvrent** (une
opposition est aussi une réponse humaine) et ne s'additionnent pas — c'est écrit
à l'écran.

### Deux régressions du tableau de bord, trouvées et corrigées

1. **La colonne « Brut » du rendement affichait `NaN %`.** Elle lisait
   `p.raw_rate`, champ inexistant (le vrai nom est `qualification_rate`). Défaut
   ancien, jamais visible dans un test qui se contentait de chercher du texte.
2. **Le script entier ne se chargeait plus.** Un mélange `??` / `||` sans
   parenthèses, **introduit par moi au §B**, est une `SyntaxError` en JavaScript :
   toutes les fonctions de rendu étaient mortes. Corrigé.

Ces deux défauts ont motivé un changement de méthode de test (§6).

Trois indicateurs ajoutés : **moyenne 52,7 et médiane 58** de la priorité
commerciale, contre-signaux par force, et pilote marchés publics en registre
distinct. Les libellés « brouillons » ont été désambiguïsés : « Fiches au statut
brouillon » (3, lecture CRM) et « Brouillons Gmail en attente » (2, lecture file)
portaient le même nom pour deux nombres différents.

---

## 2. Scoring et priorité commerciale

**16 fiches** portant un besoin exprimé ont été auditées une par une. Les
**trois axes v8 n'ont pas été modifiés** — contrôle automatisé : 0 axe altéré sur
92 fiches.

### Forces des contre-signaux relevés

| Force | Fiches | Effet sur la priorité |
|---|---:|---|
| Fort | **2** | −24 |
| Modéré | **8** | −11 |
| Faible | **7** | **0** |

Cumul plafonné à −32 avec taux de décroissance 0,4. **Un équipement existant
n'annule pas une opportunité** : un site déjà automatisé peut avoir besoin d'un
agent. C'est pourquoi la force faible ne pénalise pas.

### Anciennes et nouvelles valeurs — 9 valeurs changées, 8 paliers

| Fiche | Avant | Après | Motif |
|---|---:|---:|---|
| ERM 27 | 71 | **47** | besoin déjà couvert, forte |
| Delahautemaison | 54 | **26** | négation absolue du besoin |
| Scierie Labrue | 71 | **60** | équipement partiel |
| Ouest Affûtage | 71 | **60** | équipement partiel |
| Menuiserie Mirolo | 71 | **60** | équipement partiel |
| Cordes et Âme | 50 | **39** | processus déjà partiellement outillé |
| Forages Berenguer | 50 | **39** | idem |
| Sellerie Industrielle de l'Est | 50 | **39** | idem |

**Inchangées malgré un contre-signal** (force faible) : O Lames Déchues 71,
Caléo 61, Canfora 63, Froger 62, D2Bois 68, Leichnam 68.
Priorité haute : **12 → 8**.

### Simulation, refus, puis application

La **première calibration a été rejetée** : elle classait 6 fiches en force
forte et faisait descendre O Lames Déchues de 71 à 67 sur un simple contre-signal
faible, franchissant un seuil sans justification commerciale. Deux corrections :
la négation **partielle** (« le besoin n'est pas X ») devient modérée, seule la
négation **absolue** reste forte ; et la pénalité faible passe de 4 à **0**.

La seconde simulation sur les **92 fiches** a été acceptée, puis appliquée.
Archives : `simulation-priorite-v10-2026-11-07.json`,
`priorite-commerciale-v9-vers-v10.json` (état antérieur des 92 fiches conservé),
`simulation-contre-signaux-2026-11-07.json`.

**Revue humaine demandée sur 2 fiches : ERM 27 et Delahautemaison.** Ce sont les
deux forces fortes ; la lecture automatique d'une négation peut se tromper de
portée, et la baisse est importante. Elles ne sont pas bloquées, mais la décision
commerciale vous revient.

---

## 3. Marchés publics — pilote exécuté

**30 consultations examinées** (l'objectif était ~20 ; il est dépassé),
**29 acheteurs distincts**, **20 secteurs**. Sources : BOAMP, TED, profils
acheteurs (mp74.fr, maximilien, megalis Bretagne), agrégateurs utilisés
uniquement comme piste puis recoupés.

### Résultat : A 0 · B 10 · C 20

**Aucune consultation de catégorie A.** Ce n'est pas un échec de recherche, c'est
le résultat : **un seul règlement de consultation a pu être lu**, celui de
Mieussy, et il exige des références que la micro-entreprise ne peut pas
produire. Classer A sans avoir lu les conditions de candidature serait une
affirmation sans preuve.

### Les 10 B, par échéance

| Jours restants | Acheteur | Montant publié | Pourquoi B et non A |
|---:|---|---|---|
| **4** | ODEADOM | non publié | RC non lu, capacités inconnues |
| **4** | Ville de Craponne | non publié | RC non lu |
| **7** | Saint-Pierre-Quiberon | non publié | RC non lu ; volet cartographique (GeoJSON, QGIS) = compétence SIG à évaluer |
| **8** | Saint-Quentin-en-Yvelines | non publié | 2 lots, RC non lu |
| **8** | Ville de Gravelines | non publié | RC non lu |
| **11** | **Commune de Mieussy** | **20 000 € HT** | **RC lu** : références sur 3 ans + attestations de bonne exécution exigées |
| **18** | Commune d'Arvert | non publié | RC non lu |
| **18** | Union Sociale pour l'Habitat | non publié | **statut d'acheteur public à confirmer** |
| **32** | CHU de Bordeaux | non publié | RC non lu, capacité hospitalière |
| **38** | Météo-France (Widget Factory) | non publié | RC non lu |

**Mieussy, la piste la mieux documentée** — référence S-2026-03, clôture
**20/11/2026 12h00**, montant **20 000 € HT confirmé deux fois** (avis BOAMP §5 et
RC art. 1.4). Candidature DC1+DC2, offre = acte d'engagement + DPGF 6 lignes +
mémoire technique ; candidature et offre simultanées, variantes interdites,
aucun lot, dépôt sur mp74.fr, validité 120 jours. Mise en ligne 01/07/2027.
**Blocage : liste des missions des 3 dernières années avec attestations de bonne
exécution.** Sous-critères de l'article 4.1 non lus. Le panneau d'affichage est
hors marché ; la nouvelle identité visuelle est produite par un autre
prestataire ; aucun export du site actuel n'est fourni.

### Les 20 C, par raison

| Raison | Nombre |
|---|---:|
| Consultation expirée | **7** |
| Marché déjà attribué | **4** |
| Objet hors périmètre malgré un CPV web | **3** |
| Montant hors de portée (Clichy 210 k€, CNRS 1,5 M€, Météo-France WSF 300 k€) | **3** |
| Avis ancien sans échéance établie | **3** |

**3 annonces de prestataires privés écartées** en amont : ce sont des offres de
services, pas des demandes d'acheteurs publics.

### Trois pièges documentés

- **Le code CPV ne suffit pas.** Le 72413000 « conception de sites WWW » est
  apposé sur de l'événementiel (INRS) et de la communication globale (SPL Seine
  Park). L'objet doit être lu.
- **Une date de clôture future peut être celle d'un avis d'attribution**
  (Allier 21/11, Poitiers 18/11). Ce n'est pas une échéance de candidature.
- **Les agrégateurs désalignent parfois acheteur et intitulé.** Un commentaire
  tiers sur les références de Mieussy s'est révélé exact — mais il n'a été
  retenu qu'après lecture du RC officiel.

### IA et automatisation : constat négatif

**Aucune consultation ouverte et accessible à une micro-entreprise** sur l'IA,
les agents conversationnels ou l'automatisation. Les avis réels sont attribués,
expirés, ou dimensionnés pour des éditeurs et intégrateurs. Le besoin public
existe mais se formule en acquisition de plateformes et accompagnement de
programme, pas en intégration sur mesure.

### Accès aux dossiers

Les règlements sont généralement derrière une inscription. **Aucun compte n'a
été créé.** Exception vérifiée : sur les profils AWS / Association des Maires
(`mp74.fr`), le lien « RC » est public alors que le DCE complet exige un login —
c'est ainsi que le RC de Mieussy a été lu.

**Aucun contact acheteur, aucune candidature, aucune dépense.** Les acheteurs
publics n'entrent pas dans le CRM : un avis de marché n'est pas une fiche
prospect, et un test vérifie que les deux ensembles ne se recouvrent pas.

### Recommandation

Le canal n'est **pas mûr** pour un envoi. Deux conditions préalables : constituer
des références attestées (ou candidater en groupement), et lire les RC avant
toute décision — ce qui demande un accès aux profils acheteurs. À court terme,
**Quiberon (7 jours) et Mieussy (11 jours)** sont les deux dossiers à instruire
si vous voulez tester le canal, en connaissance du blocage de références.

---

## 4. Gmail — brouillons, réponses, rebonds, oppositions

### Les deux brouillons : relus, conformes, conservés

| | Caléo Tests & Services | Pépinières Ripaud |
|---|---|---|
| Destinataire | `contact@caleo-ts.fr` | `info@ripaudpepinieres.com` |
| Message | `1a1b672541671292` | `1a1b16dee5899e57` |
| Libellé | `DRAFT` + `Label_7` (lot 9) | `DRAFT` + `Label_6` (lot 8) |
| Taille | 970 caractères, 0 pièce jointe | 966 caractères, 0 pièce jointe |
| Signature officielle | **exacte** | **exacte** |
| Mention d'opposition | présente | présente |
| File de validation | `draft` | `pending` |
| Décision | **conservé sans modification** | **conservé sans modification** |

**Caléo :** accroche citant la page de devis réelle ; le message écrit « Le
formulaire est bien construit, mais il ne dépose rien chez vous » — il ne
propose donc pas de refaire l'existant, ce qui est cohérent avec le contre-signal
de force faible et la priorité inchangée à 61. **Le fil a été ouvert : il
contient un seul message, le brouillon.** Aucun échange antérieur. Un identifiant
de fil différent de l'identifiant de message est normal et ne signale pas une
conversation.

**Ripaud :** accroche sur la page « La pépinière » (K-bis et fiche d'ouverture de
compte exigés des nouveaux clients pro). Le second lien
`https://groupebourasseau.com` est présenté comme le site institutionnel du
groupe : **référence commerciale légitime, pas une erreur**.

**Aucun brouillon recréé, aucun envoi.**

### Audit des nouveaux messages — méthode et résultat

Première tentative par exclusion (`-from:moi -in:sent -in:drafts`) :
**201 résultats, tronqués, `complete:false`**, quasi uniquement des lettres
d'information et des hameçonnages. **Requête abandonnée comme non concluante.**

Audit refait **par adresse de destinataire réelle**, spam et corbeille inclus :

| Recherche | Résultat |
|---|---:|
| Réponses des prospects depuis le 06/11 | **0** |
| Rebonds (`mailer-daemon`, `postmaster`) | **0** |
| Nouvelles oppositions | **0** |
| Nouveaux challenges | **0** |
| Nouvelles conversations commerciales | **0** |
| Demandes de tarif ou devis | **0** |

**Un zéro avec `complete:true` ne prouve pas que les critères étaient bons.** La
même forme de requête a donc été rejouée sur une période où des résultats sont
attendus : elle retrouve **l'opposition Renarde du 05/11 et le rebond dur du
04/11**. Le zéro est donc significatif, pas un artefact de syntaxe.

Aucune demande commerciale n'étant arrivée, **aucun brouillon de réponse n'était
nécessaire**.

### Protections maintenues

Opposition **Nicolas Smets / Centre Équestre de la Renarde**
(`celarenarde@gmail.com`) : statut `opposition` au CRM et présence dans
`data/suppression.json` — **maintenues toutes les deux**. Challenge Mailinblack
(Alpha Mécanique) : **non validé**. Rebond dur `contact@severine-lesourd.com` :
adresse en liste de suppression. Liste de suppression : **2 entrées**, MD5
identique.

### Nouveaux messages non commerciaux

Trois alertes Google Search Console (`synatrap.com`, `groupebourasseau.com`,
`prospecto.website`) et un message humain de Thierry Bourasseau non traité, sans
lien avec la prospection. Plusieurs hameçonnages usurpant Chronopost et DPD
réclament des « frais de douane » : **aucun lien suivi, aucune pièce ouverte**.

### Délivrance

**3 confirmées** (accusés BSP et B3R, réponse humaine Renarde), **63 non
confirmées**. Non confirmée n'est pas échouée : sans webhook, l'absence de rebond
ne prouve rien. Deux adresses sont en `nxdomain`
(`contact@severine-lesourd.com`, `info@sas-maire.fr`).

---

## 5. Délivrabilité

Document complet : **`docs/delivrabilite-phase10bis.md`**, révisé le 09/11.

### État mesuré

Pré-vol revérifié sur une copie isolée : **`(False, 3 motifs)`** —
1. campagne non activée (`enabled=false`), activation explicite requise ;
2. DKIM non détecté pour le domaine expéditeur ;
3. domaine expéditeur gratuit (Gmail), prospection de masse déconseillée/interdite
   par les CGU.

**Le blocage de fond est le troisième, pas le premier.** Activer `enabled` ne
réglerait rien.

### Solutions comparées (prix indicatifs, à revérifier)

| Solution | Coût récurrent | Rebonds / désabonnement | Limites | Verdict |
|---|---|---|---|---|
| Domaine + SMTP hébergeur | 0 € | à construire | quota faible, réputation partagée | viable < 50/jour |
| **Domaine + Brevo gratuit** | **0 €** | **fournis (webhooks)** | ~300/jour | **recommandé** |
| Domaine + Amazon SES | ~0,10 $/1 000 | webhooks SNS à câbler | sortie de bac à sable | le moins cher au volume |
| Domaine + Workspace Starter | ~6 €/u/mois | non fournis | ~2 000/jour | coûteux, n'apporte pas la mesure |
| Domaine + Zoho gratuit | 0 € | non | **pas de SMTP/IMAP** | inadapté |

**Budget : un domaine dédié, ~10 à 15 €/an. C'est indicatif, pas une autorisation
d'achat.** Le coût d'envoi peut rester **nul** : aucune souscription n'est
nécessaire tant que l'envoi n'est pas décidé, et un volume nul n'est pas un
dysfonctionnement.

### Architecture livraison / rebond / plainte / réponse

Sept événements, sept traitements détaillés dans le document. L'essentiel :
`delivered` est **le seul** événement autorisant le statut `délivré` ; un rebond
dur alimente la liste de suppression ; une plainte supprime **le domaine** et
arrête la campagne ; une réponse mentionnant un tarif, devis ou engagement produit
un **brouillon soumis à validation**, jamais un envoi.

**Limite structurelle assumée :** `delivered`, `soft_bounce` et `spam_complaint`
**n'existent pas dans nos données**. Ils exigent un prestataire d'envoi. Aujourd'hui
seuls les événements observables dans Gmail sont traités.

### Étapes et blocages

Plan en 7 étapes avec critère d'arrêt objectif chacune : décision utilisateur →
domaine et DNS (SPF, DKIM, MX, DMARC `p=none`) → authentification **lue dans les
en-têtes réels** → webhooks → pré-vol `(True, [])` → montée en charge 10-20/jour →
durcissement DMARC. **Aucune étape exécutée.**

Blocages, tous externes à l'agent : **décision sur le domaine et budget**,
**publication DNS**, **branchement des webhooks**, **validation des brouillons**.

---

## 6. Fiabilité et tests

**670 tests, 23 fichiers, tous verts** (4,2 s). Aucun test n'écrit dans les
journaux de production.

### Ce qui est couvert

Rapprochements et dédoublonnage par identifiant · oppositions et liste de
suppression · intégrité du CRM · moteurs de score et contre-signaux · pilote
marchés publics (31 tests : règles de classement **et** archive réelle) ·
les deux brouillons · envois bloqués · **rendu réel du tableau de bord**.

### Changement de méthode : tester le rendu, pas le code source

`tests/test_dashboard_render.py` (27 tests) **exécute le JavaScript du dashboard
sous node** avec un DOM minimal et les métriques réelles du dépôt, puis inspecte
le HTML produit. Il vérifie l'absence de `NaN` et de `undefined`, la présence des
valeurs attendues, et que le bandeau d'envoi réagit bien à `enabled`.

C'est ce test qui a révélé les **deux régressions du §1**, dont une que j'avais
introduite. Un test cherchant des chaînes dans le fichier les aurait laissées
passer : en JavaScript, un champ mal nommé ne lève pas d'erreur, il affiche `NaN`.

Le harnais charge aussi `/api/campaign`, que le navigateur appelle séparément de
`/api/metrics` — sans quoi le bandeau afficherait « désactivé » par absence de
données et le test passerait pour la mauvaise raison.

### Invariants durables

Les tests ne figent pas de numéro de version de moteur : ils vérifient que les
axes v8 sont identiques et que la version de priorité est cohérente sur toutes
les fiches. Un test figeant « v10 » casserait à la prochaine évolution légitime.

### Intégrité des journaux protégés — MD5 avant/après

| Fichier | État |
|---|---|
| `data/history/send-log.json` (60 entrées) | **OK, identique** |
| `data/history/reconciliations.json` | **OK, identique** |
| `data/campaigns/v4-settings.json` (`enabled=false`, `dry_run=true`) | **OK, identique** |
| `data/suppression.json` (2 entrées) | **OK, identique** |

**4/4.** Sauvegardes complètes : `/tmp/sauvegarde_finale/data/` (264 fichiers) et
`/tmp/sauvegarde_bis/data/` (260).

Le pré-vol a été exécuté **sur une copie temporaire** : `Sender.preflight()`
persiste l'état DNS, l'appeler sur les vrais paramètres aurait modifié un journal
protégé. Vérification faite : fichier de production inchangé après l'appel.

---

## 7. Git

**Branche :** `arena/7ed6352a-agent-prosect1` (unique, aucun renommage).

| Commit | Objet |
|---|---|
| `0e85179` | Phase 10 bis — discovery, imports CRM, rapprochement des 8 envois |
| `7e2bc4d` | §B — consolidation des messages sortis (60 → 68), journaux intacts |
| `1f9b589` | §C — priorité v10, contre-signaux explicites |
| `b2865ad` | §D-§H — marchés publics, audit Gmail, indicateurs, rendu testé |

Aucune fusion automatique, aucun secret committé (vérifié sur les noms de
fichiers et le contenu du diff), aucun historique supprimé. Le push est vérifié
par lecture du SHA distant, pas présumé.

---

## 8. Conclusion

### La Phase 10 est-elle terminée ?

**Oui pour les sections A à J : toutes exécutées.** Les points qui ne peuvent pas
être exécutés par l'agent sont **documentés comme bloqués**, avec leur raison et
leur condition de levée — ce n'est pas du travail laissé en suspens.

Restent structurellement hors de ma portée : l'achat du domaine, la publication
DNS, le branchement des webhooks, la validation des brouillons, et la lecture des
règlements de consultation exigeant un compte.

### Blocages

1. **Domaine professionnel** — décision et budget vous appartiennent (~10-15 €/an).
2. **DKIM et DNS** — publication impossible sans votre autorisation.
3. **Webhooks de délivrabilité** — sans eux, 63 messages resteront « non confirmés ».
4. **Validation des 2 brouillons** — Caléo et Ripaud attendent votre accord.
5. **Références marchés publics** — bloque toute catégorie A.

### Trois améliorations prioritaires

1. **Instrumenter la délivrance avant d'envoyer davantage.** Aujourd'hui 63
   messages sur 68 sont sans preuve de remise. Envoyer plus sans mesure revient à
   accumuler de l'incertitude. Domaine + service d'envoi gratuit avec webhooks :
   c'est le seul investissement qui change la qualité de l'information.
2. **Traiter les 2 forces fortes en revue humaine** (ERM 27, Delahautemaison) et
   **instruire Quiberon sous 7 jours** si le canal public vous intéresse. Ce sont
   les seules actions à échéance courte.
3. **Réorienter la recherche vers les sites officiels.** Rendement mesuré :
   **site officiel 17 qualifiées / 70 examinées = 24 %**, contre **annuaire
   professionnel 0 / 34 = 0 %**. Les 34 examinations d'annuaires n'ont rien
   produit ; le taux lissé du planificateur (2,9 %) masquait ce zéro en lui
   accordant un prior. Les deux taux sont désormais affichés côte à côte.

### Prêt pour le Lot 11 ?

**Non — et le Lot 11 n'a pas été lancé.** Trois raisons, dans l'ordre
d'importance :

- **L'envoi est bloqué par le pré-vol sur 3 motifs**, dont un blocage de fond
  (domaine gratuit). Un nouveau lot produirait des brouillons de plus, pas des
  conversations.
- **La délivrance n'est pas mesurée.** Un lot supplémentaire ajouterait des
  messages « non confirmés » sans qu'on puisse dire s'ils arrivent.
- **8 messages viennent de partir le 09/11 et n'ont reçu aucune réponse à ce
  jour.** Il est trop tôt pour en tirer un enseignement, et prospecter davantage
  avant de savoir ce que devient le lot envoyé est prématuré.

**Séquence recommandée :** décider du domaine → publier DNS → brancher les
webhooks → valider les 2 brouillons → observer les réponses du lot du 09/11 →
**alors seulement** envisager le Lot 11.
