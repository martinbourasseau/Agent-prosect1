"""Tests de rendu RÉEL du tableau de bord (section H/I, phase 10 finale).

Pourquoi exécuter le JavaScript plutôt que chercher des chaînes dans le HTML :
un champ lu sous un nom qui n'existe pas dans les métriques ne lève aucune
erreur en JavaScript, il affiche « NaN % » ou « undefined ». Un test qui se
contente de vérifier la présence du code source passe alors que l'écran est
faux. C'est exactement le défaut trouvé ici : la colonne « Brut » du rendement
des sources lisait p.raw_rate, absent des métriques (le champ s'appelle
qualification_rate), et affichait NaN depuis l'origine.

Le harnais fournit un DOM minimal, injecte les métriques réelles du dépôt et
appelle les fonctions de rendu, puis inspecte le HTML produit.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from prospecto.metrics import compute_metrics

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "prospecto" / "dashboard.html"
NODE = shutil.which("node")

HARNESS = r"""
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// DOM minimal : assez pour que les fonctions de rendu s'exécutent vraiment.
const nodes = new Map();
function makeNode(id) {
  return {
    id, innerHTML: "", textContent: "", value: "", style: {},
    dataset: {}, children: [],
    classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
    addEventListener(){}, appendChild(c){ this.children.push(c); },
    querySelectorAll(){ return []; }, querySelector(){ return null; },
    setAttribute(){}, getAttribute(){ return null; },
    insertAdjacentHTML(pos, s){ this.innerHTML += s; },
  };
}
global.document = {
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, makeNode(id));
    return nodes.get(id);
  },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  createElement(tag) { return makeNode(tag); },
  addEventListener(){},
  body: makeNode("body"),
};
global.window = { addEventListener(){}, location: { href: "" } };
global.location = { href: "" };
global.fetch = async () => ({ status: 200, json: async () => ({}) });
global.setInterval = () => 0;
global.setTimeout = () => 0;
global.alert = () => {};
global.confirm = () => false;

// On retire l'amorçage automatique : on veut piloter les rendus nous-mêmes.
const cleaned = script
  .replace(/^\s*refresh\(\);\s*$/gm, "")
  .replace(/^\s*setInterval\([\s\S]*?\);\s*$/gm, "");

const sandbox = {};
const fn = new Function("payload", cleaned + `
  METRICS = payload.metrics;
  // Le navigateur charge /api/campaign séparément de /api/metrics : sans cette
  // seconde source, le bandeau afficherait « désactivé » par absence de données
  // et le test passerait pour la mauvaise raison.
  METRICS._campaign = payload.campaign;
  PROS = payload.prospects;
  QUEUE = payload.queue;
  const errors = [];
  const targets = ["renderBanner","renderCards","renderPipeline",
                   "renderDeliverability","renderPilotage","renderSending","renderPros","renderQueue"];
  for (const name of targets) {
    try { eval(name + "()"); }
    catch (e) { errors.push({fn: name, error: String(e && e.message || e)}); }
  }
  return { errors };
`);
const outcome = fn(payload);

