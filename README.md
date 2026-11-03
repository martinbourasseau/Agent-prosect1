# Prospecto — Agent de prospection commerciale

Moteur de prospection de **Martin BOURASSEAU** (création web · agents IA · automatisation) :
recherche d'entreprises, qualification fondée sur des preuves, génération d'emails
personnalisés et **file de validation humaine** avant tout envoi Gmail.

- Site / portfolio : [prospecto.website](https://prospecto.website)
- Stratégie commerciale de référence : [`docs/strategie-commerciale.md`](docs/strategie-commerciale.md)
- Analyse de l'historique d'envois : [`docs/analyse-emails-2026-11-03.md`](docs/analyse-emails-2026-11-03.md)

## Principe

```
Recherche web → Qualification (preuves) → Email personnalisé → File de validation → Brouillon Gmail → Validation humaine → Envoi
```

**Aucun envoi automatique.** Chaque email attend une validation (`approve`) puis la
création d'un brouillon Gmail. La démonstration gratuite personnalisée est
l'argument commercial central — toujours limitée, jamais une réalisation complète.

## Démarrage

Python ≥ 3.10, aucune dépendance externe (bibliothèque standard).

```bash
python -m prospecto.cli --help                 # aide
python -m prospecto.cli qualify data/prospects/<fichier>.json
python -m prospecto.cli generate data/prospects/<fichier>.json --campaign <nom>
python -m prospecto.cli queue list             # file de validation
python -m prospecto.cli queue approve <id>     # valider un email
python -m prospecto.cli queue export-gmail     # export pour brouillons Gmail
python -m unittest discover -s tests -v        # tests
```

## Structure

```
prospecto/            Moteur (config, modèles, stratégie, qualification, génération, file)
docs/                 Stratégie commerciale v2 + analyses
data/prospects/       Prospects qualifiés et preuves (données publiques d'entreprise)
data/campaigns/       Campagnes générées (emails prêts à valider)
data/queue/           File de validation (états pending/approved/rejected/sent)
data/history/         Historique des envois (dédoublonnage)
tests/                Tests unitaires (unittest)
```

## Sécurité

- Aucun secret dans le dépôt : `.env` ignoré, seul `.env.example` (placeholders) est versionné.
- L'accès Gmail passe par le connecteur sécurisé de l'agent, jamais par des tokens stockés ici.
- Les données versionnées sont des informations publiques d'entreprises (sites, emails de contact professionnels, preuves sourcées).
- Le projet SYNATRAPE n'est pas modifié par ce dépôt.

## Sauvegarde

Ce dépôt est la sauvegarde permanente du travail Prospecto (branche de travail
`arena/7ed6352a-agent-prosect1`, synchronisée avec GitHub à chaque étape cohérente).
