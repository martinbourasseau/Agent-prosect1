# Stratégie commerciale Prospecto — v2 (3 novembre 2026)

> Document de référence du moteur. Toute génération d'email doit respecter ce document.
> Il complète (sans l'effacer) l'approche historique analysée dans `analyse-emails-2026-11-03.md`.

## 1. Message commercial de référence

**Objet : Une idée pour [Nom de l'entreprise] ?**

Bonjour [Prénom],

J'ai découvert votre entreprise et identifié quelques possibilités pour développer votre activité grâce au web et à l'intelligence artificielle.

Je crée des **sites web modernes et professionnels**, ainsi que des **agents IA capables d'automatiser des tâches et de vous faire gagner du temps**.

J'aimerais vous montrer concrètement ce qu'il serait possible de réaliser pour votre entreprise.

**Je vous propose de créer une première démonstration personnalisée, gratuitement et sans engagement.**

Est-ce que cela pourrait vous intéresser ?

Bonne journée,

Martin BOURASSEAU
Création web · Agents IA · Automatisation
[Mon portfolio]

## 2. Principes impératifs

1. **Le message est une base, pas un modèle à envoyer à l'identique.** Chaque email est personnalisé.
2. **Ne jamais prétendre avoir identifié un problème qui n'existe pas.** Chaque affirmation doit être appuyée par une preuve conservée (`Evidence` : URL, extrait, date d'observation).
3. **Si l'entreprise a exprimé un besoin publiquement** (réseaux sociaux, forum, offre d'emploi, avis, article), **faire référence à cette demande** — c'est le signal le plus fort et il prime sur l'audit de site.
4. **Court, direct, naturel, professionnel.** Cible : 90–160 mots dans le corps, pas de jargon, pas de superlatifs creux.
5. **La démonstration gratuite est l'argument central**, jamais une réalisation complète gratuite.
6. **Une seule prestation principale par email**, choisie selon le besoin réel (pas le catalogue complet).
7. **Toujours une porte de sortie** (« ne pas me relancer »), conservée de l'approche historique.
8. **Validation humaine obligatoire avant tout envoi** (file de validation → brouillons Gmail → envoi manuel ou validé).

## 3. Personnalisation intelligente (règles moteur)

| Élément | Règle d'adaptation |
|---|---|
| Première phrase | Au besoin réellement identifié. Besoin public → le citer avec sa source. Audit site → observations vérifiées uniquement. Sinon → découverte neutre et honnête. |
| Prestation proposée | `site_web` (création), `refonte`, `agent_ia`, `automatisation` — une seule, la plus pertinente. |
| Exemples de réalisations | Adaptés au secteur du prospect (catalogue `REALISATIONS` du moteur), 1 exemple maximum. |
| Objet | Variante de « Une idée pour [Entreprise] ? » orientée besoin, courte (< 70 caractères). |
| Démonstration gratuite | Définie par besoin (voir §4), toujours limitée et sans engagement. |
| Salutation | Prénom du contact si connu avec certitude, sinon « Bonjour, ». |

## 4. Démonstration gratuite par besoin

| Besoin | Démonstration proposée (limitée) | Interdit |
|---|---|---|
| Site web (création) | Première maquette / aperçu personnalisé de page d'accueil | Promettre le site complet gratuit |
| Refonte | Proposition visuelle d'amélioration d'une page clé | Refonte complète gratuite |
| Agent IA | Exemple concret de fonctionnement adapté à l'entreprise (ex. tri de demandes de devis) | Agent déployé complet gratuit |
| Automatisation | Illustration du processus qui pourrait être automatisé (schéma / pas-à-pas) | Automatisation livrée gratuite |

Formulation de référence : « Je vous propose de créer une première démonstration personnalisée, gratuitement et sans engagement. » — suivie de la précision du livrable limité selon le besoin.

## 5. Ciblage prioritaire

1. **Priorité 1 — besoin exprimé publiquement** : entreprise cherchant explicitement un site, une refonte, de l'aide IA/automatisation (posts LinkedIn/Facebook, forums, appels d'offres, offres d'emploi révélatrices).
2. **Priorité 2 — lacunes vérifiées sur le site** : pas de HTTPS, pas de formulaire de contact, pas de CTA devis, site daté (constats factuels, jamais de procès d'intention).
3. **Priorité 3 — opportunités sectorielles** : processus répétitifs visibles (devis, RDV, relances) dans un secteur adapté.

Exclusions : entreprises déjà contactées (dédoublonnage, cf. historique du 03/11 matin), concurrents directs (agences web), absence d'email de contact exploitable, besoin non vérifiable.

## 6. Cohérence avec l'approche existante

Conservé des 8 emails du 03/11 matin : ton factuel et humble, observations concrètes sourcées, phrase d'opt-out, signature identitaire, longueur courte.
Ajouté par la v2 : argument central de démonstration gratuite personnalisée, objet « Une idée pour… ? », portfolio en signature, personnalisation pilotée par le besoin.

Signature v2 :

```
Bonne journée,
Martin BOURASSEAU
Création web · Agents IA · Automatisation
https://prospecto.website
```

## 7. Pipeline opérationnel

```
Recherche web (signaux publics + audit sites)
  → Qualification (score + preuves obligatoires)
  → Génération personnalisée (règles §3–4, garde-fous)
  → File de validation (pending → approved / rejected)
  → Brouillons Gmail (jamais d'envoi automatique)
  → Validation humaine → envoi → suivi
```

Chaque étape est traçable et sauvegardée dans ce dépôt (branche de travail), sans aucun secret.
