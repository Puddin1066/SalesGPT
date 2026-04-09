#!/usr/bin/env python3
"""
Prepare Zoho CRM + send user-research email via Zoho Mail (USE_ZOHO_STACK).

For each eligible signup email from Supabase ``marketing_events`` (signup_free):
  - Find or create a Zoho CRM Contact
  - Set Lead_Source (optional env) and append a CRM Note (what was sent + campaign id)
  - Optionally create a follow-up Task
  - Send one plain-text email via Zoho Mail

Default is dry-run (no CRM writes, no mail). Pass --execute to apply.

Environment:
  - USE_ZOHO_STACK=true, Zoho OAuth + ZOHO_MAIL_FROM / account id (see container)
  - SUPABASE_DATABASE_URL or DATABASE_URL → Supabase Postgres
  - Optional: ZOHO_USER_RESEARCH_LEAD_SOURCE (default: User research — product)
  - Optional: CAL_BOOKING_LINK → substituted as {{booking_link}} in templates

Usage:
  poetry run python scripts/zoho_user_research_outreach.py
  poetry run python scripts/zoho_user_research_outreach.py --execute --limit 20
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_env_file(path: Path, *, override: bool = False) -> None:
    """Minimal KEY=value loader (no multiline values). Optional python-dotenv not required."""
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


# Prefer .env.local for Supabase URLs (often not in committed .env)
_load_env_file(ROOT / ".env", override=False)
_load_env_file(ROOT / ".env.local", override=True)

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".env.local", override=True)
except ImportError:
    pass

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from services.attribution.marketing_events_ingestor import fix_supabase_url
from services.crm.zoho_crm_agent import ZohoCRMAgent
from sqlalchemy import create_engine, text


DEFAULT_SUBJECT = "Quick question about how you're using GemFlush"

DEFAULT_BODY = """Hi {{first_name}},

I'm {{from_name}} from GemFlush. We're talking with early users to understand what prompted you to sign up and what you're trying to accomplish with the product.

If you have two minutes, I'd love your take on:

1) What problem or job were you hoping GemFlush would help with when you registered?
2) Have you used the knowledge graph / Wikidata explorer (or related entity work)? If yes, what were you trying to learn or validate? If not, what blocked you?

Reply with bullets — totally fine.
{% if booking_link %}If you'd rather chat, here's a short calendar link: {{booking_link}}
{% endif %}
Thanks for helping us build something useful.

{{from_name}}
GemFlush

