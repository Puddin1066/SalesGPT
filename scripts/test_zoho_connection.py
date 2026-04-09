#!/usr/bin/env python3
"""
Verify Zoho OAuth refresh + Mail accounts + CRM API (stdlib only).

Loads .env from repo root via scripts/zoho_oauth_dotenv.py.
"""
from __future__ import annotations

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


def _post_form(url: str, data: dict) -> dict:
    body = urlencode(data).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, token: str) -> dict:
    req = Request(
        url,
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    load_dotenv(ROOT / ".env")

    cid = os.environ.get("ZOHO_CLIENT_ID", "").strip()
    sec = os.environ.get("ZOHO_CLIENT_SECRET", "").strip()
    refresh = os.environ.get("ZOHO_REFRESH_TOKEN", "").strip()
    accounts_domain = os.environ.get("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com").strip().rstrip("/")
    mail_base = os.environ.get("ZOHO_MAIL_API_BASE", "https://mail.zoho.com").strip().rstrip("/")
    crm_base = os.environ.get("ZOHO_CRM_API_BASE", "https://www.zohoapis.com/crm/v6").strip().rstrip("/")

    missing = [k for k, v in [
        ("ZOHO_CLIENT_ID", cid),
        ("ZOHO_CLIENT_SECRET", sec),
        ("ZOHO_REFRESH_TOKEN", refresh),
    ] if not v]
    if missing:
        print("Missing in .env:", ", ".join(missing), file=sys.stderr)
        return 1

    token_url = f"{accounts_domain}/oauth/v2/token"
    try:
        tok = _post_form(
            token_url,
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": cid,
                "client_secret": sec,
            },
        )
    except HTTPError as e:
        print("Token refresh failed:", e.code, file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace")[:500], file=sys.stderr)
        return 1
    except URLError as e:
        print("Token refresh failed:", e, file=sys.stderr)
        return 1

    access = tok.get("access_token")
    if not access:
        print("No access_token in response:", json.dumps(tok, indent=2)[:400], file=sys.stderr)
        return 1

    # Zoho returns the correct API host for this org (US/EU/IN/…); prefer over .env default.
    api_domain = (tok.get("api_domain") or "").strip().rstrip("/")
    if api_domain:
        crm_base = f"{api_domain}/crm/v6"

    print("OK: refresh_token → access_token")
    if api_domain:
        print(f"    api_domain={api_domain} (using for CRM)")

    try:
        mail = _get_json(f"{mail_base}/api/accounts", access)
    except HTTPError as e:
        print("Zoho Mail /api/accounts failed:", e.code, file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace")[:500], file=sys.stderr)
        return 1

    status = mail.get("status", {})
    data = mail.get("data")
    if isinstance(data, list):
        print(f"OK: Zoho Mail accounts returned {len(data)} account(s)")
        for i, acc in enumerate(data[:5]):
            aid = acc.get("accountId", "?")
            em = acc.get("primaryEmailAddress") or acc.get("mailboxAddress") or "?"
            print(f"  [{i+1}] accountId={aid} email={em}")
        if len(data) > 5:
            print(f"  ... and {len(data) - 5} more")
    else:
        print("Unexpected Mail response shape:", json.dumps(mail, indent=2)[:600])

    # CRM: try current user, then a minimal Contacts read (some tokens lack Users API scope).
    crm_ok = False
    try:
        crm = _get_json(f"{crm_base}/users?type=CurrentUser", access)
        users = crm.get("users")
        if isinstance(users, list) and users:
            u = users[0]
            name = u.get("full_name") or u.get("name") or "?"
            uid = u.get("id", "?")
            email = u.get("email") or u.get("zuid") or ""
            extra = f" email={email}" if email else ""
            print(f"OK: Zoho CRM current user: {name} (id={uid}){extra}")
            crm_ok = True
    except HTTPError:
        pass

    if not crm_ok:
        try:
            contacts = _get_json(f"{crm_base}/Contacts?per_page=1&fields=Email", access)
        except HTTPError as e:
            print("Zoho CRM check failed:", file=sys.stderr)
            print("  /users?type=CurrentUser — scope or permission issue", file=sys.stderr)
            print("  /Contacts?per_page=1 —", e.code, file=sys.stderr)
            body = e.read().decode("utf-8", errors="replace")[:800]
            print(body, file=sys.stderr)
            print(
                "\nHint: Re-run scripts/zoho_oauth_authorize_url.py (includes ZohoCRM.modules.ALL) → "
                "Accept → NEW code → zoho_oauth_exchange_code.py → replace ZOHO_REFRESH_TOKEN.",
                file=sys.stderr,
            )
            return 1

        rows = contacts.get("data")
        if isinstance(rows, list):
            print(f"OK: Zoho CRM Contacts readable ({len(rows)} record(s) in first page, per_page=1)")
            crm_ok = True
        else:
            print("Unexpected CRM Contacts response:", json.dumps(contacts, indent=2)[:600])
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
