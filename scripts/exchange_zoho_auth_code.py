#!/usr/bin/env python3
"""
Exchange a Zoho authorization ?code=... for access_token + refresh_token.

Uses the same .env as other scripts:
  ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_OAUTH_REDIRECT_URI, ZOHO_ACCOUNTS_DOMAIN

Usage:
  python3 scripts/exchange_zoho_auth_code.py --code '1000.xxx...'
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.zoho.oauth_env_sanitize import clean_zoho_client_id, clean_zoho_secret_or_token


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


def post_form(url: str, data: dict) -> tuple[int, str]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "SalesGPT/1.0 (Zoho OAuth)")
    req.add_header("Accept", "application/json, */*")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main() -> None:
    load_env_file(ROOT / ".env", override=False)
    load_env_file(ROOT / ".env.local", override=True)

    p = argparse.ArgumentParser()
    p.add_argument("--code", required=True, help="Authorization code from redirect URL")
    args = p.parse_args()

    client_id, w1 = clean_zoho_client_id(os.getenv("ZOHO_CLIENT_ID", ""))
    if w1:
        print(w1, file=sys.stderr)
    client_secret, w2 = clean_zoho_secret_or_token(os.getenv("ZOHO_CLIENT_SECRET", ""))
    if w2:
        print(w2, file=sys.stderr)
    redirect_uri = os.getenv("ZOHO_OAUTH_REDIRECT_URI", "").strip()
    accounts = (os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "https://accounts.zoho.com").rstrip("/")

    if not all([client_id, client_secret, redirect_uri]):
        print("Need ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_OAUTH_REDIRECT_URI in .env", file=sys.stderr)
        sys.exit(1)

    token_url = f"{accounts}/oauth/v2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": args.code.strip(),
    }

    status, text = post_form(token_url, payload)
    print(f"HTTP {status}\n")

    if not text.strip().startswith("{"):
        print(text[:1200])
        sys.exit(1)

    data = json.loads(text)
    if data.get("error"):
        print(json.dumps(data, indent=2))
        err = data.get("error")
        if err == "invalid_code":
            print(
                "\n--- Zoho invalid_code (authorization code exchange) ---\n"
                "Common causes:\n"
                "  1) Code already used or expired (codes are one-time; use within ~minutes).\n"
                "  2) redirect_uri mismatch: must match EXACTLY the URI in the authorize URL\n"
                "     AND in API Console. This script sent redirect_uri=\n"
                f"     {redirect_uri!r}\n"
                "     If that differs from print_zoho_oauth_authorize_url.py output, fix .env / .env.local.\n"
                "     Note: .env.local overrides .env for duplicate keys.\n"
                "  3) Wrong ZOHO_ACCOUNTS_DOMAIN for where you logged in (this run uses "
                f"{accounts!r}).\n"
                "  4) client_secret out of date (rotated in API Console but not in .env).\n\n"
                "Fix: run print_zoho_oauth_authorize_url.py → open link → immediately run this script\n"
                "with the NEW code= value (copy only the code, no quotes/spaces).",
                file=sys.stderr,
            )
        sys.exit(1)

    rt = data.get("refresh_token")
    at = data.get("access_token")
    api_domain = data.get("api_domain", "")

    if not rt:
        print("No refresh_token in response. First-time offline grant may require prompt=consent — see Zoho docs.")
        print(json.dumps({k: v for k, v in data.items() if k != "access_token"}, indent=2))
        sys.exit(1)

    print("Success. Add/update in .env:\n")
    print(f"ZOHO_REFRESH_TOKEN={rt}")
    if api_domain:
        print(f"\n# api_domain from Zoho (use same DC for accounts + APIs): {api_domain}")
    if at:
        print(f"\n(access_token received, len={len(at)} — expires ~1h; app will refresh via refresh_token.)")


if __name__ == "__main__":
    main()
