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
- [~] **H** Lot 10 — **13 / ~60 structures examinées**, 1 fiche importée
      (Alain Louis 78). Archive `data/history/lot10-exploration-2026-11-07.json`
      (`objective_reached:false`). **47 restantes** + **5 brouillons à créer**.
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
- [x] **K** Dashboard — panneau « Pilotage & Recherche », commit `3baaf4b`.
      `metrics` expose `qualification`, `recherche`, `revue_portefeuille`.
- [x] **L** Tests — `tests/test_phase10_livraison.py`, commit `3baaf4b`.
- [x] **M** Rapport — `docs/rapport-mission-2026-11-07-phase10.md`, commit `52c48a4`.
      (Le nom diffère de celui prévu ici : c'est le fichier réellement écrit.)

## Résultats de recherche déjà acquis (ne pas refaire)

Voir `docs/audit-phase10-portefeuille.md` sections B.5 et B.6 :
8 entreprises déjà équipées (rejets corrects), 2 rejets levables
(Zicplace 93, O Lames Déchues 95 — adresse e-mail à vérifier).

Registre d'exploration : `data/history/exploration-ledger.json` (55 entrées).


---

## Restant à la fin de la phase 10 (reprendre ici, ne pas refaire les recherches)

1. **Brouillons du lot 10 — NON FAITS.** Créer le label
   `Prospection/2026-11-07-lot10`, puis rédiger et déposer les brouillons des
   5 fiches neuves qualifiées (O Lames Déchues, Zicplace, Atelier du Bourrelier,
   Alain Louis, Étanchéité Nantaise). Rappel : plafond **170 mots, viser ≤167**,
   `LotRotation` obligatoire dans le test de longueur, `select_variant` renvoie
   `synatrap_ia` pour tout besoin IA ⇒ forcer la variante. **Ne pas modifier les
   5 brouillons existants.** `update_draft` perd les labels ⇒ re-add +
   resynchroniser `gmail_message_id`.
2. **Lot 10 : 47 structures restantes** pour atteindre ~60. Pistes déjà tracées
   dans l'historique (`plan --lot 2026-11-07-lot10`, 14 entrées) : 79 Niort,
   81 Albi, 61 Alençon, 73 Chambéry, 65 Tarbes, 47 Agen, 63 Issoire,
   60 Compiègne, 58 Nevers, 57 Thionville, 40 Mont-de-Marsan, 53 Laval.
   **Attention** : les motifs de besoin exprimé viennent d'être corrigés, les
   anciennes requêtes Corse/pressoir ont échoué pour cause de bruit — ne pas les
   rejouer telles quelles.
3. **38 fiches du lot 9 non réexaminées** (liste dans
   `data/history/approfondissement-lot9-2026-11-07.json`, décision
   `non réexaminé`). Dont **Cemer 34** « probablement fermé » jamais vérifié.
4. **6 pistes « approfondir » de G**, étape manquante écrite pour chacune :
   Rhonalpe 01 (mentions légales des 2 sites), Atelier de Lutherie 78
   (`mareil-lutherie.com`), Abc Forage 34 (`forage34.com`), Forages Berenguer 34
   (pied de page + page contact), Fermetures Leichnam 02 (Contact & Devis),
   SET AZUR 83 (**reprendre par SIREN**, identité ambigüe).
   **2 du lot 10** : Régis de Izarra 80 (aucun e-mail publié), Bossard
   Philippe 94 (e-mail non vu).
5. **Échelle commune aux 3 axes** — limite structurelle documentée en §2 du
   rapport. Demande un calibrage avec revue humaine, pas un patch.


---

# REPRISE DU 2026-11-07 (seconde passe) — travaux B à J

**CETTE SECTION PRIME sur la liste ci-dessus.** La liste A→M contenait des
cases non cochées alors que les travaux étaient commités : les `.replace()`
utilisaient des ancres inexistantes et ne faisaient rien en silence. Corrigé
ici avec assertions sur chaque ancre.

- [x] **A** Reprise vérifiée — branche `arena/7ed6352a-agent-prosect1`, HEAD
      `52c48a4` propre et poussé (local == distant). **Aucune base SQLite**
      (CRM en JSON, 83 fiches, 100 % v8). MD5 des 4 journaux **4/4 OK**.
      Dashboard vivant (HTTP 302 sur /). **473 tests** au vert à l'arrivée
      (et non 350 : 123 ont été ajoutés depuis).
- [x] **B** Calibration commerciale v9 — `prospecto/priority.py`,
      `docs/calibration-priorite-v9.md`, `tests/test_priority_v9.py` (25 tests).
      Priorité **transversale**, distincte des 3 axes **inchangés**.
      **27 priorités modifiées / 83, 0 score d'axe modifié.**
      Archives : `priorite-commerciale-v8-vers-v9.json` (CRM complet avant
      migration + avant/après par fiche) et `simulation-calibration-v9.json`.
      **498 tests.** Une calibration rejetée par la simulation est documentée.
- [x] **C** 5 brouillons lot 10 — **créés et vérifiés**. Label
      `Prospection/2026-11-07-lot10` = **`Label_8`** (créé, aucun doublon : la
      recherche `in:drafts to:<les 5>` renvoyait 0 avec `complete:true`).
      `check_email_v4` **conforme 5/5** (124 à 137 mots, objets 55-65 car.).
      | Entreprise | Brouillon | Message |
      |---|---|---|
      | O Lames Déchues | `r-5364782935530613267` | `1a1bc3d084adb267` |
      | Zicplace | `r8291386275938075826` | `1a1bc3d138306410` |
      | Atelier du Bourrelier | `r-4868647836702402127` | `1a1bc3d26f3748e2` |
      | Alain Louis | `r-3698618390914515863` | `1a1bc3d302b54ef5` |
      | Étanchéité Nantaise | `r5641186055023628194` | `1a1bc3d3aadd1cf6` |
      5/5 `["DRAFT","Label_8"]`. **Les 5 anciens brouillons sont intacts**
      (mêmes ids, mêmes labels `Label_7`/`Label_6`). CRM + file de validation
      synchronisés (**68 → 73**). Archive
      `data/messages/brouillons-2026-11-07-lot10.json`.
      **Aucune référence commerciale citée** : la bibliothèque ne documente pas
      ce que groupebourasseau.com / synatrap.com démontrent ; les présenter
      comme une réalisation comparable serait une invention.
- [ ] **D** 47 structures restantes
- [ ] **E** 38 fiches non réexaminées
- [ ] **F** 8 pistes à approfondir
- [ ] **G** Nouvel audit Gmail
- [ ] **H** Sécurité (vérification continue)
- [ ] **I** Tests + contrôles 1-10
- [ ] **J** Rapport final de seconde passe
