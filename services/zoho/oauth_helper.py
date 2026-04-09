"""
Zoho OAuth 2.0 access token refresh (shared by Zoho CRM and Zoho Mail APIs).

Token requests use the Zoho accounts host for your data center (com, eu, in, au, etc.).
"""
from typing import Any, Dict, Optional

import requests

from services.zoho.oauth_env_sanitize import (
    clean_zoho_client_id,
    clean_zoho_secret_or_token,
)

# Some Zoho endpoints return HTML errors to default Python clients; use an explicit UA.
_ZOHO_OAUTH_UA = "SalesGPT/1.0 (Zoho OAuth)"
_ZOHO_FORM_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": _ZOHO_OAUTH_UA,
    "Accept": "application/json, */*",
}


def refresh_zoho_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    accounts_domain: str = "https://accounts.zoho.com",
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Exchange refresh token for a new access token (and optional new refresh token).

    Returns:
        Parsed JSON (includes access_token) or None on failure.
    """
    cid, cw = clean_zoho_client_id(client_id)
    if cw:
        print(f"Zoho OAuth: {cw}")
    sec, sw = clean_zoho_secret_or_token(client_secret)
    if sw:
        print(f"Zoho OAuth: {sw}")
    rtok, tw = clean_zoho_secret_or_token(refresh_token)
    if tw:
        print(f"Zoho OAuth: {tw}")

    url = f"{accounts_domain.rstrip('/')}/oauth/v2/token"
    try:
        response = requests.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": rtok,
                "client_id": cid,
                "client_secret": sec,
            },
            headers=_ZOHO_FORM_HEADERS,
            timeout=timeout,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.ok and isinstance(payload, dict) and payload.get("access_token"):
            return payload

        if isinstance(payload, dict) and payload.get("error"):
            print(
                f"Zoho OAuth error: {payload.get('error')} "
                f"{payload.get('error_description', '')!r}"
            )
            return None

        print(f"Zoho OAuth HTTP {response.status_code}: {response.text[:500]}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Zoho OAuth token refresh failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(f"Zoho OAuth error body: {e.response.text[:500]}")
            except Exception:
                pass
        return None
