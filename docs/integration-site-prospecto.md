# Rattacher l'Espace Prospecto à https://prospecto.website

> Objectif : accéder à l'outil de prospection (CRM + file de validation + campagnes)
> depuis le site, avec une navigation fluide, une connexion sécurisée et une interface
> cohérente avec l'identité visuelle. **Sans reconstruire le site marketing ni créer une
> seconde application inutile.**

## 1. Architecture constatée (avant toute modification)

| Élément | Constat |
|---|---|
| Site marketing | `martinbourasseau/prospecto-site` — Next.js 16 (App Router), React 19, Tailwind v4, GSAP/three. Page unique à sections + pages légales. |
| Domaine | `https://prospecto.website` (redirect `www` → apex dans `next.config.ts`). |
| Identité | Thème sombre (`color-scheme: dark`), police **Archivo** auto-hébergée. Jetons : `--abyss #03050a`, `--night #08101f`, `--anthracite #161b25`, `--glacier #9cbcff`, `--tide #79d2d6`, `--text #e9edf4`, `--line rgba(255,255,255,.09)`. |
| Sécurité site | `X-Frame-Options: SAMEORIGIN` → **le site ne peut pas être mis en iframe cross-origin**, et inversement. L'intégration se fait donc par **lien**, pas par iframe. |
| Nav | `components/Nav.tsx` : liens de section (`/#accueil`, `/#prospecto`…), bouton « Parlons de votre projet », menu mobile. |
| Outil de prospection | Ce dépôt (`Agent-prosect1`) : moteur Python (`prospecto/`), données `data/`. Nouveau : `prospecto/server.py` = **Espace Prospecto** (dashboard + API, stdlib, aucun framework). |

**Décision :** le site marketing reste tel quel. L'Espace Prospecto est l'application
métier (celle qui pilote la prospection). On ajoute simplement un lien « Espace Prospecto »
dans la nav du site, pointant vers le dashboard déployé.

## 2. Ce qui a été construit ici

- `prospecto/server.py` : serveur HTTP stdlib (`ThreadingHTTPServer`), bind `0.0.0.0`.
  - **Connexion sécurisée** : mot de passe + cookie de session signé HMAC (12 h), `HttpOnly`,
    `SameSite=Lax`. Toutes les routes (sauf `/login`, `/healthz`) exigent la session.
  - **API JSON** reliée aux données : `/api/stats`, `/api/prospects`, `/api/queue`,
    `/api/campaigns`, `POST /api/queue/{id}/approve|reject`.
  - **Aucun envoi d'email** depuis le dashboard : approuver ne change que le statut.
  - En-têtes de sécurité : `nosniff`, `X-Frame-Options SAMEORIGIN`, `Referrer-Policy`,
    `Permissions-Policy`, `Cache-Control: no-store`.
- `prospecto/dashboard.html` : interface sombre réutilisant les jetons du site (Archivo,
  abyss/glacier/tide), onglets Prospects / Validation / Campagnes, cartes de stats,
  filtres, aperçu des emails, boutons Approuver / Rejeter.
- Secrets **gitignorés** : `data/.dash_password`, `data/.dash_secret` (générés au démarrage,
  ou `PROSPECTO_DASH_PASSWORD` en variable d'environnement).

### Lancer en local
```bash
python3 -m prospecto.server           # http://0.0.0.0:8787
# Mot de passe : data/.dash_password  (ou env PROSPECTO_DASH_PASSWORD)
# Port : env PROSPECTO_PORT (défaut 8787)
```

## 3. Déploiement recommandé (à valider par Martin — aucun déploiement auto)

Deux options, au choix :

### Option A — sous-domaine `app.prospecto.website` (recommandé)
1. Héberger le dashboard sur un petit serveur (VPS, Fly.io, Railway, Render…) qui exécute
   `python3 -m prospecto.server`. Le serveur n'a besoin que de Python 3.11+ et du dossier `data/`.
2. **DNS** : ajouter un enregistrement `CNAME app → <cible hébergeur>` (ou `A` vers l'IP).
3. **HTTPS** : terminer TLS devant le serveur (Caddy / nginx / ou TLS fourni par l'hébergeur).
   Le cookie de session doit être servi en HTTPS en production (ajouter `Secure` au cookie
   une fois en HTTPS — voir §5).
4. Définir `PROSPECTO_DASH_PASSWORD` (fort) côté hébergeur.
5. Mettre `APP_URL = "https://app.prospecto.website"` dans la nav (déjà la valeur par défaut).

### Option B — même domaine, chemin `/app` (reverse proxy)
1. Garder le site Next.js sur `prospecto.website`.
2. Devant, un reverse proxy (nginx/Caddy) route `prospecto.website/app/*` vers le serveur
   Python, et tout le reste vers Next.js.
3. Adapter le serveur pour servir sous le préfixe `/app` (ou laisser le proxy réécrire).
4. `APP_URL = "https://prospecto.website/app"`.

> L'option A est la plus simple et la plus isolée (le CRM n'est pas servi par le même
> process que le site public). L'option B garde une URL unique mais demande un proxy.

## 4. Intégration dans la nav du site (patch prêt, non appliqué)

Le patch est dans `integrations/prospecto-site/` :
- `Nav.original.tsx` : copie de référence du fichier actuel.
- `Nav.proposed.tsx` : version complète avec le lien « Espace Prospecto » (desktop + mobile).
- `nav-espace-prospecto.patch` : diff unifié (3 insertions).
- `README.md` : mode d'emploi.

**À appliquer dans le dépôt `prospecto-site`** (pas ici), après choix de l'URL :
```bash
# dans prospecto-site
git apply /chemin/vers/nav-espace-prospecto.patch
# ou remplacer components/Nav.tsx par Nav.proposed.tsx
```
Le lien utilise les classes `btn btn-glass glass` déjà présentes dans le site → rendu
cohérent, aucun CSS à ajouter.

## 5. Durcissement avant mise en production
- Servir le dashboard **uniquement en HTTPS** ; ajouter le flag `Secure` au cookie de session.
- Mot de passe fort via `PROSPECTO_DASH_PASSWORD` (ne pas committer `data/.dash_password`).
- Restreindre l'accès réseau si possible (VPN / allowlist IP) — le CRM contient des coordonnées.
- Sauvegarder `data/` (le CRM) régulièrement ; ne jamais l'exposer publiquement sans auth.
- Optionnel : ajouter un en-tête `Content-Security-Policy` et une limitation de débit sur `/login`.
- Le serveur n'envoie **aucun email** : l'envoi reste manuel via Gmail après validation.

## 6. Ce qu'il ne faut PAS faire
- Ne pas reconstruire le site marketing ni dupliquer ses sections dans le dashboard.
- Ne pas créer une seconde application « vitrine » : le dashboard EST l'outil métier.
- Ne pas mettre le site en iframe (bloqué par `X-Frame-Options`).
- Ne pas déployer automatiquement sans validation des conséquences (DNS, TLS, accès).
- Ne pas committer les secrets ni les données prospects dans un dépôt public.
