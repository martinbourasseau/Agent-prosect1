"""Journal de recherche du Lot 13 — pilote « besoins commerciaux réels ».

Chaque entité porte un `Signal` qui produit sa catégorie A/B/C/D par le moteur
`classification.py`. La catégorie n'est jamais saisie à la main : elle est
calculée, ce qui rend les décisions auditables et testables.

Aucune écriture CRM ici.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from classification import Signal, classify, importable, LABELS

D = "2026-11-03"
LOT = "2026-11-03-lot13"

# --- Requêtes réellement exécutées -----------------------------------------
# (axe visé, libellé, rendement observé)
REQUETES = [
    ("besoin_exprime", '"nous recherchons un prestataire" refonte site internet entreprise 2026',
     "Plateformes de projets : besoins explicites réels, mais identité client souvent masquée"),
    ("marche_public", "appel d'offres refonte site internet réservation office de tourisme 2026 consultation",
     "Acheteurs nommés, mais多数 échéances dépassées"),
    ("developpement", 'entreprise "nouvelle agence" ouverture 2026 "développer notre présence" site internet',
     "Franchises et grands groupes ; aucune TPE indépendante"),
    ("processus", '"recrute" "assistant administratif" "traitement des demandes clients" devis PME 2026',
     "Agrégateurs d'offres ; employeur affiché = agence d'intérim"),
    ("automatisation", 'entreprise "nous souhaitons automatiser" traitement devis demandes clients 2026',
     "PIÈGE : uniquement des vendeurs de solutions d'automatisation"),
    ("marche_public", '"refonte" "site internet" consultation entreprise novembre 2026 date limite réponse marché',
     "Avis expirés ou hors cible budget ; mot-clé « site » bruité"),
    ("besoin_exprime", 'codeur.com projet "AD Rénovation" refonte site vitrine Charente-Maritime',
     "Projet clos depuis 7 mois, page projet non retrouvée"),
    ("besoin_exprime", '"Styl\'Home" OR "stylhome.fr" entreprise artisanale site',
     "ENTREPRISE IDENTIFIÉE : site officiel + besoin explicite recoupés"),
    ("marche_public", '"création d\'un site internet" commune village marché procédure adaptée novembre 2026 décembre 2026',
     "Petites collectivités nommées, échéances souvent closes"),
    ("besoin_exprime", "Adastra cabinet formalités juridiques création société en ligne France",
     "Homonyme avocats à écarter ; société correspondante trouvée, rattachement non établi"),
    ("developpement", '"refonte de notre site" actualité entreprise 2026 annonce nouveau site internet PME',
     "PIÈGE : pages de témoignages d'agences, clients déjà équipés"),
    ("besoin_exprime", 'codeur.com "Finalisation et optimisation du site vitrine Styl\'Home"',
     "URL du projet retrouvée, besoin lu intégralement"),
    ("marche_public", '"COMMUNE D ARVERT" refonte site internet communal appel d\'offres 27 novembre 2026',
     "Acheteur identifié, avis primaire non lu"),
    ("marche_public", '"COMMUNE DE GRAVELINES" refonte hébergement maintenance site web appel d\'offres novembre 2026',
     "Dates contradictoires entre agrégateurs, avis primaire non lu"),
    ("automatisation", "codeur.com projet automatisation processus Make n8n entreprise recherche prestataire",
     "3 projets, tous clos depuis plus de 9 mois, porteurs anonymes"),
    ("processus", '"nous recherchons" "assistant ADV" "saisie des commandes" recrutement entreprise 2026 -indeed -linkedin -apec',
     "PIÈGE : agences d'intérim, client final anonyme"),
    ("developpement", 'entreprise annonce "nouvelle agence" 2026 "site internet" développement activité communiqué officiel',
     "Réseaux de franchise et grands groupes ; décision web mutualisée"),
]
# Deux libellés contiennent un caractère non latin introduit par erreur de
# saisie ; ils sont nettoyés au chargement pour rester lisibles.
REQUETES = [(a, b.replace("多数", "majorité d'"), c.replace("多数", "majorité d'"))
            for a, b, c in REQUETES]

# --- Pages tentées ---------------------------------------------------------
# (url, statut, objet)
PAGES = [
    ("https://www.biscagrandslacs.com/espace-pro/les-consultations-des-entreprises/appel-d-offre-refonte-site-web", "ok", "OT Bisca Grands Lacs"),
    ("https://www.codeur.com/refonte-site-vitrine", "ok", "plateforme — 3 tronçons lus"),
    ("https://www.codeur.com/projects/491582-refonte-du-site-cave-a-vin-toulouse", "ok", "cave à vin Toulouse"),
    ("https://www.codeur.com/projects/491245-conception-et-realisation-d-un-site-vitrine-internet", "ok", "réseau 5 boulangeries"),
    ("https://www.codeur.com/projects/491192-refonte-de-site-web-evolution-vers-application", "ok", "fournisseur fluides frigorigènes"),
    ("https://www.codeur.com/projects/489291-finalisation-et-optimisation-du-site-vitrine-styl-home", "ok", "Styl'Home"),
    ("https://www.codeur.com/projects/488406-site-web", "ok", "Adastra ( cahier des charges )"),
    ("https://stylhome.fr/", "ok", "Styl'Home"),
    ("https://stylhome.fr/contact", "ok", "Styl'Home"),
    ("https://www.adastra-legal.fr/", "ok", "Adastra"),
    ("https://www.codeur.com/creation-site-vitrine", "ok", "plateforme"),
    ("https://www.codeur.com/creation-automatisation-n8n", "ok", "plateforme"),
    ("https://www.francemarches.com/appels-offre/creation-site-web", "ok", "agrégateur de marchés"),
    # Revue des 4 brouillons du Lot 11 (lecture seule)
    ("https://www.miditracage-esvia.com/actualites/2026-04-29/assistant-e-administratif-et-commercial-avignon/", "ok", "Miditraçage Esvia — revue brouillon"),
    ("https://metalleriedesalpilles.fr/", "ok", "Métallerie des Alpilles — revue brouillon"),
    ("https://www.etudebbc.fr/contactus", "ok", "Bureau Bois Concept — revue brouillon"),
    ("https://www.etudebbc.fr/", "ok", "Bureau Bois Concept — revue brouillon"),
    ("https://www.frezouls.fr/controle-dacces/", "ok", "ETS Frézouls — revue brouillon"),
    # Échecs : URL de proxy mal formée par l'agent, jamais une restriction du site
    ("(url proxy mal formée)", "echec", "erreur agent"),
    ("(url proxy mal formée)", "echec", "erreur agent"),
]

# La page codeur.com/refonte-site-vitrine a été lue en 3 tronçons : 3 appels de
# lecture pour une seule page. On distingue donc les appels des pages distinctes.
APPELS_TRONCONS_SUPPLEMENTAIRES = 2

# --- Entités examinées -----------------------------------------------------
E: list[dict] = []


def add(nom, dep, secteur, signal: Signal, motif, *, url="", lecture="recherche_seule",
        source_type="autre"):
    errors = signal.validate()
    assert not errors, (nom, errors)
    cat, raisons = classify(signal)
    E.append({"nom": nom, "departement": dep, "secteur": secteur,
              "categorie": cat, "categorie_label": LABELS[cat],
              "decision": "importee" if importable(cat) else
                          ("approfondir" if cat == "C" else "écartée"),
              "motif": motif, "raisons_moteur": raisons, "url": url,
              "lecture": lecture, "source_type": source_type, "date": D,
              "signal": {
                  "exprimed": signal.expressed,
                  "identite_etablie": signal.identity_established,
                  "page_lue": signal.page_read,
                  "pertinent": signal.still_relevant,
                  "observe": signal.observed,
                  "rattachement_etabli": signal.attachment_established,
                  "disqualifiants": signal.disqualifiers,
              }})


# -- A : besoin explicite, identité établie, page lue, encore pertinent ------
add("Styl'Home", "59", "Rénovation intérieure / peinture en bâtiment",
    Signal("Styl'Home", expressed=True, identity_established=True, page_read=True,
           observed=True),
    "Demande publique de finalisation/correction du site stylhome.fr, lue "
    "intégralement ; défauts corroborés indépendamment sur le site officiel "
    "(photo des gérants encore en placehold.co « Soon.. », ancienneté "
    "incohérente). Consultation close après 122 offres : contre-signal retenu.",
    url="https://www.codeur.com/projects/489291-finalisation-et-optimisation-du-site-vitrine-styl-home",
    lecture="officielle", source_type="plateforme_projet")

# -- C : éléments insuffisants ----------------------------------------------
add("Adastra", "75", "Formalités juridiques et création de sociétés",
    Signal("Adastra", expressed=True, identity_established=True, page_read=True,
           attachment_established=False),
    "Un cahier des charges public demande refonte + automatisation pour une "
    "entité nommée Adastra dont l'activité correspond, mais l'URL du site et le "
    "contact y sont masqués. adastra-legal.fr concorde par activité et adresse ; "
    "le contact cité (« Djamil ») n'apparaît pas dans l'équipe publiée. "
    "Rattachement non établi : aucune fiche créée.",
    url="https://www.adastra-legal.fr/", lecture="officielle",
    source_type="site_officiel")

for nom, dep, sec, url, motif in [
    ("Cave à vin et épicerie fine (Toulouse)", "31", "Commerce de détail alimentaire",
     "https://www.codeur.com/projects/491582-refonte-du-site-cave-a-vin-toulouse",
     "Besoin explicite et projet OUVERT (21/10/2026) : site Wix lent, mal adapté "
     "au téléphone, mises à jour difficiles. Mais « le profil du client est "
     "réservé aux prestataires abonnés » : identité non publique, aucun canal "
     "de contact. Accès payant non contourné."),
    ("Réseau de 5 boulangeries", "", "Boulangerie / commerce de bouche",
     "https://www.codeur.com/projects/491245-conception-et-realisation-d-un-site-vitrine-internet",
     "Besoin explicite, projet OUVERT (14/10/2026), site vitrine multi-boutiques "
     "pensé mobile. Identité du porteur réservée aux abonnés : non exploitable."),
    ("Fournisseur français de fluides frigorigènes", "", "Distribution de fluides frigorigènes",
     "https://www.codeur.com/projects/491192-refonte-de-site-web-evolution-vers-application",
     "Projet OUVERT (13/10/2026) mais périmètre applicatif imposé "
     "(React/TanStack SSR, Supabase, 230 redirections) au-delà de l'offre "
     "Prospecto, et identité réservée aux abonnés."),
]:
    add(nom, dep, sec,
        Signal(nom, expressed=True, identity_established=False, page_read=True),
        motif, url=url, lecture="officielle", source_type="plateforme_projet")

for nom, dep, sec, motif in [
    ("AD Rénovation", "17", "Entreprise générale du bâtiment",
     "Besoin explicite repéré (refonte, site de plus de 8 ans) mais projet clos "
     "depuis 7 mois et page projet non retrouvée : ni lecture ni site officiel."),
    ("Via Prépa", "", "Plateforme d'accompagnement prépa ECG",
     "Demande de refonte complète vue en résultat de recherche seulement ; "
     "page projet non lue, site officiel non lu."),
    ("Zenspire Army", "", "Commerce en ligne",
     "Demande de modernisation vue en extrait de recherche ; page non lue."),
    ("Commune d'Arvert", "17", "Collectivité territoriale",
     "Acheteur nommé pour une refonte de site communal (échéance 27/11/2026 "
     "annoncée) mais avis primaire non lu : montant et éligibilité inconnus."),
    ("Commune de Gravelines", "59", "Collectivité territoriale",
     "Refonte/hébergement/maintenance annoncés au 17/11/2026 par un agrégateur, "
     "dates contradictoires ailleurs ; avis primaire non lu."),
    ("HEXAPAGE", "92", "Services bureautiques",
     "Offre ADV vue via agrégateur ; employeur final et processus non vérifiés "
     "sur source officielle."),
    ("SIMPLICITI", "78", "Éditeur de logiciels",
     "Offre ADV « optimisation et fluidification » vue via agrégateur ; "
     "éditeur logiciel, vendeur probable plutôt qu'acheteur."),
    ("Europe Contract", "", "Services aux entreprises",
     "Offres ADV multiples vues via agrégateur ; agit comme intermédiaire."),
    ("O'RECUP", "971", "Récupération / négoce",
     "Offre « assistante administrative et chargé de planning » vue via "
     "agrégateur ; site officiel non lu."),
    ("HEXIS", "971", "Distribution de films adhésifs",
     "Offre d'assistant polyvalent vue via agrégateur ; site officiel non lu."),
    ("SCI PRO IMMO", "971", "Immobilier",
     "Offre administrative vue via agrégateur ; hors périmètre métropolitain "
     "et site non lu."),
    ("KHM", "95", "Automobile / garage",
     "Offre secrétaire comptable (devis, facturation, planning) vue via "
     "agrégateur ; entreprise non vérifiée."),
    ("NG PRO MULTI SERVICES", "95", "Multi-services bâtiment",
     "Offre secrétaire polyvalente vue via agrégateur ; entreprise non vérifiée."),
    ("EXPERTNET TECHNOLOGIES SA", "95", "BTP",
     "Offre d'assistant administrative vue via agrégateur ; entreprise non vérifiée."),
    ("Afigec", "92", "Expertise comptable",
     "Offre d'assistant administratif externalisé vue via agrégateur ; "
     "prestation vendue, pas un processus interne documenté."),
]:
    add(nom, dep, sec, Signal(nom, identity_established=True, page_read=False), motif)

# -- D : appel d'offres et organismes — disqualifiés -------------------------
for nom, dep, sec, disq, motif in [
    ("Office de Tourisme Bisca Grands Lacs", "40", "Office de tourisme", "signal_expire",
     "Besoin explicite très détaillé (refonte, réservation, RGAA/OPQUAST) LU sur "
     "le site officiel, mais « limite de réception des offres avant le vendredi "
     "31 octobre 2025 » : expiré depuis plus d'un an. L'extrait de recherche "
     "ne montrait pas la date ; seule la lecture l'a révélée."),
    ("CRT Centre-Val de Loire", "45", "Comité régional du tourisme", "signal_expire",
     "Consultation 26-51899 close le 24/06/2026."),
    ("OT Clermont Auvergne Volcans", "63", "Office de tourisme", "signal_expire",
     "Refonte de clermontauvergnevolcans.com, dépôt clos le 07/04/2026."),
    ("SPL Gorges de l'Ardèche - Pont d'Arc", "07", "SPL touristique", "signal_expire",
     "Refonte du dispositif digital, réponse close le 14/10/2026."),
    ("Commune de Marciac", "32", "Collectivité territoriale", "signal_expire",
     "Création du site du Pôle des Augustins, MP2026_003, clos le 30/10/2026."),
    ("EESAB", "29", "Enseignement supérieur", "signal_expire",
     "Refonte du site, remise des plis close le 16/10/2026."),
    ("Hôpitaux Universitaires de Strasbourg / CH Erstein", "67", "Santé", "signal_expire",
     "Refonte site + intranet, avis archivé, clos le 12/10/2026."),
    ("Le Mans Métropole — Office de Tourisme", "72", "Office de tourisme", "signal_expire",
     "Refonte site OT et Bureau des Congrès, clos le 20/02/2026."),
    ("Sénéo", "92", "Syndicat des eaux", "signal_expire",
     "Refonte/hébergement/maintenance, clos le 26/11/2025."),
    ("Ville de Clichy", "92", "Collectivité territoriale", "hors_cible_taille",
     "Refonte ouverte jusqu'au 23/11/2026 mais estimée à 210 k€, accord-cadre "
     "reconductible 3 fois : hors de portée d'une micro-entreprise."),
    ("Ville de Lyon — Théâtre des Célestins", "69", "Collectivité territoriale", "hors_cible_taille",
     "Hébergement, maintenance et développement, échéance 20/11/2026 : "
     "marché de taille institutionnelle."),
    ("Centre National de Gestion", "75", "Établissement public", "hors_cible_taille",
     "Tierce maintenance applicative, échéance 13/11/2026 : hors offre."),
    ("CMA Centre-Val de Loire", "45", "Chambre consulaire", "attribution_deja_prononcee",
     "Marché conclu le 03/02/2026 : avis d'attribution, pas une opportunité."),
    ("NEOMA Business School", "51", "Enseignement supérieur", "attribution_deja_prononcee",
     "Avis d'attribution pour le nouveau site web."),
    ("Commune de Mieussy", "74", "Collectivité territoriale", "hors_cible_taille",
     "Déjà instruite au Lot 11 : 20 000 € HT, références de 3 ans et "
     "attestations exigées, bloquantes pour une micro-entreprise."),
    ("Région Occitanie", "34", "Collectivité régionale", "hors_cible_statut",
     "Avis remonté par le mot-clé « site » alors qu'il porte sur un Site de "
     "Maintenance et de Remisage ferroviaire : faux positif de requête."),
]:
    # Un avis seulement vu en résultat de recherche n'est pas « lu » : le
    # besoin n'est donc pas marqué comme exprimé-vérifié. Le rejet reste
    # fondé sur la date ou le montant annoncés, et cette limite est tracée.
    lu = nom == "Office de Tourisme Bisca Grands Lacs"
    add(nom, dep, sec,
        Signal(nom, expressed=lu, identity_established=True, page_read=lu,
               disqualifiers=[disq]),
        motif, source_type="registre_public",
        lecture="officielle" if lu else "recherche_seule",
        url=("https://www.biscagrandslacs.com/espace-pro/les-consultations-des-entreprises/"
             "appel-d-offre-refonte-site-web" if lu else ""))

# -- D : développement annoncé mais décision mutualisée ou hors cible -------
for nom, dep, sec, disq, motif in [
    ("Néosoft", "35", "ESN / conseil", "hors_cible_taille",
     "Objectif 240 M€ de CA en 2028, ouvertures d'agences annuelles : ETI."),
    ("TechFirm Engineering", "", "Ingénierie", "hors_territoire",
     "Groupe suisse basé à Genève : hors territoire français."),
    ("Agency Car", "", "Réseau automobile", "reseau_decision_mutualisee",
     "Ouvertures d'agences multiples en 2026 mais réseau de franchise : "
     "la présence web est décidée au niveau national."),
    ("Arthurimmo.com", "", "Réseau immobilier", "reseau_decision_mutualisee",
     "Plus de 300 implantations ; les nouvelles agences bénéficient du site "
     "national et de la multidiffusion du réseau."),
    ("Kuehne+Nagel", "", "Transport / logistique", "hors_cible_taille",
     "Nouvelles agences relayées par la presse professionnelle : grand groupe."),
    ("CARBURO", "", "Réseau de garages", "prestataire_deja_en_place",
     "Nouveau site internet lancé en octobre 2026, architecture pensée pour "
     "l'IA : le besoin vient d'être satisfait."),
]:
    add(nom, dep, sec,
        Signal(nom, identity_established=True, page_read=False, disqualifiers=[disq]),
        motif)

# -- D : clients cités en témoignage d'agence ⇒ déjà équipés ----------------
for nom, dep, sec, motif in [
    ("Moulin de Radray", "61", "Hébergement / tourisme",
     "Cité en témoignage : site web déjà réalisé par une agence de Normandie."),
    ("FSGT 61", "61", "Association sportive",
     "Cité en témoignage : « peut enfin se vanter d'avoir son propre site "
     "internet » — site déjà livré par l'agence."),
    ("Baert.fr", "", "Négoce",
     "Cité en témoignage pour la refonte de son site, cahier des charges et "
     "délais respectés : prestataire en place."),
    ("Armel Levesque", "", "Activité de services",
     "Cité en témoignage : refonte totale accompagnée par une agence."),
    ("Future4care", "", "Santé / innovation",
     "Cité en témoignage : refonte du site vitrine réalisée par une agence "
     "parisienne."),
    ("Escarbille", "", "Restauration",
     "Cité en réalisation : refonte complète avec réservation simplifiée "
     "déjà livrée."),
    ("Instant Mouvement", "38", "Cours de yoga",
     "Cité en réalisation : site vitrine et e-commerce créé en avril 2026 "
     "avec module de réservation."),
    ("Disques Anciens", "14", "Commerce en ligne",
     "Cité en réalisation : dépannage et refonte progressive en juin 2026."),
    ("Pepin Pialou Avocates", "973", "Cabinet d'avocates",
     "Cité en réalisation : site vitrine créé en septembre 2026."),
]:
    add(nom, dep, sec,
        Signal(nom, identity_established=True, page_read=False,
               disqualifiers=["prestataire_deja_en_place"]),
        motif)

# -- D : vendeurs de solution, jamais des acheteurs -------------------------
for nom, sec, motif in [
    ("Automatisation-Intelligence-Artificielle.fr", "Conseil automatisation",
     "Guide commercial « automatiser la génération de devis PDF » : vendeur."),
    ("Tamarin Flow", "Conseil automatisation",
     "Méthode PME pour automatiser devis/factures : vendeur."),
    ("PROPRET", "Éditeur logiciel",
     "Logiciel de devis/facturation multiservices : vendeur."),
    ("IMAGIN", "Agence automatisation",
     "Prestation d'automatisation devis/factures chiffrée 800 à 1 500 € : vendeur."),
    ("Just Use AI", "Conseil IA",
     "Guide et cas clients d'automatisation de devis : vendeur."),
    ("Agence Intelligence Artificielle", "Conseil IA",
     "Comparatif d'agences n8n : vendeur ; sa statistique sur 39 annonces "
     "Codeur n'est pas une preuve et n'a pas été retenue comme telle."),
    ("Aurone", "Agence web",
     "Page de service « refonte de site internet » : vendeur."),
    ("Je Communique", "Agence web",
     "Agence normande de création/refonte : vendeur ; ses témoignages ont "
     "servi à identifier des clients déjà équipés, pas des prospects."),
    ("Agence Dilo", "Agence web",
     "Page de service création/refonte TPE-PME : vendeur."),
    ("Digital Unicorn", "Agence web",
     "Classement d'agences et tarifs d'automatisation IA : vendeur."),
    ("Arrêt Net", "Webmaster indépendant",
     "Page SEO « refonte de site internet » par ville : vendeur."),
    ("SeriousWeb", "Agence web",
     "Articles promotionnels relayés sur deux sites : vendeur."),
]:
    add(nom, "", sec,
        Signal(nom, identity_established=True, page_read=False,
               disqualifiers=["vendeur_de_solution"]),
        motif)

# --- Intermédiaires et agrégateurs : jamais des prospects ------------------
INTERMEDIAIRES = [
    ("Codeur.com", "plateforme de projets", "Source de découverte ; identité des clients réservée aux abonnés"),
    ("France Marchés", "agrégateur de marchés", "Agrégateur ; mot-clé « site » fortement bruité"),
    ("Marchés Online", "agrégateur de marchés", "Agrégateur"),
    ("Instao", "agrégateur de marchés", "Agrégateur"),
    ("Akkel", "agrégateur de marchés", "Agrégateur"),
    ("Semagora", "agrégateur de marchés", "Agrégateur ; son « astuce » commerciale n'est pas une preuve"),
    ("francemarches (liste création site web)", "agrégateur de marchés", "199 avis, majorité hors sujet"),
    ("Indeed", "agrégateur d'offres", "Employeur affiché souvent l'agence, pas l'entreprise"),
    ("Jooble", "agrégateur d'offres", "Idem"),
    ("Le Figaro Emploi", "agrégateur d'offres", "Idem"),
    ("Meteojob", "agrégateur d'offres", "Idem"),
    ("FreeHire", "agrégateur d'offres", "Idem"),
    ("GrabJobs", "agrégateur d'offres", "Idem"),
    ("SIMON", "agence de recrutement", "Recrute pour un client anonyme"),
    ("Adecco", "agence d'intérim", "Recrute pour un client anonyme"),
    ("Randstad", "agence d'intérim", "Recrute pour un client anonyme"),
    ("LIP Tertiaire", "agence d'intérim", "Recrute pour un client anonyme"),
    ("Walters People", "agence d'intérim", "Recrute pour un client anonyme ; offre close"),
    ("Harry Hope", "cabinet de recrutement", "Recrute pour un client anonyme"),
    ("Talents ADV Supply", "cabinet de recrutement", "Recrute pour un client anonyme"),
    ("Manpower", "agence d'intérim", "Recrute pour un client anonyme"),
    ("Proman", "agence d'intérim", "Recrute pour un client anonyme"),
    ("Iziwork", "plateforme d'intérim", "Recrute pour un client anonyme"),
    ("Actual", "agence d'intérim", "Recrute pour un client anonyme"),
    ("Pappers", "registre d'entreprises", "Découverte only, jamais une preuve de besoin"),
    ("Annuaire Entreprises (data.gouv)", "registre public", "Identité, pas besoin"),
    ("Le Journal des Entreprises", "média", "Source de signaux, pas un prospect"),
    ("L'Express Franchise", "média", "Source de signaux, pas un prospect"),
    ("Observatoire de la Franchise", "média", "Source de signaux, pas un prospect"),
    ("FAQ Logistique", "média", "Source de signaux, pas un prospect"),
    ("Emploi-Événementiel", "média emploi", "Source de signaux, pas un prospect"),
    ("Ancoris", "média implantations", "Source de signaux, pas un prospect"),
]


def stats() -> dict:
    ok = [p for p in PAGES if p[1] == "ok"]
    cats = Counter(e["categorie"] for e in E)
    deps = sorted({e["departement"] for e in E if e["departement"].isdigit()})
    return {
        "requetes": len(REQUETES),
        "appels_lecture": len(PAGES) + APPELS_TRONCONS_SUPPLEMENTAIRES,
        "appels_reussis": len(ok) + APPELS_TRONCONS_SUPPLEMENTAIRES,
        "appels_echoues": len(PAGES) - len(ok),
        "pages_distinctes_lues": len({p[0] for p in ok}),
        "pages_lecture_revue_brouillons": len([p for p in ok if "revue brouillon" in p[2]]),
        "entites_examinees": len(E),
        "intermediaires_agregateurs": len(INTERMEDIAIRES),
        "categories": {c: cats.get(c, 0) for c in "ABCD"},
        "decisions": dict(Counter(e["decision"] for e in E)),
        "importables": sum(1 for e in E if importable(e["categorie"])),
        "lectures": dict(Counter(e["lecture"] for e in E)),
        "departements": deps,
        "secteurs": len({e["secteur"] for e in E}),
        "axes_recherche": dict(Counter(r[0] for r in REQUETES)),
    }


def archiver(path: Path) -> dict:
    payload = {
        "lot": LOT, "date": D, "strategie": "besoins commerciaux exprimés et processus observés",
        "stats": stats(),
        "requetes": [dict(zip(("axe", "libelle", "rendement"), r)) for r in REQUETES],
        "pages": [{"url": u, "statut": s, "objet": o} for u, s, o in PAGES],
        "entites": E,
        "intermediaires": [{"nom": n, "type": t, "note": x} for n, t, x in INTERMEDIAIRES],
        "securite": {"envoi_autorise": False, "dry_run": True, "aucun_envoi_reel": True,
                     "aucun_achat": True, "aucun_abonnement": True,
                     "acces_payant_non_contourne": True,
                     "aucun_contournement_antibot": True},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    import pprint
    pprint.pprint(stats())
