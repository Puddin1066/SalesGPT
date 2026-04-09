#!/usr/bin/env python3
"""
Populate Zoho CRM from files under data/outreach/:

  - seo_vertical_agencies.csv     (primary — full research columns → Description)
  - seo_vertical_agencies_apollo.csv (merge by Company Name → Email / Phone / Name / Title / LinkedIn)
  - campaigns/seo_vertical_agencies_campaign.json (optional --use-campaign-json — richer contact objects)

Creates Contacts when a valid email is present after merge; otherwise Leads (company + website + description).
Dedupes in one run by normalized website domain. Optional link to an existing Campaign id.

Environment:
  ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN
  ZOHO_OUTREACH_LEAD_SOURCE — picklist-safe Lead_Source for new Leads (recommended)
  ZOHO_POPULATE_CAMPAIGN_ID — if set, relate each new Lead to this Campaign (--campaign-id overrides)

Usage:
  poetry run python scripts/zoho_crm_populate_from_data.py
  poetry run python scripts/zoho_crm_populate_from_data.py --execute
  poetry run python scripts/zoho_crm_populate_from_data.py --execute --campaign-id CAMPAIGN_RECORD_ID
  poetry run python scripts/zoho_crm_populate_from_data.py --execute --use-campaign-json --limit 50
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "outreach"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_env_file(path: Path, *, override: bool = False) -> None:
    """Minimal KEY=value loader so Zoho vars load even without python-dotenv."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if not key:
            continue
        if not override and key in os.environ:
            continue
        os.environ[key] = val


_load_env_file(ROOT / ".env", override=False)
_load_env_file(ROOT / ".env.local", override=True)

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".env.local", override=True)
except ImportError:
    pass

from services.crm.zoho_crm_agent import ZohoCRMAgent

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _norm_company(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _domain_from_url(url: str) -> str:
    if not (url or "").strip():
        return ""
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    try:
        host = urlparse(u).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _valid_email(s: Optional[str]) -> bool:
    if not s or not str(s).strip():
        return False
    return bool(_EMAIL_RE.match(str(s).strip().lower()))


def is_valid_outreach_email(s: Optional[str]) -> bool:
    """True if string looks like a usable email for Zoho Contact create."""
    return _valid_email(s)


def _load_apollo(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.is_file():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            co = _norm_company(row.get("Company Name") or "")
            if not co:
                continue
            out[co] = {
                "first": (row.get("First Name") or "").strip(),
                "last": (row.get("Last Name") or "").strip(),
                "title": (row.get("Title") or "").strip(),
                "email": (row.get("Email") or "").strip(),
                "phone": (row.get("Phone") or "").strip(),
                "linkedin": (row.get("Person Linkedin Url") or "").strip(),
                "stage": (row.get("Stage") or "").strip(),
            }
    return out


def _csv_description(row: Dict[str, str]) -> str:
    lines: List[str] = []
    order = [
        "vertical",
        "agency_name",
        "website",
        "notes",
        "hq_region",
        "leadership_snapshot",
        "portfolio_public_hooks",
        "core_services_tagged",
        "ai_geo_answer_engine_signals",
        "gemflush_outreach_angle",
        "wikidata_knowledge_graph_angle",
        "enrichment_source_date",
    ]
    for k in order:
        v = (row.get(k) or "").strip()
        if v:
            label = k.replace("_", " ").title()
            lines.append(f"{label}: {v}")
    for k, v in sorted(row.items()):
        if k in order or not (v or "").strip():
            continue
        lines.append(f"{k}: {(v or '').strip()}")
    return "\n".join(lines)[:65000]


def _load_main_csv(path: Path, limit: int) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v or "") for k, v in row.items()})
            if len(rows) >= limit:
                break
    return rows


def _campaign_json_rows(path: Path, limit: int) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    contacts = data.get("contacts") or []
    if not isinstance(contacts, list):
        return []
    return contacts[:limit]


