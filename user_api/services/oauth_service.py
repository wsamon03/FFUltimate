"""
OAuth 2.0 PKCE helpers for Google and Microsoft (Azure AD).

Flow:
  1. build_authorization_url() — generate code_verifier, code_challenge, and signed
     state (which encodes the verifier for the round-trip), return redirect URL.
  2. exchange_code() — verify state, extract verifier, POST to token endpoint,
     return normalized UserInfo dict.
"""

import base64
import hashlib
import json
import secrets
from urllib.parse import urlencode

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from user_api.config import settings

_signer = URLSafeTimedSerializer(settings.STATE_SECRET_KEY)

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, dict] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
    },
    "microsoft": {
        "auth_url": f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/authorize",
        "token_url": f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/oidc/userinfo",
        "client_id": settings.AZURE_CLIENT_ID,
        "client_secret": settings.AZURE_CLIENT_SECRET,
        "redirect_uri": settings.AZURE_REDIRECT_URI,
        "scope": "openid email profile",
    },
}


def _get_provider(provider: str) -> dict:
    cfg = _PROVIDERS.get(provider)
    if not cfg:
        raise ValueError(f"Unsupported provider: {provider}")
    return cfg


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def _generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_authorization_url(provider: str) -> tuple[str, str]:
    """Return (redirect_url, signed_state).

    The signed state encodes the code_verifier so no server-side session is
    needed; itsdangerous enforces a 10-minute TTL.
    """
    cfg = _get_provider(provider)
    verifier = _generate_code_verifier()
    challenge = _code_challenge(verifier)

    payload = {"provider": provider, "verifier": verifier}
    state = _signer.dumps(payload)

    params = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "scope": cfg["scope"],
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = cfg["auth_url"] + "?" + urlencode(params)
    return url, state


async def exchange_code(state: str, code: str) -> dict:
    """Verify state, exchange authorization code for tokens, return user info.

    Returns dict with keys: provider, sub, email, display_name, avatar_url.
    Raises ValueError on bad/expired state or failed token exchange.
    """
    try:
        payload = _signer.loads(state, max_age=settings.STATE_MAX_AGE_SECONDS)
    except SignatureExpired:
        raise ValueError("OAuth state expired — please try logging in again")
    except BadSignature:
        raise ValueError("Invalid OAuth state — possible CSRF attempt")

    provider: str = payload["provider"]
    verifier: str = payload["verifier"]
    cfg = _get_provider(provider)

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            cfg["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": cfg["redirect_uri"],
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code_verifier": verifier,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise ValueError(f"Token exchange failed: {token_resp.text}")
        tokens = token_resp.json()

        access_token = tokens.get("access_token", "")
        userinfo_resp = await client.get(
            cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise ValueError(f"Userinfo fetch failed: {userinfo_resp.text}")
        info = userinfo_resp.json()

    return {
        "provider": provider,
        "sub": info.get("sub") or info.get("id") or "",
        "email": info.get("email", ""),
        "display_name": info.get("name") or info.get("displayName") or "",
        "avatar_url": info.get("picture") or info.get("photo") or None,
    }
