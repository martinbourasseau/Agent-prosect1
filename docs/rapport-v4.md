# Rapport final — Prospecto v4 « évolution majeure »

**Date : 4 novembre 2026 · Branche `arena/7ed6352a-agent-prosect1` · 16 commits poussés et vérifiés sur GitHub · 107 tests verts**

Ce rapport décrit ce qui a été **réellement implémenté et testé**, les chiffres, les blocages honnêtes, et ce qui reste à configurer avant d'activer l'envoi automatique à grande échelle. Aucune fonctionnalité n'est survendue : tout ce qui est « prêt » a été exécuté ; tout ce qui est « bloqué » l'est volontairement par des garde-fous.

---

## 1. Ce qui a été développé (nouveaux modules v4)

| Module | Rôle | État |
|---|---|---|
| `prospecto/references.py` + `data/references.json` | Bibliothèque de références commerciales extensible **sans code**. Sélection auto selon besoin + secteur. | ✅ testé |
| `prospecto/messaging.py` | Moteur de messages à **8 variantes**, objet + accroche + observation + proposition + démo + CTA + signature + opt-out. Contrôle qualité `check_email_v4`. | ✅ testé |
| `prospecto/suppression.py` + `data/suppression.json` | **Liste de suppression centralisée** (email exact + domaine entier). Alimentée par opt-out, refus, rebonds, plaintes. | ✅ testé |
| `prospecto/deliverability.py` | Vérifications **DNS réelles SPF / DKIM / DMARC** (dnspython), détection des fournisseurs gratuits, limites fournisseur, recommandations. | ✅ testé |
| `prospecto/sender.py` | Moteur d'envoi automatisé : pré-vol, sélection qualifiés, dédoublonnage, **ramp-up / limite journalière**, transports `dry_run` / `smtp` / `gmail_connector`, journal, **conditions d'arrêt** rebonds/plaintes. | ✅ testé |
| `prospecto/replies.py` | Réception/interprétation : **classification d'intention**, association prospect, MAJ CRM, préparation de réponse, relances autorisées, suppression opt-out/refus/rebond. | ✅ testé |
| `prospecto/metrics.py` | Indicateurs agrégés CRM + file + envois + réponses + **performance par variante et par référence**. | ✅ testé |
| `prospecto/models.py` | **4 niveaux de vérification d'email** (`verified` / `public_unverified` / `probable` / `none`), métadonnées v4 des emails. | ✅ testé |
| `data/campaigns/v4-settings.json` | Paramètres de campagne : **`enabled=false`, `dry_run=true`** par défaut, limites, ramp-up, seuils d'arrêt, conformité. | ✅ |
| `dashboard.html` + `server.py` | Tableau de bord complet (12 cartes, filtres, 5 onglets) + API `/api/metrics`, `/api/references`, `/api/campaign` (auth requise). | ✅ testé |
| CLI v4 | `generate-v4`, `references`, `deliverability`, `campaign`, `replies`, `suppression`, `metrics`. | ✅ testé |

Les versions v2/v3 sont **conservées** (générateur, stratégie, file, campagnes, sauvegarde `data/backups/2026-11-04-avant-v4/`). Rien n'a été écrasé.

---

## 2. Chiffres réels (après cette session)

### Prospects
- **Total CRM : 21** (16 existants + **5 nouveaux v4**).
- **Qualifiés : 6** (3 priorité haute, 3 moyenne).
- **Besoins exprimés publiquement : 9** · **Opportunités probables : 3**.
- **8 entreprises déjà contactées** (historique) — exclues de tout nouvel envoi.

### Les 5 nouveaux prospects v4
| Prospect | Secteur / Lieu | Signal | Email |
|---|---|---|---|
| Restaurant traditionnel des quais de Quimper | Restauration / Quimper (29) | Besoin exprimé Codeur (site vitrine + réservation) | aucun (contact masqué) |
| Parfumerie indépendante de Paris | Commerce / Paris (75) | Besoin exprimé Codeur (Shopify 150 produits, POS) | aucun (contact masqué) |
| Organisme de formation — relance prospects | Services | Besoin exprimé Codeur (automatisation relance SMS/IA) | aucun (contact masqué) |
| Activité de revente Vinted — outil IA | Commerce | Besoin exprimé Codeur (automatisation IA) | aucun (contact masqué) |
| **Camping Mer et Camargue / Restaurant Le Pano** | Restauration / Calvisson (30) | Opportunité observable : réservations téléphone uniquement | **`campingmeretcamargue@orange.fr` (vérifié, site officiel)** |

