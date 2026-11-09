# Reprise — état de la Phase 10 finale

**Dernière mise à jour :** 2026-11-09 (date de référence des données sources).
**Branche :** `arena/7ed6352a-agent-prosect1`.

## État : sections A à J exécutées, K livré

Rapport complet en 8 parties :
**`docs/rapport-final-phase10-2026-11-09.md`**.

| Section | État | Livrable |
|---|---|---|
| A — audit, sauvegarde, Git | faite | MD5 des 4 journaux, `/tmp/sauvegarde_finale/data/` |
| B — consolidation production | faite | `prospecto/outbound.py`, commit `7e2bc4d` |
| C — scoring et contre-signaux | faite | `prospecto/counter_signals.py`, priorité v10, commit `1f9b589` |
| D — marchés publics | faite | `prospecto/public_tenders.py` + archive 30 consultations |
| E — 2 brouillons | faite | relus dans Gmail, conformes, **conservés sans modification** |
| F — délivrabilité | faite | `docs/delivrabilite-phase10bis.md` révisé |
| G — audit Gmail | faite | `data/history/audit-gmail-phase10-finale-2026-11-09.json` |
| H — indicateurs dashboard | faite | moyenne/médiane, contre-signaux, marchés publics, rendement |
| I — tests et intégrité | faite | **670 tests / 23 fichiers**, MD5 4/4 |
| J — garde-fous | respectée | `enabled=false`, aucun envoi, aucun achat, aucun DNS |
| K — rapport | livré | `docs/rapport-final-phase10-2026-11-09.md` |

## Derniers commits

```
b2865ad  §D-§H : marchés publics, audit Gmail, indicateurs, rendu testé
1f9b589  §C : priorité v10, contre-signaux explicites
7e2bc4d  §B : consolidation des messages sortis (60 -> 68)
0e85179  Phase 10 bis
```

Dernier fichier modifié : `docs/reprise-phase10.md` (ce document), puis le commit
final §K qui l'inclut avec le rapport.

## Chiffres de référence, vérifiés

- CRM **92** fiches · registre d'exploration **131** · file **73** items.
- Messages sortis **68** = 60 production + 8 rapprochés de Gmail. **Journal de
  production inchangé : 60 entrées.**
- Délivrances : **3 confirmées**, **63 non confirmées**, 1 rebond dur,
  1 challenge, 1 réponse humaine, 2 automatiques, 1 opposition.
- Doublons écartés **37**, non attribuables **0**.
- Priorité : moyenne **52,7**, médiane **58**, haute **8** (était 12).
- Contre-signaux : **2 forts / 8 modérés / 7 faibles** sur 16 fiches, 9 pénalisées.
- Marchés publics : **30 examinées, A 0 / B 10 / C 20**, 29 acheteurs.
- Rendement : site officiel **17/70 = 24 %**, annuaire pro **0/34 = 0 %**.
- Suppression : **2** entrées. Pré-vol **`(False, 3 motifs)`**.

## Où reprendre exactement

**Rien n'est en cours.** La prochaine action ne dépend pas de l'agent :

1. **Décider du domaine professionnel** et autoriser (ou non) la dépense
   indicative de 10-15 €/an. Puis publier SPF, DKIM, MX, DMARC `p=none`.
2. **Brancher les webhooks** de remise, rebond et désabonnement. Sans eux, les
   63 messages resteront « non confirmés » — c'est structurel.
3. **Valider ou refuser les 2 brouillons** : Caléo Tests & Services
   (`contact@caleo-ts.fr`, message `1a1b672541671292`) et Pépinières Ripaud
   (`info@ripaudpepinieres.com`, message `1a1b16dee5899e57`).
4. **Revue humaine de 2 fiches** : ERM 27 (71→47) et Delahautemaison (54→26),
   les deux contre-signaux de force forte.
5. **Marchés publics, si le canal est souhaité** : lire le RC de
   Saint-Pierre-Quiberon (échéance **16/11/2026 12h00**, 7 jours) et arbitrer
   Mieussy (**20/11/2026 12h00**, 20 000 € HT, bloqué par les exigences de
   références sur 3 ans avec attestations).

**Le Lot 11 ne doit pas être lancé** avant les points 1 à 3 : l'envoi est bloqué
par le pré-vol, la délivrance n'est pas mesurée, et les 8 messages partis le
09/11 n'ont pas encore reçu de réponse.

## Pièges à ne pas rejouer

- **Un zéro sur une requête Gmail filtrée ne prouve rien**, même `complete:true`.
  Toujours rejouer un **contrôle positif** sur une période à résultat connu.
  Une requête trop large est aussi inutilisable : 201 résultats tronqués.
- **`thread_id ≠ message_id` n'implique pas un échange antérieur.** Le fil Caléo
  contient un seul message.
- **Ne jamais fusionner un rapprochement sur la seule adresse.** File = id de
  fil/brouillon ; rapprochement = id de message.
- **`preflight()` persiste l'état DNS** : ne l'appeler que sur une copie
  `tempfile`, sinon un journal protégé est modifié.
- **`metrics.py` utilise des imports relatifs.** La clé d'axe création est
  `site_web`.
- **`CRM().records` et `ValidationQueue().items`** : il n'existe pas de
  `load_crm()` ni `load_queue()`.
- **Le dashboard charge `/api/campaign` séparément de `/api/metrics`.** Un test
  de rendu qui n'injecte que les métriques valide un bandeau « désactivé » pour
  la mauvaise raison.
- **`??` et `||` ne se mélangent pas sans parenthèses en JavaScript** : c'est une
  `SyntaxError` qui tue tout le script. `node --check` et les tests de rendu le
  détectent.
- **Un champ mal nommé en JS n'erreur pas, il affiche `NaN`.** Tester le rendu,
  pas la présence des chaînes.
- **Marchés publics** : le CPV seul produit des faux positifs ; un avis
  d'attribution peut porter une date de clôture future ; une annonce de
  prestataire privé n'est pas une demande d'acheteur.
- **`.replace()` silencieux** : toujours `assert old in s` avant de remplacer.
- Tests : `python3 -m unittest discover tests -q` (`pytest` absent).

## Environnement

- Python 3.11.2, node v22.22.3 (utilisé par les tests de rendu).
- Dashboard : `python3 -m prospecto.server --host 0.0.0.0 --port 8787`, mot de
  passe dans `data/.dash_password`. Process
  `tableau-de-bord-prospecto-9b3bac42`. **Redémarrer le serveur après toute
  modification de `metrics.py`** : il garde le code en mémoire.
- Journaux protégés : `md5sum -c /tmp/protected_final.md5` (4 fichiers).
- Aucune base SQLite : le CRM est `data/crm/prospects.json`.
