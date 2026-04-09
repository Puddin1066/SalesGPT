#!/usr/bin/env python3
"""
Identify the GEMflush "team space" in Zoho Cliq (Teams + Channels) via API, optionally
create a standard layout, post a launch checklist, and emit a JSON manifest for GTM.

Requires the SAME Zoho OAuth app as CRM/Mail, but Cliq scopes must be granted on the
refresh token. Append to ZOHO_OAUTH_SCOPES (then re-consent → new refresh token):

  ZohoCliq.Teams.READ,ZohoCliq.Teams.CREATE,
  ZohoCliq.Channels.READ,ZohoCliq.Channels.CREATE,
  ZohoCliq.messages.CREATE

(Optional EU/IN: set ZOHO_CLIQ_API_BASE=https://cliq.zoho.eu )

Usage:
  poetry run python scripts/zoho_gemflush_workspace_setup.py
  poetry run python scripts/zoho_gemflush_workspace_setup.py --bootstrap
  poetry run python scripts/zoho_gemflush_workspace_setup.py --bootstrap --post-welcome
  poetry run python scripts/zoho_gemflush_workspace_setup.py --write-manifest
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".env.local", override=True)
except ImportError:
    pass

from salesgpt.config import get_settings
from services.crm.zoho_crm_agent import ZohoCRMAgent
from services.zoho.cliq_client import ZohoCliqClient
from services.zoho.oauth_helper import refresh_zoho_access_token

RECOMMENDED_CLIQ_SCOPES = (
    "ZohoCliq.Teams.READ,ZohoCliq.Teams.CREATE,"
    "ZohoCliq.Channels.READ,ZohoCliq.Channels.CREATE,ZohoCliq.messages.CREATE"
)

TEAM_NAME_DEFAULT = "GEMflush GTM"
# Display names as Zoho shows them (unique_name is derived, e.g. gemflush-sales).
CHANNELS_DEFAULT = (
    ("GEMflush-Sales", "Pipeline, replies, CRM updates, call notes."),
    ("GEMflush-Marketing", "Campaign copy, sends, segments, landing + event tracking."),
    ("GEMflush-Launch", "Cross-functional: calendar, blockers, ship checklist."),
)


def _matches_gemflush(name: Optional[str], description: Optional[str] = None) -> bool:
    blob = f"{name or ''} {description or ''}".lower()
    return "gemflush" in blob or "gem flush" in blob


def _print_cliq_scope_help() -> None:
    print(
        "\nCliq API returned 401/403. Add Cliq scopes to your Zoho OAuth client, then:\n"
        "  1) Put this (plus your existing scopes) in ZOHO_OAUTH_SCOPES:\n"
        f"     {RECOMMENDED_CLIQ_SCOPES}\n"
        "  2) Run: python3 scripts/print_zoho_oauth_authorize_url.py\n"
        "  3) Exchange the new code → update ZOHO_REFRESH_TOKEN\n"
        "  4) Re-run this script.\n"
    )


def _cliq_list_teams(client: ZohoCliqClient) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    merged: Dict[str, Dict[str, Any]] = {}
    last_err: Optional[str] = None
    for joined in ("false", "true"):
        r = client.get("/api/v2/teams", params={"joined": joined})
        if r.status_code in (401, 403):
            return [], r.text[:300]
        if r.status_code != 200:
            last_err = r.text[:300]
            continue
        data = r.json()
        teams = data.get("teams") or []
        if not isinstance(teams, list):
            last_err = str(data)[:300]
            continue
        for t in teams:
            tid = str(t.get("team_id", ""))
            if tid:
                merged[tid] = t
    return list(merged.values()), last_err


def _cliq_list_channels(client: ZohoCliqClient) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    r = client.get("/api/v2/channels", params={"joined": "true"})
    if r.status_code in (401, 403):
        return [], r.text[:300]
    if r.status_code != 200:
        return [], r.text[:300]
    data = r.json()
    ch = data.get("channels") or []
    if not isinstance(ch, list):
        return [], str(data)[:300]
    return ch, None


def _pick_gemflush_team(teams: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    exact = [t for t in teams if (t.get("name") or "").strip().lower() in ("gemflush", "gemflush gtm")]
    if exact:
        return exact[0]
    fuzzy = [t for t in teams if _matches_gemflush(t.get("name"), t.get("description"))]
    return fuzzy[0] if fuzzy else None


def _pick_gemflush_channels(channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [c for c in channels if _matches_gemflush(c.get("name"), c.get("description"))]


def _crm_current_user(crm: ZohoCRMAgent) -> Dict[str, Any]:
    r = crm._request("GET", f"{crm.crm_api_base}/users", params={"type": "CurrentUser"})
    if r.status_code != 200:
        return {"error": r.status_code, "body": r.text[:500]}
    data = r.json()
    users = data.get("users") or data.get("data")
    if isinstance(users, list) and users:
        u = users[0]
        return {
            "id": u.get("id"),
            "email": u.get("email"),
            "name": u.get("full_name") or u.get("name"),
        }
    return {"error": "unexpected_shape", "raw": str(data)[:400]}


def _launch_manifest(
    *,
    cliq_team: Optional[Dict[str, Any]],
    cliq_channels: List[Dict[str, Any]],
    crm_user: Dict[str, Any],
    settings_summary: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cliq": {
            "api_base": os.getenv("ZOHO_CLIQ_API_BASE", "https://cliq.zoho.com"),
            "gemflush_team": cliq_team,
            "gemflush_related_channels": cliq_channels,
            "recommended_env_after_bootstrap": {
                "GEMFLUSH_CLIQ_TEAM_ID": str(cliq_team.get("team_id", ""))
                if cliq_team
                else "",
                "GEMFLUSH_CLIQ_CHANNEL_SALES": next(
                    (
                        str(c.get("channel_id", ""))
                        for c in cliq_channels
                        if "sales" in (c.get("name") or "").lower()
                    ),
                    "",
                ),
                "GEMFLUSH_CLIQ_CHANNEL_MARKETING": next(
                    (
                        str(c.get("channel_id", ""))
                        for c in cliq_channels
                        if "marketing" in (c.get("name") or "").lower()
                    ),
                    "",
                ),
            },
        },
        "crm_mail_stack": settings_summary,
        "crm_operator": crm_user,
        "gtm_launch_parameters": {
            "objectives": [
                "Single source of truth for ICP, offer, and calendar link in CRM + Cliq pins.",
                "Contact/Lead hygiene (Lead Source, Campaign name, owner).",
                "Outbound: Zoho Mail + scripts (USE_ZOHO_STACK) or Smartlead; log touches in CRM Notes.",
                "Inbound: forms → CRM; Supabase events → marketing_events → ingestors.",
            ],
            "salesgpt_repo_tools": [
                "scripts/zoho_user_research_outreach.py — CRM note + Zoho Mail send",
                "scripts/zoho_crm_audit.py — junk / duplicate contact heuristics",
                "scripts/build_zoho_outreach_email_templates.py — CRM template JSON",
                "services/crm/zoho_crm_agent.py — Contacts, Deals, Notes, Tasks",
            ],
            "zoho_console_manual": [
                "CRM: Lead Source / Campaign picklists aligned with Supabase event names",
                "CRM: Email templates (Contacts) from data/outreach/zoho_crm_email_templates.json",
                "Cliq: pin message with CAL_BOOKING_LINK + pipeline stages",
                "Optional: Zoho Campaigns / Zoho Social — separate OAuth products",
            ],
        },
    }


def _welcome_message() -> str:
    return """GEMflush GTM — launch checklist (pin this)

