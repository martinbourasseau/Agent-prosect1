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
- [x] **D** Scoring v8 — commit `b3cda10`, **388 tests**
      4 niveaux (exprimé 1,0 / observé 0,85 / indirect 0,45 / hypothétique 0,25),
      besoin exprimé porteur sur l'axe qu'il désigne, une preuve ne paie qu'une
      fois (signaux répartis sur les preuves), `evaluated_at` par axe,
      bloc `contactability` séparé des scores, 4 nouveaux signaux faibles.
      **4 bugs de fond corrigés** : lecture du détail comme preuve ; absence de
      garde de négation ; empilement des signaux sur la preuve 0 ; `process_hint`
      cité comme extrait de l'entreprise.
      78 rescorées / **65 modifiées**, baseline v7.1 + deltas dans
      `data/history/scores-v71-vers-v8.json` (clé `crm_before_migration`).
      Régressions lot 9 (données réelles) dans `tests/test_phase10.py`.
      Résultats : annonces Codeur 10-25 → **34-60** ; Brasserie VDL IA 0 → 46 ;
      Dance Center 0 → 39 ; SAM31 0 → 44 ; Canfora 60 → 70 ; Froger 56 → 66 ;
      Caléo 74 → 64 ; Cordes 43 → 39 ; Charme de l'Hêtre 40 → **0**
      (le « aucun site » n'était que dans le détail : preuve `site_absent`
      à créer en G, ne pas réinventer le fait).
- [x] **E** Planificateur — `prospecto/planner.py`, `tests/test_planner.py`
      (26 tests), CLI **`python3 -m prospecto.cli plan`** (`--overview`,
      `--record`, `--lot`, `--count`, `--expressed-share`, `--json`).
      `SearchHistory` (`data/history/search-history.json`, **0 entrée pour
      l'instant**) empêche de relancer une requête ; rendement des sources en
      moyenne a posteriori (prior 8 observations à 15 %) ; couverture suivie
      **par région** (13 régions, 45 départements travaillés, **Corse vierge**).
      Rendement réel : site_officiel 12→4 (**0,260**), page_professionnelle
      12→0 (0,060), **annuaire_pro 31→0 (0,031)**. 40 % du plan consacré aux
      besoins déjà publiés. 27 secteurs neufs encore disponibles.
- [x] **F** Qualification — `prospecto/dossier.py`, `tests/test_dossier.py`
      (30 tests), CLI **`python3 -m prospecto.cli dossier [--company X] [--json]`**.
      Vérification fondée sur la **preuve datée de publication sur source
      officielle**, pas sur un drapeau hérité. Le MX ne prouve que le routage.
      `email_provenance` explicite prime sur l'heuristique de notes.
      **3 coordonnées reconfirmées par relecture le 2026-11-07** (archive
      `data/history/confirmations-coordonnees-2026-11-07.json`) :
      Canfora `david.canfora@sfr.fr` (mentions légales, SIREN 482141652),
      Cordes `ateliercordesetame@gmail.com` (accueil, 3 occurrences),
      **Froger `frogeretancheite@gmail.com` désormais publié EN CLAIR sur
      l'accueil ⇒ la reconstitution est confirmée, plus une hypothèse**.
      Les 4 fiches du lot 9 qualifient. Bilan 78 : **7 qualifiées au sens
      strict**, 48 emails vérifiés, 26 téléphones vérifiés, 13 sans adresse,
      **0 adresse reconstituée non confirmée**. 53 bloquées car déjà contactées.
- [x] **G** Approfondissement lot 9 — **13 / 51 réexaminées**, 38 explicitement
      « non réexaminé » (motif initial NON revalidé, ne pas le présenter comme acquis).
      Archive `data/history/approfondissement-lot9-2026-11-07.json`.
      **4 qualifiées et importées** (lot `2026-11-07-approfondissement`, CRM 78→82,
      4/4 `mx_ok`, 0 doublon) : **O Lames Déchues** 95 (5/89/27, haute),
      **Zicplace** 93 (5/81/31, haute), **Atelier du Bourrelier** 45 (5/98/12, haute),
      **Étanchéité Nantaise** 44 (5/39/22, basse).
      **6 « approfondir »** avec l'étape précise manquante : Rhonalpe (01, e-mail
      JSON-LD seulement, 2 sites), Atelier de Lutherie Cassat/Wellmer (78, e-mail
      vu sur Facebook seulement), Abc Forage 34 (forage34.com non ouvert),
      Forages Berenguer (34, e-mail en snippet seulement), Fermetures Leichnam
      (02, site non ouvert), SET AZUR 83 (identité ambigüe, reprendre par SIREN).
      **3 rejets maintenus** : Aqua Forage (aucun site, absence confirmée par
      l'annuaire), INSIDE (annuaire seul), Cemer (fermeture non levée).
      **2 corrections de département** : Atelier du Bourrelier 91→**45**,
      Rhonalpe 69→**01**. Registre 55→**59** (anciennes décisions conservées,
      nouvelles ajoutées). Historique de recherche : **9 requêtes tracées**.
      Rendement recalculé : site_officiel 13→5 (**0,295**), annuaire_pro 31→0 (0,031).
- [ ] **H** Lot 10 : ~60 structures, nouveaux départements, brouillons qualifiés
- [x] **I** Audit Gmail — `docs/audit-gmail-phase10.md` +
      `data/history/audit-gmail-phase10.json`. **69 adresses interrogées** en
      4 requêtes (domaines + adresses grand public), spam/corbeille inclus,
      `complete:true` exigé. **1 réponse humaine** (opposition Renarde, déjà
      réconciliée), **1 rebond** (severine-lesourd.com, déjà connu),
      **1 challenge** Mailinblack/Alpha Mécanique **non validé**, **0 nouveauté**.
      **0 demande commerciale ⇒ 0 brouillon de réponse** (rien à quoi répondre).
      **5 brouillons vérifiés intacts**, aucun modifié. Rien à réconcilier.
- [x] **J** Sécurité — pré-vol `(False, 3 blocages)` revérifié. `enabled=false`,
      SPF/DKIM/DMARC et protections intacts. Aucun achat, aucun contournement.
      **Incident évité** : `Sender().preflight()` en production réécrit
      `last_checked_at` ; détecté par MD5 et annulé. MD5 des 4 fichiers de
      production stables avant/après tests.
- [ ] **K** Dashboard : performance par lot, sources, faux positifs/négatifs
- [ ] **L** Tests complets + contrôles 1 à 11
- [ ] **M** Rapport final `docs/rapport-phase10.md`

## Résultats de recherche déjà acquis (ne pas refaire)

Voir `docs/audit-phase10-portefeuille.md` sections B.5 et B.6 :
8 entreprises déjà équipées (rejets corrects), 2 rejets levables
(Zicplace 93, O Lames Déchues 95 — adresse e-mail à vérifier).

Registre d'exploration : `data/history/exploration-ledger.json` (55 entrées).
