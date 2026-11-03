# Stratégie commerciale Prospecto — v3 (3 novembre 2026)

> Évolution de la v2. Objectif : emails très courts, hook percutant dès la première
> phrase, prestation unique, démonstration gratuite centrale, volume de prospects
> fortement élargi sans sacrifier la personnalisation ni l'honnêteté.

## 1. Message de référence v3

**Objet : [accroche personnalisée et intrigante]**

Bonjour [Prénom],

[Hook personnalisé qui montre immédiatement que tu as compris un besoin ou un projet de l'entreprise.]

Je développe des sites web modernes ainsi que des agents IA capables d'automatiser certaines tâches et de faire gagner du temps aux entreprises.

**Je peux vous préparer gratuitement une démonstration personnalisée pour vous montrer concrètement ce qu'il serait possible de réaliser pour votre activité, sans engagement.**

Seriez-vous intéressé pour la découvrir ?

Bonne journée,
Martin BOURASSEAU
Création web · Agents IA · Automatisation

## 2. Principes impératifs (renforcés)

1. **Hook d'abord.** La première phrase doit être spécifique, crédible et fondée sur une
   information vérifiable (annonce, problème mentionné, projet, recrutement, tâche automatisable).
2. **Une seule prestation** par email (web OU IA/automatisation), choisie selon le besoin réel.
   Jamais le catalogue complet.
3. **Très court** : cible 60–130 mots, naturel, humain, direct, orienté bénéfice.
4. **Aucun problème inventé**, aucune fausse urgence, aucune flatterie artificielle.
5. **Démonstration gratuite limitée** au centre (maquette / aperçu / cas d'usage / processus).
6. **Objet court, naturel, intrigant mais honnête** (≤ 70 caractères), jamais racoleur.
7. **Liens d'exemple** uniquement s'ils sont dans la whitelist officielle `data/realisations.json`
   (URLs transmises par Martin). Un seul lien max, seulement s'il apporte de la valeur.
8. **Opt-out** conservé ; **validation humaine obligatoire** avant tout envoi.

## 3. Hooks — approches par type de preuve

| Preuve | Hook type |
|---|---|
| Besoin public (annonce) | « J'ai lu votre annonce : [besoin précis + source]. » |
| Lacune site vérifiée | « En parcourant votre site ([domaine]), j'ai relevé un point concret : [constat]. » |
| Processus automatisable | « En découvrant [entreprise], j'ai vu que [processus] : une piste concrète pour gagner du temps. » |
| Projet / recrutement | Rebondir sur le projet annoncé ou le poste publié (preuve à l'appui). |
| Aucun signal fort | Découverte neutre et honnête, sans prétendre à un problème. |

Les accroches sur mesure (`custom_hook`) priment sur les accroches générées, pour une
personnalisation maximale. Chaque hook reste adossé à une preuve conservée.

## 4. Niveaux de priorité CRM

- **haute** : besoin explicitement exprimé + contact email exploitable → email préparé.
- **moyenne** : besoin fortement probable, éléments concrets + contact → email préparé aussi.
- **a_approfondir** : opportunité intéressante mais infos insuffisantes → conservée, pas d'email.

On ne rejette pas les opportunités moyennes : elles sont enrichies et conservées avec leur niveau.

## 5. Ciblage élargi (mission v3)

Sources multipliées : plateformes de projets (Codeur.com et similaires), presse locale
(lancements, projets, recrutements), publications professionnelles publiques, offres d'emploi
révélatrices de tâches automatisables, sites d'entreprises, forums. Toute la France,
entreprises francophones. Priorité absolue aux besoins **explicitement exprimés** (preuve + URL).
Dédoublonnage systématique avec le CRM et l'historique d'envois.

## 6. Garde-fous techniques

- `check_email` : longueur, démo gratuite + sans engagement, opt-out, signature portfolio,
  anti-invention (hook ↔ preuve), promesses interdites, whitelist des liens d'exemple.
- CRM : fusion sans écrasement, aucune coordonnée fabriquée (`email_source`), preuves conservées.
- Aucun envoi automatique ; file de validation `pending → approved/rejected → sent`.
