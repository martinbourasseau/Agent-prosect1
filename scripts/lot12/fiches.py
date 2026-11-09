"""Fiches du Lot 12 — preuves réellement lues, aucune écriture.

Principes appliqués, hérités des corrections du Lot 11 :
* une preuve ne cite que ce qui a été vu dans une page récupérée ;
* les contre-signaux sont typés `maturite_existante` pour être réellement
  lus par `counter_signals.collect()` et peser sur la priorité ;
* l'axe IA ne monte que sur un processus publié et cité, jamais sur le secteur ;
* une coordonnée n'est jamais déduite d'un motif de domaine.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from prospecto.models import Evidence, Prospect
from prospecto.scoring import score_prospect
from prospecto.priority import ENGINE_VERSION, assess

TODAY = date(2026, 11, 3)
D = "2026-11-03"
LOT = "2026-11-03-lot12"
DNS_PATH = Path(__file__).resolve().parents[2] / "data/history/lot12-dns-2026-11-03.json"
def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


# La clé du relevé DNS peut différer par la casse ou la ponctuation du nom
# commercial ("L.C. BOIS" relevé vs "L.C. Bois" au CRM). On normalise des deux
# côtés plutôt que de perdre le statut MX et de plafonner la priorité à tort.
DNS = {_norm(k): v["status"] for k, v in
       json.loads(DNS_PATH.read_text(encoding="utf-8")).items() if v.get("email")}


def ev(kind, url, quote, detail, *, level=None, source="site_officiel",
       reliability="haute", observed=True):
    e = {"kind": kind, "source_url": url, "quote": quote, "detail": detail,
         "source_type": source, "reliability": reliability,
         "observed_at": D, "verified_at": D, "observed": observed}
    if level:
        e["signal_level"] = level
    return e


FICHES = [
    # ------------------------------------------------------------------ 01
    {
        "company": "Laizeau Génie Climatique", "domain": "lgc28.fr",
        "website": "https://lgc28.fr/",
        "sector": "Génie climatique, maintenance CVC et fluides industriels",
        "city": "Fontenay-sur-Eure", "department": "28",
        "address": "Z.I Euroval, 34 rue du Val de l'Eure, 28630 Fontenay-sur-Eure",
        "email": "", "phone": "02 37 30 14 15",
        "contact_name": "Pascal Laizeau", "contact_role": "gérant",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux refondre le site pour que vos demandes de contrat d'entretien arrivent par un formulaire relié à votre boîte, au lieu du seul téléphone",
        "observation": "votre page contact invite à joindre l'équipe par courrier ou par téléphone et publie encore un numéro de fax",
        "demo_detail": "une demande de contrat d'entretien reçue par formulaire, classée par site et par type d'installation",
        "custom_subject": "LGC : demandes de contrat d'entretien et page contact",
        "custom_hook": "Votre page contact indique « Contactez l'équipe LGC par courrier ou par téléphone » et publie un fax.",
        "notes": "Aucune adresse e-mail publiée sur les deux pages lues : contact téléphonique uniquement.",
        "evidence": [
            ev("site_obsolete", "https://lgc28.fr/",
               "![](https://lgc28.fr/images/lgc_header.gif)",
               "L'intégralité de la mise en page repose sur des images GIF (en-tête, séparateurs de menu, titres de rubriques, coins de blocs) et sur des tableaux HTML. Les titres « l'entreprise », « activités » et « Contact » sont des fichiers .gif et non du texte. Navigation en pages .html statiques."),
            ev("website_gap", "https://lgc28.fr/contact.html",
               "Contactez l'équipe LGC par courrier ou par téléphone, retrouvez ci-dessous nos coordonnées",
               "La page contact ne propose aucun formulaire et aucune adresse e-mail. Les seuls canaux publiés sont l'adresse postale, le téléphone 02 37 30 14 15 et le fax 02 37 30 14 16. Un professionnel qui cherche à demander un devis en dehors des horaires d'ouverture n'a aucun canal écrit."),
            ev("parcours_incomplet", "https://lgc28.fr/",
               "Contrat d'entretien pour les installations de chauffage et climatisation.",
               "L'entreprise vend des contrats d'entretien et des chiffrages, mais le site ne propose aucun chemin de demande en ligne : tous les boutons « Nous contacter » renvoient à la même page contact sans formulaire."),
        ],
        "contre_signaux": [
            {"source_url": "https://lgc28.fr/",
             "quote": "Comptant déjà parmi ces plus fidèles clients : Lancaster Production, Guerlain",
             "detail": "Portefeuille de grands comptes et de collectivités déjà établi : le besoin n'est pas la création. La présence en ligne existe, le manque est le canal de demande écrit."},
        ],
    },
    # ------------------------------------------------------------------ 02
    {
        "company": "L.C. Bois", "domain": "lc-bois.fr",
        "website": "https://www.lc-bois.fr/",
        "sector": "Négoce de bois et matériaux, livraison professionnels et particuliers",
        "city": "Barbezieux-Saint-Hilaire", "department": "16",
        "address": "13 avenue de Plaisance, 16300 Barbezieux-Saint-Hilaire",
        "email": "contact@lcbois.fr", "phone": "05 45 78 85 83",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte", "automatisation"], "need": "refonte",
        "process_hint": "demandes de devis reçues par formulaire et par téléphone, catalogue de panneaux et de bois sans commande en ligne, livraisons planifiées sur quatre départements",
        "recommended_service": "Je peux remplacer les quatre boutons services qui reviennent à l'accueil par de vraies pages, pour que chaque demande arrive déjà qualifiée",
        "observation": "les quatre raccourcis « Rénover ma toiture », « Démousser ma toiture », « Rénover ma charpente » et « Ramoner ma cheminée » pointent tous vers la page d'accueil",
        "demo_detail": "un raccourci « bois de charpente » qui ouvre la bonne gamme et prépare une demande de devis avec les longueurs souhaitées",
        "custom_subject": "L.C. Bois : les quatre raccourcis services reviennent à l'accueil",
        "custom_hook": "Sur votre accueil, les quatre raccourcis services pointent tous vers la même page d'accueil.",
        "notes": "Adresse publiée dans les publications Facebook intégrées au site officiel ; domaine lcbois.fr distinct du domaine du site lc-bois.fr, ce qui correspond à une adresse commerciale distincte du domaine vitrine.",
        "evidence": [
            ev("parcours_incomplet", "https://www.lc-bois.fr/",
               "[Rénover ma toiture](https://www.lc-bois.fr/)",
               "Les quatre raccourcis illustrés de la page d'accueil (« Rénover ma toiture », « Démousser ma toiture », « Rénover ma charpente », « Ramoner ma cheminée ») ont tous pour cible l'URL racine https://www.lc-bois.fr/. Le visiteur qui clique revient au point de départ. Ces prestations ne correspondent d'ailleurs pas au cœur d'activité affiché, le négoce de bois."),
            ev("website_gap", "https://www.lc-bois.fr/contact",
               "Contacter votre spécialiste du bois à Barbezieux-Saint-Hilaire",
               "La page contact fonctionne (formulaire, téléphone, adresse) mais son titre de page est « Menuiserie pvc, Alu à Barbezieux-Saint-Hilaire en Charente (16) », sans rapport avec le négoce de bois. Le contenu affiché en tête d'accueil annonce « plus de 15 ans » alors qu'un pictogramme de la même page affiche « 30 ans d'expérience »."),
            ev("processus_manuel", "https://www.lc-bois.fr/",
               "Nous proposons également des dérivés PVC",
               "Le catalogue est décrit comme diversifié (agglomérés, contreplaqués, OSB, mélaminés, isolation, plaques fibro) mais aucune commande en ligne n'est proposée : le parcours publié se limite à « Devis gratuit » et au téléphone. Les demandes de prix et de disponibilité passent donc par un échange humain, pour une entreprise qui livre sur les départements 16, 17, 33 et 24."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.lc-bois.fr/contact",
             "quote": "En cochant cette case, j’accepte que les données saisies dans le formulaire ci-dessus soient utilisées",
             "detail": "Un formulaire de contact fonctionne et le consentement est configuré : le besoin porte sur les liens cassés et le parcours de devis, pas sur la création d'un canal de contact."},
        ],
    },
    # ------------------------------------------------------------------ 03
    {
        "company": "A.C.P.T.", "domain": "acpt-vidange.com",
        "website": "https://www.acpt-vidange.com/",
        "sector": "Assainissement, vidange et curage, nettoyage de voirie",
        "city": "Argentan", "department": "61",
        "address": "4 rue du Commerce, 61200 Argentan",
        "email": "", "phone": "",
        "contact_name": "", "contact_role": "",
        "needs": ["automatisation", "agent_ia"], "need": "automatisation",
        "process_hint": "après chaque intervention établissement d'un bordereau de suivi de déchets et d'une facture détaillée",
        "recommended_service": "Je peux préparer le bordereau de suivi de déchets et la facture à partir des éléments saisis en intervention, pour éviter la double saisie au retour",
        "observation": "votre site indique qu'après chaque intervention vous établissez un bordereau de suivi de déchets et une facture détaillée",
        "demo_detail": "une intervention saisie une fois qui produit le bordereau de déchets et la facture correspondante",
        "custom_subject": "A.C.P.T. : bordereau de déchets et facture après intervention",
        "custom_hook": "Votre site précise qu'après chaque intervention vous établissez un bordereau de suivi de déchets et une facture détaillée.",
        "notes": "Raison sociale indiquée dans le bloc RGPD de la page contact : TRAVAUX PUBLICS AIGLONS SARL. Aucune adresse e-mail ni téléphone publiés sur les deux pages lues.",
        "evidence": [
            ev("processus_manuel", "https://www.acpt-vidange.com/",
               "Après chaque intervention, nous établissons également un bordereau de suivi de déchets et une facture détaillée en toute transparence.",
               "Processus administratif répétitif explicitement publié par l'entreprise : deux documents sont produits après chaque intervention. Pour une activité de vidange avec tournées sur l'Orne et le Calvados, cela représente un volume documentaire récurrent. Le site ne décrit aucun outil produisant ces documents : le mode de production reste non vérifié."),
            ev("website_gap", "https://www.acpt-vidange.com/contactez-nous.php",
               "Pour toute demande de renseignements ou suggestions sur notre site",
               "La page contact ne propose qu'un formulaire générique (nom, téléphone, e-mail, message) sans champ décrivant l'intervention : type de fosse, volume, commune. Aucune adresse e-mail directe n'est publiée. Chaque demande doit être requalifiée par échange."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.acpt-vidange.com/contactez-nous.php",
             "quote": "(TRAVAUX PUBLICS AIGLONS SARL s'engage à ce que la collecte et le traitement de vos données",
             "detail": "Un formulaire de contact fonctionne avec consentement et politique de confidentialité : le besoin porte sur la production documentaire, pas sur le canal de contact."},
        ],
    },
    # ------------------------------------------------------------------ 04
    {
        "company": "Alcamparol", "domain": "alcamparol.com",
        "website": "https://www.alcamparol.com/",
        "sector": "Hébergement insolite, gîte de groupe et ferme équestre",
        "city": "Sainte-Croix-Volvestre", "department": "09",
        "address": "Lieu-dit Berreté, 09230 Sainte-Croix-Volvestre",
        "email": "", "phone": "",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte", "automatisation"], "need": "refonte",
        "process_hint": "réservations de groupe traitées par échange de mails pour envoyer les conditions particulières et générales du contrat de location",
        "recommended_service": "Je peux mettre en ligne une demande de séjour de groupe qui envoie automatiquement les conditions et rassemble les dates, au lieu d'un échange de mails",
        "observation": "votre accueil indique que pour les réservations de groupe il faut vous contacter directement par mail pour recevoir les conditions du contrat de location",
        "demo_detail": "une demande de stage avec dates et effectif qui déclenche l'envoi des conditions et prépare le contrat de location",
        "custom_subject": "Alcamparol : réservations de groupe et contrat de location",
        "custom_hook": "Votre accueil demande de vous écrire par mail pour recevoir les conditions du contrat de location de groupe.",
        "notes": "Deux tentatives de lecture de la page contact ont échoué ; aucune coordonnée électronique officielle n'a pu être relevée. Le téléphone trouvé en annuaire n'est pas importé.",
        "evidence": [
            ev("processus_manuel", "https://www.alcamparol.com/",
               "Pour les réservations de groupe, merci de me contacter directement par mail pour recevoir les conditions particulières et générales du contrat de location.",
               "Le parcours de réservation de groupe est explicitement manuel et publié par l'hébergeur : chaque demande déclenche un échange de mails pour transmettre les conditions, puis l'établissement du contrat. La structure accueille des groupes de 10 à 25 personnes en stages et retraites, ce qui rend ce parcours récurrent."),
            ev("site_obsolete", "https://www.alcamparol.com/",
               "http://www.alcamparol.com/wp-admin/post.php?post=2545&action=edit",
               "Le lien « pour recevoir des groupes » inséré dans le texte de l'accueil pointe vers l'URL d'édition de l'administration WordPress (wp-admin/post.php?action=edit), inutilisable pour un visiteur. Les liens internes et les images du diaporama sont en http:// alors que le site est servi en https://."),
            ev("website_gap", "https://www.alcamparol.com/",
               "Nous utilisons des cookies pour vous garantir la meilleure expérience sur notre site. Si vous continuez à utiliser ce dernier, nous considérerons que vous acceptez l'utilisation des cookies.",
               "Le bandeau de cookies repose sur un consentement implicite (« si vous continuez à utiliser ce dernier, nous considérerons que vous acceptez ») avec un simple bouton Ok, sans choix de refus. Aucune réservation en ligne n'est proposée pour les hébergements."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.alcamparol.com/",
             "quote": "La ferme est un lieu d'accueil depuis 2010.",
             "detail": "Le site est structuré et présente chaque hébergement sur une page dédiée : la présence en ligne existe, le besoin porte sur le parcours de réservation et sur des liens défectueux, pas sur la création."},
        ],
    },
    # ------------------------------------------------------------------ 05
    {
        "company": "Kap'oupa Kap", "domain": "kapoupakap.fr",
        "website": "https://www.kapoupakap.fr/",
        "sector": "Parc de loisirs et d'aventure en plein air",
        "city": "Eus", "department": "66",
        "address": "12 route de Prades, 66500 Eus",
        "email": "", "phone": "06 88 48 06 45",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux intégrer la réservation du Deval'Mountain à la billetterie existante, pour qu'elle ne dépende plus du seul appel téléphonique",
        "observation": "le Deval'Mountain est annoncé en réservation uniquement par téléphone alors que les autres activités ont un bouton réserver en ligne",
        "demo_detail": "un créneau Deval'Mountain réservé dans la même billetterie que l'accrobranche, avec le nombre de participants",
        "custom_subject": "Kap'oupa Kap : le Deval'Mountain réservé par téléphone",
        "custom_hook": "Le Deval'Mountain est en « réservation uniquement par téléphone » alors que les autres activités ont un bouton Réserver.",
        "notes": "Aucune adresse e-mail publiée sur la page contact lue : formulaire et téléphone uniquement.",
        "evidence": [
            ev("parcours_incomplet", "https://www.kapoupakap.fr/activites.html",
               "Réservation uniquement par téléphone.",
               "La section Deval'Mountain de la page activités précise « Réservation uniquement par téléphone » et n'affiche aucun bouton RÉSERVER, alors que Ventriglisse, Accrobranche, Mini-Golf et Base de loisirs en ont un qui pointe vers /reserver.html. Le parcours de réservation est donc incomplet pour une activité disponible toute l'année."),
            ev("website_gap", "https://www.kapoupakap.fr/contact.html",
               "Merci de remplir le formulaire ci-dessous afin que nous puissionstraiter votre demande",
               "La page contact comporte une faute d'agglutination dans sa phrase d'introduction (« nous puissionstraiter »). Le formulaire et la newsletter imposent tous deux la recopie d'un code captcha. Aucune adresse e-mail directe n'est publiée."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.kapoupakap.fr/",
             "quote": "UNIQUEMENT SUR RÉSERVATION, par téléphone ou via la billetterie en ligne.",
             "detail": "Une billetterie en ligne existe et fonctionne pour la majorité des activités : ce contre-signal est modéré, le besoin porte sur l'activité restante et non sur la création d'un système de réservation."},
        ],
    },
    # ------------------------------------------------------------------ 06
    {
        "company": "MFMG", "domain": "mfmg.eu",
        "website": "https://www.mfmg.eu/",
        "sector": "Traitement de surface, mécano-soudure et usinage",
        "city": "Vrigne-aux-Bois", "department": "08",
        "address": "64 rue Pasteur, 08330 Vrigne-aux-Bois",
        "email": "contact@mfmg.fr", "phone": "03 24 52 14 05",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux corriger le bandeau de cookies resté en anglais et l'adresse postale erronée de la page contact",
        "observation": "le panneau de gestion des cookies de votre site est entièrement en anglais et la page contact indique une adresse postale « 08 330 Vignes aux Bois »",
        "demo_detail": "un bandeau de consentement en français et une adresse postale cohérente avec l'établissement",
        "custom_subject": "MFMG : bandeau cookies en anglais et adresse de la page contact",
        "custom_hook": "Le panneau de cookies de mfmg.eu est en anglais et la page contact affiche « 08 330 Vignes aux Bois ».",
        "notes": "Le site est mfmg.eu mais l'adresse publiée est contact@mfmg.fr : les deux domaines sont publiés par l'entreprise, aucune adresse n'a été déduite.",
        "evidence": [
            ev("website_gap", "https://www.mfmg.eu/contact/",
               "Adresse : 64 rue Pasteur 08 330 Vignes aux Bois FRANCE",
               "Le bloc « NOS COORDONNÉES » de la page contact affiche un code postal mal formé (« 08 330 ») et un nom de commune erroné (« Vignes aux Bois »). La carte intégrée de la même page indique pourtant « 64 Rue Pasteur, 08330 Vrigne aux Bois ». L'incohérence est visible sur la page qui sert de référence pour un devis ou une livraison."),
            ev("website_gap", "https://www.mfmg.eu/zingage/",
               "Cookies management panel",
               "Le panneau de gestion du consentement est intégralement en anglais sur un site rédigé en français et destiné à des donneurs d'ordre français : « Cookies management panel », « Allow all cookies  Deny all cookies », « Privacy policy », « This website does not use any cookie requiring your consent ». Constat identique sur /contact/ et /recrutement/."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.mfmg.eu/contact/",
             "quote": "Comment nous avez-vous connus ?",
             "detail": "Formulaire de demande de devis structuré avec dépôt de fichier et suivi de la source commerciale, plus une page recrutement avec dépôt de CV : un formulaire de demande existe et le site est structuré. Le besoin est cosmétique et ne porte pas sur le parcours de devis."},
        ],
    },
    # ------------------------------------------------------------------ 07
    {
        "company": "Tortora", "domain": "tortora.fr",
        "website": "https://tortora.fr/",
        "sector": "Vente, installation et maintenance d'équipements de boulangerie-pâtisserie",
        "city": "Bouilly", "department": "10",
        "address": "20 rue de la Paix, 10320 Bouilly",
        "email": "", "phone": "03 25 40 30 45",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux remplacer la carte intégrée qui affiche une interface d'édition par un plan stable, et remettre les informations de direction à jour",
        "observation": "la carte intégrée à votre site affiche un message d'édition « Ceci est le lien d'édition secret, gardez-le en lieu sûr » au lieu d'un plan",
        "demo_detail": "un plan d'accès stable sur la page contact, sans message technique apparent",
        "custom_subject": "Tortora : la carte du site affiche un message d'édition",
        "custom_hook": "La carte intégrée à vos pages affiche « Ceci est le lien d'édition secret » au lieu d'un plan.",
        "notes": "Une adresse fred.tortora@tortora.fr est publiée mais la page d'accueil indique une transmission en 2021 à Frank Douet et Franck Pavie : le destinataire réel est incertain, aucun brouillon n'est préparé. Adresse non importée comme canal exploitable.",
        "evidence": [
            ev("website_gap", "https://tortora.fr/contacter-lentreprise-tortora-dans-laube-pres-de-troyes/",
               "Ceci est le lien d'édition secret, gardez-le en lieu sûr :",
               "Le bloc carte de la page contact, comme celui de la page d'accueil, affiche l'interface d'édition de uMap au lieu d'un plan : « Oups, c'est involontaire, je voudrais créer un compte ou me connecter », « Oui, je veux continuer à éditer sans être connecté », « Ceci est le lien d'édition secret ». Le visiteur ne voit pas de carte utilisable."),
            ev("website_gap", "https://tortora.fr/",
               "Créé en 1976, la société Tortora a été transmise en 2021 à deux employés de longue date, Frank Douet et Franck Pavie.",
               "Incohérences éditoriales entre deux pages du même site : l'accueil annonce une création en 1976 et une transmission en 2021 à Frank Douet et Franck Pavie, tandis que la page contact titre « Installé à Bouilly, près de Troyes, dans l’Aube depuis 1983 » et invite à « Contacter directement le dirigeant de l'entreprise, Frédéric Tortora ». Les informations de dirigeant et de date ne sont pas alignées."),
        ],
        "contre_signaux": [
            {"source_url": "https://tortora.fr/",
             "quote": "Traçabilité de nos interventions, respect de la charte Qualité ACB",
             "detail": "L'entreprise revendique une traçabilité de ses interventions et une charte qualité : un suivi d'intervention existe. Le besoin porte sur le site, pas sur un processus à créer."},
        ],
    },
    # ------------------------------------------------------------------ 08
    {
        "company": "Ajzenstein Louis et Associés", "domain": "ajzenstein-expert-comptable.com",
        "website": "https://www.ajzenstein-expert-comptable.com/",
        "sector": "Expertise comptable et conseil",
        "city": "Sedan", "department": "08",
        "address": "Sedan (08200), Ardennes",
        "email": "", "phone": "03 24 29 13 11",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux corriger le lien de source cassé et alléger le titre de page pour qu'il décrive le cabinet plutôt qu'une liste de mots-clés",
        "observation": "le lien « www.experts-comptables.fr » cité comme source renvoie vers une adresse inexistante de votre propre domaine",
        "demo_detail": "un lien de source qui ouvre réellement le site de l'ordre, et un titre de page lisible",
        "custom_subject": "Ajzenstein : lien de source cassé et titre de page",
        "custom_hook": "Le lien « www.experts-comptables.fr » de votre page pointe vers votre propre domaine et non vers l'ordre.",
        "notes": "Aucune adresse e-mail publiée : la page renvoie à un formulaire de contact. Adresse postale complète non vérifiée sur les pages lues.",
        "evidence": [
            ev("website_gap", "https://www.ajzenstein-expert-comptable.com/expertise-comptable-08",
               "Source : [www.experts-comptables.fr](https://www.ajzenstein-expert-comptable.com/www.experts-comptables.fr)",
               "Le lien présenté comme la source de la citation déontologique est construit en URL relative : il pointe vers https://www.ajzenstein-expert-comptable.com/www.experts-comptables.fr au lieu du site de l'ordre professionnel. Le lien est donc cassé sur la page qui cite l'article 158 du code de déontologie."),
            ev("site_obsolete", "https://www.ajzenstein-expert-comptable.com/expertise-comptable-08",
               "Conseil fiscalité Sedan. Conseil juridique Ardennes. Expert comptable 08 : Ajzenstein Louis",
               "Le titre de la page est une juxtaposition de mots-clés géolocalisés plutôt qu'un intitulé de cabinet. Le panneau de gestion des cookies tarteaucitron est rendu deux fois dans la page, et l'URL d'ancrage de retour en haut pointe vers « expertise-comptable-08# » sans extension, incohérente avec les autres liens en .php."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.ajzenstein-expert-comptable.com/expertise-comptable-08",
             "quote": "Ou envoyez-nous un mail via le formulaire contact que vous trouverez ici",
             "detail": "Un formulaire de contact fonctionne et le consentement est configuré : le besoin porte sur des défauts ponctuels, pas sur le canal de contact."},
        ],
    },
    # ------------------------------------------------------------------ 09
    {
        "company": "Blanchefleur", "domain": "blanchefleur-metallerie.fr",
        "website": "https://www.blanchefleur-metallerie.fr/",
        "sector": "Métallerie, chaudronnerie et agencement sur mesure",
        "city": "Sommedieue", "department": "55",
        "address": "Rue de l'usine, 55320 Sommedieue",
        "email": "", "phone": "06 69 01 83 28",
        "contact_name": "Julien Blanchefleur", "contact_role": "fondateur",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux faire pointer le lien « mail » vers une vraie adresse ou un formulaire, puisque la page contact n'en affiche aucune",
        "observation": "vos pages invitent à prendre contact « par téléphone ou par mail » mais le lien mail renvoie à la page contact, qui n'affiche aucune adresse",
        "demo_detail": "un lien mail qui ouvre réellement une adresse, ou une formulation qui annonce le formulaire",
        "custom_subject": "Blanchefleur : le lien « mail » ne mène à aucune adresse",
        "custom_hook": "Vos pages proposent un contact « par mail » mais le lien renvoie à la page contact, sans adresse affichée.",
        "notes": "Aucune adresse e-mail publiée sur les deux pages lues, malgré deux invitations à écrire par mail.",
        "evidence": [
            ev("parcours_incomplet", "https://www.blanchefleur-metallerie.fr/contact.php",
               "Prenez contact par téléphone, par e-mail ou via le formulaire ci-dessous.",
               "La page contact annonce trois canaux (téléphone, e-mail, formulaire) mais n'affiche que le téléphone et le formulaire. Le lien « mail » présent en bas de page pointe vers https://www.blanchefleur-metallerie.fr/contact.php, c'est-à-dire la page courante, et non vers une adresse. Le canal e-mail annoncé n'existe pas."),
            ev("website_gap", "https://www.blanchefleur-metallerie.fr/",
               "This site uses cookies and gives you control over what you want to activate",
               "Le panneau de consentement tarteaucitron est en anglais (« Cookies management panel », « Allow all cookies  Deny all cookies », « Mandatory cookies ») sur un site entièrement rédigé en français pour une clientèle de Lorraine. Le lien téléphone de l'accueil est écrit « tel:06 69 01 83 28 », avec des espaces dans l'URI."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.blanchefleur-metallerie.fr/contact.php",
             "quote": "vous disposez d'un droit d'accès, de rectification, de modification et de suppression",
             "detail": "Un formulaire de contact fonctionne avec lien de suppression des données : le besoin porte sur le canal e-mail annoncé mais absent, pas sur la création d'un formulaire."},
        ],
    },
    # ------------------------------------------------------------------ 10
    {
        "company": "TAM NET 87", "domain": "tam-net-87.fr",
        "website": "https://www.tam-net-87.fr/",
        "sector": "Nettoyage professionnel et remise en état",
        "city": "Limoges", "department": "87",
        "address": "33 rue de Bretagne, 87100 Limoges",
        "email": "", "phone": "06 10 17 05 57",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux corriger les liens et les textes cassés de l'accueil pour que le parcours vers vos pages professionnels et particuliers fonctionne",
        "observation": "sur votre accueil le texte « entreprise de nettoyage d e confiance » est coupé par des liens imbriqués et le visuel « Particuliers » renvoie à l'accueil",
        "demo_detail": "un texte d'accueil intact et un visuel Particuliers qui ouvre la bonne page",
        "custom_subject": "TAM NET 87 : liens et textes cassés sur l'accueil",
        "custom_hook": "Votre accueil affiche « entreprise de nettoyage d e confiance » et le visuel Particuliers renvoie à l'accueil.",
        "notes": "Aucune adresse e-mail publiée sur les deux pages lues : formulaire et téléphone uniquement.",
        "evidence": [
            ev("website_gap", "https://www.tam-net-87.fr/",
               "est une [Entreprise de nettoyage à Limoges ][**entreprise de nettoyage**][d] e confiance",
               "Le paragraphe de présentation est fragmenté par des liens imbriqués qui coupent les mots : « est une Entreprise de nettoyage à Limoges entreprise de nettoyage d e confiance ». Plus bas, la section professionnels comporte la coquille « Intervention auprès des professionneles »."),
            ev("parcours_incomplet", "https://www.tam-net-87.fr/",
               "[![ Entreprise de nettoyage Haute-Vienne](https://www.tam-net-87.fr/oktThemes/ra165-s/images/accueil/encart2.jpg)](https://www.tam-net-87.fr/)",
               "Dans le bloc « Société de nettoyage », le visuel associé aux particuliers pointe vers la racine du site alors que le lien texte voisin pointe correctement vers /particuliers. Le visiteur qui clique sur l'image revient à l'accueil."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.tam-net-87.fr/contact",
             "quote": "En cochant cette case, j’accepte que les données saisies dans le formulaire ci-dessus soient utilisées",
             "detail": "Un formulaire de contact fonctionne avec consentement et politique de confidentialité : le besoin porte sur des défauts de liens et de texte, pas sur le canal de contact."},
        ],
    },
    # ------------------------------------------------------------------ 11
    {
        "company": "Les Ateliers Genetier", "domain": "ebeniste-genetier.com",
        "website": "https://www.ebeniste-genetier.com/",
        "sector": "Ébénisterie, fabrication de mobilier et agencement sur mesure",
        "city": "Charolles", "department": "71",
        "address": "Pôle d'activité du Charolais, 3 rue Jean Ducerf, 71120 Charolles",
        "email": "", "phone": "09 74 56 58 70",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux traduire le bandeau de consentement resté en anglais et aligner l'ancienneté annoncée sur la date de création",
        "observation": "le bandeau de consentement de votre site est en anglais et l'accueil annonce « 45 ans » tout en indiquant une création en 1976",
        "demo_detail": "un bandeau de consentement en français et une ancienneté cohérente avec 1976",
        "custom_subject": "Ateliers Genetier : bandeau cookies en anglais et ancienneté",
        "custom_hook": "Votre bandeau de consentement est en anglais et l'accueil annonce « 45 ans » pour une création en 1976.",
        "notes": "Aucune adresse e-mail en clair sur les pages lues : le bloc coordonnées propose un lien « E-mail » dont la cible n'a pas pu être relevée. Adresse non importée.",
        "evidence": [
            ev("website_gap", "https://www.ebeniste-genetier.com/meuble.php",
               "Your privacy is our priority",
               "Le bandeau de consentement aux cookies est intégralement en anglais sur un site français destiné à une clientèle de Saône-et-Loire : « Your privacy is our priority », « I Agree », « Reject All », « Ad personalization », « Save and Exit ». Constat identique sur la page /contactez-nous.php."),
            ev("website_gap", "https://www.ebeniste-genetier.com/meuble.php",
               "45 ans dans la fabrication de meubles sur mesure",
               "Le titre de section annonce « 45 ans dans la fabrication de meubles sur mesure » alors que le paragraphe qui suit indique « Depuis 1976, nous sommes spécialisés dans la conception et la fabrication de meubles sur mesure ». En 2026, l'écart entre les deux affirmations est de cinq ans."),
        ],
        "contre_signaux": [
            {"source_url": "https://www.ebeniste-genetier.com/contactez-nous.php",
             "quote": "Ce site est protégé par reCAPTCHA",
             "detail": "Formulaire de devis qualifié (type de demande, précisions) protégé par reCAPTCHA, et réglages d'accessibilité proposés : un formulaire de demande existe et le site est structuré. Le besoin est cosmétique."},
        ],
    },
    # ------------------------------------------------------------------ 12
    {
        "company": "BETEP", "domain": "betep.fr",
        "website": "http://www.betep.fr/",
        "sector": "Bureau d'études techniques, calcul de structure et plans d'exécution",
        "city": "Tarbes", "department": "65",
        "address": "13 rue Gaston Manent, 65000 Tarbes",
        "email": "betep@betep.fr", "phone": "05 62 93 14 70",
        "contact_name": "", "contact_role": "",
        "needs": ["refonte"], "need": "refonte",
        "process_hint": "",
        "recommended_service": "Je peux remettre le site sur une structure moderne en HTTPS, avec une page de contact qui présente vos missions et vos références",
        "observation": "votre site est servi en http et sa mise en page repose sur des tableaux imbriqués",
        "demo_detail": "une page d'accueil en HTTPS présentant les missions et un moyen simple de transmettre un plan",
        "custom_subject": "BETEP : site en http et mise en page par tableaux",
        "custom_hook": "Le site betep.fr est servi en http et sa mise en page repose sur des tableaux imbriqués.",
        "notes": "Une seule page a pu être lue : la confiance sur l'axe refonte reste limitée, aucun brouillon n'est préparé.",
        "evidence": [
            ev("site_obsolete", "http://www.betep.fr/",
               "http://www.betep.fr/images/local.jpg",
               "Le site est servi en http sans redirection HTTPS observable, et l'ensemble de la mise en page est construit en tableaux HTML imbriqués servant à positionner le texte, les coordonnées et les images. Les rubriques MISSIONS, DOMAINE D'INTERVENTION et LOGICIELS ET MATERIEL sont de simples titres dans une colonne de tableau. Aucun formulaire de contact n'est proposé, seulement une adresse e-mail et un téléphone."),
        ],
        "contre_signaux": [
            {"source_url": "http://www.betep.fr/",
             "quote": "Tous ces logiciels étant compatibles au BIM",
             "detail": "Le bureau d'études est outillé (Graitec, Arche, Advance, Allplan, compatibles BIM) : la maturité technique existe. Ce contre-signal porte sur l'outillage métier, pas sur le site ; le besoin porte sur la présence en ligne."},
        ],
    },
]


def build(fiche: dict) -> dict:
    raw = list(fiche["evidence"])
    for cs in fiche.get("contre_signaux", []):
        raw.append(ev("maturite_existante", cs["source_url"], cs["quote"],
                      cs["detail"], level="observe"))
    evs = [Evidence(**e) for e in raw]
    for e in evs:
        errors = e.validate()
        assert not errors, (fiche["company"], e.kind, errors)
    p = Prospect(
        company=fiche["company"], domain=fiche["domain"],
        contact_email=fiche["email"], sector=fiche["sector"],
        needs=fiche["needs"], evidences=evs, website=fiche["website"],
        process_hint=fiche["process_hint"], demo_detail=fiche["demo_detail"],
        custom_hook=fiche["custom_hook"], custom_subject=fiche["custom_subject"],
        city=fiche["city"], department=fiche["department"], phone=fiche["phone"],
        contact_name=fiche["contact_name"], contact_role=fiche["contact_role"],
        recommended_service=fiche["recommended_service"],
        observation=fiche.get("observation", ""),
        source="site_officiel", lot=LOT, discovered_at=D,
        email_verification="verified" if fiche["email"] else "none",
        email_dns_status=DNS.get(_norm(fiche["company"]), "") if fiche["email"] else "",
        notes=fiche.get("notes", ""),
    )
    scores = score_prospect(p, today=TODAY)
    assessment = assess(p, scores, today=TODAY)
    return {"fiche": fiche, "prospect": p, "scores": scores, "assessment": assessment}


if __name__ == "__main__":
    rows = [build(f) for f in FICHES]
    print(f"{'Entreprise':32} {'créa':>5} {'refon':>6} {'IA':>4} {'prio':>5} {'palier':14} {'cs':>4} {'conf':>8} {'email'}")
    for r in rows:
        f, s, a = r["fiche"], r["scores"], r["assessment"]
        print(f"{f['company'][:32]:32} {s['site_web']['score']:5} {s['refonte']['score']:6} "
              f"{s['ia_automatisation']['score']:4} {a.value:5} {a.tier:14} "
              f"{a.counter_signal_penalty:4} {s['refonte']['confidence'][:8]:>8} {'oui' if f['email'] else 'NON'}")
    print()
    print("Moteur :", ENGINE_VERSION, "| Fiches :", len(rows))
    from collections import Counter
    print("Paliers :", dict(Counter(r["assessment"].tier for r in rows)))
    print("Avec e-mail :", sum(1 for r in rows if r["fiche"]["email"]))
