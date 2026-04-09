#!/usr/bin/env python3
"""
Build the Zoho OAuth authorize URL from .env (ZOHO_CLIENT_ID, ZOHO_ACCOUNTS_DOMAIN).

What to do with the URL:
  1. Open it in your browser (while logged into the right Zoho org).
  2. Click Allow. Zoho redirects to your redirect_uri with ?code=... in the query string.
  3. Copy that code immediately (it expires quickly).
  4. Run: python3 scripts/zoho_oauth_exchange_code.py --code PASTE_CODE_HERE

Usage:
  python3 scripts/zoho_oauth_authorize_url.py
  python3 scripts/zoho_oauth_authorize_url.py --redirect-uri "http://localhost:8080/oauth/callback"
  python3 scripts/zoho_oauth_authorize_url.py --scopes "ZohoCRM.modules.READ,ZohoMail.messages.CREATE"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from zoho_oauth_dotenv import load_dotenv

# Scopes for SalesGPT Zoho stack (CRM + send mail + list accounts). Narrow if you prefer.
DEFAULT_SCOPES = (
    "ZohoCRM.modules.ALL,ZohoMail.messages.CREATE,ZohoMail.accounts.READ"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Zoho OAuth browser URL")
    parser.add_argument(
        "--redirect-uri",
        default="http://localhost:8080/oauth/callback",
        help="Must match Authorized Redirect URIs in Zoho API Console exactly",
    )
    parser.add_argument(
        "--scopes",
        default=DEFAULT_SCOPES,
        help="Comma-separated Zoho OAuth scopes",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    client_id = os.environ.get("ZOHO_CLIENT_ID", "").strip()
    if not client_id:
        print("Missing ZOHO_CLIENT_ID in .env — add it from the API Console Client Secret tab.", file=sys.stderr)
        sys.exit(1)

    accounts = os.environ.get("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com").strip().rstrip("/")
    params = {
        "scope": args.scopes,
        "client_id": client_id,
        "response_type": "code",
        "access_type": "offline",
        "redirect_uri": args.redirect_uri,
    }
    url = f"{accounts}/oauth/v2/auth?{urlencode(params)}"

    print(url)
    print()
    print("Next:")
    print("  • Paste the URL into your browser, approve access.")
    print("  • On redirect, copy the `code` query parameter from the address bar.")
    print(f"  • Run: python3 scripts/zoho_oauth_exchange_code.py --code <code>")
    print(f"     (redirect URI must stay: {args.redirect_uri})")


if __name__ == "__main__":
    main()
