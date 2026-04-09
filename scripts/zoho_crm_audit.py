#!/usr/bin/env python3
"""
Audit Zoho CRM via API: inventory Contacts, Leads, Campaigns (and Deals count);
flag likely fake/test/junk using heuristics (not perfect — review before bulk delete).

Requires: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN
Optional: USE_MOCK_APIS=true → no network (empty/mock).

Usage:
  poetry run python scripts/zoho_crm_audit.py
  poetry run python scripts/zoho_crm_audit.py --module Contacts --max-pages 5
  poetry run python scripts/zoho_crm_audit.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load env (same pattern as other scripts)
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".env.local", override=True)
except ImportError:
    pass

from services.crm.zoho_crm_agent import ZohoCRMAgent

# Domains / patterns commonly used for throwaways or placeholders
_DISPOSABLE_DOMAINS = frozenset(
    x.lower()
    for x in (
        "mailinator.com",
        "guerrillamail.com",
        "yopmail.com",
        "tempmail.com",
        "10minutemail.com",
        "trashmail.com",
        "fakeinbox.com",
        "maildrop.cc",
        "getnada.com",
        "sharklasers.com",
    )
)
_PLACEHOLDER_DOMAINS = frozenset({"example.com", "example.org", "test.com", "localhost"})

_LOCAL_TRASH_TOKENS = re.compile(
    r"(^test|test$|testing|fake|asdf|qwerty|xxx|junk|spam|trash|temp|"
    r"^admin$|^user\d+$|no-?reply|donotreply|mailer-daemon)",
    re.I,
)


def _norm_email(e: Optional[str]) -> str:
    return (e or "").strip().lower()


def _contact_flags(row: Dict[str, Any], module: str) -> List[str]:
    flags: List[str] = []
    if module == "Campaigns":
        cn = (row.get("Campaign_Name") or row.get("Name") or "").strip()
        if cn and re.search(r"\b(test|fake|tmp|trash|debug|asdf|sample|demo)\b", cn, re.I):
            flags.append("suspicious_campaign_name")
        if not cn or cn in (".", "-", "?", "test"):
            flags.append("empty_or_trivial_campaign_name")
        return flags

    email = _norm_email(row.get("Email"))
    fn = (row.get("First_Name") or "").strip()
    ln = (row.get("Last_Name") or "").strip()
    name = f"{fn} {ln}".strip().lower()

    if not email:
        flags.append("no_email")
    elif "@" not in email:
        flags.append("invalid_email")
    else:
        local, _, domain = email.partition("@")
        if domain in _PLACEHOLDER_DOMAINS:
            flags.append("placeholder_domain")
        if domain in _DISPOSABLE_DOMAINS:
            flags.append("disposable_domain")
        if _LOCAL_TRASH_TOKENS.search(local):
            flags.append("suspicious_local_part")

    if fn in ("-", ".", "") and ln in ("-", ".", ""):
        flags.append("placeholder_name")
    if name in ("test test", "fake user", "asdf asdf", "first last"):
        flags.append("generic_name")

    return flags


def _paginate_module(
    crm: ZohoCRMAgent,
    module: str,
    fields: str,
    *,
    per_page: int,
    max_pages: Optional[int],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """GET /{module} with pagination. Returns (rows, last_info)."""
    all_rows: List[Dict[str, Any]] = []
    page = 1
    info: Dict[str, Any] = {}
    while True:
        url = f"{crm.crm_api_base}/{module}"
        resp = crm._request(
            "GET",
            url,
            params={"page": page, "per_page": per_page, "fields": fields},
        )
        if resp.status_code != 200:
            return all_rows, {"error": resp.status_code, "body": resp.text[:800], "page": page}

        data = resp.json()
        rows = data.get("data") or []
        if not isinstance(rows, list):
            return all_rows, {"error": "bad_shape", "raw": str(data)[:500]}

        all_rows.extend(rows)
        info = data.get("info") or {}
        more = bool(info.get("more_records"))
        if not more:
            break
        page += 1
        if max_pages is not None and page > max_pages:
            info["truncated_at_page"] = max_pages
            break
    return all_rows, info


def _summarize_contacts_like(rows: List[Dict[str, Any]], module: str) -> Dict[str, Any]:
    by_flag: Counter[str] = Counter()
    samples: Dict[str, List[str]] = defaultdict(list)
    emails_seen: Dict[str, int] = {}
    empty_email = 0

    for row in rows:
        e = _norm_email(row.get("Email"))
        if not e:
            empty_email += 1
        else:
            emails_seen[e] = emails_seen.get(e, 0) + 1

        for f in _contact_flags(row, module):
            by_flag[f] += 1
            rid = str(row.get("id", "?"))
            if len(samples[f]) < 8:
                label = e or "(no email)"
                samples[f].append(f"{label}  id={rid}")

    dup_emails = sum(1 for v in emails_seen.values() if v > 1)
    return {
        "total": len(rows),
        "empty_email": empty_email,
        "distinct_emails": len(emails_seen),
        "duplicate_email_addresses": dup_emails,
        "flag_counts": dict(by_flag),
        "flag_samples": {k: v for k, v in samples.items()},
    }


def _summarize_campaigns(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_flag: Counter[str] = Counter()
    samples: Dict[str, List[str]] = defaultdict(list)
    names: List[str] = []

    for row in rows:
        name = (row.get("Campaign_Name") or row.get("Name") or "?").strip()
        names.append(name)
        for f in _contact_flags(row, "Campaigns"):
            by_flag[f] += 1
            rid = str(row.get("id", "?"))
            if len(samples[f]) < 12:
                samples[f].append(f"{name!r} id={rid}")

    return {
        "total": len(rows),
        "flag_counts": dict(by_flag),
        "flag_samples": {k: v for k, v in samples.items()},
        "name_prefixes_top": Counter(n[:20] for n in names if n).most_common(15),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Zoho CRM API audit / junk heuristics")
    parser.add_argument("--per-page", type=int, default=200)
    parser.add_argument("--max-pages", type=int, default=None, help="Cap pages per module (default: all)")
    parser.add_argument(
        "--module",
        choices=("all", "Contacts", "Leads", "Campaigns", "Deals"),
        default="all",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary only")
    args = parser.parse_args()

    if os.getenv("USE_MOCK_APIS", "").lower() == "true":
        print("USE_MOCK_APIS=true — connect real OAuth to audit your org.", file=sys.stderr)
        return 1

    try:
        crm = ZohoCRMAgent()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    out: Dict[str, Any] = {
        "crm_api_base": crm.crm_api_base,
        "modules": {},
    }

    modules_to_run: List[str] = []
    if args.module == "all":
        modules_to_run = ["Contacts", "Leads", "Campaigns", "Deals"]
    else:
        modules_to_run = [args.module]

    for mod in modules_to_run:
        if mod == "Deals":
            rows, info = _paginate_module(
                crm,
                "Deals",
                "Deal_Name,Stage,Amount,Created_Time",
                per_page=args.per_page,
                max_pages=args.max_pages,
            )
            if "error" in info:
                out["modules"]["Deals"] = {"error": info}
                continue
            out["modules"]["Deals"] = {
                "total": len(rows),
                "info": {k: v for k, v in info.items() if k != "truncated_at_page"},
                "truncated": info.get("truncated_at_page"),
                "stage_counts": Counter((r.get("Stage") or "?") for r in rows).most_common(20),
            }
            continue

        if mod == "Contacts":
            fields = "Email,First_Name,Last_Name,Created_Time,Lead_Source,Modified_Time"
        elif mod == "Leads":
            fields = "Email,First_Name,Last_Name,Created_Time,Lead_Source,Company,Modified_Time"
        elif mod == "Campaigns":
            fields = "Campaign_Name,Type,Status,Created_Time,Modified_Time"
        else:
            fields = "id"

        rows, info = _paginate_module(
            crm,
            mod,
            fields,
            per_page=args.per_page,
            max_pages=args.max_pages,
        )
        if "error" in info:
            out["modules"][mod] = {"error": info}
            continue

        block: Dict[str, Any] = {
            "total": len(rows),
            "pagination": {k: v for k, v in info.items()},
        }
        if mod in ("Contacts", "Leads"):
            block["heuristics"] = _summarize_contacts_like(rows, mod)
        elif mod == "Campaigns":
            block["heuristics"] = _summarize_campaigns(rows)
        out["modules"][mod] = block

    if args.json:
        print(json.dumps(out, indent=2, default=str))
        return 0

    print(f"Zoho CRM API base: {out['crm_api_base']}\n")
    for name, block in out["modules"].items():
        print(f"=== {name} ===")
        if "error" in block:
            print(f"  ERROR: {block['error']}")
            continue
        print(f"  Records fetched: {block.get('total', 0)}")
        if block.get("pagination", {}).get("truncated_at_page"):
            print(f"  (truncated at page {block['pagination']['truncated_at_page']})")
        h = block.get("heuristics")
        if h:
            print(f"  Distinct emails: {h.get('distinct_emails', 'n/a')}  duplicate addresses: {h.get('duplicate_email_addresses', 'n/a')}")
            fc = h.get("flag_counts") or {}
            if fc:
                print("  Heuristic flags (review before delete):")
                for k, v in sorted(fc.items(), key=lambda x: -x[1]):
                    print(f"    {k}: {v}")
                    for line in (h.get("flag_samples") or {}).get(k, []):
                        print(f"      - {line}")
            if name == "Campaigns" and h.get("name_prefixes_top"):
                print("  Common name prefixes (first 20 chars):")
                for pref, cnt in h["name_prefixes_top"][:10]:
                    print(f"    {cnt}x  {pref!r}")
        if name == "Deals" and block.get("stage_counts"):
            print("  Top stages:")
            for st, cnt in block["stage_counts"][:10]:
                print(f"    {cnt}x  {st!r}")
        print()

    print(
        "Note: Zoho Mail / Smartlead 'campaigns' are usually NOT Zoho CRM Campaigns records.\n"
        "Trash in CRM often comes from tests, imports, or integrations — use Zoho's UI bulk actions\n"
        "or COQL export after you verify a saved filter matching these heuristics."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