Sales
- CRM: stage definitions + Lead Source for each outbound source
- Daily: unanswered replies, call notes on Contact, next-step Task

Marketing
- Copy + segment in Cliq #gemflush-marketing → send via Zoho Mail / campaign script
- Landing + events: confirm Supabase → marketing_events → CRM ingestors

Shared
- Booking link in CRM templates and footers
- Repo: scripts/zoho_user_research_outreach.py, zoho_crm_audit.py

(Add your CAL_BOOKING_LINK and pipeline links below in a thread.)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="GEMflush Zoho Cliq + CRM workspace discovery/setup")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create default Cliq team + channels if none match GEMflush",
    )
    parser.add_argument(
        "--post-welcome",
        action="store_true",
        help="Post launch checklist to #gemflush-launch (needs ZohoCliq.messages.CREATE)",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help=f"Write {ROOT / 'data' / 'zoho' / 'gemflush_workspace_manifest.json'}",
    )
    args = parser.parse_args()

    cid = os.getenv("ZOHO_CLIENT_ID", "").strip()
    sec = os.getenv("ZOHO_CLIENT_SECRET", "").strip()
    refresh = os.getenv("ZOHO_REFRESH_TOKEN", "").strip()
    accounts = (os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "https://accounts.zoho.com").rstrip("/")

    if not all([cid, sec, refresh]):
        print("Set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN", file=sys.stderr)
        return 1

    tok = refresh_zoho_access_token(cid, sec, refresh, accounts_domain=accounts)
    if not tok or not tok.get("access_token"):
        print("Could not refresh Zoho access token.", file=sys.stderr)
        return 1

    access = tok["access_token"]
    cliq = ZohoCliqClient(access)
    teams, terr = _cliq_list_teams(cliq)
    if terr and not teams:
        print(f"Cliq teams list failed: {terr}")
        _print_cliq_scope_help()
        teams = []

    channels, cerr = _cliq_list_channels(cliq)
    if cerr and not channels:
        print(f"Cliq channels list failed: {cerr}")
        _print_cliq_scope_help()
        channels = []

    gem_team = _pick_gemflush_team(teams) if teams else None
    gem_ch = _pick_gemflush_channels(channels) if channels else []

    print("=== Zoho Cliq: GEMflush team space ===\n")
    if gem_team:
        print(
            f"Team match: {gem_team.get('name')!r}  team_id={gem_team.get('team_id')}  "
            f"members={gem_team.get('participant_count')}"
        )
    else:
        print("No GEMflush-named team found in Cliq API results (check scopes or create in UI).")

    if gem_ch:
        print(f"\nMatching channels ({len(gem_ch)}):")
        for c in gem_ch:
            print(
                f"  - {c.get('name')!r}  channel_id={c.get('channel_id')}  "
                f"unique_name={c.get('unique_name')}"
            )
    else:
        print("\nNo GEMflush-named channels in joined=true list.")

    created: Dict[str, Any] = {}

    if args.bootstrap and not gem_team:
        tr = cliq.post(
            "/api/v2/teams",
            json={
                "name": TEAM_NAME_DEFAULT,
                "description": "GEMflush go-to-market: sales, marketing, launch coordination.",
            },
        )
        if tr.status_code not in (200, 201):
            print(f"\nBootstrap: create team failed HTTP {tr.status_code}: {tr.text[:500]}")
        else:
            body = tr.json()
            created["team"] = body
            gem_team = body
            print(f"\nBootstrap: created team {body.get('name')!r} team_id={body.get('team_id')}")

    tid = str(gem_team.get("team_id", "")) if gem_team else ""

    if args.bootstrap and tid:
        existing_unique = {
            (c.get("unique_name") or "").lower() for c in channels if c.get("unique_name")
        }
        for display_name, desc in CHANNELS_DEFAULT:
            hint = display_name.lower().replace(" ", "")
            if hint in existing_unique:
                print(f"Bootstrap: channel {hint!r} already exists — skip")
                continue
            cr = cliq.post(
                "/api/v2/channels",
                json={
                    "name": display_name,
                    "description": desc,
                    "level": "team",
                    "team_ids": [tid],
                },
            )
            if cr.status_code not in (200, 201):
                print(
                    f"Bootstrap: create channel {display_name!r} failed HTTP {cr.status_code}: {cr.text[:400]}"
                )
            else:
                chb = cr.json()
                created.setdefault("channels", []).append(chb)
                print(f"Bootstrap: created channel {chb.get('name')!r} channel_id={chb.get('channel_id')}")
                channels.append(chb)
                un = (chb.get("unique_name") or "").lower()
                if un:
                    existing_unique.add(un)

    gem_ch = _pick_gemflush_channels(channels)

    if args.post_welcome:
        launch_ch = next(
            (c for c in channels if "launch" in (c.get("unique_name") or c.get("name") or "").lower()),
            None,
        )
        if not launch_ch:
            launch_ch = next(
                (c for c in channels if "gemflush" in (c.get("name") or "").lower()),
                gem_ch[0] if gem_ch else None,
            )
        cid_ch = (launch_ch or {}).get("channel_id")
        if not cid_ch:
            print("\n--post-welcome: no target channel (run --bootstrap or join a GEMflush channel).")
        else:
            pr = cliq.post(
                f"/api/v2/channels/{cid_ch}/message",
                json={"text": _welcome_message(), "sync_message": True},
            )
            if pr.status_code not in (200, 201):
                print(f"\nPost welcome failed HTTP {pr.status_code}: {pr.text[:400]}")
                _print_cliq_scope_help()
            else:
                print(f"\nPosted welcome checklist to channel_id={cid_ch}")

    # CRM operator + settings snapshot (best-effort)
    settings = get_settings()
    try:
        crm = ZohoCRMAgent()
        crm_user = _crm_current_user(crm)
    except Exception as e:
        crm_user = {"error": str(e)}

    settings_summary = {
        "use_zoho_stack": settings.use_zoho_stack,
        "zoho_mail_from": settings.smartlead_from_email,
        "zoho_crm_api_base": settings.zoho_crm_api_base,
        "cal_booking_link_set": bool(settings.cal_booking_link),
        "supabase_database_url_set": bool(settings.supabase_database_url),
    }

    manifest = _launch_manifest(
        cliq_team=gem_team,
        cliq_channels=gem_ch,
        crm_user=crm_user,
        settings_summary=settings_summary,
    )
    manifest["cliq"]["bootstrap_actions"] = created

    out_path = ROOT / "data" / "zoho" / "gemflush_workspace_manifest.json"
    if args.write_manifest:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        print(f"\nWrote manifest: {out_path}")

    print("\n=== Summary ===")
    print(json.dumps(manifest.get("gtm_launch_parameters", {}), indent=2, default=str)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
