"""Délivrabilité v4 — SPF / DKIM / DMARC réels + analyse du domaine expéditeur.

Vérifie les enregistrements DNS du domaine expéditeur, identifie les fournisseurs
gratuits (Gmail, Outlook…) inadaptés à la prospection de masse, et rappelle les
limites des fournisseurs. Ne prétend jamais qu'un email est délivré : il s'agit
de contrôles de configuration, pas de garanties de boîte de réception.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

try:
    import dns.resolver  # type: ignore
    _HAS_DNS = True
except ImportError:  # pragma: no cover
    _HAS_DNS = False

FREE_PROVIDERS = {
    "gmail.com": "Gmail (gratuit)", "googlemail.com": "Gmail (gratuit)",
    "outlook.com": "Outlook.com", "hotmail.com": "Hotmail", "live.com": "Live",
    "yahoo.com": "Yahoo Mail", "yahoo.fr": "Yahoo Mail", "laposte.net": "La Poste",
    "orange.fr": "Orange", "wanadoo.fr": "Orange", "free.fr": "Free", "sfr.fr": "SFR",
}

# Limites indicatives (à confirmer avec le fournisseur ; ne pas viser ces maxima).
PROVIDER_LIMITS = {
    "gmail.com": {"daily": 500, "note": "Compte gratuit : ~500 envois/jour max, mais la prospection commerciale en masse déclenche les filtres anti-spam bien avant. Déconseillé."},
    "workspace": {"daily": 2000, "note": "Google Workspace : ~2000/jour, mais même risque de réputation pour du cold outreach."},
}

DEFAULT_DKIM_SELECTORS = ["google", "default", "selector1", "selector2", "k1", "s1", "s2", "dkim", "mail"]


def _txt(name: str) -> list[str]:
    if not _HAS_DNS:
        return []
    try:
        r = dns.resolver.Resolver()
        r.timeout = 4
        r.lifetime = 6
        return [b"".join(t.strings).decode("utf-8", "replace") for t in r.resolve(name, "TXT")]
    except Exception:
        return []


@dataclass
class DeliverabilityReport:
    domain: str
    is_free_provider: bool = False
    provider: str = ""
    spf_present: bool = False
    spf_record: str = ""
    dkim_present: bool = False
    dkim_selector: str = ""
    dmarc_present: bool = False
    dmarc_record: str = ""
    dmarc_policy: str = ""
    dns_checked: bool = False
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    ok_for_bulk: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_domain(domain: str, dkim_selectors: list[str] | None = None) -> DeliverabilityReport:
    domain = domain.lower().strip()
    rep = DeliverabilityReport(domain=domain)
    rep.is_free_provider = domain in FREE_PROVIDERS
    rep.provider = FREE_PROVIDERS.get(domain, "domaine personnalisé")

    if _HAS_DNS:
        rep.dns_checked = True
        # SPF
        for rec in _txt(domain):
            if rec.lower().startswith("v=spf1"):
                rep.spf_present = True
                rep.spf_record = rec
                break
        # DMARC
        for rec in _txt(f"_dmarc.{domain}"):
            if rec.lower().startswith("v=dmarc1"):
                rep.dmarc_present = True
                rep.dmarc_record = rec
                for part in rec.split(";"):
                    part = part.strip()
                    if part.startswith("p="):
                        rep.dmarc_policy = part[2:]
                break
        # DKIM (sélecteurs courants ; un domaine pro a son propre sélecteur)
        for sel in (dkim_selectors or DEFAULT_DKIM_SELECTORS):
            recs = _txt(f"{sel}._domainkey.{domain}")
            if any("v=dkim1" in r.lower() and "p=" in r.lower() for r in recs):
                # Une clé avec p= vide est révoquée.
                valid = [r for r in recs if "p=" in r.lower() and not r.lower().split("p=")[-1].strip().rstrip(";").strip() == ""]
                if valid:
                    rep.dkim_present = True
                    rep.dkim_selector = sel
                    break

    # Analyse / recommandations
    if rep.is_free_provider:
        rep.warnings.append(
            f"Le domaine expéditeur '{domain}' est un fournisseur gratuit ({rep.provider}). "
            "La prospection commerciale en masse depuis un compte gratuit est contraire aux CGU "
            "et dégrade fortement la délivrabilité (voire suspend le compte)."
        )
        rep.recommendations.append(
            "Utiliser un domaine professionnel dédié (ex. contact@prospecto.website ou un domaine "
            "d'envoi dédié) avec SPF, DKIM et DMARC configurés, et un prestataire d'envoi adapté "
            "(Google Workspace sur domaine propre, ou ESP : Brevo, Sendgrid, Mailgun…)."
        )
        rep.ok_for_bulk = False
    else:
        if not rep.spf_present:
            rep.warnings.append("SPF absent ou introuvable : à publier avant tout envoi.")
        if not rep.dkim_present:
            rep.warnings.append("DKIM non détecté (sélecteurs courants) : configurer la signature DKIM.")
        if not rep.dmarc_present:
            rep.warnings.append("DMARC absent : publier une politique DMARC (au moins p=none pour démarrer).")
        elif rep.dmarc_policy in ("", "none"):
            rep.recommendations.append("DMARC en p=none : passer progressivement à quarantine puis reject.")
        rep.ok_for_bulk = rep.spf_present and rep.dkim_present and rep.dmarc_present
        if rep.ok_for_bulk:
            rep.recommendations.append(
                "Chauffe progressive du domaine (ramp-up), surveillance des rebonds/plaintes, "
                "et démarrage à faible volume."
            )
    if not _HAS_DNS:
        rep.warnings.append("dnspython indisponible : vérifications DNS non effectuées (pip install dnspython).")
    return rep


def analyze_sender(email: str, dkim_selectors: list[str] | None = None) -> DeliverabilityReport:
    domain = email.split("@", 1)[1].lower().strip() if "@" in email else ""
    return check_domain(domain, dkim_selectors)


def provider_daily_limit(domain: str) -> dict[str, Any]:
    if domain in ("gmail.com", "googlemail.com"):
        return PROVIDER_LIMITS["gmail.com"]
    return {"daily": None, "note": "Domaine personnalisé : limites selon l'hébergeur/ESP. Démarrer bas et monter progressivement."}