const rendered = {};
for (const [id, node] of nodes) rendered[id] = node.innerHTML;
process.stdout.write(JSON.stringify({ errors: outcome.errors, rendered }));
"""


@unittest.skipIf(NODE is None, "node absent : rendu JavaScript non testable")
class RenduDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = compute_metrics()
        from prospecto.crm import CRM
        from prospecto.queue import ValidationQueue

        cls.prospects = CRM().records
        cls.queue = [i.to_dict() for i in ValidationQueue().items]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            harness = tmp / "harness.js"
            harness.write_text(HARNESS, encoding="utf-8")
            data = tmp / "payload.json"
            from prospecto.server import api_campaign_status

            data.write_text(json.dumps({
                "metrics": cls.metrics,
                "campaign": api_campaign_status(),
                "prospects": cls.prospects,
                "queue": cls.queue,
            }, ensure_ascii=False, default=str), encoding="utf-8")
            proc = subprocess.run(
                [NODE, str(harness), str(DASHBOARD), str(data)],
                capture_output=True, text=True, timeout=120,
            )
        if proc.returncode != 0:
            raise AssertionError(f"Rendu impossible : {proc.stderr[:2000]}")
        cls.result = json.loads(proc.stdout)
        cls.html = "\n".join(cls.result["rendered"].values())

    def test_aucune_fonction_de_rendu_ne_leve(self):
        self.assertEqual(self.result["errors"], [],
                         f"fonctions en échec : {self.result['errors']}")

    def test_aucun_nan_affiche(self):
        """Le défaut qui a motivé ce test : p.raw_rate produisait « NaN % »."""
        self.assertNotIn("NaN", self.html)

    def test_aucun_undefined_affiche(self):
        self.assertNotIn("undefined", self.html)

    def test_le_rendement_affiche_un_vrai_taux_brut(self):
        source = next(s for s in self.metrics["recherche"]["source_performance"]
                      if s["source_type"] == "site_officiel")
        attendu = f"{source['qualification_rate'] * 100:.0f} %"
        self.assertIn(attendu, self.result["rendered"]["srcBox"])

    def test_la_distinction_envoye_delivre_est_affichee(self):
        html = self.result["rendered"]["delivReal"]
        self.assertIn("Acceptés par le fournisseur", html)
        self.assertIn("Délivrés confirmés", html)
        self.assertIn("Délivrance non confirmée", html)
        self.assertIn("68", html)

    def test_la_note_sur_les_rapprochements_est_visible(self):
        self.assertIn("constatés dans Gmail et rapprochés", self.html)
        self.assertIn("37 doublons écartés par identifiant", self.result["rendered"]["delivReal"])
        self.assertIn("Aucun journal historique modifié", self.result["rendered"]["delivReal"])

    def test_le_pipeline_est_affiche_sans_double_compte(self):
        html = self.result["rendered"]["delivReal"]
        self.assertIn("Messages préparés", html)
        self.assertIn("Brouillons Gmail en attente", html)

    def test_le_bandeau_reflete_les_donnees_reelles(self):
        html = self.result["rendered"]["campaignBanner"]
        self.assertIn("Envoi automatique désactivé", html)
        self.assertIn("Domaine à configurer avant envoi de masse", html)
        self.assertIn("gmail_connector", html)

    def test_la_configuration_d_envoi_affiche_le_blocage_reel(self):
        html = self.result["rendered"]["sendConfig"]
        self.assertIn("Activée", html)
        self.assertIn("simulation (dry_run)", html)
        dns = self.result["rendered"]["delivBox"]
        self.assertIn("gmail.com", dns)
        self.assertIn("❌", dns)  # DKIM absent

    def test_le_bandeau_reagirait_si_l_envoi_etait_active(self):
        """Garde-fou contre un affichage « désactivé » vrai par accident :
        avec enabled=true, le bandeau doit changer. S'il ne change pas, c'est
        qu'il ne lit pas la donnée."""
        script = DASHBOARD.read_text(encoding="utf-8")
        body = re.search(r"function renderBanner\(\)\{([\s\S]*?)\n\}", script).group(1)
        self.assertIn("c.enabled?", body)
        self.assertIn("Envoi automatique désactivé", body)
        self.assertIn("Activée · envoi réel", body)

    def test_les_deux_lectures_des_brouillons_sont_distinguees(self):
        """3 fiches au statut brouillon et 2 éléments en file : même chiffre
        sous le même libellé serait un double compte apparent."""
        html = self.result["rendered"]["delivReal"]
        self.assertIn("Fiches au statut brouillon", html)
        self.assertIn("Brouillons Gmail en attente", html)

    def test_moyenne_et_mediane_sont_affichees(self):
        html = self.result["rendered"]["prioBox"]
        self.assertIn("Moyenne", html)
        self.assertIn("Médiane", html)
        pv = self.metrics["scoring"]["priority_value"]
        # JavaScript rend 58.0 sous la forme « 58 » : comparer les nombres, pas
        # leur représentation Python.
        shown = [float(x) for x in re.findall(r"<b>([0-9]+(?:\.[0-9]+)?)</b>", html)]
        self.assertIn(float(pv["moyenne"]), shown)
        self.assertIn(float(pv["mediane"]), shown)

    def test_les_contre_signaux_sont_affiches(self):
        html = self.result["rendered"]["csBox"]
        self.assertIn("contre-signal", html)
        attendu = self.metrics["scoring"]["contre_signaux"]["fiches_avec_contre_signal"]
        self.assertIn(str(attendu), html)

    def test_les_marches_publics_sont_affiches_comme_registre_distinct(self):
        html = self.result["rendered"]["mpBox"]
        self.assertIn("Consultations examinées", html)
        self.assertIn("30", html)
        self.assertIn("B · à vérifier", html)
        self.assertIn("10", html)
        self.assertIn("Mieussy", html)

    def test_le_zero_categorie_a_est_affiche_sans_etre_maquille(self):
        html = self.result["rendered"]["mpBox"]
        self.assertIn("A · directement exploitables", html)
        self.assertRegex(html, r"A · directement exploitables</span><b>0</b>")

    def test_les_raisons_d_exclusion_sont_visibles(self):
        html = self.result["rendered"]["mpBox"]
        self.assertIn("consultation expirée", html)
        self.assertIn("marché déjà attribué", html)
        self.assertIn("montant hors de portée", html)

    def test_le_libelle_du_taux_lisse_previent_qu_il_n_est_pas_un_taux(self):
        self.assertIn("ce n'est PAS un taux", DASHBOARD.read_text(encoding="utf-8"))

    def test_tous_les_identifiants_utilises_sont_declares(self):
        source = DASHBOARD.read_text(encoding="utf-8")
        declared = set(re.findall(r'id="([A-Za-z0-9_-]+)"', source))
        used = set(re.findall(r'getElementById\("([A-Za-z0-9_-]+)"\)', source))
        self.assertEqual(used - declared, set())


