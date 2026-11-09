# Délivrabilité — audit technique et plan de mise en service

**Date :** 2026-11-07, **chiffres révisés le 2026-11-09** (phase 10 finale, §F).
**Aucune modification DNS effectuée. Aucun achat. Aucun compte créé.**
Ce document est un plan, pas une mise en œuvre. Le budget de 10 à 15 €/an cité
plus bas est **indicatif** : ce n'est pas une autorisation d'achat.

---

## 1. État réel, revérifié à partir des données

Chiffres recalculés depuis `data/history/send-log.json`, `reconciliations.json`
et `prospecto.metrics.compute_metrics()` — et non repris du rapport précédent.

**Révision du 09/11 :** la consolidation (`prospecto/outbound.py`) a rapproché
**8 messages réellement partis de Gmail le 09/11 hors agent**, absents du journal
de production. Le total passe de 60 à **68 messages sortis**, sans qu'aucune
ligne n'ait été ajoutée au journal historique : les 8 sont comptés depuis la
source Gmail, avec leur identifiant de message. **Envoyé hors agent ≠ envoyé par
Prospecto**, et la provenance reste distinguée dans le tableau de bord.

| Mesure | Valeur vérifiée | Correction |
|---|---:|---|
| Messages sortis (consolidés) | **68** | 60 production + 8 rapprochés de Gmail |
| Délivrances **confirmées** | **3** | conforme |
| Délivrances **non confirmées** | **63** | 55 au brief, 56 au 07/11, 63 après rapprochement |
| Rebonds durs | **1** | conforme |
| Rebonds souples | 0 | — |
| Réponses automatiques | 2 | — |
| Challenges de délivrance | **1** | Mailinblack, non validé |
| Réponses humaines | 1 | l'opposition Renarde |
| Oppositions | 1 | — |
| Taux de rebond | 1,5 % | 1 rebond / 68 messages |

**Rappel de lecture, non négociable :** *délivrance non confirmée* ≠ *échec de
délivrance*. Sur 68 messages sortis, 3 sont prouvés par un accusé ou une réponse
humaine ; les 63 autres sont **sans preuve**, ni dans un sens ni dans l'autre.
L'absence de rebond ne prouve pas la remise en boîte de réception : un message
peut être accepté puis classé en indésirable sans jamais générer de rebond.

Les cinq états à ne jamais confondre, et ce que nous savons réellement :

| État | Preuve nécessaire | Notre situation |
|---|---|---|
| Envoyé | journal de production **ou** message `SENT` constaté dans Gmail | 68 |
| Accepté par Gmail | identifiant de message renvoyé | 68 |
| Délivré | accusé, webhook ESP ou réponse | **3** |
| Lu | aucune (pixel non fiable, non utilisé) | **inconnu** |
| Répondu | message entrant d'un humain | 1 |

---

## 2. Les trois blocages réels du pré-vol

Reproduits sur une **copie isolée** des paramètres, pour ne pas réécrire
`last_checked_at` en production :

```
(False, [
  'Campagne non activée (enabled=false). Activation explicite requise.',
  'DKIM non détecté pour le domaine expéditeur.',
  'Domaine expéditeur gratuit (Gmail (gratuit)) : prospection de masse '
  'déconseillée/interdite par les CGU.'
])
```

### Le blocage de fond est le troisième, pas le premier

Le compte d'envoi est une adresse **`gmail.com` gratuite**. Deux conséquences
que aucune configuration ne peut contourner :

1. **Vous ne contrôlez pas l'authentification du domaine.** Les enregistrements
   SPF, DKIM et DMARC de `gmail.com` appartiennent à Google. Il est impossible
   d'y publier votre propre politique DMARC ni d'aligner votre marque. Ajouter
   un DKIM « pour gmail.com » n'a pas de sens : c'est le domaine de Google.
2. **Les conditions d'utilisation de Gmail encadrent l'envoi en volume.** C'est
   pour cette raison que le pré-vol bloque, et cette raison est légitime.
   **Il n'est pas question de la contourner.**

Conclusion : un **domaine professionnel dédié n'est pas une optimisation, c'est
un prérequis**. Tant qu'il n'existe pas, les 2 brouillons restants ne peuvent pas partir
proprement, quel que soit le reste.

### Problème de mesure, distinct du problème d'envoi

Même avec un domaine parfait, nous resterions à 3 confirmations sur 60 : le
dispositif actuel **n'instrumente pas la délivrance**. Il journalise l'envoi,
pas la remise. Corriger l'authentification sans corriger la mesure reviendrait
à envoyer mieux sans savoir si cela fonctionne.

---

## 3. Comparaison des solutions — sans achat ni souscription

Prix publics indicatifs, à revérifier au moment de la décision. Aucun compte
n'a été créé et aucune offre n'a été souscrite dans cette mission.

