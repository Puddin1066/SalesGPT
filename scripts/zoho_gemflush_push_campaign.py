#!/usr/bin/env python3
"""
Create a Zoho CRM **Campaign** for GEMflush, then push `data/outreach` into CRM and link
every new **Lead** and **Contact** to that campaign (best-effort API).

Uses the same row builder as `zoho_crm_populate_from_data.py` (CSV + Apollo merge).

Environment:
  ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN
  ZOHO_OUTREACH_LEAD_SOURCE — optional; defaults to campaign-themed label
  ZOHO_CAMPAIGN_TYPE, ZOHO_CAMPAIGN_STATUS — optional picklists

Usage:
  poetry run python scripts/zoho_gemflush_push_campaign.py
  poetry run python scripts/zoho_gemflush_push_campaign.py --execute
  poetry run python scripts/zoho_gemflush_push_campaign.py --execute --limit 42 --campaign-name "GEMflush GEO partners"
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "zoho_crm_populate_from_data",
    ROOT / "scripts" / "zoho_crm_populate_from_data.py",
)
_zd = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_zd)

from services.crm.zoho_crm_agent import ZohoCRMAgent


def _campaign_playbook_note(campaign_name: str) -> str:
    return f"""GEMflush — {campaign_name}

Objectives
- Outreach to vertical SEO agencies (legal / medical / real estate) for AI/GEO + entity (Wikidata) positioning.

Data source
- data/outreach/seo_vertical_agencies.csv (+ Apollo CSV merge when emails exist).

Repo automation
- scripts/zoho_crm_populate_from_data.py — refresh/import only
- scripts/zoho_user_research_outreach.py — existing-user research mail (Zoho Mail)
- scripts/zoho_crm_audit.py — hygiene

Next
- Enrich person emails; convert qualified Leads → Contacts; log touches as Notes.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create GEMflush Zoho CRM Campaign + push data/outreach records linked to it"
    )
    parser.add_argument("--execute", action="store_true", help="Write to Zoho CRM")
    parser.add_argument("--limit", type=int, default=500, help="Max records (cap 2000)")
    parser.add_argument(
        "--campaign-name",
        default="",
        help="Campaign_Name in Zoho (default: GEMflush — agency GEO outreach YYYY-MM)",
    )
    parser.add_argument(
        "--use-campaign-json",
        action="store_true",
        help="Build rows from campaigns/seo_vertical_agencies_campaign.json",
    )
    args = parser.parse_args()

    lim = max(1, min(int(args.limit), 2000))
    unified, apollo_n = _zd.build_unified_outreach_records(
        lim, use_campaign_json=args.use_campaign_json
    )

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    campaign_name = (args.campaign_name or "").strip() or f"GEMflush — agency GEO outreach ({month})"
    lead_src = (os.getenv("ZOHO_OUTREACH_LEAD_SOURCE") or "").strip() or "GEMflush — agency GEO outreach"

    print(f"Campaign name: {campaign_name}")
    print(f"Lead_Source for new records: {lead_src[:80]}{'…' if len(lead_src) > 80 else ''}")
    print(f"Rows to sync (deduped): {len(unified)}  |  Apollo file rows: {apollo_n}")

    if not args.execute:
        for i, u in enumerate(unified[:10], 1):
            kind = "Contact" if _zd.is_valid_outreach_email(u["email"]) else "Lead"
            print(f"  {i}. [{kind}] {u['company']!r}")
        if len(unified) > 10:
            print(f"  ... +{len(unified) - 10} more")
        print("\nDry-run. Run with --execute to create Campaign + records in Zoho.")
        return 0

    try:
        crm = ZohoCRMAgent()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    camp_id = crm.create_campaign(
        campaign_name,
        description="GEMflush outbound: vertical SEO agencies — AI visibility / GEO / Knowledge Graph (data/outreach import).",
    )
    if not camp_id:
        print("Failed to create Campaign.", file=sys.stderr)
        return 1
    print(f"Created Campaign id={camp_id}")

    crm.add_note_to_record(
        "Campaigns",
        camp_id,
        "GEMflush playbook",
        _campaign_playbook_note(campaign_name),
    )

    today = datetime.now(timezone.utc).date()
    crm.create_task_for_campaign(
        camp_id,
        "Enrich top targets (email + role)",
        (today + timedelta(days=3)).isoformat(),
        "Apollo or manual; then promote Lead → Contact when you have a person email.",
    )
    crm.create_task_for_campaign(
        camp_id,
        "CRM hygiene check",
        (today + timedelta(days=7)).isoformat(),
        "Run scripts/zoho_crm_audit.py; remove test/junk records.",
    )

    stats = _zd.push_unified_to_zoho(
        crm, unified, campaign_id=camp_id, lead_src=lead_src[:120]
    )
    print(
        f"\nDone.\n"
        f"  Campaign id: {camp_id}\n"
        f"  Contacts created: {stats['contacts']}\n"
        f"  Leads created: {stats['leads']}\n"
        f"  Contacts linked to campaign: {stats['linked_contacts']}\n"
        f"  Leads linked to campaign: {stats['linked_leads']}\n"
        f"  Skipped (dup email): {stats['skipped']}\n"
        f"\nIn Zoho: open **Campaigns** → this record; **Leads** / **Contacts** for members "
        f"(linking may require UI if API related-list shape differs)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