class MetriquesDashboardTests(unittest.TestCase):
    """Contrats de données attendus par l'écran, sans JavaScript."""

    @classmethod
    def setUpClass(cls):
        cls.metrics = compute_metrics()

    def test_le_champ_lu_par_le_dashboard_existe(self):
        """Régression directe du bug raw_rate / qualification_rate."""
        for row in self.metrics["recherche"]["source_performance"]:
            self.assertIn("qualification_rate", row)
            self.assertIn("yield_score", row)
            self.assertNotIn("raw_rate", row)

    def test_priorite_statistiques_coherentes(self):
        from prospecto.crm import CRM

        pv = self.metrics["scoring"]["priority_value"]
        values = [r for r in CRM().records
                  if isinstance(r.get("commercial_value"), (int, float))]
        self.assertEqual(pv["n"], len(values))
        self.assertLessEqual(pv["min"], pv["mediane"])
        self.assertLessEqual(pv["mediane"], pv["max"])
        self.assertLessEqual(pv["min"], pv["moyenne"])
        self.assertLessEqual(pv["moyenne"], pv["max"])

    def test_la_mediane_est_calculee_correctement(self):
        """Vérification indépendante du calcul, sur les fiches réelles."""
        from prospecto.crm import CRM

        values = sorted(int(r["commercial_value"]) for r in CRM().records
                        if isinstance(r.get("commercial_value"), (int, float)))
        mid = len(values) // 2
        expected = (values[mid] if len(values) % 2
                    else (values[mid - 1] + values[mid]) / 2)
        self.assertEqual(self.metrics["scoring"]["priority_value"]["mediane"], expected)

    def test_contre_signaux_exposes_par_force(self):
        from prospecto.crm import CRM

        cs = self.metrics["scoring"]["contre_signaux"]
        records = CRM().records
        attendu = {"fort": 0, "modere": 0, "faible": 0}
        avec, penalisees = 0, 0
        for rec in records:
            block = rec.get("commercial") or {}
            details = block.get("counter_signal_details") or []
            if details:
                avec += 1
            for d in details:
                if d.get("strength") in attendu:
                    attendu[d["strength"]] += 1
            if block.get("counter_signal_penalty"):
                penalisees += 1
        self.assertEqual(cs["par_force"], attendu)
        self.assertEqual(cs["fiches_avec_contre_signal"], avec)
        self.assertEqual(cs["fiches_penalisees"], penalisees)
        self.assertLessEqual(penalisees, avec)

    def test_marches_publics_registre_distinct(self):
        mp = self.metrics["marches_publics"]
        self.assertTrue(mp["disponible"])
        self.assertTrue(mp["registre_distinct_du_crm"])
        self.assertEqual(mp["consultations_examinees"], 30)
        self.assertEqual(mp["categories"], {"A": 0, "B": 10, "C": 20})

    def test_aucun_acheteur_public_n_entre_dans_le_crm(self):
        """Un avis de marché n'est pas une fiche prospect."""
        from prospecto.crm import CRM
        from prospecto.public_tenders import load_pilot

        pilot, _ = load_pilot()
        buyers = {n.buyer.lower() for n in pilot.notices}
        names = {(r.get("company") or "").lower() for r in CRM().records}
        self.assertFalse(buyers & names,
                         "un acheteur public a été importé dans le CRM")

    def test_les_raisons_d_exclusion_totalisent_les_c(self):
        mp = self.metrics["marches_publics"]
        self.assertEqual(sum(mp["raisons_exclusion"].values()), mp["categories"]["C"])

    def test_le_rendement_sources_n_expose_que_des_sources_explorees(self):
        for row in self.metrics["rendement_sources"]:
            self.assertGreater(row["examinees"], 0)
            self.assertLessEqual(row["taux_brut"], 1.0)

    def test_taux_brut_et_lisse_ne_sont_pas_confondus(self):
        """34 annuaires, 0 qualifiée : brut 0, lissé > 0. Les distinguer est le but."""
        annuaire = next(r for r in self.metrics["rendement_sources"]
                        if r["source"] == "annuaire_pro")
        self.assertEqual(annuaire["taux_brut"], 0.0)
        self.assertGreater(annuaire["taux_lisse"], 0.0)


if __name__ == "__main__":
    unittest.main()
