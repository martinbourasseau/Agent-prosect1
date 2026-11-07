# Phase 10 — fichier de reprise

Mis à jour au fil de l'avancement. En cas d'interruption, reprendre à la
première étape non cochée **sans refaire les recherches déjà faites**.

## Contraintes permanentes

- Aucun nouvel email de prospection. `enabled=false` intact. DNS/SPF/DKIM/DMARC intacts.
- Aucune suppression de fiche, d'historique ou de brouillon.
- Scores historiques conservés ; toute nouvelle évaluation est tracée à part.
- Coordonnées jamais devinées. Adresse décodée = non confirmée.
- Label lot 10 : `Prospection/2026-11-07-lot10`. Anciens brouillons intacts.
- Pas de fusion automatique, pas de secret publié, pas de dépense.

## Étapes

- [x] **A** Audit initial — `docs/audit-phase10-portefeuille.md`, commit `811d9d1`
      Sauvegarde `data/backups/2026-11-07-avant-phase10/` (41 fichiers).
      Premesse corrigée : aucune base SQLite, CRM en JSON.
- [x] **B** Audit des 78 fiches — 41 constats,
      `data/history/audit-portefeuille-phase10.json`, commit `811d9d1`
- [ ] **D** Scoring v8 : 4 niveaux de signal, dédoublonnage des preuves,
      signaux manquants, `evaluated_at`, tests de régression lot 9
- [ ] **E** Planificateur : performance des sources, historique des recherches,
      secteurs/départements dynamiques
- [ ] **F** Qualification : adresse décodée non confirmée, angle commercial
- [ ] **G** Approfondissement lot 9 : 24 annuaire seul + 27 écartées
- [ ] **H** Lot 10 : ~60 structures, nouveaux départements, brouillons qualifiés
- [ ] **I** Audit Gmail + réconciliation
- [ ] **J** Sécurité envois (vérification continue)
- [ ] **K** Dashboard : performance par lot, sources, faux positifs/négatifs
- [ ] **L** Tests complets + contrôles 1 à 11
- [ ] **M** Rapport final `docs/rapport-phase10.md`

## Résultats de recherche déjà acquis (ne pas refaire)

Voir `docs/audit-phase10-portefeuille.md` sections B.5 et B.6 :
8 entreprises déjà équipées (rejets corrects), 2 rejets levables
(Zicplace 93, O Lames Déchues 95 — adresse e-mail à vérifier).

Registre d'exploration : `data/history/exploration-ledger.json` (55 entrées).