| Solution | Coût récurrent | Authentification | Gestion rebonds / désabonnement | Limites | Verdict |
|---|---|---|---|---|---|
| **Domaine seul + SMTP d'un hébergeur mutualisé** (OVH, Infomaniak inclus) | **0 €** en plus du domaine | SPF/DKIM fournis, DMARC à publier | à construire soi-même | quota horaire faible, réputation partagée | viable pour < 50/jour |
| **Domaine + Brevo offre gratuite** | **0 €** | SPF/DKIM guidés, DMARC à publier | **fournis** (webhooks, désinscription) | ~300 e-mails/jour | **recommandé pour démarrer** |
| **Domaine + Amazon SES** | ~**0,10 $ / 1 000** e-mails | SPF/DKIM/DMARC à publier | webhooks SNS à câbler | sortie de bac à sable à demander, mise en œuvre technique | le moins cher au volume |
| **Domaine + Google Workspace Starter** | ~**6 €/utilisateur/mois** | DKIM en un clic | non fournis pour la prospection | ~2 000/jour, prospection de masse encadrée | coûteux, n'apporte pas la mesure |
| **Domaine + Zoho Mail offre gratuite** | 0 € | SPF/DKIM fournis | non | **pas de SMTP/IMAP sur l'offre gratuite** | inadapté à un envoi programmatique |

### Recommandation économique

**Un domaine dédié (~10 à 15 €/an) + un service d'envoi à offre gratuite
type Brevo.** Coût récurrent d'envoi : **0 €** au démarrage, dans la limite
d'environ 300 messages/jour — très au-delà de notre rythme actuel. Le domaine
est la seule dépense, annuelle et modeste.

Pourquoi ce choix plutôt que le moins cher absolu : l'offre gratuite d'un
prestataire d'envoi apporte **la gestion des rebonds et des désabonnements par
webhooks**, c'est-à-dire exactement la mesure qui nous manque. Avec SES il
faudrait la construire. Le surcoût de SES est nul, mais le coût de développement
est réel.

**Le volume peut rester nul.** Tant que l'envoi n'est pas autorisé, le coût
récurrent est de **0 €** : aucune offre payante n'est nécessaire pour préparer
le terrain, et l'absence d'envoi n'est pas un dysfonctionnement à corriger.

**Architecture conseillée :** envoyer depuis un sous-domaine dédié, par exemple
`envoi.votre-domaine.fr`, et garder la boîte de réception actuelle pour les
réponses. Un incident de réputation sur le sous-domaine d'envoi n'abîme alors
pas le domaine principal ni la correspondance normale.

---

## 4. Prérequis techniques à réunir

| Élément | Cible | Pourquoi |
|---|---|---|
| Domaine dédié | acheté et actif | contrôler l'authentification |
| **SPF** | un seul enregistrement, incluant le seul prestataire retenu | autoriser les serveurs d'envoi ; deux SPF invalident tout |
| **DKIM** | clé ≥ 2048 bits publiée par le prestataire | signer les messages |
| **DMARC** | `p=none` → `quarantine` → `reject` par paliers | politique et rapports d'alignement |
| Alignement | domaine du `From` aligné avec SPF et DKIM | exigence des grands fournisseurs |
| MX du domaine d'envoi | configuré | un domaine qui ne reçoit pas est suspect |
| Adresse `postmaster` / `abuse` | active | exigence des fournisseurs de messagerie |
| Rebonds | webhook → `data/suppression.json` | ne jamais réécrire à une adresse morte |
| Désabonnement | lien + traitement automatique | obligation légale et respect de l'opposition |
| En-tête `List-Unsubscribe` | présent | exigé par les grands fournisseurs au-delà d'un certain volume |

**Cadre légal B2B français.** La prospection professionnelle par e-mail est
admise sans consentement préalable lorsque le message est en rapport avec
l'activité professionnelle du destinataire, identifie clairement l'expéditeur
et offre un moyen simple de s'opposer. Les paramètres actuels vont déjà dans ce
sens (`b2b_only`, `identify_sender`, `include_opt_out`,
`honor_suppression_list`) et doivent rester activés. Ce n'est pas un avis
juridique : à faire confirmer avant tout envoi en volume.

### Architecture événementielle : livraison, rebond, plainte, réponse

Quatre familles d'événements, quatre traitements. Les confondre est la cause
directe de l'incertitude actuelle sur 63 messages.

