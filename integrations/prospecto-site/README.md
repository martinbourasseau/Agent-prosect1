# Patch « Espace Prospecto » pour le site prospecto.website

Ce dossier contient le nécessaire pour ajouter un lien **Espace Prospecto** dans la
navigation du site marketing, pointant vers le dashboard de prospection.

> ⚠️ Ce patch est destiné au dépôt **`martinbourasseau/prospecto-site`**, pas à celui-ci.
> Il n'est **pas appliqué automatiquement** : à relire puis appliquer après avoir choisi
> l'URL de déploiement du dashboard (voir `docs/integration-site-prospecto.md`).

## Fichiers
- `Nav.original.tsx` — copie de référence de `components/Nav.tsx` (à jour à la date du patch).
- `Nav.proposed.tsx` — version complète proposée (remplacement direct possible).
- `nav-espace-prospecto.patch` — diff unifié, 3 insertions.

## Ce que fait le patch
1. Ajoute une constante `APP_URL = "https://app.prospecto.website"` (à adapter).
2. Ajoute un bouton **« Espace Prospecto »** (style `btn btn-glass glass`) dans la barre
   d'actions desktop, à côté de « Parlons de votre projet ».
3. Ajoute le même lien dans le pied du menu mobile.

Aucun CSS supplémentaire : réutilise les classes et jetons déjà présents dans le site.

## Appliquer
```bash
# dans le dépôt prospecto-site, à la racine
git apply /chemin/vers/nav-espace-prospecto.patch
# — ou —
cp Nav.proposed.tsx components/Nav.tsx
```
Puis adapter `APP_URL` à l'URL réelle du dashboard déployé, et vérifier le rendu
(desktop + mobile) avant de committer/pousser.

## Pré-requis côté dashboard
Le dashboard (`prospecto/server.py` dans `Agent-prosect1`) doit être déployé et accessible
à l'URL choisie, en HTTPS, avec mot de passe. Voir `docs/integration-site-prospecto.md`.