> Les 4 projets Codeur sont des **besoins exprimés réels et frais (4 nov)**, mais Codeur **masque les coordonnées des porteurs** (réservées aux prestataires abonnés). Ils sont enregistrés comme signaux forts « à approfondir » : aucun email fabriqué, aucun envoi tant que la coordonnée n'est pas récupérée légalement.

### Coordonnées
- **14 emails** : **4 vérifiés** (publiés sur le site officiel de l'entreprise) + **10 publics non vérifiés** (sources presse/annuaires).
- **6 téléphones professionnels**.
- Définition honnête : `verified` = email publié sur le site officiel de l'entreprise ; `public_unverified` = email issu d'une source tierce, non testé en délivrabilité. **Aucun email supposé n'est présenté comme vérifié.**

### Messages
- **6 nouveaux emails v4 en file** (variantes `public_need`, `synatrap_ia`, `no_site` + références commerciales).
- File de validation : **13 en attente** (7 v2/v3 + 6 v4), **0 envoyé**.
- **8 variantes** disponibles, chacune contrôlée (40–150 mots, objet ≤ 70 car., démo gratuite + sans engagement, opt-out, signature, pas de promesse interdite).

### Envois / réponses
- **0 email envoyé automatiquement** (campagne désactivée, dry-run par défaut — voir blocages).
- Pipeline **démontré en simulation** : 3 candidats vérifiés sélectionnés, plan ramp-up appliqué, exécution dry-run, **envoi réel correctement bloqué**.
- **0 réponse** des 8 entreprises contactées (recherche Gmail complète, spam inclus). Le module de détection est prêt mais il n'y a pas encore de réponse à traiter.
- Liste de suppression : 0 (alimentée automatiquement dès qu'un opt-out/refus/rebond arrive).

---

## 3. Comment les 2 sites ont été intégrés

- **https://groupebourasseau.com** et **https://synatrap.com** ont été **analysés réellement** (identité visuelle, structure, fonctionnalités, positionnement, secteur) et stockés dans `data/references.json`.
- **Sélection automatique** : besoin site/refonte → Groupe Bourasseau (site institutionnel) ; besoin IA/automatisation → Synatrap (plateforme d'agents IA). Bonus de « kind » pour éviter les mauvais appariements.
- **Extensible sans code** : ajouter une référence = éditer `data/references.json`.
- **URLs cliquables**, un seul lien par email (pas de surcharge).
- **Paternité — point de vigilance** : les mentions légales des 2 sites ne sont pas publiées et aucun dépôt GitHub dédié n'a été trouvé. Le statut est donc **`owner_declared`** avec des formulations **attributives au groupe** (« le site institutionnel que j'ai conçu pour mon groupe », « SYNATRAP, la plateforme que je développe avec mon groupe »). **À confirmer avec Martin avant activation à grande échelle** — aucune affirmation de réalisation personnelle au-delà de ces formulations.

---

## 4. Démo gratuite (argument central)

Chaque email distingue clairement :
- **Démo gratuite** = première démonstration personnalisée et limitée, **sans engagement** (maquette de site ou démo concrète d'agent IA sur un cas réel).
- **Création complète** = prestation payante, jamais promise gratuite.
Formulations contrôlées par `check_email_v4` (pas de « réalisation complète gratuite », pas de fausse promesse).

---

## 5. Sécurité / conformité (garde-fous actifs)

- **Envoi désactivé par défaut** (`enabled=false`, `dry_run=true`). Activation explicite + pré-vol obligatoire.
- **Pré-vol bloque l'envoi réel** tant que : campagne non activée, SPF/DKIM/DMARC non conformes, ou domaine expéditeur gratuit.
- **Liste de suppression centralisée** vérifiée à la sélection ET juste avant chaque envoi.
- **Aucune relance après opposition ou refus explicite** (ajout automatique à la suppression).
- **Arrêt automatique** si rebonds > 5 % ou plaintes > 0,1 % (après 20 envois).
- **Dédoublonnage** (pas de double envoi), **montée en charge progressive** (5→10→15→20→30→40/jour), délai entre envois.
- **Opt-out simple** dans chaque email, expéditeur identifié, signature professionnelle.
- **Aucun secret sur GitHub** (mots de passe / jetons dans des fichiers gitignorés). **Aucune donnée sensible exposée au navigateur** (API authentifiée).
- **Ne prétend jamais qu'un email est délivré** parce que l'API l'a accepté : le journal distingue `sent` / `delivered` / `bounced` / `dry_run`.

---

## 6. Tests

- **107 tests unitaires verts** (`python3 -m unittest discover -s tests`), dont **43 nouveaux tests v4** couvrant : niveaux de vérification, références, 8 variantes, suppression (email + domaine), délivrabilité, portes de sécurité du sender (vérifié-only, suppression, dédoublonnage, score, ramp-up, arrêt rebonds), classification d'intention, mise à jour CRM + suppression sur opt-out, métriques.
- Smoke tests CLI : `references`, `deliverability` (DNS réel), `campaign preflight`, `suppression`, `replies classify`, `metrics`, `generate-v4`.
- Dashboard testé : login 302, endpoints OK, 401 sans auth.

---

## 7. Blocages honnêtes (ce qui empêche l'envoi de masse aujourd'hui)

1. **Domaine expéditeur = `gmail.com` (gratuit).** SPF/DKIM/DMARC sont gérés par Google, non configurables par Martin. La prospection commerciale en masse depuis un compte Gmail gratuit est **contraire aux CGU** et dégrade la délivrabilité (voire suspend le compte). Le pré-vol le signale et **bloque l'envoi réel**. → **Un domaine professionnel dédié + un prestataire d'envoi adapté sont indispensables.**
2. **Codeur masque les contacts des porteurs.** Les besoins exprimés sont réels mais les emails ne sont pas récupérables sans abonnement prestataire. → Ces prospects restent « à approfondir » tant que la coordonnée n'est pas obtenue légalement.
3. **Paternité des 2 exemples non établie formellement** (`owner_declared`). → À confirmer avant grande échelle.
4. **Aucune réponse pour l'instant** : le module est prêt, mais la boucle réponses/relances n'a pas encore de données réelles.

---

## 8. Ce qui reste à configurer avant activation complète

**Par Martin (prérequis bloquants) :**
1. **Domaine d'envoi professionnel** (ex. `contact@prospecto.website` ou domaine dédié) avec **SPF, DKIM, DMARC** publiés.
2. **Prestataire d'envoi** : Google Workspace sur domaine propre, ou ESP (Brevo, Sendgrid, Mailgun…) avec SMTP/API. Renseigner `PROSPECTO_SMTP_HOST/PORT/USER/PASSWORD` (env, jamais sur GitHub) pour le transport `smtp`, ou utiliser le connecteur Gmail via l'agent.
3. **Confirmer la paternité** des 2 références (Groupe Bourasseau / Synatrap) et la formulation commerciale.
4. **Valider les paramètres de campagne** (limites, ramp-up, seuils d'arrêt) puis activer : `campaign activate` (dry-run) → vérifier → `campaign activate --live`.
5. **Récupérer légalement les coordonnées** des prospects « à approfondir » (abonnement Codeur ou autre source publique) avant de les envoyer.

**Chauffe recommandée :** démarrer à 5/jour, surveiller rebonds/plaintes, monter progressivement, ne jamais viser les maxima fournisseur.

---

## 9. Commandes utiles

```bash
python3 -m prospecto.cli references list                 # bibliothèque de références
python3 -m prospecto.cli deliverability                  # SPF/DKIM/DMARC du domaine expéditeur
python3 -m prospecto.cli campaign preflight              # contrôles avant envoi
python3 -m prospecto.cli campaign status                 # état de la campagne
python3 -m prospecto.cli generate-v4 <fichier> --campaign <nom> --include-moyenne
python3 -m prospecto.cli campaign run                    # envoi (dry-run par défaut)
python3 -m prospecto.cli replies process --file <json>   # traiter les réponses reçues
python3 -m prospecto.cli suppression list                # liste de suppression
python3 -m prospecto.cli metrics                         # indicateurs agrégés
python3 -m unittest discover -s tests                    # 107 tests
```

**Tableau de bord :** Espace Prospecto (serveur local, port 8787, protégé par mot de passe — fichier gitignoré, non publié sur GitHub).

---

*Prospecto — Martin BOURASSEAU · Création web · Agents IA · Automatisation · https://prospecto.website*