P.S. If you're not the right person for this, who on your team cares most about entity / KG visibility or how you show up in AI-assisted search?
"""


def _strip_jinja_placeholders_for_plaintext(body: str, booking_link: str) -> str:
    """Remove minimal jinja-like lines when booking_link is empty."""
    if not booking_link.strip():
        body = re.sub(
            r"\{%\s*if\s+booking_link\s*%}.*?{%\s*endif\s*%}\s*",
            "",
            body,
            flags=re.DOTALL | re.IGNORECASE,
        )
    else:
        body = body.replace("{% if booking_link %}", "").replace("{% endif %}", "")
    return body


def _render(
    template: str,
    *,
    first_name: str,
    from_name: str,
    booking_link: str,
) -> str:
    t = _strip_jinja_placeholders_for_plaintext(template, booking_link)
    return (
        t.replace("{{first_name}}", first_name)
        .replace("{{from_name}}", from_name)
        .replace("{{booking_link}}", booking_link.strip())
    )


def _email_local_part(email: str) -> str:
    return email.split("@", 1)[0].strip() if "@" in email else email.strip()


def _guess_first_last(email: str) -> Tuple[str, str]:
    local = _email_local_part(email)
    parts = re.split(r"[._\-+]+", local)
    parts = [p for p in parts if p and not p.isdigit()]
    if not parts:
        return "there", "-"
    first = parts[0].title()
    last = parts[1].title() if len(parts) > 1 else "-"
    return first, last


def _should_exclude(email: str, extra_exclude: Set[str]) -> bool:
    e = email.strip().lower()
    if not e or "@" not in e:
        return True
    if e in extra_exclude:
        return True
    local = e.split("@", 1)[0]
    if "j.jayround" in e or "jayround" in local:
        return True
    if "test" in local:
        return True
    return False


def _fetch_signup_emails(supabase_url: str, limit: int) -> List[str]:
    db_url = fix_supabase_url(supabase_url)
    engine = create_engine(db_url, pool_pre_ping=True)
    q = text(
        """
        SELECT DISTINCT LOWER(TRIM(email)) AS email
        FROM marketing_events
        WHERE event_type = 'signup_free'
          AND email IS NOT NULL
          AND TRIM(email) <> ''
        ORDER BY 1
        LIMIT :lim
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(q, {"lim": limit * 3}).fetchall()
    out: List[str] = []
    seen: Set[str] = set()
    for (em,) in rows:
        if not em or em in seen:
            continue
        seen.add(em)
        out.append(em)
        if len(out) >= limit:
            break
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Zoho CRM + Mail user research outreach")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Write to Zoho CRM and send email (default: print plan only, no API calls)",
    )
    parser.add_argument("--limit", type=int, default=50, help="Max recipients after filters")
    parser.add_argument(
        "--follow-up-days",
        type=int,
        default=7,
        help="Due date for CRM follow-up task (days from today, UTC)",
    )
    parser.add_argument("--no-task", action="store_true", help="Skip CRM follow-up task")
    parser.add_argument(
        "--campaign-label",
        default="user_research_kg_wikidata",
        help="Short id stored in CRM note for reporting",
    )
    args = parser.parse_args()
    dry_run = not args.execute

    settings = get_settings()
    if not settings.use_zoho_stack:
        print("Set USE_ZOHO_STACK=true and configure Zoho OAuth + mail.", file=sys.stderr)
        return 1
    if not settings.supabase_database_url:
        print(
            "Supabase URL missing: set SUPABASE_DATABASE_URL or DATABASE_URL (e.g. in .env.local).",
            file=sys.stderr,
        )
        return 1

    lead_source = (os.getenv("ZOHO_USER_RESEARCH_LEAD_SOURCE") or "User research — product").strip()
    booking_link = (settings.cal_booking_link or "").strip()
    from_name = (settings.smartlead_from_name or settings.smartlead_from_email.split("@")[0]).strip()

    body_template = os.getenv("ZOHO_USER_RESEARCH_EMAIL_BODY", DEFAULT_BODY)
    subject_template = os.getenv("ZOHO_USER_RESEARCH_EMAIL_SUBJECT", DEFAULT_SUBJECT)

    emails = _fetch_signup_emails(settings.supabase_database_url, limit=args.limit * 3)
    filtered: List[str] = []
    for em in emails:
        if _should_exclude(em, set()):
            continue
        filtered.append(em)
        if len(filtered) >= args.limit:
            break

    if not filtered:
        print("No eligible signup emails after filters (check marketing_events / exclusions).")
        return 0

    print(f"Eligible recipients: {len(filtered)} (dry_run={dry_run})")
    for em in filtered[:15]:
        print(f"  - {em}")
    if len(filtered) > 15:
        print(f"  ... and {len(filtered) - 15} more")

    if dry_run:
        sample = filtered[0]
        fn, _ = _guess_first_last(sample)
        print("\nSample rendered email (first recipient):")
        print("Subject:", _render(subject_template, first_name=fn, from_name=from_name, booking_link=booking_link))
        print("---")
        print(_render(body_template, first_name=fn, from_name=from_name, booking_link=booking_link))
        print("\nDry-run: no Zoho CRM or Mail calls. Re-run with --execute to apply.")
        return 0

    container = ServiceContainer(settings)
    crm = container.crm
    if not isinstance(crm, ZohoCRMAgent):
        print("CRM is not ZohoCRMAgent; this script only supports Zoho CRM.", file=sys.stderr)
        return 1

    outbound = container.smartlead
    due = (datetime.now(timezone.utc) + timedelta(days=args.follow_up_days)).strftime("%Y-%m-%d")
    note_title = f"User research email — {args.campaign_label}"
    ok_crm = 0
    ok_mail = 0

    for em in filtered:
        first, last = _guess_first_last(em)
        subject = _render(subject_template, first_name=first, from_name=from_name, booking_link=booking_link)
        body = _render(body_template, first_name=first, from_name=from_name, booking_link=booking_link)

        existing = crm.get_contact_by_email(em)
        if existing and existing.get("id"):
            cid = str(existing["id"])
            crm.update_contact_properties(cid, {"Lead_Source": lead_source})
        else:
            cid = crm.create_contact(
                email=em,
                first_name=first,
                last_name=last,
                additional_properties={"Lead_Source": lead_source},
            )
        if not cid:
            print(f"CRM skip (no contact id): {em}")
            continue
        ok_crm += 1

        note_body = (
            f"Campaign: {args.campaign_label}\n"
            f"Sent at (UTC): {datetime.now(timezone.utc).isoformat()}\n"
            f"Subject: {subject}\n\n"
            "Use replies to tag insights (signup motivation, KG/Wikidata usage, blockers)."
        )
        if not crm.add_note_for_contact(cid, note_title, note_body):
            print(f"Warning: note failed for {em} (contact id {cid})")

        if not args.no_task:
            crm.create_task_for_contact(
                cid,
                subject=f"Follow up: user research — {em}",
                due_date=due,
                description="If no reply: one polite bump or close the loop. Capture learnings in a Note.",
            )

        lead_payload = {
            "email": em,
            "first_name": first,
            "last_name": last,
            "custom_fields": {"email_subject": subject, "email_body": body},
        }
        if outbound.add_leads_to_campaign(1, [lead_payload]):
            ok_mail += 1
        else:
            print(f"Mail send failed: {em}")

    print(f"\nDone. CRM contacts touched: {ok_crm}; emails sent: {ok_mail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