| Événement | Source de preuve | Traitement | Statut CRM résultant |
|---|---|---|---|
| **Livraison** (`delivered`) | webhook du prestataire, ou accusé / réponse humaine | horodater, rattacher par identifiant de message | `délivré` — **seul cas** autorisant ce statut |
| **Rebond dur** (`hard_bounce`) | webhook, ou notification du serveur destinataire | ajouter à `data/suppression.json`, ne **jamais** réécrire | `rebond` |
| **Rebond souple** (`soft_bounce`) | webhook | nouvelle tentative bornée, puis abandon | `à réessayer` puis `rebond` |
| **Plainte** (`spam_complaint`) | boucle de rétroaction du prestataire | suppression **du domaine**, arrêt de la campagne | `opposition` |
| **Réponse humaine** | message entrant d'un correspondant identifié | revue humaine ; tarif, devis ou engagement ⇒ brouillon soumis à validation | `répondu` |
| **Réponse automatique** | en-têtes `Auto-Submitted`, accusé de vacances | journaliser, **ne pas** compter comme intérêt | inchangé |
| **Opposition** | mots-clés explicites du destinataire | suppression immédiate et définitive | `opposition` |

Trois règles de rattachement, tirées des erreurs réellement rencontrées :

1. **Rapprocher par identifiant de message**, jamais par seule adresse : une
   même entreprise peut avoir reçu plusieurs messages.
2. **Un identifiant de fil n'est pas un identifiant de message.** Un fil peut
   contenir un seul message — c'est le cas du brouillon Caléo vérifié le 09/11.
3. **Aucun événement ≠ aucune information.** Sans webhook, l'état reste
   `délivrance non confirmée`, jamais `délivré` par défaut.

Aujourd'hui, seuls les événements observables **dans Gmail** sont traités
(rebonds, accusés, réponses, oppositions). Les événements `delivered`,
`soft_bounce` et `spam_complaint` **n'existent pas dans nos données** : ils
requièrent le prestataire d'envoi de l'étape 3. C'est une limite structurelle de
mesure, pas un défaut conjoncturel.

---

## 5. Plan de mise en service, par étapes vérifiables

Chaque étape a un **critère d'arrêt objectif**. On ne passe pas à la suivante
tant que le critère n'est pas mesuré. **Aucune de ces étapes n'a été exécutée.**

**Étape 0 — décision utilisateur.** Choisir le domaine et le prestataire.
Autoriser explicitement la dépense annuelle. *Critère : accord écrit.*

**Étape 1 — domaine et DNS.** Publier SPF, DKIM, MX, DMARC `p=none`.
*Critère : les trois enregistrements répondent publiquement et le prestataire
affiche le domaine « vérifié ».*

**Étape 2 — authentification.** Envoyer un message test vers une adresse que
vous contrôlez, puis lire les en-têtes.
*Critère : `spf=pass`, `dkim=pass`, `dmarc=pass` **lus dans les en-têtes réels**,
pas déduits de la configuration.*

**Étape 3 — instrumentation.** Brancher les webhooks de remise, rebond et
désabonnement. *Critère : un envoi test produit une entrée « délivré » dans le
journal, et un rebond test ajoute l'adresse à la liste de suppression.*

**Étape 4 — pré-vol.** Relancer `deliverability` sur les vrais paramètres.
*Critère : pré-vol `(True, [])`. Tant qu'il renvoie False, `enabled` reste
false.*

**Étape 5 — montée en charge prudente.** Commencer par **10 à 20 messages/jour**
pendant une semaine, sur les brouillons déjà validés, puis doubler par paliers
hebdomadaires seulement si les indicateurs tiennent.
*Critère par palier : rebonds durs < 2 %, plaintes < 0,1 %, oppositions
honorées immédiatement, aucune mise en indésirable constatée sur les adresses
de test.*

**Étape 6 — durcissement DMARC.** Passer `p=quarantine` après deux semaines de
rapports propres, puis `p=reject`. *Critère : rapports DMARC sans échec
d'alignement légitime.*

**Étape 7 — surveillance continue.** Tableau de bord des rebonds, oppositions
et taux de réponse par lot. *Critère : arrêt automatique de la campagne au
premier rebond dur en série ou à la première plainte.*

**Règle de non-déclaration :** un domaine n'est **jamais** annoncé « prêt » sur
la base de sa configuration. Il l'est sur la base d'en-têtes d'authentification
lus et d'un cycle remise/rebond mesuré de bout en bout.

---

## 6. Ce qui reste bloqué, et pourquoi c'est normal

- `enabled=false` — **inchangé**, activation explicite requise.
- `dry_run=true` — inchangé.
- Pré-vol `(False, 3 motifs)` — inchangé.
- **Aucun DNS modifié, aucun achat, aucune souscription, aucun contournement.**
- Les **2 brouillons restants** (Caléo Tests & Services, Pépinières Ripaud)
  restent en attente de votre validation. Ils ont été relus intégralement dans
  Gmail le 09/11 et **conservés sans modification** : destinataire, signature
  officielle, mention d'opposition et personnalisation sont conformes. Les 8
  autres messages préparés ont été envoyés hors agent le 09/11 et rapprochés.

Le chemin critique est court et il ne dépend pas de l'agent : **décider du
domaine, publier quatre enregistrements, brancher les webhooks**. Ensuite
seulement, l'envoi peut être envisagé — et il restera soumis à votre accord.
