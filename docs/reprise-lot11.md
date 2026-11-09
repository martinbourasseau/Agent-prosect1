# Reprise — état après le Lot 11 (9 novembre 2026)

## Où on en est

Lot 11 **exécuté et clos** : 82 structures examinées, 16 fiches importées,
4 brouillons prêts, **0 envoi**. Rapport complet :
`docs/rapport-final-lot11-2026-11-09.md`.

| Élément | Valeur |
|---|---|
| CRM | `data/crm/prospects.json` — **108 fiches** |
| Registre d'exploration | `data/history/exploration-ledger.json` — **213** |
| File de validation | **77 items** : 60 `sent`, 6 brouillons, 1 en attente, 10 obsolètes |
| Journal d'envois | **60** (protégé, MD5) |
| Suppression | **2** (protégé, MD5) |
| Tests | **703 verts / 24 fichiers** — `python3 -m unittest discover tests -q` |
| Axes / priorité | **v8** / **v10-priority** sur les 108 fiches |
| Dashboard | port **8787**, `python3 -m prospecto.server --host 0.0.0.0 --port 8787` |

## Blocage à ne pas contourner

Le pré-vol renvoie `(False, 3 motifs)` :

1. `enabled=false` — activation explicite requise ;
2. DKIM non détecté pour le domaine expéditeur ;
3. **domaine expéditeur gratuit (Gmail)** — prospection de masse déconseillée/
   interdite par les CGU. **C'est le blocage de fond.**

`enabled=false`, `dry_run=true`. Ne pas activer, ne pas acheter de service, ne pas
modifier les DNS, ne pas valider de challenge anti-bot.

## Prochaine action humaine

Valider ou rejeter les 4 brouillons du lot 11 (libellé Gmail
`Prospection/2026-11-09-lot11`, `Label_9`) :

| Entreprise | Destinataire | File | Brouillon Gmail |
|---|---|---|---|
| Miditraçage Esvia | `contactweb@miditracage.com` | `2026-11-09-lot11-001` | `1a1c2638fdfbe9c8` |
| Métallerie des Alpilles | `contact@metalleriedesalpilles.fr` | `2026-11-09-lot11-002` | `1a1c2639c4412b5b` |
| Bureau Bois Concept | `contact@etudebbc.fr` | `2026-11-09-lot11-003` | `1a1c263ab077a895` |
| ETS Frézouls | `contact@frezouls.fr` | `2026-11-09-lot11-004` | `1a1c263b80ce4a95` |

Les 2 brouillons antérieurs (Caléo, Ripaud) sont conservés **sans modification**.

## Pistes non épuisées, par ordre d'intérêt

- **3 fiches en priorité haute mais confiance faible** sur l'axe porteur :
  **FMESURE**, **Plast e-Concept**, **SAS Adrien Fernandes D&S**. Une seconde page
  lue suffirait à lever le doute et à autoriser un brouillon.
- **3 fiches sans adresse publiée** : **3DM Impression** (défaut le plus net du lot :
  liens boutique vers le domaine de préproduction), **Occibox**,
  **Léonard & Parmentier**. Approche téléphonique ou courrier à envisager.
- **15 structures classées « à approfondir »** dans
  `data/history/lot11-recherches-2026-11-09.json`, dont SICA POM ALPES (offre France
  Travail `203BKRD`, saisie Excel/factures, pas de site) et Aura Sun (Aurillac 15,
  RGE expiré le 15/03/2026).

## Ne pas refaire

- **Ne pas recontacter** les 8 entreprises envoyées le 09/11 : Étanchéité Nantaise,
  Alain Louis, Atelier du Bourrelier, Zicplace, O Lames Déchues, Cordes et Âme,
  Froger, Canfora David.
- **Ne pas « corriger »** les brouillons déjà envoyés.
- **Opposition** : Renarde / Nicolas Smets `celarenarde@gmail.com`.
  **Rebond dur** : `contact@severine-lesourd.com`.
- **Challenge Mailinblack / Alpha Mécanique** : non validé, à laisser tel quel.
- **Lectures échouées, ne plus insister** : `3domega.fr`,
  `bernardforestier-ramonage-auch32.fr`, `maxelec89.fr` (2 échecs).
- **Réseaux et marketplaces** : proxi-*, Izi/Proxi Grue, Grue Experts, SOCOREBAT,
  Les Compagnons Dépanneurs, allo-panneau-solaire, Les Grandes Imprimeries,
  Codeur.com, StarOfService, PagesJaunes, Kompass, Nextdoor, Jooble.
- **Annuaires seuls** : 58 examinés, **0 qualifié**. Ne pas y consacrer de requêtes.

## Pièges techniques confirmés ce lot

- **Types de preuve** : seuls `public_need`, `website_gap`, `sector_opportunity`,
  `site_absent`, `site_indisponible`, `site_obsolete`, `processus_manuel`,
  `parcours_incomplet`, `maturite_existante`, `signal_confiance` existent. Un type
  inconnu est **ignoré en silence** par le moteur : toujours appeler
  `Evidence.validate()`.
- **Contre-signaux** : le moteur ne lit que les preuves `maturite_existante`, et la
  force dépend de **marqueurs textuels** dans la citation et le détail. Une liste
  séparée n'a aucun effet.
- **`email_dns_status`** doit être renseigné, sinon `priority.assess` plafonne tout
  à « à approfondir » même avec une adresse valide.
- **`custom_subject` > 70 caractères** retombe silencieusement sur
  « Une idée pour votre entreprise ? ».
- **`recommended_service` commençant par une majuscule** est repris tel quel :
  c'est le moyen d'écrire une proposition naturelle.
- **`gmail_draft_id`** (et non `gmail_message_id`) classe un item de file en
  brouillon dans le tableau de bord.
- **`Sender(settings_path=…)`** : `preflight()` **persiste** l'état DNS. Toujours
  passer une copie `tempfile`, sinon `v4-settings.json` est modifié.
- **`by_lot` compte les brouillons sur `status == "brouillon_créé"`.**
- **`load_outbound()`** expose `.from_production`, pas `.entries`.
- **`analyse_page()`** renvoie un dict : `proves_purchase_intent` est un champ de
  chaque problème de `report["problems"]`.
- **Login du dashboard** : `POST /login` en form-urlencoded, pas `/api/login`.
- **Tests** : ne pas figer un compteur de portefeuille. Recalculer depuis
  `CRM().records`, la file ou le registre.

## Scripts

- `scripts/lot11/fiches.py` — définitions sourcées des 16 fiches (preuves, citations,
  contre-signaux). Aucune écriture.
- `scripts/lot11/importer.py` — import **idempotent**, simulation par défaut ;
  `--applique` pour écrire. Relancé après import : 16 collisions, 0 création.

Sauvegardes de ce lot : `/tmp/sauvegarde_lot11/data/` (268 fichiers) et
`/tmp/protected_lot11.md5` (4 fichiers) — non persistées hors session.
