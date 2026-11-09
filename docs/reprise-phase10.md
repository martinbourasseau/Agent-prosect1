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
- [~] **D** **20 structures examinées sur 47 — objectif NON atteint, assumé.**
      2 qualifiées et importées : **Ouest Affûtage** (22, `refonte 89`, haute 71,
      lien e-mail en `email:` au lieu de `mailto:`) et **Sellerie Industrielle
      de l'Est** (57, moyenne 50). 6 écartées, 7 à approfondir, 5 non retenues.
      **NE PAS REFAIRE ces 20 décisions** : `lot10-suite-exploration-2026-11-07.json`.
      **27 structures restent.** Les 13 recherches antérieures n'ont pas été refaites.
      **DÉCOUVERTE MÉTHODE : les requêtes « besoin exprimé » sont structurellement
      captées par les agences, MÊME avec `NEED_QUERY_EXCLUSIONS`** (Niort/Alençon/
      Chambéry : 4 vendeurs, 0 prospect). Les agences citent les mots du prospect
      dans leur argumentaire. Les exclusions lexicales ne peuvent pas corriger
      cela : changer de canal (appels d'offres), pas de requête.
- [x] **E** 38 entrées auditées — **correction factuelle : ce ne sont PAS des
      fiches CRM**, mais 38 entrées du registre d'exploration jamais promues
      (**0/38 au CRM**, vérifié aussi par nom approché). Donc ni score, ni
      coordonnées, ni statut Gmail à auditer. Audit sur le motif de rejet :
      annuaire seul 14, à revalider 13, déjà outillée 9, concurrent 2.
      **11 à clore, 27 maintenues.** 0 doublon, 0 opposition, 0 dérive.
      `audit-38-fiches-2026-11-07.json`. Aucune donnée historique modifiée.
- [~] **F** 8 pistes traitées, **2 qualifiées — pas 8 prospects.**
      **QUALIFIÉES** : Fermetures Leichnam 02 (email en clair ×2, **formulaire
      Typeform FERMÉ** remplacé par la pub de l'éditeur, `refonte 81`) ·
      Forages Berenguer 34 (`forageberenguer@orange.fr` en clair, formulaire
      sans qualification). **ÉCARTÉES** : Atelier de Lutherie 78 (2 pages lues,
      aucun email) · Abc Forage 34 (**déjà outillé**, devis qualifié) ·
      Régis de Izarra 80 (2 pages, aucun email).
      **ENCORE OUVERTES — ne refaire que l'étape indiquée** :
      **Rhonalpe 01** → lire les mentions légales du site officiel (SIREN
      751732702 ; rue René Nicod **fermée le 31/01/2025**, siège 1 rue Grandes
      Roches ; email vu sur annuaire tiers seulement, NON retenu) ·
      **Bossard 94** → lire la page Contact (accueil seul lu).
      **SET AZUR 83** → identité levée, **SIREN 983435405, La Seyne-sur-Mer**,
      aucun site officiel trouvé. `approfondissement-8-pistes-2026-11-07.json`.
- [x] **G** Audit Gmail — `audit-gmail-seconde-passe-2026-11-07.json`.
      Rebonds **et** oppositions : requêtes **exhaustives** (`complete:true`),
      **1 chacune, les connues, 0 nouveauté**. 0 réponse humaine, 0 demande
      commerciale, 0 challenge nouveau. 10 brouillons de prospection, anciens
      5 intacts. **PIÈGE DOCUMENTÉ : exclure son propre expéditeur** — une
      requête sur « ne pas me relancer » matche nos propres emails, qui
      contiennent tous cette formule. Mailinblack **NON validé**.
- [x] **H** Sécurité — `enabled=false`, `dry_run=true`, pré-vol **`(False, 3)`**,
      liste de suppression 2, opposition Renarde maintenue. **0 envoi.**
- [x] **I** **508 tests OK** (+10 livraison seconde passe). 257 JSON, 0 invalide.
      **MD5 4/4 revérifiés APRÈS les tests** (aucune pollution). Dashboard
      HTTP 302, login 302, API : 87 fiches / 16 qualifiables / priorités v9.
      Deux invariants de test corrigés car trop forts (fiche postérieure à la
      migration ⇒ trace de création, pas entrée de migration).
- [x] **J** `docs/rapport-final-phase10-2026-11-07.md`, 10 parties.

## État de fin — à lire avant toute reprise

**CRM 87 fiches** (83 + 4), 100 % axes v8 + priorité `v9-priority`.
**16 dossiers qualifiables / 87 (18 %)**. Priorités : haute 9, moyenne 51,
basse 13, à approfondir 14. Registre d'exploration **100** structures.
**58 départements, 13/13 régions.** File de validation **73**. **10 brouillons
en attente, 0 envoi.** Les 4 nouvelles fiches sont au statut `nouveau`,
**sans brouillon**.

**NE PAS LANCER LE LOT 11.** Voir §10 du rapport final. Le déblocage réel est
DNS + validation des brouillons, ce qui **exige l'accord de l'utilisateur**.
Ensuite, sans coût : approfondir les 12 pistes ouvertes du registre (dont
**La Châtaigneraie de Bel Air** 23 et **ERM 27**, où il ne manque que la page
contact), puis les 27 structures restantes de D, **en sites officiels
uniquement** (rendement 0,352 contre 0,029 pour les annuaires).

---

# PHASE 10 BIS — 2026-11-07 ( CETTE SECTION PRIME SUR TOUTES LES AUTRES )

Rapport : `docs/rapport-final-phase10bis-2026-11-07.md`
Délivrabilité : `docs/delivrabilite-phase10bis.md`
**557 tests OK. CRM 92 fiches. 13 qualifiables. 0 envoi par l'agent.**

## DEUX PRÉMISSES DU BRIEF ÉTAIENT FAUSSES — À SAVOIR AVANT TOUTE REPRISE

1. **Il ne restait PAS 10 brouillons.** 8 ont été **envoyés hors agent le
   09/11/2026 entre 12:22:30 et 12:23:17** (5 `Label_8` lot 10, 3 `Label_7`
   lot 9), libellé `SENT` constaté. **Il reste 2 brouillons** : Caléo
   (`Label_7`, `1a1b672541671292`) et Ripaud (`Label_6`, `1a1b16dee5899e57`).
   Les 8 fiches sont passées à `contacté` ⇒ **aucune nouvelle approche**.
   Réconciliation additive : journal des rapprochements **4 → 5** entrées.
   `send-log.json` reste à **60** (inchangé, protégé). Total observé : **68**.
2. **`Label_8` ÉTAIT le bon libellé.** `list_labels` : `Label_8` →
   `Prospection/2026-11-07-lot10`. Gmail utilise des identifiants opaques.
   **Aucun reclassement nécessaire, aucun brouillon recréé.**

**PIÈGE GRAVE ÉVITÉ — à réutiliser :** `label:Prospection/2026-11-07-lot10`
(nom imbriqué) **et** `label_ids=["Label_8"]` + `in:drafts` ont renvoyé **0
avec `complete:true`** alors que les messages existaient, en `SENT`.
**Un zéro filtré ne prouve jamais une disparition.** Toujours `in:anywhere`
sur les destinataires avant de conclure.

## Travaux réalisés

- [x] **A** Reprise vérifiée. Aucune base SQLite. Sauvegarde `data/` dans
      `/tmp/sauvegarde_bis` (260 fichiers). MD5 relevés avant intervention.
- [x] **B1** **Périmètre de recherche ATTEINT : 29 structures examinées** (27
      restants visés), 11 sites réellement lus. 4 retenues, 6 écartées,
      19 à approfondir. **NE PAS REFAIRE** : voir
      `phase10bis-recherches-2026-11-07.json`, clé `B1_perimetre_recherche`.
      **5 fiches importées** : Scierie Labrue 19, Menuiserie Mirolo 02,
      D2Bois 02, Delahautemaison 84, ERM 27 27. Toutes `mx_ok`, adresse
      **lue directement**, statut `nouveau`, **aucun brouillon**.
      **2 corrections de département** : Mirolo 68→**02**, AZ 68→**60**.
- [~] **B2** Registre : D2Bois et Mirolo **qualifiées**, AZ Menuiseries
      **ouverte** (adresse non lue), **Travaux Obat CLÔTURÉE avec preuve**
      (Obat = éditeur SaaS de devis, concurrent direct). Les autres entrées
      gardent leur étape manquante. Registre **131**, portefeuille **92**,
      séparation verrouillée par test.
- [x] **C** **La Châtaigneraie de Bel Air 23 → approfondir, PAS de brouillon.**
      Avis bien publié sur son site mais **NON DATÉ** ⇒ ne prouve pas un
      problème actuel. Signal solide = formulaire de réservation sans dates
      ni nombre/gabarit de chiens. Adresse vue en index de recherche mais
      **absente des 2 lectures directes** ⇒ non confirmée.
      **ERM 27 27 → qualifiée, PAS de brouillon.** SIRET 33215991200085,
      `erm27@erm27.fr` lu en clair, 3 pages lues. Besoin **modeste**
      (consentement implicite) ; contenu à jour + prestataire web déjà crédité
      (My Market Office). **Les horaires contradictoires du lot précédent
      n'ont PAS été retrouvés ⇒ signal abandonné.**
- [x] **D** **`prospecto/discovery.py` + 25 tests.** Classement par
      **identité d'auteur**, statut de vendeur **éliminatoire et évalué en
      premier**. 6 classes. 9 détecteurs de problèmes opérationnels, aucun ne
      prouve une intention d'achat. Régressions sur les vraies pages d'agences.
      **RENDEMENT : « 0,352 / 0,029 » étaient des `yield_score` LISSÉS**
      `(q + 8×0,15)/(n + 8)`, pas des taux bruts. Réel même méthode :
      **site_officiel 70 exam / 17 qual = 0,243 brut** ;
      **annuaire_pro 34 exam / 0 qual = 0,000 brut**. `SourceYield` refuse de
      comparer des méthodes différentes.
      **Canal recrutement testé : même défaut d'auteur** via agrégateurs.
- [x] **E** **DÉFAUT VÉRIFIÉ, NON CORRIGÉ** : `MATURITY_FACTOR=0.8` ne
      s'applique qu'aux automatisations détectées, **pas aux preuves typées
      `maturite_existante`** ⇒ aucun axe réduit, `counter_signals` vide.
      ERM 27 = `refonte 89 / haute 71` malgré des contre-signaux dominants.
      **16 fiches concernées, 5 en haute, écart simulé jusqu'à 18 points.**
      Simulation lecture seule archivée ; **2 fiches marquées
      `revue_humaine_requise`** (Delahautemaison, ERM 27).
      **Aucun score modifié.** Recalibration = protocole v9 + accord utilisateur.
- [x] **F** `check_email_v4` **5/5 conformes** sur les messages du lot 10
      (contrôle a posteriori, ils ont été envoyés hors agent, non modifiés).
      Libellés corrects. 2 brouillons restants.
- [x] **G** **3 motifs réels du pré-vol** : campagne désactivée · **DKIM non
      détecté** · **domaine expéditeur gratuit (Gmail), prospection de masse
      proscrite par les CGU**. Le 3e est le blocage de fond : SPF/DKIM/DMARC
      de `gmail.com` appartiennent à Google. **Domaine dédié = prérequis.**
      Plan 7 étapes à critères d'arrêt objectifs, comparatif 5 options,
      solution à **~10–15 €/an et 0 € d'envoi**. **Aucun DNS modifié.**
- [x] **H** Requêtes `in:anywhere` spam+corbeille inclus, `complete:true` :
      **0 réponse, 0 rebond, 0 opposition, 0 challenge nouveaux**.
      Opposition Nicolas Smets maintenue. Mailinblack **NON validé**.
- [x] **I** `enabled=false`, `dry_run=true`, pré-vol `(False,3)`. Aucun achat,
      aucune souscription, aucun contournement, aucune suppression.
- [x] **J** Dashboard HTTP 302, API 92 fiches / 13 qualifiables / v9.
      **LIMITE À CORRIGER : l'API compte 60 envois (journal production) et
      ignore les 8 du journal des rapprochements ⇒ total réel 68.**
- [x] **K** **557 tests OK.** MD5 : `send-log`, `v4-settings`, `suppression`
      **identiques** ; `reconciliations.json` **+1 entrée par conception**.
      3 invariants de test corrigés (une fiche contactée n'est plus
      « qualifiable » : vérifier la **qualité** du dossier, pas l'éligibilité).
- [x] **L** Rapport final en 8 parties.

## Reprise : où continuer exactement

1. **NE PAS LANCER LE LOT 11.**
2. **Ne pas recontacter les 8 entreprises envoyées le 09/11** (statut
   `contacté`, `gmail_sent_message_id` renseigné).
3. Priorité réelle : **décision domaine + webhooks de délivrance** (accord
   utilisateur et dépense), puis **recalibration des contre-signaux**.
4. Sans coût, ensuite : les **19 « à approfondir »** du B1 et les **3 pistes au
   signal fort mais adresse non lue** — **DBS Location Benne 13** (la page
   demande « type de benne, taille, ville » que le formulaire ne collecte
   pas ; contradiction de prix 150 €/200 € HT), **AZ Menuiseries 60**
   (`{title}` et `{vendor_count}` publiés ; mention RGPD parlant d'un champ
   téléphone inexistant), **La Châtaigneraie 23**. Pour chacune il ne manque
   que **lire l'adresse publiée** sur une page officielle.
5. **Règle adresse inchangée :** l'extracteur laisse tomber certains pieds de
   page. Une adresse présente dans l'index de recherche de la bonne URL mais
   absente de la lecture directe reste **NON CONFIRMÉE**. Ne jamais la
   deviner, ne jamais l'utiliser sur la foi d'un extrait.
