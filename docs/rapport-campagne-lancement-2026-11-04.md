# Rapport de campagne — LANCEMENT réel · Lot 1

**Date : 4 novembre 2026 · Campagne `2026-11-04-lancement` · Identité expéditeur : Martin Boisseau**

Campagne réellement exécutée avec le moteur Prospecto : recherche → qualification → messages personnalisés → brouillons Gmail → CRM. **Aucun envoi réel n'a été forcé** : le pré-vol reste bloqué par les restrictions du fournisseur (voir §Blocages), conformément à la consigne « ne pas contourner ».

---

## Chiffres du lot (demandés)

| Indicateur | Valeur |
|---|---|
| Entreprises examinées / recherchées | **≈ 50** (≈ 35 projets Codeur + ≈ 15 entreprises via recherche web multi-régions) |
| Nouveaux prospects ajoutés au CRM | **8** |
| Prospects qualifiés (total CRM) | **9** (3 haute, 6 moyenne) |
| Besoins réels exprimés identifiés (total) | **14** |
| Opportunités probables observables (total) | **6** |
| Emails professionnels **vérifiés** (total) | **7** |
| Emails publics non vérifiés (total) | 10 |
| Téléphones professionnels récupérés (total) | **9** |
| Brouillons Gmail créés (ce lot) | **8** |
| Emails **réellement envoyés** | **0** (bloqué par le pré-vol — voir §Blocages) |
| Emails en attente (file totale) | **21** (dont **8** pour la campagne de lancement) |
| Réponses reçues | **0** (recherche Gmail complète, spam inclus) |
| Opportunités commerciales actionnables | **9** qualifiés + 12 « à approfondir » |
| Total CRM | **29 prospects** |

---

## Les 8 nouveaux prospects

### Besoins exprimés publics (Codeur, 4 nov) — contacts porteurs masqués → « à approfondir »
| Prospect | Besoin | Secteur |
|---|---|---|
| Fabricant de sacs à dos sur mesure | Site e-commerce WordPress/WooCommerce | Commerce |
| Boutique e-commerce produits haut de gamme | Design + boutique en ligne | Commerce |
| Projet boutique Shopify (dizaine de produits) | Site de vente en ligne | Commerce |
| Vente d'espaces publicitaires TV | Outil IA : centraliser offres + générer propositions | Services |
| Marque de soins | Agent IA pour traiter les commentaires réseaux | Commerce |

> Ces 5 besoins sont **réels et publics**, mais Codeur **masque les coordonnées** des porteurs (réservées aux prestataires abonnés). Aucun email fabriqué ; ils restent « à approfondir » jusqu'à récupération légale de la coordonnée.

### Entreprises contactables — emails publics vérifiés sur sites officiels, lacunes observables
| Prospect | Lieu | Lacune / opportunité observable | Email (vérifié) |
|---|---|---|---|
| **Camping Le Galet** | Marseillan-Plage (34) | Emplacements réservables **uniquement par téléphone** | reception@camping-galet.com |
| **Restaurant La Renardière** | Col de Marcieu (38) | Réservations/devis groupes, séminaires, traiteur **par téléphone** | larenardieredelyna@gmail.com |
| **Restaurant Les Santons** | La Turbie (06) | Devis événements/groupes (15–60 pers.) traités manuellement | lessantons.laturbie@gmail.com |

> Entreprises écartées pour ne **pas inventer de besoin** : La Garangeoire (positionnement « déconnexion digitale »), Erisay, Pont d'Aliès, Le Montant, Le Pessac, Château de l'Hom, Les Jardins d'Epicure, La Calèche, La Baie des Singes (déjà équipés : réservation en ligne / e-boutique / formulaires), Domaine du Forez (site inaccessible).

---

## Messages & campagne
- **8 emails personnalisés** générés avec le moteur v4 (variantes `public_need`, `synatrap_ia`, `no_site`), chacun : accroche sur preuve réelle, proposition adaptée, **démo gratuite sans engagement**, CTA simple, opt-out, signature **Martin Boisseau**.
- **Références sélectionnées automatiquement** : Synatrap pour les besoins IA/automatisation, Groupe Bourasseau pour les besoins web. Liens cliquables, un seul lien d'exemple par email. Paternité formulée au groupe (« la plateforme que je développe avec mon groupe »), non affirmée comme réalisation personnelle.
- **8 brouillons Gmail créés** et attachés à la file + CRM (statut `brouillon_créé`).
- Anciennes campagnes **conservées** (v2, v3, v4) ; nouvelle campagne identifiable `2026-11-04-lancement`.

### Identité expéditeur
- **Signature** : `Martin Boisseau · Création de sites web · Refonte · Agents IA · Automatisation` (appliquée partout).
- **Expéditeur technique** : le compte connecté `martin.bourasseau4@gmail.com` — **aucune usurpation**, aucune modification artificielle de l'identité. Le « nom affiché » dans Gmail est un réglage du compte (que Martin peut ajuster dans ses paramètres Gmail s'il le souhaite) ; le connecteur ne permet pas de le forcer sans contourner le fournisseur.

---

## Blocages précis des envois réels (pré-vol re-vérifié)
Le pré-vol `campaign preflight` retourne **BLOQUÉ** pour 3 raisons :
1. **Campagne non activée** (`enabled=false`) — activation explicite requise.
2. **DKIM non détecté** pour le domaine expéditeur.
3. **Domaine expéditeur gratuit (`gmail.com`)** : la prospection commerciale en masse depuis un compte Gmail gratuit est **contraire aux CGU** et dégrade la délivrabilité (risque de suspension).

**Conformément à la consigne, ces verrous n'ont pas été contournés.** Aucun service payant souscrit, aucun DNS modifié. Résultat : **0 envoi réel**, mais **8 brouillons prêts** + campagne entièrement préparée.

### Pour débloquer les envois réels (décision de Martin)
1. **Domaine d'envoi professionnel** (ex. `contact@prospecto.website`) avec **SPF + DKIM + DMARC** publiés.
2. **Prestataire d'envoi** : Google Workspace sur domaine propre, ou ESP (Brevo/Sendgrid/Mailgun) → transport `smtp` (variables `PROSPECTO_SMTP_*`) ou connecteur.
3. Valider les paramètres puis `campaign activate` (dry-run) → vérifier → `campaign activate --live`.

---

## Réponses & suivi
- **0 réponse** des 8 entreprises contactées le 3 nov (recherche complète, spam inclus). Module de détection/classification prêt (8 intentions), mise à jour CRM + suppression automatiques dès qu'une réponse arrive.
- Liste de suppression : 0 (alimentée automatiquement sur opt-out/refus/rebond).
- Aucune relance après opposition/refus (garde-fou actif).

---

## Préservation & sécurité
- Données existantes, anciennes campagnes et versions de messages **conservées** ; rien d'écrasé.
- Projet **SYNATRAPE non touché** (Synatrap = référence publique uniquement).
- Aucun secret sur GitHub ; API du dashboard authentifiée ; aucune donnée sensible exposée au navigateur.
- **107 tests verts.**

*Prospecto — Martin Boisseau · Création de sites web · Refonte · Agents IA · Automatisation · https://prospecto.website*
