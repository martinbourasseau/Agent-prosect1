# Rapport campagne — Lot 3 (2026-11-04)

## Synthèse
- **6 nouveaux prospects** ajoutés au CRM, tous qualifiés **moyenne**, tous avec **email professionnel vérifié** et **téléphone**.
- **6 brouillons Gmail** créés, personnalisés, signature **Martin BOURASSEAU**, classés campagne `2026-11-04-lot3` + label Gmail `Prospection/2026-11-04-lot3`.
- **0 envoi réel** : blocage Gmail/DKIM/domaine gratuit toujours actif, activation non validée.
- **0 réponse** sur les 8 prospects déjà contactés (re-vérifié boîte + spam, 14 jours).
- Qualification renforcée : uniquement des **lacunes de processus observables** (commande/inscription/devis encore manuels), pas de sélection sur l'âge du site ou le secteur.

## Chiffres du lot 3
| Indicateur | Lot 3 |
|---|---:|
| Entreprises examinées (search + fetch + exclus) | ~40 |
| Ajoutées au CRM | 6 |
| Qualifiées | 6 (0 haute / 6 moyenne) |
| Besoins exprimés publiquement | 0 |
| Opportunités probables étayées | 6 |
| Emails vérifiés | 6 |
| Téléphones | 6 |
| Brouillons Gmail | 6 |
| Envoyés réels | 0 |
| Réponses | 0 |

## Prospects ajoutés
| Entreprise | Région / secteur | Lacune précise | Email vérifié | Téléphone | Responsable public | Brouillon |
|---|---|---|---|---|---|---|
| Base nautique de Picquigny | 80, loisirs nautiques | Résa individuelle en ligne, mais **devis groupes par email/téléphone** ; paiements virement/chèque | canoesomme@gmail.com | 06 29 38 67 73 | Johann Beldame | r-3787275227626326877 |
| Brasserie VDL | 74, brasserie/brewpub | **« Commande uniquement par téléphone ! »** pour l'emporter | brasserievdl74@gmail.com | 04 50 68 15 05 | David Molicard | r-640883466194859786 |
| Dance Center | 59, école de danse | Inscriptions **sur place**, fiche PDF, **3 chèques** trimestriels | contact@dance-center.fr | 07 83 28 96 23 | Pauline Lefebvre (gérante) | r-8638899377923513656 |
| SAM31 | 31, auto-école | Dossier d'inscription **par téléphone/email/agence**, suivi ANTS manuel | contact@sam31.fr | 05 61 80 65 80 | Océane SAMR / Bouchaib SAMR | r-5558695767684022470 |
| La Bruchoise / Casa Blu | 67, restaurant/pizzeria | **« Commande uniquement par téléphone »** | cedmu@yahoo.fr | 03 88 47 90 35 | Cédric Fischer | r4467495994281543374 |
| L'Occidentale | 83, lieu de réception | Devis mariage/séminaire par téléphone/email/formulaire, **réponse manuelle** (opportunité plus prudente) | directionloccidentale@gmail.com | 04 69 00 15 35 | Schéhérazade (DS RECEPTION) | r-4581943460065111604 |

Sources officielles conservées dans `data/prospects/campagne-2026-11-04-lot3.json` (evidences datées 2026-11-04).

## Qualification renforcée — ce qui a été écarté
- **Brasserie Garrica (38)** : d'abord candidate, mais **boutique en ligne déjà présente** (Ajouter au panier) → pas de lacune commande, écartée.
- **Studio de la Danse (95)** : association loi 1901, hors cible B2B entreprises → écartée.
- **H2O Sports, AN Rafting, Tours&Canoë, Canoë Rapido, 2 Caps** : réservation/boutique en ligne déjà matures → écartés.
- **La Grange des Saveurs (18)** : formulaire structuré, pas d'email affiché, gap non vérifié → écartée.
- **Danseleopart (94)** : formulaire de demande structuré, lacune moins nette → non retenue.
- **Auto-écoles MONT/CFAC** : non retenues au profit de SAM31, dont le parcours d'inscription manuel est explicitement décrit.

## Messages
- Accroche factuelle propre à chaque entreprise, proposition unique, référence adaptée (**Groupe Bourasseau** pour les projets web, **SYNATRAP** pour l'automatisation), **démo gratuite sans engagement** (maquette site ou démo IA), CTA simple, opt-out, signature Martin BOURASSEAU.
- Anciennes campagnes et anciens messages conservés ; nouvelle campagne identifiable `2026-11-04-lot3`.

## Cumul depuis le lancement
| Indicateur | Cumul |
|---|---:|
| CRM total | 42 |
| Qualifiés | 22 (4 haute / 18 moyenne) |
| À approfondir | 12 |
| Besoins exprimés | 15 |
| Opportunités probables | 18 |
| Emails | 30 (20 verified / 10 public_unverified) |
| Téléphones | 22 |
| Brouillons Gmail attachés | 23 |
| File de validation | 34 pending / 0 sent |
| Envoyés réels | 0 |
| Réponses | 0 |
| Suppressions | 0 |
| Tests | 107 OK |

## Blocages envoi réel (inchangés)
1. Campagne non activée (`enabled=false`) — activation explicite requise.
2. DKIM non détecté pour le domaine expéditeur.
3. Domaine expéditeur gratuit (gmail.com) — prospection de masse déconseillée/interdite par les CGU.

Aucun envoi réel, aucun service payant, aucune modification DNS. Prochaine étape possible : domaine pro + ESP + DKIM, puis validation explicite de l'activation.
