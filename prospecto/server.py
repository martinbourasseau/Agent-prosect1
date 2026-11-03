"""Espace Prospecto — dashboard + API (stdlib, aucun framework).

Rattache l'outil de prospection au site https://prospecto.website :
- interface sombre cohérente avec l'identité visuelle du site (Archivo, abyss/glacier/tide) ;
- API JSON reliée au CRM, à la file de validation et aux campagnes ;
- connexion sécurisée par mot de passe + cookie de session signé (HMAC) ;
- AUCUN envoi d'email depuis le dashboard : approuver ne fait que changer le statut.

Lancement :  python3 -m prospecto.server
Config (env) : PROSPECTO_PORT (défaut 8787), PROSPECTO_DASH_PASSWORD (sinon data/.dash_password).

Sécurité : lier derrière HTTPS en production (le preview Arena est déjà HTTPS).
Le mot de passe et le secret de session sont stockés dans data/ (gitignorés).
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from . import config
from .crm import CRM
from .queue import ValidationQueue, PENDING, APPROVED, REJECTED

HERE = Path(__file__).resolve().parent
DASHBOARD_HTML = HERE / "dashboard.html"
PASSWORD_FILE = config.DATA_DIR / ".dash_password"
SECRET_FILE = config.DATA_DIR / ".dash_secret"
SESSION_COOKIE = "prospecto_session"
SESSION_TTL = 60 * 60 * 12  # 12 h


# ---------------------------------------------------------------------------
# Secrets / sessions
# ---------------------------------------------------------------------------
def _read_or_create(path: Path, nbytes: int = 24) -> str:
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = secrets.token_urlsafe(nbytes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return value


def get_password() -> str:
    env = os.environ.get("PROSPECTO_DASH_PASSWORD", "").strip()
    if env:
        return env
    return _read_or_create(PASSWORD_FILE)


def get_secret() -> str:
    return _read_or_create(SECRET_FILE, nbytes=32)


def make_session_token() -> str:
    expiry = str(int(time.time()) + SESSION_TTL)
    sig = hmac.new(get_secret().encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return f"{expiry}.{sig}"


def valid_session_token(token: str) -> bool:
    if not token or "." not in token:
        return False
    expiry, sig = token.rsplit(".", 1)
    expected = hmac.new(get_secret().encode(), expiry.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        return int(expiry) > int(time.time())
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Données (lecture CRM / file / campagnes)
# ---------------------------------------------------------------------------
def api_stats() -> dict:
    crm = CRM()
    queue = ValidationQueue()
    return {"crm": crm.stats(), "queue": queue.counts()}


def api_prospects() -> list:
    return CRM().records


def api_queue() -> list:
    return [i.to_dict() for i in ValidationQueue().list()]


def api_campaigns() -> list:
    out = []
    if config.CAMPAIGNS_DIR.exists():
        for p in sorted(config.CAMPAIGNS_DIR.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            out.append({
                "id": data.get("campaign", p.stem),
                "file": p.name,
                "generated_count": data.get("generated_count", len(data.get("emails", []))),
                "strategy": data.get("strategy", ""),
            })
    return out


# ---------------------------------------------------------------------------
# Handler HTTP
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "Prospecto/3.0"

    # -- utilitaires --------------------------------------------------------
    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    def _send(self, code: int, body: bytes, ctype: str, extra_headers: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _html(self, code: int, markup: str, extra_headers: dict | None = None) -> None:
        self._send(code, markup.encode("utf-8"), "text/html; charset=utf-8", extra_headers)

    def _redirect(self, location: str, extra_headers: dict | None = None) -> None:
        headers = {"Location": location}
        headers.update(extra_headers or {})
        self._send(302, b"", "text/plain; charset=utf-8", headers)

    def _session_ok(self) -> bool:
        raw = self.headers.get("Cookie", "")
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except Exception:
            return False
        morsel = cookie.get(SESSION_COOKIE)
        return bool(morsel and valid_session_token(morsel.value))

    def _require_auth(self) -> bool:
        if self._session_ok():
            return True
        self._json(401, {"error": "authentification requise"})
        return False

    def log_message(self, fmt, *args):  # log discret
        pass

    # -- GET ----------------------------------------------------------------
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/healthz":
            self._send(200, b"ok", "text/plain; charset=utf-8")
            return

        if path == "/login":
            self._html(200, login_page())
            return

        if path == "/logout":
            self._redirect("/login", {"Set-Cookie": f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})
            return

        if path == "/":
            if not self._session_ok():
                self._redirect("/login")
                return
            self._html(200, DASHBOARD_HTML.read_text(encoding="utf-8"))
            return

        if path.startswith("/api/"):
            if not self._require_auth():
                return
            if path == "/api/stats":
                self._json(200, api_stats())
            elif path == "/api/prospects":
                self._json(200, api_prospects())
            elif path == "/api/queue":
                self._json(200, api_queue())
            elif path == "/api/campaigns":
                self._json(200, api_campaigns())
            else:
                self._json(404, {"error": "route inconnue"})
            return

        self._json(404, {"error": "introuvable"})

    # -- POST ---------------------------------------------------------------
    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""

        if path == "/login":
            form = parse_qs(raw.decode("utf-8", errors="replace"))
            password = (form.get("password", [""])[0]).strip()
            if password and hmac.compare_digest(password, get_password()):
                token = make_session_token()
                self._redirect("/", {"Set-Cookie": f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL}"})
            else:
                self._html(401, login_page(error="Mot de passe incorrect."))
            return

        if path.startswith("/api/queue/"):
            if not self._require_auth():
                return
            parts = path.strip("/").split("/")  # api / queue / <id> / <action>
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "queue":
                item_id, action = parts[2], parts[3]
                queue = ValidationQueue()
                try:
                    if action == "approve":
                        item = queue.approve(item_id)
                    elif action == "reject":
                        body = {}
                        try:
                            body = json.loads(raw.decode("utf-8") or "{}")
                        except json.JSONDecodeError:
                            pass
                        item = queue.reject(item_id, body.get("reason", ""))
                    else:
                        self._json(404, {"error": "action inconnue"})
                        return
                    queue.save()
                    self._json(200, {"ok": True, "item": item.to_dict()})
                except KeyError:
                    self._json(404, {"error": "élément introuvable"})
                except ValueError as exc:
                    self._json(409, {"error": str(exc)})
                return

        self._json(404, {"error": "introuvable"})


def login_page(error: str = "") -> str:
    err = f'<p class="err">{html.escape(error)}</p>' if error else ""
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connexion — Espace Prospecto</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--abyss:#03050a;--night:#08101f;--anthracite:#161b25;--glacier:#9cbcff;--tide:#79d2d6;
--text:#e9edf4;--dim:#9aa6b8;--line:rgba(255,255,255,.09)}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;display:grid;place-items:center;
background:radial-gradient(1200px 600px at 50% -10%,#0b1626 0%,var(--abyss) 60%);
color:var(--text);font-family:Archivo,system-ui,sans-serif}}
.card{{width:min(400px,92vw);background:linear-gradient(180deg,var(--night),#060b16);
border:1px solid var(--line);border-radius:20px;padding:36px 32px;box-shadow:0 30px 80px rgba(0,0,0,.5)}}
.mark{{font-weight:700;font-size:22px;letter-spacing:.02em}}
.mark span{{color:var(--glacier)}}
h1{{font-size:17px;font-weight:600;margin:20px 0 6px}}
p.sub{{color:var(--dim);font-size:13.5px;margin:0 0 22px}}
label{{display:block;font-size:12.5px;color:var(--dim);margin-bottom:8px}}
input{{width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--line);
background:var(--anthracite);color:var(--text);font-size:15px;outline:none}}
input:focus{{border-color:var(--glacier)}}
button{{margin-top:18px;width:100%;padding:12px;border:0;border-radius:12px;cursor:pointer;
background:linear-gradient(90deg,var(--glacier),var(--tide));color:#04101c;font-weight:600;font-size:15px}}
.err{{color:#ff9b9b;font-size:13px;margin:14px 0 0}}
.foot{{margin-top:22px;font-size:12px;color:var(--dim);text-align:center}}
.foot a{{color:var(--glacier);text-decoration:none}}
</style></head><body>
<form class="card" method="post" action="/login">
<div class="mark">Prospecto<span>.</span></div>
<h1>Espace Prospecto</h1>
<p class="sub">CRM, file de validation et campagnes. Accès protégé.</p>
<label for="password">Mot de passe</label>
<input id="password" name="password" type="password" autocomplete="current-password" autofocus required>
<button type="submit">Se connecter</button>
{err}
<div class="foot"><a href="https://prospecto.website">← Retour au site</a></div>
</form></body></html>"""


def main() -> None:
    port = int(os.environ.get("PROSPECTO_PORT", "8787"))
    # Initialise les secrets au démarrage (gitignorés).
    get_password()
    get_secret()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Espace Prospecto démarré sur http://0.0.0.0:{port}")
    print(f"Mot de passe : fichier {PASSWORD_FILE} (ou env PROSPECTO_DASH_PASSWORD)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
