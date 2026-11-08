# Audit Gmail — phase 10, section I

**Date : 2026-11-07** · Compte : `martin.bourasseau4@gmail.com` · Aucun envoi effectué.

## Méthode

La boîte contient plus de 29 000 messages : une requête large ne prouve rien.
L'audit interroge donc **chaque adresse et chaque domaine du CRM**, spam et
corbeille inclus, et ne retient un résultat que si `search_scope.complete` est
vrai. Les 69 adresses du portefeuille ont été réparties en quatre requêtes :
deux sur les domaines d'entreprise, deux sur les adresses portées par des
domaines grand public (gmail.com, orange.fr, sfr.fr, wanadoo.fr, yahoo.fr),
interrogées par adresse complète pour éviter le bruit.

> **Piège documenté.** `label:Prospection` ne matche **pas** les labels
> imbriqués. Une recherche sur le parent renvoie zéro et ferait croire à une
> perte de brouillons. La requête fiable énumère les feuilles :
> `in:drafts {label:Prospection/2026-11-06-lot9 …}`.

## Résultats

| Recherche | Requête | Résultat |
|---|---|---|
| Réponses, domaines d'entreprise (15) | `{from:akla-architectes.com … from:fromagerieetbaratte.fr}` | **0**, `complete:true` |
| Réponses, domaines d'entreprise (20) | `{from:itelecom.pro … from:thearchitectes.com}` | **0**, `complete:true` |
| Réponses, adresses grand public (14) | `{from:celarenarde@gmail.com …}` | **1** |
| Réponses, adresses grand public (15) | `{from:goudalerestaurant@gmail.com …}` | **0**, `complete:true` |
| Rebonds | `{from:mailer-daemon from:postmaster …} newer_than:5d` | **1** rebond réel |
| Challenge | `from:mailinblack` | **1** |
| Brouillons | `in:drafts {label:Prospection/…feuilles}` | **5** |

### Réponse humaine : une seule, et c'est une opposition

`1a1ada77bcf46db9` — Centre équestre de la Renarde, `celarenarde@gmail.com`,
5 novembre, en réponse à « Centre Équestre de la Renarde : automatiser les
inscriptions ? » :

> « Ne pas me relancer » — Smets Nicolas, Chemin des Pourraques, 83170 Brignoles

Déjà réconciliée : statut `opposition`, `opposed:true`, adresse en liste de
suppression. **Aucune nouvelle approche, jamais.** Le scoring v8 a remonté son
score d'IA de 0 à 22 ; cela ne change rien à son statut, et le dossier de
qualification la bloque explicitement. C'est le comportement attendu : la
force d'une opportunité et le droit de contacter sont deux questions distinctes.

### Rebond : un seul, déjà connu

`1a1a87452d7ca7c0` — `contact@severine-lesourd.com`, domaine introuvable.
Statut `rebond`, `bounce_severity` dure, adresse non routable. Aucun nouveau
rebond sur les 14 envois réconciliés du 6 novembre.

### Challenge de sécurité : en attente, non validé

`1a1abeb8ee41cbb7` — Mailinblack pour Alpha Mécanique : « Un clic pour délivrer
votre email ! ». **Aucun clic, aucune validation**, conformément à la section J.
Le message reste classé `challenge_en_attente` : ce n'est ni une réponse
humaine, ni une délivrance confirmée.

### Demandes commerciales : aucune

Aucune demande d'information, de tarif, de devis ou de rendez-vous n'a été
trouvée dans les conversations existantes. **Aucun brouillon de réponse n'a donc
été créé** : il n'y avait rien à quoi répondre. La règle qui autorise une
réponse simple et explicite ne s'applique pas faute d'objet.

### Brouillons : cinq, intacts

| Entreprise | Message | Label |
|---|---|---|
| Caléo Tests & Services | `1a1b672541671292` | `Label_7` |
| Cordes et Âme | `1a1b1b991300c965` | `Label_7` |
| Froger Étanchéité | `1a1b1b98459979b3` | `Label_7` |
| Cordonnerie Canfora David | `1a1b1b9735345222` | `Label_7` |
| Pépinières Ripaud | `1a1b16dee5899e57` | `Label_6` |

Les quatre du lot 9 et celui du lot 8 sont tous `["DRAFT", …]`. **Aucun n'a été
modifié** pendant cette phase.

## Réconciliation

Rien à réconcilier : aucun envoi nouveau n'apparaît côté Gmail, et les 14 envois
hors agent du 6 novembre l'ont déjà été (`matched 14, unmatched 0`). Les
journaux de production n'ont pas été touchés — empreintes MD5 vérifiées avant et
après la suite de tests :

- `data/history/reconciliations.json` — inchangé (4 réconciliations réelles)
- `data/history/send-log.json` — inchangé (60 entrées)
- `data/campaigns/v4-settings.json` — inchangé, `enabled=false`
- `data/suppression.json` — inchangé (2 entrées)

## Sécurité — section J

Pré-vol revérifié : **`(False, 3 blocages)`**

1. Campagne non activée (`enabled=false`) — activation explicite requise
2. DKIM non détecté pour le domaine expéditeur
3. Domaine expéditeur gratuit (Gmail) : prospection de masse déconseillée/interdite

Aucun paramètre DNS, SPF, DKIM, DMARC ni aucune protection d'envoi n'a été
modifié. Aucun achat, aucun abonnement, aucun contournement.

> **Note d'incident évité.** Un appel direct à `Sender().preflight()` en
> production réécrit l'horodatage `last_checked_at` du fichier de réglages.
> Détecté par comparaison MD5, le changement a été annulé : seuls les fichiers
> voulus figurent dans les commits. Les tests, eux, travaillent sur une copie
> (`settings_path`) depuis le commit `0a4b0d7`.

## Ce que cet audit ne dit pas

Les requêtes prouvent l'absence de réponse **aux adresses connues du CRM**. Elles
ne couvrent pas une réponse qui arriverait d'une autre adresse que celle
contactée (un collègue, une adresse de direction). Ce cas reste à surveiller par
objet de conversation plutôt que par expéditeur.