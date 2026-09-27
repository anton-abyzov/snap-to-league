"""EasyChamp sign-in for publishing.

The page signs the organizer in with EasyChamp (Keycloak, authorization code + PKCE) and sends the
access token with the publish call. The server checks the token with EasyChamp (/user/me) before
trusting anything in it, then publishes with that same token, so the league is created in the
organizer's own EasyChamp account and they manage it there.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import time

import httpx

ISSUER = os.environ.get("SNAP_OIDC_ISSUER", "https://auth.easychamp.com/realms/easychamp")
CLIENT_ID = os.environ.get("SNAP_OIDC_CLIENT", "ec-console-ui")
API = os.environ.get("EC_API_URL", "https://easychamp.com/ec-standings-api")
UA = "Mozilla/5.0 (Macintosh) snap-to-league/0.2"  # Cloudflare refuses default HTTP client agents

_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def config() -> dict:
    return {"issuer": ISSUER, "clientId": CLIENT_ID}


def _claims(token: str) -> dict:
    try:
        part = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except (IndexError, ValueError):
        return {}


def bearer(header: str | None) -> str | None:
    if header and header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def user(token: str | None) -> dict | None:
    """The signed-in organizer for this token, or None when the token is missing, expired or forged.

    EasyChamp validates the signature and expiry and returns the platform user id; once it has answered,
    the token's own claims (name, email) can be read.
    """
    if not token:
        return None
    now = time.time()
    with _lock:
        hit = _cache.get(token)
        if hit and hit[0] > now:
            return hit[1]
    try:
        # EasyChamp itself checks the token and answers with the platform user id (legacyUserId or sub)
        r = httpx.get(f"{API}/user/me", headers={"Authorization": f"Bearer {token}", "User-Agent": UA}, timeout=15)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    uid, claims = (r.json() or {}).get("userId"), _claims(token)
    if not uid:
        return None
    who = {"id": str(uid), "name": claims.get("name") or claims.get("preferred_username") or claims.get("email") or "Organizer",
           "email": claims.get("email"), "plan": (r.json() or {}).get("plan")}
    with _lock:
        _cache[token] = (min(float(claims.get("exp") or now + 60), now + 300), who)
        if len(_cache) > 500:
            for k in [k for k, (exp, _) in _cache.items() if exp <= now]:
                _cache.pop(k, None)
    return who