def _campaign_contact_description(c: Dict[str, Any]) -> str:
    skip = {"contact_id", "emails", "merge_fields_expected", "merge_field_hints", "status", "domain"}
    lines: List[str] = []
    for k in (
        "vertical",
        "agency_name",
        "website",
        "research_notes",
        "hq_region",
        "leadership_snapshot",
        "portfolio_public_hooks",
        "core_services_tagged",
        "ai_geo_signals",
        "gemflush_outreach_angle",
        "wikidata_angle",
        "enrichment_source_date",
    ):
        v = c.get(k)
        if v:
            lines.append(f"{k.replace('_', ' ').title()}: {v}")
    for k, v in sorted(c.items()):
        if k in skip or k in (
            "vertical",
            "agency_name",
            "website",
            "research_notes",
            "hq_region",
            "leadership_snapshot",
            "portfolio_public_hooks",
            "core_services_tagged",
            "ai_geo_signals",
            "gemflush_outreach_angle",
            "wikidata_angle",
            "enrichment_source_date",
        ):
            continue
        if isinstance(v, (dict, list)) or v in (None, ""):
            continue
        lines.append(f"{k}: {v}")
    return "\n".join(lines)[:65000]


def _merge_row(
    csv_row: Dict[str, str],
    apollo: Dict[str, Dict[str, str]],
) -> Tuple[str, str, str, str, str, str, str, str, str]:
    """company, website, description, email, phone, first, last, title, linkedin"""
    company = (csv_row.get("agency_name") or csv_row.get("Company Name") or "").strip() or "Unknown"
    website = (csv_row.get("website") or "").strip()
    desc = _csv_description(csv_row)
    key = _norm_company(company)
    ap = apollo.get(key, {})
    email = ap.get("email", "")
    phone = ap.get("phone", "")
    first = ap.get("first", "")
    last = ap.get("last", "")
    title = ap.get("title", "")
    linkedin = ap.get("linkedin", "")
    return company, website, desc, email, phone, first, last, title, linkedin


