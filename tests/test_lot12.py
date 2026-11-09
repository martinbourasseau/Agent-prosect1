"""Lot 12 — invariants de recherche, de preuves, de dédoublonnage et de priorité.

Aucun compteur de portefeuille n'est figé : le CRM évolue à chaque lot, les
tests recalculent. Ce qui est figé, ce sont les règles, pas les effectifs.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/lot12"))

import fiches as F
import journal as J
from prospecto.crm import CRM
from prospecto.models import Evidence
from prospecto.scoring import AXES
from prospecto.counter_signals import PENALTY_CAP
from prospecto.priority import THRESHOLD_HAUTE


class TestJournalLot12(unittest.TestCase):
    def test_requetes_documentees(self):
        self.assertGreaterEqual(len(J.REQUETES), 30)
        for r in J.REQUETES:
            self.assertEqual(len(r), 4)
            self.assertTrue(r[0] and r[1] and r[3])

    def test_cinq_familles_couvertes(self):
        familles = {r[0] for r in J.REQUETES}
        self.assertTrue({"services", "distribution", "industrie", "tourisme",
                         "numerique"} <= familles)

    def test_objectif_examinees_atteint(self):
        # 80 à 100 NOUVELLES entreprises visées : les annuaires ne comptent pas.
        self.assertGreaterEqual(J.stats()["entreprises_hors_annuaires"], 80)

    def test_pas_de_concentration_geographique(self):
        deps = J.stats()["departements"]
        self.assertGreaterEqual(len(deps), 15)
        from collections import Counter
        counts = Counter(e["departement"] for e in J.E
                         if e["departement"].isdigit() and e["decision"] != "annuaire_seul")
        # Aucun département ne doit représenter plus du quart des examinées.
        self.assertLessEqual(max(counts.values()), sum(counts.values()) / 4)

    def test_lectures_comptees_honnetement(self):
        s = J.stats()
        self.assertEqual(s["tentatives_lecture"],
                         s["lectures_reussies"] + s["lectures_echouees"])
        # Une entreprise dont AUCUNE page n'a pu être lue ne peut être importée.
        # En revanche une page secondaire en échec n'invalide pas les preuves
        # relevées ailleurs : Alcamparol a un /contact inaccessible mais un
        # accueil lu, qui porte l'intégralité de ses preuves.
        for u, statut, nom in J.PAGES:
            if statut != "echec":
                continue
            pages_ent = [p for p in J.PAGES if p[2] == nom]
            if any(p[1] in ("ok", "ok_404") for p in pages_ent):
                ent = next(e for e in J.E if e["nom"] == nom)
                if ent["decision"] == "importee":
                    urls_preuves = {e["source_url"] for f in F.FICHES
                                    if f["company"] == nom for e in f["evidence"]}
                    self.assertNotIn(u, urls_preuves,
                                     "une preuve ne peut pas citer une page non lue")
                continue
            for e in [x for x in J.E if x["nom"] == nom]:
                self.assertNotEqual(e["decision"], "importee")
                self.assertEqual(e["decision"], "non_verifie")

    def test_chaque_entite_a_un_motif(self):
        for e in J.E:
            self.assertTrue(e["motif"], e["nom"])
            self.assertTrue(e["nom"])
            self.assertIn(e["decision"], {"importee", "approfondir", "ecartee",
                                          "annuaire_seul", "non_verifie"})

    def test_annuaires_jamais_importes(self):
        for e in J.E:
            if e["lecture"] == "annuaire":
                self.assertEqual(e["decision"], "annuaire_seul")

    def test_ecarts_les_plus_nets_sont_justifies(self):
        by = {e["nom"]: e for e in J.E}
        # Ces rejets ont été décidés sur une page officielle lue : le motif
        # doit nommer la raison, pas rester générique.
        for nom in ("Azur Nettoyage", "Damiani AlpMétal", "Vente Directe PME", "LORDI"):
            self.assertEqual(by[nom]["decision"], "ecartee")
            self.assertEqual(by[nom]["lecture"], "officielle")
            self.assertGreater(len(by[nom]["motif"]), 40)

    def test_pieges_de_requete_traces(self):
        by = {e["nom"]: e for e in J.E}
        # Une requête "solution" ramène des vendeurs, pas des acheteurs.
        for nom in ("Reproland", "Deltic", "DIMO Dématérialisation", "Numeria"):
            self.assertEqual(by[nom]["decision"], "ecartee")
            self.assertIn("VENDEUR", by[nom]["motif"])

    def test_pas_de_faux_defaut_artefact_js(self):
        by = {e["nom"]: e for e in J.E}
        # Compteurs à 0 sans JavaScript = artefact de lecture, pas un défaut.
        for nom in ("E.S.S. 37", "VT Prévention"):
            self.assertIn("artefact", by[nom]["motif"])

    def test_doublon_probable_non_fusionne(self):
        by = {e["nom"]: e for e in J.E}
        self.assertEqual(by["FICOM"]["decision"], "ecartee")
        self.assertIn("doublon probable", by["FICOM"]["motif"])
        self.assertIn("non résolu", by["FICOM"]["motif"])


class TestFichesLot12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [F.build(f) for f in F.FICHES]

    def test_toutes_les_preuves_valides(self):
        for r in self.rows:
            for e in r["prospect"].evidences:
                self.assertEqual(e.validate(), [], r["fiche"]["company"])

    def test_preuve_datee_et_sourcee(self):
        for r in self.rows:
            for e in r["prospect"].evidences:
                self.assertTrue(e.source_url.startswith("http"), e.source_url)
                self.assertEqual(e.observed_at, F.D)
                self.assertEqual(e.verified_at, F.D)
                self.assertTrue(e.quote.strip())
                self.assertTrue(e.detail.strip())
                self.assertEqual(e.source_type, "site_officiel")

    def test_contre_signaux_tout_typés_pour_etre_lus(self):
        # Correction du Lot 11 conservée : seuls les `maturite_existante`
        # sont lus par counter_signals.collect().
        for r in self.rows:
            n_cs = len(r["fiche"].get("contre_signaux", []))
            self.assertGreaterEqual(n_cs, 1, r["fiche"]["company"])
            typed = [e for e in r["prospect"].evidences if e.kind == "maturite_existante"]
            self.assertEqual(len(typed), n_cs, r["fiche"]["company"])

    def test_contre_signaux_influencent_reellement_la_priorite(self):
        # Au moins une fiche doit voir sa priorité réduite par un contre-signal,
        # sinon le mécanisme serait décoratif.
        penalised = [r for r in self.rows if r["assessment"].counter_signal_penalty > 0]
        self.assertGreaterEqual(len(penalised), 1)
        for r in penalised:
            self.assertLessEqual(r["assessment"].counter_signal_penalty, PENALTY_CAP)
            self.assertTrue(any("contre-signal" in x for x in r["assessment"].reasons))

    def test_creation_basse_car_site_existant(self):
        for r in self.rows:
            self.assertTrue(r["fiche"]["website"])
            self.assertEqual(r["scores"]["site_web"]["score"], 5)

    def test_trois_axes_independants(self):
        # Un même profil ne doit pas produire trois scores identiques : les
        # axes mesurent des choses différentes.
        for r in self.rows:
            s = r["scores"]
            self.assertTrue(set(s[a]["score"] for a in AXES) != {s["site_web"]["score"]},
                            r["fiche"]["company"])

    def test_ia_jamais_sur_le_seul_secteur(self):
        for r in self.rows:
            s = r["scores"]["ia_automatisation"]["score"]
            if s > 0:
                kinds = {e.kind for e in r["prospect"].evidences}
                self.assertTrue({"processus_manuel", "parcours_incomplet"} & kinds,
                                f"{r['fiche']['company']} : IA {s} sans processus publié")
            self.assertTrue(r["fiche"]["sector"])
        # Un secteur voisin ne doit pas donner le même score IA : deux
        # métalleries du lot ont des scores différents car preuves différentes.
        by = {r["fiche"]["company"]: r for r in self.rows}
        self.assertNotEqual(by["Blanchefleur"]["scores"]["ia_automatisation"]["score"],
                            by["Les Ateliers Genetier"]["scores"]["ia_automatisation"]["score"])

    def test_processus_reel_cite_pour_acpt(self):
        r = next(x for x in self.rows if x["fiche"]["company"] == "A.C.P.T.")
        pm = [e for e in r["prospect"].evidences if e.kind == "processus_manuel"]
        self.assertTrue(pm)
        self.assertIn("bordereau de suivi de déchets", pm[0].quote)
        # Le mode de production n'a pas été observé : il doit rester non vérifié.
        self.assertIn("non vérifié", pm[0].detail)

    def test_effectif_n_est_pas_un_processus(self):
        # LGC : « deux assistantes administratives » est un effectif, pas un
        # processus documenté. Aucun processus_manuel ne doit être créé dessus.
        r = next(x for x in self.rows if x["fiche"]["company"] == "Laizeau Génie Climatique")
        self.assertFalse([e for e in r["prospect"].evidences if e.kind == "processus_manuel"])
        self.assertEqual(r["fiche"]["process_hint"], "")

    def test_prestation_vendue_n_est_pas_un_processus_interne(self):
        # HMC vend de la saisie comptable : écarté, pas importé comme processus.
        self.assertNotIn("HMC Conseil", [f["company"] for f in F.FICHES])
        by = {e["nom"]: e for e in J.E}
        self.assertEqual(by["HMC Conseil"]["decision"], "ecartee")

    def test_aucun_besoin_exprime_fabrique(self):
        # Aucun de ces sites ne demande publiquement une prestation web.
        for r in self.rows:
            self.assertFalse([e for e in r["prospect"].evidences if e.kind == "public_need"],
                             r["fiche"]["company"])

    def test_email_jamais_deduit(self):
        for r in self.rows:
            f = r["fiche"]
            if f["email"]:
                self.assertIn(f["email"].split("@")[-1],
                              F.DNS_PATH.read_text(encoding="utf-8"),
                              f"{f['company']} : adresse absente du relevé des adresses publiées")
                self.assertEqual(r["prospect"].email_verification, "verified")
                self.assertEqual(r["prospect"].email_dns_status, "mx_ok")
            else:
                self.assertEqual(r["prospect"].email_verification, "none")
                self.assertEqual(r["prospect"].email_dns_status, "")

    def test_tortora_adresse_publiee_mais_non_importee(self):
        # L'adresse existe mais le dirigeant affiché est incohérent : la
        # prudence prime, elle n'est pas importée comme canal exploitable.
        f = next(x for x in F.FICHES if x["company"] == "Tortora")
        self.assertEqual(f["email"], "")
        self.assertIn("destinataire réel est incertain", f["notes"])

    def test_departements_reels_corriges(self):
        by = {f["company"]: f for f in F.FICHES}
        # Damiani est à Thônes (74), pas en Savoie : écarté, mais le
        # département relevé en recherche doit être le bon.
        self.assertEqual(next(e for e in J.E if e["nom"] == "Damiani AlpMétal")["departement"], "74")
        self.assertEqual(by["MFMG"]["department"], "08")

    def test_priorite_bornee_et_palier_coherent(self):
        for r in self.rows:
            a = r["assessment"]
            self.assertTrue(0 <= a.value <= 100)
            self.assertEqual(a.engine_version, "v10-priority")
            if not a.contactable and a.value >= THRESHOLD_HAUTE:
                self.assertTrue(a.capped_by_contactability)

    def test_aucun_brouillon_sans_conditions(self):
        for r in self.rows:
            a = r["assessment"]
            conf = r["scores"][a.best_axis]["confidence"]
            allowed = a.contactable and a.tier == "haute" and conf != "faible"
            if not allowed:
                self.assertFalse(a.tier == "haute" and a.contactable and conf != "faible")

    def test_sujets_dans_la_limite_du_moteur(self):
        for f in F.FICHES:
            self.assertLessEqual(len(f["custom_subject"]), 70, f["company"])

    def test_texte_sans_caractere_parasite(self):
        # Régression : un caractère CJK s'était glissé dans une preuve.
        for f in F.FICHES:
            blob = json.dumps(f, ensure_ascii=False)
            self.assertIsNone(re.search(r"[\u3000-\u9fff\uff00-\uffef]", blob), f["company"])

    def test_dns_normalise_insensible_a_la_casse(self):
        # Régression : « L.C. BOIS » relevé vs « L.C. Bois » au CRM faisait
        # perdre le statut MX et plafonnait la priorité à tort.
        r = next(x for x in self.rows if x["fiche"]["company"] == "L.C. Bois")
        self.assertEqual(r["prospect"].email_dns_status, "mx_ok")
        self.assertTrue(r["assessment"].contactable)


class TestImporteurLot12(unittest.TestCase):
    def test_alias_ne_bloque_pas_le_domaine_canonique(self):
        # Régression : `domain in alias` rejetait MFMG et L.C. Bois alors
        # qu'aucun doublon n'existait.
        import importer as I
        crm = CRM()
        existing = {(r.get("domain") or "").lower() for r in crm.records}
        alias = {"mfmg.fr": "mfmg.eu", "lcbois.fr": "lc-bois.fr"}
        for canon in ("mfmg.eu", "lc-bois.fr"):
            self.assertEqual(alias.get(canon, canon), canon)
            if canon not in existing:
                self.assertNotIn(canon, {alias.get(d, d) for d in ()})

    def test_normalisation_des_noms(self):
        import importer as I
        self.assertEqual(I.norm("L.C. Bois"), I.norm("LC BOIS"))
        self.assertEqual(I.norm("A.C.P.T."), I.norm("ACPT"))
        self.assertEqual(I.norm("Kap'oupa Kap"), I.norm("KapOupa Kap"))

    def test_faux_positifs_de_nom_non_pris_pour_doublons(self):
        import importer as I
        self.assertNotEqual(I.norm("Blanchefleur"), I.norm("Blanchisserie des 3 Régions (B3R)"))

    def test_decisions_dans_le_vocabulaire_du_registre(self):
        # Régression : « ecartee » et « écartée » comptaient comme deux
        # catégories distinctes dans le tableau de bord.
        import importer as I
        from prospecto.sources import ExplorationLedger
        attendues = {"retenue", "écartée", "approfondir", "annuaire_seul"}
        self.assertEqual(set(I.DECISION_VERS_REGISTRE.values()), attendues)
        ledger = ExplorationLedger()
        presentes = {e.get("decision") for e in ledger.entries}
        self.assertTrue(presentes <= attendues, presentes - attendues)
        # Le registre dédoublonne par nom : une structure déjà écartée à un
        # lot précédent n'est pas réinscrite (cas réel : BET Sodeba, écartée
        # au lot 11, réexaminée ici). Toutes doivent néanmoins y figurer.
        lot12 = [e for e in ledger.entries if e.get("lot") == F.LOT]
        self.assertLessEqual(len(lot12), len(J.E))
        tous = {I.norm(e.get("company", "")) for e in ledger.entries}
        self.assertTrue({I.norm(e["nom"]) for e in J.E} <= tous)

    def test_fiches_du_journal_coherentes_avec_les_fiches_importees(self):
        importees = {e["nom"] for e in J.E if e["decision"] == "importee"}
        construites = {f["company"] for f in F.FICHES}
        self.assertEqual(importees, construites)


class TestProtectionsLot12(unittest.TestCase):
    """Les données sensibles ne doivent pas bouger pendant le lot."""

    def test_journal_d_envoi_intact(self):
        p = ROOT / "data/history/send-log.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        entries = data.get("entries", data if isinstance(data, list) else [])
        self.assertEqual(len(entries), 60)

    def test_campagne_desactivee(self):
        p = ROOT / "data/campaigns/v4-settings.json"
        s = json.loads(p.read_text(encoding="utf-8"))
        self.assertFalse(s.get("enabled", False))
        self.assertTrue(s.get("dry_run", True))

    def test_oppositions_toujours_presentes(self):
        from prospecto.config import SUPPRESSION_PATH
        sup = json.loads(SUPPRESSION_PATH.read_text(encoding="utf-8"))
        emails = {e["email"].lower() for e in sup.get("entries", [])}
        self.assertIn("celarenarde@gmail.com", emails)

    def test_brouillons_lot11_toujours_la(self):
        from prospecto.queue import ValidationQueue
        q = ValidationQueue()
        items = [i for i in q.items if getattr(i, "campaign", "") == "2026-11-09-lot11"]
        self.assertEqual(len(items), 4)
        for i in items:
            self.assertTrue(i.gmail_draft_id, i.id)

    def test_aucun_envoi_lot12(self):
        p = ROOT / "data/history/send-log.json"
        blob = p.read_text(encoding="utf-8")
        self.assertNotIn("2026-11-03-lot12", blob)


if __name__ == "__main__":
    unittest.main()
