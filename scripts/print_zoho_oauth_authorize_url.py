#!/usr/bin/env python3
"""
Print the Zoho browser URL to start OAuth (authorization code + offline refresh).

Prereqs in .env / .env.local:
  ZOHO_CLIENT_ID
  ZOHO_OAUTH_REDIRECT_URI   — must match EXACTLY what you registered in Zoho API Console
  ZOHO_ACCOUNTS_DOMAIN      — optional, default https://accounts.zoho.com

Optional:
  ZOHO_OAUTH_SCOPES — comma-separated; default includes Mail (+ CRM) for SalesGPT stack

Usage:
  python3 scripts/print_zoho_oauth_authorize_url.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.zoho.oauth_env_sanitize import clean_zoho_client_id


def load_env_file(path: Path, *, override: bool = False) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = val


def main() -> None:
    load_env_file(ROOT / ".env", override=False)
    load_env_file(ROOT / ".env.local", override=True)

    raw_cid = os.getenv("ZOHO_CLIENT_ID", "").strip()
    client_id, cid_warn = clean_zoho_client_id(raw_cid)
    if cid_warn:
        print(cid_warn, file=sys.stderr)
    redirect_uri = os.getenv("ZOHO_OAUTH_REDIRECT_URI", "").strip()
    accounts = (os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "https://accounts.zoho.com").rstrip("/")
    scopes = os.getenv(
        "ZOHO_OAUTH_SCOPES",
        "ZohoMail.messages.CREATE,ZohoMail.accounts.READ,ZohoCRM.modules.ALL",
    ).strip()

    if not client_id:
        print("Set ZOHO_CLIENT_ID in .env", file=sys.stderr)
        sys.exit(1)
    if not redirect_uri:
        print(
            "Set ZOHO_OAUTH_REDIRECT_URI in .env to the same redirect URL registered "
            "in API Console → Gemflush_SalesGPT → Client Details (e.g. https://127.0.0.1:8080/zoho/callback).",
            file=sys.stderr,
        )
        sys.exit(1)

    auth_url = f"{accounts}/oauth/v2/auth?{urlencode({
        'scope': scopes,
        'client_id': client_id,
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'redirect_uri': redirect_uri,
    })}"

    print("1) Confirm this redirect URI is registered in Zoho API Console (exact match, https):")
    print(f"   {redirect_uri}\n")
    print("2) Log into Zoho in the browser as the user who owns jay@gemflush.com (or your send mailbox).")
    print("3) Open this URL:\n")
    print(auth_url)
    print("\n4) After you approve, the browser redirects with ?code=... in the URL.")
    print("5) Run:")
    print("   python3 scripts/exchange_zoho_auth_code.py --code 'PASTE_CODE_HERE'")
    print("\n6) Put the printed ZOHO_REFRESH_TOKEN into .env, then:")
    print("   python3 scripts/diagnose_zoho_oauth.py")


if __name__ == "__main__":
    main()
