"""Journal de recherche du Lot 12 — toutes les entités examinées, décision et motif.

Règle appliquée : une entité n'est « lue » que si une page a réellement été
récupérée. Ce qui n'a été vu que dans un résultat de moteur reste
`non_verifie` et ne peut produire aucune preuve importée.

Aucune écriture dans le CRM ici : ce module ne fait que décrire et compter.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

D = "2026-11-03"
LOT = "2026-11-03-lot12"

# --- Requêtes réellement exécutées ------------------------------------------
# (familie, libellé, département visé, rendement observé)
REQUETES = [
    ("services", "expertise comptable Ardennes 08 cabinet", "08", "3 cabinets indépendants + 2 réseaux"),
    ("services", "cabinet recrutement Orne 61 Alencon", "61", "aucune TPE : réseaux nationaux à pages-villes"),
    ("services", "nettoyage après sinistre Calvados 14", "14", "aucune TPE : plateforme SEO + comparateur"),
    ("industrie", "décolletage usinage Doubs 25", "25", "annuaires seulements, noms à reprendre"),
    ("tourisme", "camping indépendant Lozère 48 Florac réservation", "48", "office de tourisme + campings chaînés"),
    ("tourisme", "hébergement insolite cabanes yourtes Ariège 09", "09", "1 site officiel exploitable (Alcamparol)"),
    ("distribution", "grossiste pièces détachées Vendée 85 catalogue pro", "85", "annuaires + grossistes nationaux"),
    ("services", "organisme formation Qualiopi Indre-et-Loire 37", "37", "2 associations + réseaux SEO"),
    ("numerique", "numérisation archivage GED Haute-Vienne 87", "87", "annuaires ; piège vendeurs de GED"),
    ("industrie", "traitement de surface Belfort 90 zingage", "90", "1 TPE exploitable (MFMG, actually 08)"),
    ("industrie", "fabricant mobilier bois Saône-et-Loire 71", "71", "1 site officiel (Ateliers Genetier)"),
    ("services", "maintenance CVC contrat entretien Eure-et-Loir 28", "28", "2 TPE (LGC, Tuvache) + réseaux"),
    ("tourisme", "base de loisirs plein air Pyrénées-Orientales 66", "66", "2 sites officiels (Kap'oupa Kap, Extérieur Nature)"),
    ("services", "cabinet conseil RH QVT Meuse 55 Verdun", "55", "aucune TPE locale : cabinets nationaux"),
    ("distribution", "distributeur fournitures industrielles Charente 16", "16", "1 site officiel (L.C. Bois) + réseaux"),
    ("services", "nettoyage industriel spécialisé Haute-Vienne Limoges", "87", "2 TPE (TAM NET, Azur) + plateforme SEO"),
    ("numerique", "recrutement assistant ADV saisie des commandes", "national", "1 PDF d'entreprise (Stratus) hors zone ciblée"),
    ("industrie", "tôlerie fine découpe pliage Savoie 73", "73", "1 TPE (Damiani, actually 74) + annuaires"),
    ("services", "organisme formation Aude 11 Carcassonne catalogue", "11", "1 association (Défi 11) + organismes publics"),
    ("numerique", "conseil informatique infogérance Tarn-et-Garonne 82", "82", "1 TPE (LORDI) + franchise + réseau"),
    ("services", "assainissement vidange Orne 61 Argentan", "61", "3 TPE (ACPT, Assainissement Argentanais, ALM)"),
    ("distribution", "fabricant agroalimentaire biscuiterie Aube 10", "10", "1 site officiel (Tortora, équipement) + annuaires"),
    ("services", "cabinet recrutement indépendant Seine-Maritime 76", "76", "2 cabinets multi-bureaux, hors cible TPE"),
    ("services", "bureau études techniques BTP Hautes-Pyrénées 65 Tarbes", "65", "1 site officiel (BETEP) + LinkedIn"),
    ("industrie", "matériel agricole atelier Aisne 02 Saint-Quentin", "02", "1 site officiel (MG02) + annuaires"),
    ("distribution", "commerce spécialisé fabricant Vendée 85 boutique pro", "85", "1 site officiel (Vente Directe PME)"),
    ("industrie", "chaudronnerie métallerie Meuse 55 Verdun", "55", "3 sites officiels (BKCS, ATS 55, Blanchefleur)"),
    ("services", "formation sécurité incendie SST Calvados 14 Caen", "14", "1 TPE (VT Prévention) + réseaux SEO"),
    ("numerique", "dématérialisation factures Territoire de Belfort 90", "90", "PIÈGE : uniquement des vendeurs de solutions"),
    ("tourisme", "Alcamparol contact Sainte-Croix-Volvestre", "09", "annuaires uniquement, aucun e-mail publié"),
    ("tourisme", "domaine viticole indépendant Côte des Bar Aube 10", "10", "4 domaines, non approfondis faute de temps"),
    ("distribution", "menuiserie agencement Charente fabricant catalogue", "16", "annuaires + BODACC, aucun site officiel neuf"),
    ("numerique", "société traduction technique documentation manuels", "national", "agences nationales + 1 indépendant"),
    ("tourisme", "camping domaine indépendant Creuse Corrèze", "23/19", "2 sites officiels, chaînés Castels"),
]

# --- Pages réellement récupérées --------------------------------------------
# (url, statut, entreprise ou None si annuaire)
PAGES = [
    ("https://www.ajzenstein-expert-comptable.com/expertise-comptable-08", "ok", "Ajzenstein Louis et Associés"),
    ("https://www.alcamparol.com/", "ok", "Alcamparol"),
    ("https://www.ess37.fr/", "ok", "E.S.S. 37"),
    ("https://www.mfmg.eu/zingage/", "ok", "MFMG"),
    ("https://www.ebeniste-genetier.com/meuble.php", "ok", "Les Ateliers Genetier"),
    ("https://hmcconseil.fr/", "ok", "HMC Conseil"),
    ("https://www.mfmg.eu/contact/", "ok", "MFMG"),
    ("https://lgc28.fr/", "ok", "Laizeau Génie Climatique"),
    ("https://www.kapoupakap.fr/activites.html", "ok", "Kap'oupa Kap"),
    ("https://lgc28.fr/contact.html", "ok", "Laizeau Génie Climatique"),
    ("https://www.lc-bois.fr/", "ok", "L.C. Bois"),
    ("https://www.kapoupakap.fr/", "ok", "Kap'oupa Kap"),
    ("https://azur-nettoyage-limoges.fr/", "ok", "Azur Nettoyage"),
    ("https://www.tam-net-87.fr/", "ok", "TAM NET 87"),
    ("https://www.tam-net-87.fr/contact", "ok", "TAM NET 87"),
    ("https://defi11.fr/", "ok", "Défi 11"),
    ("https://damiani-laser-tolerie.fr/", "ok", "Damiani AlpMétal"),
    ("https://www.acpt-vidange.com/", "ok", "A.C.P.T."),
    ("https://www.lordi.info/", "ok", "LORDI"),
    ("https://tortora.fr/", "ok", "Tortora"),
    ("http://www.assainissement-argentanais-orne.fr/", "echec", "Assainissement Argentanais"),
    ("https://www.acpt-vidange.com/contactez-nous.php", "ok", "A.C.P.T."),
    ("http://www.betep.fr/", "ok", "BETEP"),
    ("https://www.mg-02.fr/", "ok", "MG02"),
    ("https://www.kapoupakap.fr/contact.html", "ok", "Kap'oupa Kap"),
    ("https://www.alcamparol.com/contact/", "echec", "Alcamparol"),
    ("https://www.mg-02.fr/contact.php", "ok", "MG02"),
    ("https://www.ebeniste-genetier.com/contactez-nous.php", "ok", "Les Ateliers Genetier"),
    ("https://www.ess37.fr/contact", "echec", "E.S.S. 37"),
    ("https://www.lc-bois.fr/contact", "ok", "L.C. Bois"),
    ("https://www.alcamparol.com/contact-2/", "ok_404", "Alcamparol"),
    ("https://tortora.fr/contacter-lentreprise-tortora-dans-laube-pres-de-troyes/", "ok", "Tortora"),
    ("https://www.mfmg.eu/recrutement/", "ok", "MFMG"),
    ("https://damiani-laser-tolerie.fr/fr/page/contact", "ok", "Damiani AlpMétal"),
    ("https://www.vente-directe-pme.com/", "ok", "Vente Directe PME"),
    ("https://bkcs.fr/", "echec", "BKCS"),
    ("https://www.ats55.fr/", "ok", "ATS 55"),
    ("https://www.vt-prevention-formation-caen.fr/", "ok", "VT Prévention"),
    ("https://www.blanchefleur-metallerie.fr/", "ok", "Blanchefleur"),
    ("https://www.ats55.fr/contact-et-devis.php", "ok", "ATS 55"),
    ("https://www.blanchefleur-metallerie.fr/contact.php", "ok", "Blanchefleur"),
    ("https://www.vente-directe-pme.com/infos/4-a-propos-vdpme", "ok", "Vente Directe PME"),
    ("https://www.vt-prevention-formation-caen.fr/contact/", "ok", "VT Prévention"),
]
# 3 appels supplémentaires ont échoué sur une URL de proxy mal formée (erreur
# de l'agent, pas du site) : comptés comme tentatives, jamais comme preuve.
TENTATIVES_PROXY_INVALIDES = 3

# --- Entités examinées -------------------------------------------------------
# decision : importee | approfondir | ecartee | annuaire_seul | non_verifie
# lecture  : officielle | recherche_seule | annuaire
E = []


def add(nom, dep, secteur, decision, motif, lecture="recherche_seule", url=""):
    E.append({"nom": nom, "departement": dep, "secteur": secteur,
              "decision": decision, "motif": motif, "lecture": lecture,
              "url": url, "date": D})


# -- Importées (12) : preuves lues, voir scripts/lot12/fiches.py --------------
for nom, dep, sec, url in [
    ("Laizeau Génie Climatique", "28", "Génie climatique / maintenance CVC", "https://lgc28.fr/"),
    ("BETEP", "65", "Bureau d'études structure", "http://www.betep.fr/"),
    ("Tortora", "10", "Équipement boulangerie / maintenance", "https://tortora.fr/"),
    ("L.C. Bois", "16", "Négoce de bois / distribution", "https://www.lc-bois.fr/"),
    ("MFMG", "08", "Traitement de surface / mécano-soudure", "https://www.mfmg.eu/"),
    ("A.C.P.T.", "61", "Assainissement / vidange", "https://www.acpt-vidange.com/"),
    ("Kap'oupa Kap", "66", "Parc de loisirs / tourisme", "https://www.kapoupakap.fr/"),
    ("Alcamparol", "09", "Hébergement insolite / tourisme", "https://www.alcamparol.com/"),
    ("Ajzenstein Louis et Associés", "08", "Expertise comptable", "https://www.ajzenstein-expert-comptable.com/"),
    ("TAM NET 87", "87", "Nettoyage professionnel", "https://www.tam-net-87.fr/"),
    ("Blanchefleur", "55", "Métallerie / chaudronnerie", "https://www.blanchefleur-metallerie.fr/"),
    ("Les Ateliers Genetier", "71", "Ébénisterie / fabrication mobilier", "https://www.ebeniste-genetier.com/"),
]:
    add(nom, dep, sec, "importee", "Défaut ou processus constaté sur page officielle lue", "officielle", url)

# -- Lues mais écartées : motif explicite ------------------------------------
add("Azur Nettoyage", "87", "Nettoyage professionnel", "ecartee",
    "Site récent et structuré, formulaire qualifié, e-mail et téléphone publiés : aucun défaut exploitable", "officielle",
    "https://azur-nettoyage-limoges.fr/")
add("Damiani AlpMétal", "74", "Tôlerie / découpe laser", "ecartee",
    "Site moderne, suivi de production informatisé revendiqué, formulaire complet : contre-signal fort", "officielle",
    "https://damiani-laser-tolerie.fr/")
add("Vente Directe PME", "85", "Fabricant mobilier / e-commerce", "ecartee",
    "Boutique en ligne pleinement fonctionnelle (prix, panier, avis) : rien à créer ni refondre", "officielle",
    "https://www.vente-directe-pme.com/")
add("HMC Conseil", "08", "Expertise comptable", "ecartee",
    "Site sobre mais complet, formulaire + reCAPTCHA, e-mail publié ; groupe Fizalys mutualisé", "officielle",
    "https://hmcconseil.fr/")
add("LORDI", "82", "Prestataire informatique", "ecartee",
    "Est lui-même prestataire informatique et cybersécurité : pertinence offre faible", "officielle",
    "https://www.lordi.info/")
add("VT Prévention", "14", "Organisme de formation", "ecartee",
    "Site WordPress récent et complet ; compteurs à 0 = artefact de lecture sans JavaScript, pas un défaut", "officielle",
    "https://www.vt-prevention-formation-caen.fr/")
add("E.S.S. 37", "37", "Association formation secourisme", "ecartee",
    "Association ; compteurs à 0 = artefact JS ; page /contact en AccessDenied, parcours non vérifiable", "officielle",
    "https://www.ess37.fr/")
add("Défi 11", "11", "Association insertion / handicap", "ecartee",
    "Association d'insertion financée sur fonds publics : hors cible commerciale B2B", "officielle",
    "https://defi11.fr/")
add("ATS 55", "55", "Métallerie / serrurerie", "approfondir",
    "Site correct, processus devis publié mais aucune preuve de charge manuelle ; pas d'e-mail publié", "officielle",
    "https://www.ats55.fr/")
add("MG02", "02", "Mécanique de précision", "approfondir",
    "Site correct avec formulaire et dépôt de plans ; aucun défaut net, pas d'e-mail publié", "officielle",
    "https://www.mg-02.fr/")
add("Assainissement Argentanais", "61", "Assainissement", "non_verifie",
    "Page non récupérée (échec de lecture) : aucun signal retenable", "officielle",
    "http://www.assainissement-argentanais-orne.fr/")
add("BKCS", "55", "Chaudronnerie / réparation engins", "non_verifie",
    "Page non récupérée (échec de lecture) : aucun signal retenable", "officielle", "https://bkcs.fr/")

# -- Vues en recherche seulement : écartées sans preuve ----------------------
for nom, dep, sec, motif in [
    ("C-W-A Colas Wilemme & Associés", "08", "Expertise comptable", "Réseau H10 (6 cabinets) : décision web mutualisée"),
    ("FICOM", "08", "Expertise comptable", "Même adresse et même téléphone que HMC Conseil : doublon probable, non résolu"),
    ("Florian Mantione Institute", "61", "Recrutement", "Réseau national à pages-villes SEO"),
    ("Keyman Executive Search", "61", "Recrutement", "Réseau national à pages-villes SEO"),
    ("Talents Banque Assurance", "61", "Recrutement", "Réseau national à pages-villes SEO"),
    ("Talents Commerciaux", "61", "Recrutement", "Réseau national à pages-villes SEO"),
    ("Nova Clean", "14", "Nettoyage après sinistre", "Plateforme à milliers de pages-villes, téléphones variables : contre-signal fort"),
    ("Cleanolia", "14", "Comparateur de devis", "Marketplace de mise en relation, pas une TPE cliente"),
    ("Climatisation-28 / SE Habitat", "28", "Climatisation", "Réseau Climatifrance à pages-départements"),
    ("Degré Celsius", "28", "Génie climatique", "Groupe à 3 filiales, GMAO revendiquée : maturité et taille hors cible"),
    ("Tuvache", "28", "Chauffage / plomberie", "Non approfondi, priorité aux cas plus nets"),
    ("Extérieur Nature", "66", "Parc de loisirs", "Réservation en ligne aboutie : contre-signal, non approfondi"),
    ("Outdoor 66", "66", "Activités pleine nature", "Réservation et paiement en ligne avec confirmation immédiate"),
    ("Écosystème QVT", "55", "Conseil RH", "Cabinet national, 10 consultants, aucune implantation 55 établie"),
    ("LFC Humain", "55", "Conseil QVT", "Cabinet national, page générique"),
    ("HR Move Conseil", "55", "Conseil RH", "Cabinet national, 250 références"),
    ("Ad'Solutions", "55", "Conseil RH / RSE", "Cabinet national, page générique"),
    ("T'hompouss Consultants", "55", "Conseil QVCT", "Cabinet national, page générique"),
    ("SOCOREBAT Propreté", "87", "Nettoyage", "Réseau à pages-villes, gabarit dupliqué"),
    ("Amireged SARL", "87", "GED / reprographie", "Annuaire seul (site-solocal), aucun site officiel lu"),
    ("Grapho Tech 87", "87", "Reprographie", "Annuaire seul, non vérifié"),
    ("Graphicolor SARL", "87", "Imprimerie", "Annuaire seul, non vérifié"),
    ("Malinvaud et Cie", "87", "Imprimerie / signalétique", "Annuaire seul, groupe ancien, non vérifié"),
    ("Copies Centre", "87", "Reprographie", "Annuaire seul, non vérifié"),
    ("Copifac", "87", "Reprographie", "Annuaire seul, non vérifié"),
    ("Axe Fournitures", "87", "Fournitures de bureau", "Annuaire seul, non vérifié"),
    ("Dactylo'Claire", "87", "Secrétariat / saisie", "Annuaire seul ; activité de saisie = prestataire, pas client"),
    ("MS Gestion", "87", "Secrétariat externalisé", "Annuaire seul ; prestataire administratif"),
    ("Limousin Entreprise Solution Administrative", "87", "Gestion RH / archivage", "Annuaire seul ; prestataire administratif"),
    ("Stratus Packaging", "87", "Fabricant d'étiquettes", "520 salariés, 100 M€ CA : hors cible TPE"),
    ("SENS & Compétences", "80", "Cabinet de recrutement", "Offre vue sur LinkedIn seulement, entreprise non vérifiée"),
    ("Le CabRH", "76", "Cabinet de recrutement", "5 bureaux régionaux : structure multi-implantations"),
    ("AMALO Recrutement", "76", "Cabinet de recrutement", "5 implantations nationales"),
    ("XEFI Montauban", "82", "Infogérance", "Franchise d'un réseau national"),
    ("Infranat", "82", "Infogérance", "Réseau à pages-départements SEO"),
    ("Ordi 82", "82", "Assistance informatique", "Services à la personne pour particuliers : hors B2B"),
    ("CDG 82", "82", "Collectivité / numérique", "Organisme public, hors cible"),
    ("ALM Assainissement", "61", "Assainissement", "Créée en 2025, non approfondie"),
    ("Tegma", "90", "Traitement de surface", "4 sociétés, 12 M€ CA : hors cible TPE"),
    ("Stach Industries", "90", "Traitement de surface", "Groupe industriel, chaînes haute capacité"),
    ("Chromelec Groupe & Industries", "90", "Traitement de surface", "Groupe, consortium européen CTAC"),
    ("Inodec", "74", "Décolletage", "Non approfondi,hors zone 25 visée"),
    ("Pliages Online / Pliages Pays de Savoie", "73", "Tôle pliée en ligne", "Configurateur et commande en ligne aboutis"),
    (TCS := "TCS Tôlerie", "73", "Tôlerie", "Page de zone d'intervention = SEO multi-villes"),
    ("Garnier Industries", "73", "Chaudronnerie / découpe laser", "Annuaire seul, non vérifié"),
    ("S2P Métallerie", "73", "Métallerie / tuyauterie", "Gabarit SEO à pages-villes et prestations"),
    ("Someto", "55", "Métallerie", "Gabarit SEO à pages-villes"),
    ("Titan Chaudronnerie", "55", "Chaudronnerie", "Adossée à Titan Prefa, non vérifiée"),
    ("EROB", "25", "Décolletage", "Annuaire seul, aucun site officiel trouvé"),
    ("Atelier de Mécanique Deniziot", "25", "Décolletage", "Annuaire seul, aucun site officiel trouvé"),
    ("STS Industrie", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("A2Métal", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("Perrenoud Décolletage", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("SITTB", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("Putaud Mécanique", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("SOSOLIC Industries", "25", "Décolletage", "Annuaire seul, non vérifié"),
    ("AMPS61", "61", "Micro-usinage", "Annuaire seul, non vérifié"),
    ("Microtec", "25", "Décolletage", "Certifié ISO/EN9100, taille supérieure : maturité"),
    ("IDMM", "25", "Décolletage", "Certifié, taille supérieure : maturité"),
    ("AFPA Centre de Carcassonne", "11", "Formation", "Établissement public national"),
    ("Sud Formation CCI Aude", "11", "Formation", "CCI : organisme consulaire"),
    ("CFPPA des Pays d'Aude", "11", "Formation", "Établissement public agricole"),
    ("AFFIC CRIA 37", "37", "Formation / illettrisme", "Association, formations gratuites : hors cible"),
    ("B et C Formation", "37", "Formation SSIAP", "Annuaire seul, non vérifié"),
    ("Odyssée Formations", "37", "Formation SSIAP", "Annuaire seul, non vérifié"),
    ("Guard's Conseil Formation", "37", "Formation SSIAP", "Annuaire seul, non vérifié"),
    ("OFSP", "14", "Formation sécurité", "Réseau à pages-villes, basé Bourg-en-Bresse"),
    ("Alertis", "14", "Formation sécurité", "Réseau national à pages-centres"),
    ("Caen Rescue / FFSS 14", "14", "Formation secourisme", "Association agréée, hors cible commerciale"),
    ("Magasins Bleus", "85", "Vente à domicile", "Réseau national de vente à domicile"),
    ("DASIR", "85", "Distribution pièces auto", "Groupe national, 3 M pièces/an, portail pro abouti"),
    ("Distri Cash", "85", "Grossiste pneumatiques", "715 salariés, leader national : hors cible"),
    ("Exaparts", "85", "Grossiste pièces auto", "Non localisé 85, aire Île-de-France"),
    ("Autodistribution Rembaud", "85", "Distribution pièces auto", "Réseau national Autodistribution"),
    ("T.D.N. TDR", "85", "Radiateurs / thermique", "Annuaire seul, non vérifié"),
    ("VM Matériaux", "16", "Négoce matériaux", "Groupe SAMSE"),
    ("Partedis", "16", "Négoce matériaux", "Réseau national de distribution"),
    ("Tout Faire", "16", "Négoce matériaux", "Réseau 450 points de vente"),
    ("Promeca Distribution", "43", "Fournitures industrielles", "700 000 références, hors zone et hors taille"),
    ("Maison Fossier", "10", "Biscuiterie", "6 magasins + boutique en ligne : maturité"),
    ("Salaisons La Champenoise", "10", "Charcuterie", "Annuaire seul, non vérifié"),
    ("Bioster", "10", "Condiments", "Annuaire seul, non vérifié"),
    ("Nogue Structures Ingénierie", "65", "Bureau d'études", "Vu sur un club d'affaires seulement, site non lu"),
    ("SETES.SA", "65", "Bureau d'études", "LinkedIn seul, 11-50 salariés"),
    ("BET Sodeba", "65", "Bureau d'études béton", "Gabarit SEO à pages-départements"),
    ("David SA", "02", "Matériel agricole", "Réseau multi-départements"),
    ("Rocha SA", "02", "Matériel agricole", "Annuaire seul, non vérifié"),
    ("Motor'Aisne", "02", "Motoculture", "3 magasins, non approfondi"),
    ("Charente Menuiseries Miroiterie", "16", "Menuiserie / agencement", "Annuaire seul, non vérifié"),
    ("Atlantique Stores et Fermetures", "17", "Menuiserie", "Réseau Solabaie"),
    ("Reproland", "90", "GED / dématérialisation", "VENDEUR de solutions, pas un acheteur : piège de requête"),
    ("Deltic", "90", "GED / dématérialisation", "VENDEUR de solutions : piège de requête"),
    ("DIMO Dématérialisation", "90", "GED / dématérialisation", "VENDEUR de solutions : piège de requête"),
    ("Numeria", "90", "GED", "VENDEUR de solutions : piège de requête"),
    ("Sotratech", "75", "Traduction technique", "Agence nationale, TAO outillée : maturité"),
    ("OT Technique", "75", "Traduction technique", "Agence nationale, non vérifiée"),
    ("Alphatrad", "75", "Traduction technique", "Groupe international, post-édition IA déjà offerte"),
    ("Diléal / Alessia Vonau", "national", "Traduction technique", "Indépendante outillée Trados ; elle-même prestataire"),
    ("TT Traduction Technique", "national", "Traduction technique", "Agence, non vérifiée"),
    ("Camping Le Pont du Tarn", "48", "Camping", "Chaîne Flower Campings, moteur de réservation intégré"),
    ("Camping Château de Poinsouze", "23", "Camping", "Chaîne Les Castels, réservation en ligne aboutie"),
    ("Domaine de la Chapelle en Corrèze", "19", "Hébergement / gîtes", "Non approfondi, tarifs et hébergements publiés"),
    ("Champagne René Jolly", "10", "Vignoble / œnotourisme", "Réservation de visite en ligne déjà en place"),
    ("Champagne Urbain", "10", "Vignoble / chambres d'hôtes", "Réservation par formulaire en ligne, non approfondi"),
    ("Champagne Laurent Courtillier", "10", "Vignoble", "Non approfondi"),
    ("Tolix La Manufacture", "71", "Fabricant mobilier", "Marque nationale distribuée largement"),
    ("Creabois 71", "71", "Fabrication mobilier", "Annuaire seul, vente en ligne signalée"),
    ("Frédéric Bardin", "71", "Fabrication mobilier", "Annuaire seul, non vérifié"),
    ("Nicolas Bassot", "71", "Ébénisterie d'art", "Annuaire seul, non vérifié"),
    ("Rhetat Cardon SARL", "71", "Ébénisterie", "Annuaire seul, non vérifié"),
]:
    add(nom, dep, sec, "ecartee", motif)

# -- Annuaires et plateformes rencontrés (jamais des prospects) --------------
for nom, url in [
    ("PagesJaunes", "https://www.pagesjaunes.fr/"),
    ("PagesPro", "https://www.pagespro.com/"),
    ("Kompass", "https://fr.kompass.com/"),
    ("Fabriquons.fr", "https://www.fabriquons.fr/"),
    ("Manageo", "https://www.manageo.fr/"),
    ("Europages", "https://www.europages.fr/"),
    ("118712", "https://www.118712.fr/"),
    ("Solocal / site-solocal", "https://amiregedsarl.site-solocal.com/"),
    ("Webrankinfo", "https://www.webrankinfo.net/"),
    ("Artisans du Patrimoine", "https://artisansdupatrimoine.fr/"),
    ("Omizi", "https://omizi.com/"),
    ("ssiap.pro", "https://ssiap.pro/"),
    ("Lozère Tourisme", "https://www.lozere-tourisme.com/"),
    ("Perpignan Tourisme", "https://www.perpignantourisme.com/"),
    ("Gîtes de France Ariège", "https://www.gites-de-france-ariege.com/"),
    ("GreenGo", "https://www.greengo.voyage/"),
    ("CampingFrance", "https://www.campingfrance.com/"),
    ("Les Castels", "https://www.les-castels.co.uk/"),
    ("camping-insolite.fr", "https://camping-insolite.fr/"),
    ("chambres-hotes.org", "https://www.chambres-hotes.org/"),
    ("InterCarifOref", "https://www.intercariforef.org/"),
    ("MéfomerEnRégion", "https://www.meformerenregion.fr/"),
    ("Annuaire service-public", "https://lannuaire.service-public.gouv.fr/"),
    ("Equiressources", "https://www.equiressources.fr/"),
    ("Apec", "https://www.apec.fr/"),
    ("France Travail", "https://candidat.francetravail.fr/"),
    ("Indeed", "https://fr.indeed.com/"),
    ("Jooble", "https://fr.jooble.org/"),
    ("LinkedIn", "https://fr.linkedin.com/"),
    ("talent.com", "https://fr.talent.com/"),
    ("trabajo.org", "https://fr.trabajo.org/"),
    ("BODACC", "https://www.bodacc.fr/"),
    ("LocalityBiz", "https://localitybiz.com/"),
    ("Mapstr", "https://mapstr.com/"),
    ("Google Hotels", "https://www.google.com/travel/hotels/"),
    ("Bigorre & Business", "https://www.bigorre-business.fr/"),
    ("Imaginalsalce", "https://www.marque.alsace/"),
    ("La Dépêche", "https://www.ladepeche.fr/"),
    ("Aube Champagne (guide PDF)", "https://www.aube-champagne.com/"),
]:
    add(nom, "", "annuaire / plateforme", "annuaire_seul",
        "Annuaire, place de marché ou média : rendement import nul, jamais une preuve", "annuaire", url)


def stats():
    ok = [p for p in PAGES if p[1] in ("ok", "ok_404")]
    return {
        "requetes": len(REQUETES),
        "tentatives_lecture": len(PAGES) + TENTATIVES_PROXY_INVALIDES,
        "lectures_reussies": len(ok),
        "lectures_echouees": len(PAGES) - len(ok) + TENTATIVES_PROXY_INVALIDES,
        "entites_examinees": len(E),
        "entreprises_hors_annuaires": len([e for e in E if e["decision"] != "annuaire_seul"]),
        "annuaires_rencontres": len([e for e in E if e["decision"] == "annuaire_seul"]),
        "decisions": dict(Counter(e["decision"] for e in E)),
        "lectures": dict(Counter(e["lecture"] for e in E)),
        "departements": sorted({e["departement"] for e in E
                                if e["departement"] and e["departement"].isdigit()}),
        "sites_officiels_lus": len({p[2] for p in ok if p[2]}),
    }


def archiver(path: Path):
    payload = {"lot": LOT, "date": D, "stats": stats(),
               "requetes": [dict(zip(("famille", "libelle", "departement_vise", "rendement"), r))
                            for r in REQUETES],
               "pages": [{"url": u, "statut": s, "entite": n} for u, s, n in PAGES],
               "tentatives_proxy_invalides": TENTATIVES_PROXY_INVALIDES,
               "entites": E,
               "securite": {"envoi_autorise": False, "dry_run": True,
                            "aucun_envoi_reel": True, "aucun_achat": True,
                            "aucun_contournement_antibot": True}}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    import pprint
    pprint.pprint(stats())
