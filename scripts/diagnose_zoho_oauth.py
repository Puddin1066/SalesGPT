#!/usr/bin/env python3
"""
Step through Zoho Mail OAuth setup without printing secrets.

Loads .env then .env.local (same rules as run_gemflush_solopreneur_test_flow.py),
reports what is set (names + non-secret values + lengths), then POSTs refresh_token.

Usage:
  python3 scripts/diagnose_zoho_oauth.py
  .venv/bin/python scripts/diagnose_zoho_oauth.py
"""
from __future__ import annotations

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


def secret_status(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        return "MISSING"
    # Never print fragments of secrets (could leak in logs/screenshots)
    return f"set (len={len(v)})"


def post_refresh(accounts_domain: str, client_id: str, client_secret: str, refresh_token: str) -> tuple[int, str]:
    url = f"{accounts_domain.rstrip('/')}/oauth/v2/token"
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("utf-8")
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

    print("=== 1) Env files ===")
    for name in (".env", ".env.local"):
        p = ROOT / name
        print(f"  {name}: {'found' if p.is_file() else 'not found'}")

    print("\n=== 2) Feature flags ===")
    print(f"  USE_ZOHO_STACK={os.getenv('USE_ZOHO_STACK', '')!r}")
    print(f"  USE_MOCK_APIS={os.getenv('USE_MOCK_APIS', '')!r}")

    print("\n=== 3) Zoho endpoints (not secrets) ===")
    acct = os.getenv("ZOHO_ACCOUNTS_DOMAIN", "").strip() or "(missing — default would be https://accounts.zoho.com in app code)"
    mail = os.getenv("ZOHO_MAIL_API_BASE", "").strip() or "(missing — default https://mail.zoho.com)"
    print(f"  ZOHO_ACCOUNTS_DOMAIN={acct}")
    print(f"  ZOHO_MAIL_API_BASE={mail}")

    print("\n=== 4) OAuth credentials (masked) ===")
    for key in (
        "ZOHO_CLIENT_ID",
        "ZOHO_CLIENT_SECRET",
        "ZOHO_REFRESH_TOKEN",
    ):
        print(f"  {key}: {secret_status(key)}")

    print("\n=== 5) Mail identity (usually not secret) ===")
    print(f"  ZOHO_MAIL_FROM={os.getenv('ZOHO_MAIL_FROM', '') or 'MISSING'}")
    print(f"  ZOHO_MAIL_ACCOUNT_ID={os.getenv('ZOHO_MAIL_ACCOUNT_ID', '') or '(optional)'}")

    print("\n=== 6) Refresh-token request (same as app) ===")
    client_id, dw1 = clean_zoho_client_id(os.getenv("ZOHO_CLIENT_ID", ""))
    client_secret, dw2 = clean_zoho_secret_or_token(os.getenv("ZOHO_CLIENT_SECRET", ""))
    refresh_token, dw3 = clean_zoho_secret_or_token(os.getenv("ZOHO_REFRESH_TOKEN", ""))
    for w in (dw1, dw2, dw3):
        if w:
            print(f"  WARNING: {w}", file=sys.stderr)
    accounts_domain = (os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "https://accounts.zoho.com").strip().rstrip("/")

    if not all([client_id, client_secret, refresh_token]):
        print("  SKIP: need ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN all non-empty.")
        sys.exit(1)

    token_url = f"{accounts_domain}/oauth/v2/token"
    print(f"  POST {token_url}")

    status, text = post_refresh(accounts_domain, client_id, client_secret, refresh_token)
    print(f"  HTTP {status}")

    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            print("  Body: (invalid JSON)")
            print(text[:800])
            sys.exit(1)
        if "access_token" in data:
            print("  OK: JSON includes access_token (length %d)" % len(data.get("access_token", "")))
            if "refresh_token" in data:
                print("  NOTE: Zoho returned a new refresh_token — update .env if you rely on file-only storage.")
            if "error" in data:
                print(
                    f"  error={data.get('error')!r} "
                    f"description={data.get('error_description', '')!r}"
                )
            sys.exit(0 if status == 200 and "access_token" in data else 1)
        print(f"  JSON keys: {list(data.keys())}")
        err = data.get("error")
        desc = data.get("error_description", "") or ""
        print(f"  error={err!r} description={desc!r}")
        if err == "invalid_code":
            print(
                "  Hint: On the refresh_token grant, Zoho uses error=invalid_code when the\n"
                "  refresh token is missing, wrong, revoked, or not for this client_id.\n"
                "  Do a new browser auth (print_zoho_oauth_authorize_url.py) → exchange_zoho_auth_code.py\n"
                "  and replace ZOHO_REFRESH_TOKEN in .env."
            )
        sys.exit(1)

    print("  Body is not JSON (often wrong ZOHO_ACCOUNTS_DOMAIN or blocked request). Snippet:")
    print(text[:600])
    sys.exit(1)


if __name__ == "__main__":
    main()
