# Rapport campagne — Lot 4 (2026-11-04)

## 1) Correction prioritaire d'identité
- Nom officiel imposé : **Martin BOURASSEAU** (B-O-U-R-A-S-S-E-A-U).
- Signature officielle utilisée :
  - `Martin BOURASSEAU`
  - `Création de sites web · Refonte · Agents IA · Automatisation`
  - `https://prospecto.website`
- Vérification Gmail des 23 messages Prospecto précédents : **ils ne sont plus des brouillons, ils sont déjà envoyés** (`label_ids: ["SENT"]`) et **déjà signés Martin BOURASSEAU**. Aucun message contenant l'ancienne orthographe n'a été trouvé.
- **Brouillons Gmail corrigés avec le vrai nom : 0** (il n'y avait plus de brouillon Prospecto à corriger ; les 23 étaient envoyés et déjà corrects côté Gmail).
- **Contenus locaux corrigés : 23 corps de messages + modèles/config/rapports** (10 fichiers) pour remplacer l'ancienne orthographe par **Martin BOURASSEAU**.
- Garde-fou ajouté dans `prospecto/messaging.py::check_email_v4` : rejet de toute variante orthographique interdite et exigence de la signature `config.SENDER_NAME`.
- Chaque brouillon du lot 4 a été vérifié localement avant création Gmail : **0 problème d'identité/qualité**.
- Aucune autre modification d'identité ou de contenu déjà correct n'a été faite.

## 2) Recherche et qualification du lot 4
- Entreprises examinées : **≈50** (recherches élargies + vérifications de sources officielles).
- Nouveaux prospects ajoutés : **8**.
- Qualifiés : **8** (3 haute priorité, 5 moyenne).
- Besoins exprimés publiquement : **0**.
- Opportunités probables étayées : **8**.
- Emails vérifiés : **7** ; email public non vérifié : **1** (Goudale Orchies, extrait indexé officiel).
- Téléphones professionnels : **8**.
- Doublons avec les 42 fiches existantes : **0**.

### Prospects retenus
| # | Entreprise | Dept | Secteur | Lacune observable | Service proposé | Priorité |
|---|------------|------|---------|-------------------|-----------------|----------|
| 1 | Restaurant Le Canotier | 69 | Restaurant / événementiel | Réservation uniquement par téléphone ; devis groupes/séminaires manuels | Réservation en ligne + devis événementiel | haute |
| 2 | Boucherie Florian | 82 | Boucherie / traiteur | Commandes traiteur/plateaux par téléphone, tarifs PDF | Click & collect traiteur/plateaux | haute |
| 3 | La Fromagerie Les 2 Alpes | 38 | Fromagerie / épicerie fine | Boutique en ligne présente mais commande impossible via le site | Activation commande en ligne / click & collect | haute |
| 4 | Fromagerie et Baratte | 69 | Fromagerie / crémerie | Finalisation des plateaux uniquement téléphone/boutique | Commande de plateaux en ligne + créneau retrait | moyenne |
| 5 | La Chocolatisserie | 68 | Pâtisserie / chocolaterie | Commandes privilégiées par téléphone | Commande en ligne / gâteaux sur-mesure | moyenne |
| 6 | Matproloc | 59 | Location matériel BTP | Catalogue en ligne mais devis/réservations téléphone/email | Réservation de matériel en ligne + disponibilités | moyenne |
| 7 | Allo'cation | 94 | Location matériel événementiel | Formula devis structuré mais traitement manuel | Automatisation devis/disponibilités (agent IA) | moyenne |
| 8 | Restaurant Goudale Orchies | 59 | Restaurant / brasserie | Site d'Orchies en réservation téléphonique uniquement | Réservation en ligne pour Orchies | moyenne |

### Exclus / non retenus
- Associations loi 1901 / réseaux de type Gîtes de France : hors cible B2B directe.
- Entreprises déjà équipées (réservation/commande en ligne mature, boutique e-commerce active).
- 1001 Locations : email obfusqué, non vérifiable proprement.
- Écoles de musique municipales/associatives : inscription manuelle mais hors cible B2B.

## 3) Brouillons Gmail créés (lot 4)
- Campagne : `2026-11-04-lot4`.
- Label Gmail : `Prospection/2026-11-04-lot4` (`Label_2`), appliqué aux 8 brouillons.
- **8 brouillons créés**, personnalisés, avec accroche spécifique, démo gratuite sans engagement, référence pertinente (Groupe Bourasseau ou Synatrap), CTA simple et opt-out.
- Tous signés **Martin BOURASSEAU**.

| ID queue | Entreprise | Draft Gmail |
|----------|------------|-------------|
| 2026-11-04-lot4-001 | Restaurant Le Canotier | r-441106915474065912 |
| 2026-11-04-lot4-002 | Boucherie Florian | r-2227193041875889795 |
| 2026-11-04-lot4-003 | La Fromagerie Les 2 Alpes | r-3261002470483516264 |
| 2026-11-04-lot4-004 | Fromagerie et Baratte | r2349920759718953430 |
| 2026-11-04-lot4-005 | La Chocolatisserie | r-8188127379332518233 |
| 2026-11-04-lot4-006 | Matproloc | r8133168118816518162 |
| 2026-11-04-lot4-007 | Allo'cation | r6132347275537598063 |
| 2026-11-04-lot4-008 | Restaurant Goudale Orchies | r4069016850255698710 |

## 4) Envois, réponses et surveillance
- **Envois réels par l'agent : 0** (pré-vol bloqué).
- Envois réels constatés dans Gmail (hors agent, historique) : **23 messages**, **21 destinataires uniques** (R Premium et Secteur 72 ont reçu 2 emails). Tous déjà signés Martin BOURASSEAU.
- Réponses détectées (spam inclus) : **0**.
- Opt-out / opposition : **0**.
- Rebonds / plaintes : **0**.
- CRM et send-log locaux réconciliés avec les 23 envois constatés (statut `contacté`, `gmail_message_id`).

## 5) Cumul global depuis le lancement
- CRM : **50 fiches**.
- Actifs : **21** ; contactés : **29**.
- Qualifiés actifs : **9** (3 haute, 6 moyenne) ; à approfondir : **12**.
- Qualifiés historiques (tous statuts, tiers haute/moyenne) : **30**.
- Besoins exprimés : **15** ; opportunités probables actives : **6**.
- Emails : **38** (27 verified, 11 public_unverified).
- Téléphones : **30**.
- File de validation : **19 pending**, **23 sent**.
- Brouillons Gmail lot 4 : **8**.
- Réponses : **0** ; suppressions : **0**.
- Tests : **110 OK**.

## 6) Blocages (pré-vol conservé)
`PRÉ-VOL : BLOQUÉ`
1. Campagne non activée (`enabled=false`) : activation explicite requise.
2. DKIM non détecté pour le domaine expéditeur.
3. Domaine expéditeur gratuit (`gmail.com`) : prospection de masse déconseillée/interdite par les CGU.

Aucun envoi réel ne sera effectué tant que ces blocages ne sont pas résolus **et** que l'activation n'est pas explicitement validée. Aucun abonnement payant, aucune modification DNS sans accord, aucun contournement de verrou.
