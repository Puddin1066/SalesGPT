#!/usr/bin/env python3
"""
Begin a marketing/outreach campaign in Zoho CRM via API:

  1) Create a Campaign record
  2) Add a Note on the Campaign (playbook: channels, repo scripts, compliance reminders)
  3) Seed Leads from data/outreach/seo_vertical_agencies.json (company + website; no fake emails)
  4) Relate each Lead to the Campaign (best-effort; org-specific related-list shapes)
  5) Create a few Tasks on the Campaign for follow-through

Default is dry-run. Use --execute to call Zoho.

Environment:
  ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN
  Optional picklists: ZOHO_CAMPAIGN_TYPE (default Email), ZOHO_CAMPAIGN_STATUS (default Planning)
  ZOHO_OUTREACH_LEAD_SOURCE — if set, used as Lead_Source (else first 120 chars of campaign name)

Usage:
  poetry run python scripts/zoho_crm_start_outreach_campaign.py
  poetry run python scripts/zoho_crm_start_outreach_campaign.py --execute --limit 15
  poetry run python scripts/zoho_crm_start_outreach_campaign.py --execute --campaign-name "GEO agency wave — Apr 2026"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_env_file(path: Path, *, override: bool = False) -> None:
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

DEFAULT_AGENCIES_JSON = ROOT / "data" / "outreach" / "seo_vertical_agencies.json"


def _load_agencies(path: Path, limit: int) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("agencies") or []
    if not isinstance(rows, list):
        return []
    return rows[:limit]


def _playbook_note(campaign_name: str, agencies_file: str) -> str:
    return f"""GEMflush outreach — campaign shell (“{campaign_name}”)

Objectives
- Book conversations with vertical SEO agencies (legal / medical / real estate) on AI visibility + entity/Knowledge Graph positioning.
- Keep CRM as source of truth: Lead status, Campaign membership, Notes per touch.

Data
- Starter targets (research only): {agencies_file}
- Enrich decision-maker emails via Apollo / manual research before promoting Lead → Contact.

Execution (repo)
- Zoho Mail stack: USE_ZOHO_STACK + scripts/zoho_user_research_outreach.py (existing users) / bespoke sends.
- CRM hygiene: scripts/zoho_crm_audit.py
- Email template merge JSON: scripts/build_zoho_outreach_email_templates.py

Compliance
- One-to-one research: still prefer unsubscribe/prefs link in footer for trust + deliverability.
- Do not invent emails for Leads in this seed list.

Next steps
1) Finalize ICP + offer one-liner; pin in Zoho Cliq (scripts/zoho_gemflush_workspace_setup.py).
2) Enrich top N Leads; log calls/emails as Notes.
3) Move qualified Leads to Contacts + Deal when appropriate.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Zoho CRM campaign + seed outreach Leads")
    parser.add_argument("--execute", action="store_true", help="Perform CRM writes (default: plan only)")
    parser.add_argument("--campaign-name", default="", help="Override default campaign name")
    parser.add_argument("--limit", type=int, default=25, help="Max agencies to import as Leads (capped at 500)")
    parser.add_argument(
        "--agencies-json",
        type=Path,
        default=DEFAULT_AGENCIES_JSON,
        help="Path to seo_vertical_agencies.json",
    )
    args = parser.parse_args()

    if not args.agencies_json.is_file():
        print(f"Agencies file not found: {args.agencies_json}", file=sys.stderr)
        return 1

    lim = max(1, min(int(args.limit), 500))
    agencies = _load_agencies(args.agencies_json, lim)
    if not agencies:
        print("No agencies in JSON.", file=sys.stderr)
        return 1

    default_name = f"GEMflush GEO agency outreach — {datetime.now(timezone.utc).strftime('%Y-%m')}"
    campaign_name = (args.campaign_name or default_name).strip()

    today = datetime.now(timezone.utc).date()
    due_review = (today + timedelta(days=1)).isoformat()
    due_enrich = (today + timedelta(days=3)).isoformat()
    due_metrics = (today + timedelta(days=7)).isoformat()

    print(f"Campaign name: {campaign_name}")
    print(f"Leads to seed (max {lim}): {len(agencies)} rows from {args.agencies_json.name}")
    if not args.execute:
        print("\nDry-run. Re-run with --execute to create Campaign + Leads in Zoho CRM.\n")
        for i, a in enumerate(agencies[:8], 1):
            print(f"  {i}. {a.get('agency_name')} — {a.get('vertical')} — {a.get('website', '')[:50]}")
        if len(agencies) > 8:
            print(f"  ... +{len(agencies) - 8} more")
        return 0

    try:
        crm = ZohoCRMAgent()
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    cid = crm.create_campaign(
        campaign_name,
        description="Outbound to vertical SEO agencies — AI/GEO visibility + KG positioning (seed from repo JSON).",
    )
    if not cid:
        print("Failed to create Campaign.", file=sys.stderr)
        return 1
    print(f"Created Campaign id={cid}")

    crm.add_note_to_record(
        "Campaigns",
        cid,
        "Outreach playbook (API)",
        _playbook_note(campaign_name, str(args.agencies_json.relative_to(ROOT))),
    )

    crm.create_task_for_campaign(
        cid,
        "Finalize message + CTA for this campaign",
        due_review,
        "Align subject/body with CAL_BOOKING_LINK; store approved copy in a Note.",
    )
    crm.create_task_for_campaign(
        cid,
        "Enrich top Leads (email + role)",
        due_enrich,
        "Apollo or manual; convert to Contact when you have a person email.",
    )
    crm.create_task_for_campaign(
        cid,
        "Review reply rate + CRM hygiene",
        due_metrics,
        "Run scripts/zoho_crm_audit.py; archive junk test records.",
    )

    lead_src = (os.getenv("ZOHO_OUTREACH_LEAD_SOURCE") or "").strip() or campaign_name[:120]

    created = 0
    related = 0
    for a in agencies:
        company = (a.get("agency_name") or "").strip() or "Unknown"
        website = (a.get("website") or "").strip()
        vert = (a.get("vertical") or "").strip()
        notes = (a.get("notes") or "").strip()
        desc = f"Vertical: {vert}\nResearch notes: {notes[:500]}" if notes else f"Vertical: {vert}"

        lid = crm.create_lead(
            company=company,
            last_name="-",
            first_name="",
            website=website or None,
            lead_source=lead_src,
            description=desc,
        )
        if not lid:
            print(f"  Lead failed: {company}")
            continue
        created += 1
        if crm.relate_lead_to_campaign(cid, lid):
            related += 1
        else:
            print(f"  (Lead created id={lid} but Campaign link failed — link in CRM UI if needed.)")

    print(f"\nDone. Leads created: {created}; linked to Campaign: {related}. Campaign id={cid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
