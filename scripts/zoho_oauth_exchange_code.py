#!/usr/bin/env python3
"""
Exchange a Zoho OAuth authorization code for access + refresh tokens.

Run after you opened scripts/zoho_oauth_authorize_url.py in a browser and copied ?code=...

Usage:
  python3 scripts/zoho_oauth_exchange_code.py --code "1000.xxx..."
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from zoho_oauth_dotenv import load_dotenv


def _print_zoho_error(status: int, raw: str) -> None:
    print(f"Token exchange failed: HTTP {status}", file=sys.stderr)
    raw_stripped = raw.strip()
    try:
        err_json = json.loads(raw_stripped)
        print(json.dumps(err_json, indent=2), file=sys.stderr)
    except json.JSONDecodeError:
        snippet = raw_stripped[:600] + ("..." if len(raw_stripped) > 600 else "")
        if snippet:
            print(snippet, file=sys.stderr)
    print(
        "\nCommon causes:\n"
        "  • Code already used or expired — run scripts/zoho_oauth_authorize_url.py again, Accept, copy the NEW code, exchange within ~1–2 minutes.\n"
        "  • redirect_uri mismatch — must match the authorize URL and Zoho API Console exactly "
        '(e.g. http://localhost:8080/oauth/callback).\n'
        "  • Wrong ZOHO_CLIENT_ID / ZOHO_CLIENT_SECRET or ZOHO_ACCOUNTS_DOMAIN (US vs EU, etc.).",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Exchange Zoho OAuth code for tokens")
    parser.add_argument("--code", required=True, help="Authorization code from redirect URL")
    parser.add_argument(
        "--redirect-uri",
        default="http://localhost:8080/oauth/callback",
        help="Must match the redirect_uri used in the authorize URL",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print token URL, redirect_uri, and client_id prefix (no secrets)",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    cid = os.environ.get("ZOHO_CLIENT_ID", "").strip()
    sec = os.environ.get("ZOHO_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        print("Set ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET in .env", file=sys.stderr)
        sys.exit(1)

    accounts = os.environ.get("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com").strip().rstrip("/")
    token_url = f"{accounts}/oauth/v2/token"

    if args.debug:
        print(f"token_url={token_url}", file=sys.stderr)
        print(f"redirect_uri={args.redirect_uri!r}", file=sys.stderr)
        print(f"client_id_prefix={cid[:12]}..." if len(cid) > 12 else f"client_id={cid!r}", file=sys.stderr)

    body = urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": cid,
            "client_secret": sec,
            "redirect_uri": args.redirect_uri,
            "code": args.code.strip(),
        }
    ).encode("utf-8")
    req = Request(
        token_url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        _print_zoho_error(e.code, err_body)
        sys.exit(1)
    except URLError as e:
        print(f"Token exchange failed: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON from Zoho: {e}", file=sys.stderr)
        sys.exit(1)

    refresh = data.get("refresh_token")
    if not refresh:
        print("Response had no refresh_token. Full JSON:", file=sys.stderr)
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(1)

    print("Add to .env:")
    print(f"ZOHO_REFRESH_TOKEN={refresh}")
    print()
    print("(Access token is short-lived; the app refreshes it using the refresh token.)")


if __name__ == "__main__":
    main()