def build_unified_outreach_records(
    limit: int,
    *,
    use_campaign_json: bool,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Build deduped outreach rows from data/outreach (CSV + Apollo merge, or campaign JSON + Apollo).

    Returns:
        (unified_rows, apollo_enrichment_count)
    """
    lim = max(1, min(int(limit), 2000))
    apollo_path = DATA / "seo_vertical_agencies_apollo.csv"
    apollo = _load_apollo(apollo_path)

    unified: List[Dict[str, Any]] = []
    seen_domains: Set[str] = set()

    if use_campaign_json:
        cpath = DATA / "campaigns" / "seo_vertical_agencies_campaign.json"
        for c in _campaign_json_rows(cpath, lim):
            company = (c.get("agency_name") or "").strip() or "Unknown"
            website = (c.get("website") or "").strip()
            dom = _domain_from_url(website) or _norm_company(company)
            if dom in seen_domains:
                continue
            seen_domains.add(dom)
            desc = _campaign_contact_description(c)
            key = _norm_company(company)
            ap = apollo.get(key, {})
            unified.append(
                {
                    "company": company,
                    "website": website,
                    "description": desc,
                    "email": ap.get("email", ""),
                    "phone": ap.get("phone", ""),
                    "first": ap.get("first", ""),
                    "last": ap.get("last", ""),
                    "title": ap.get("title", ""),
                    "linkedin": ap.get("linkedin", ""),
                }
            )
    else:
        csv_path = DATA / "seo_vertical_agencies.csv"
        for row in _load_main_csv(csv_path, lim):
            company, website, desc, email, phone, first, last, title, linkedin = _merge_row(row, apollo)
            dom = _domain_from_url(website) or _norm_company(company)
            if dom in seen_domains:
                continue
            seen_domains.add(dom)
            unified.append(
                {
                    "company": company,
                    "website": website,
                    "description": desc,
                    "email": email,
                    "phone": phone,
                    "first": first,
                    "last": last,
                    "title": title,
                    "linkedin": linkedin,
                }
            )

    return unified, len(apollo)


def push_unified_to_zoho(
    crm: ZohoCRMAgent,
    unified: List[Dict[str, Any]],
    *,
    campaign_id: str,
    lead_src: str,
) -> Dict[str, int]:
    """
    Create Contacts (when email) or Leads; optionally link to Campaign.

    Returns counts: contacts, leads, linked_leads, linked_contacts, skipped
    """
    contacts = 0
    leads = 0
    linked_leads = 0
    linked_contacts = 0
    skipped = 0
    link_campaign = (campaign_id or "").strip()

    for u in unified:
        email = u["email"]
        company = u["company"]
        website = u["website"]
        desc = u["description"]
        phone = u["phone"]
        title = u["title"]
        linkedin = u["linkedin"]
        first = (u["first"] or "").strip() or "-"
        last = (u["last"] or "").strip() or "-"

        if _valid_email(email):
            existing = crm.get_contact_by_email(email.lower())
            if existing and existing.get("id"):
                print(f"  skip duplicate Contact email={email}")
                skipped += 1
                continue
            full_desc = desc
            if linkedin:
                full_desc = f"{full_desc}\n\nLinkedIn: {linkedin}".strip()
            add: Dict[str, Any] = {}
            if lead_src:
                add["Lead_Source"] = lead_src[:120]
            if full_desc:
                add["Description"] = full_desc[:65000]
            cid = crm.create_contact(
                email=email.strip().lower(),
                first_name=first,
                last_name=last,
                company=company,
                website=website or None,
                phone=phone or None,
                title=title or None,
                linkedin_url=None,
                additional_properties=add or None,
            )
            if cid:
                contacts += 1
                if link_campaign and crm.relate_contact_to_campaign(link_campaign, cid):
                    linked_contacts += 1
            else:
                print(f"  Contact failed: {company}")
        else:
            ldesc = desc
            if linkedin:
                ldesc = f"{ldesc}\n\nLinkedIn: {linkedin}".strip()
            xfields: Dict[str, Any] = {}
            if phone:
                xfields["Phone"] = phone
            if title:
                xfields["Title"] = title
            lid = crm.create_lead(
                company=company,
                last_name=last if last != "-" else "-",
                first_name=first if first != "-" else "",
                website=website or None,
                lead_source=lead_src[:120],
                description=ldesc,
                extra_fields=xfields or None,
            )
            if not lid:
                print(f"  Lead failed: {company}")
                continue
            leads += 1
            if link_campaign and crm.relate_lead_to_campaign(link_campaign, lid):
                linked_leads += 1

    return {
        "contacts": contacts,
        "leads": leads,
        "linked_leads": linked_leads,
        "linked_contacts": linked_contacts,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate Zoho CRM from data/outreach files")
    parser.add_argument("--execute", action="store_true", help="Write to Zoho (default: plan only)")
    parser.add_argument("--limit", type=int, default=500, help="Max records (capped at 2000)")
    parser.add_argument(
        "--use-campaign-json",
        action="store_true",
        help="Use campaigns/seo_vertical_agencies_campaign.json instead of CSV",
    )
    parser.add_argument(
        "--campaign-id",
        default="",
        help="Zoho CRM Campaign record id to link new Leads (or set ZOHO_POPULATE_CAMPAIGN_ID)",
    )
    args = parser.parse_args()

    lim = max(1, min(int(args.limit), 2000))
    campaign_id = (args.campaign_id or os.getenv("ZOHO_POPULATE_CAMPAIGN_ID") or "").strip()
    lead_src = (os.getenv("ZOHO_OUTREACH_LEAD_SOURCE") or "Data import — seo_vertical_agencies").strip()

    unified, apollo_n = build_unified_outreach_records(lim, use_campaign_json=args.use_campaign_json)

    print(f"Records to push (after domain dedupe): {len(unified)}")
    print(f"Apollo enrichment rows loaded: {apollo_n}")
    if campaign_id:
        print(f"Campaign link: {campaign_id}")
    else:
        print("Campaign link: (none — set --campaign-id or ZOHO_POPULATE_CAMPAIGN_ID)")

    if not args.execute:
        for i, u in enumerate(unified[:12], 1):
            has = "Contact" if _valid_email(u["email"]) else "Lead"
            print(f"  {i}. [{has}] {u['company']!r}  email={u['email'] or '-'}  {u['website'][:48] if u['website'] else ''}")
        if len(unified) > 12:
            print(f"  ... +{len(unified) - 12} more")
        print("\nDry-run. Use --execute to create records in Zoho CRM.")
        return 0

    try:
        crm = ZohoCRMAgent()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    stats = push_unified_to_zoho(
        crm, unified, campaign_id=campaign_id, lead_src=lead_src
    )
    print(
        f"\nDone. Contacts created: {stats['contacts']}; Leads created: {stats['leads']}; "
        f"Leads linked to Campaign: {stats['linked_leads']}; "
        f"Contacts linked to Campaign: {stats['linked_contacts']}; skipped: {stats['skipped']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
