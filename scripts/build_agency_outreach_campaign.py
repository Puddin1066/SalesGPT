#!/usr/bin/env python3
"""
Build a semi-automated outreach campaign + custom emails from data/outreach CSV.

Reads enriched agency rows (research notes, angles, hooks) and emits a JSON campaign
suitable for human review, CRM import, or Smartlead/Zoho merge fields.

No live Apollo/OpenAI calls — all copy is deterministic from your data file (mock-safe).

Usage:
  python scripts/build_agency_outreach_campaign.py
  python scripts/build_agency_outreach_campaign.py --csv data/outreach/seo_vertical_agencies.csv \\
      --out data/outreach/campaigns/seo_vertical_agencies_campaign.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root on path (for optional dotenv)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERTICAL_COPY = {
    "legal": {
        "client_noun": "law firm clients",
        "vertical_phrase": "legal / PI and litigation markets",
    },
    "medical": {
        "client_noun": "healthcare and medical practice clients",
        "vertical_phrase": "healthcare marketing",
    },
    "real_estate": {
        "client_noun": "real estate teams and brokerages",
        "vertical_phrase": "real estate SEO",
    },
    "legal_au": {
        "client_noun": "Australian law firm clients",
        "vertical_phrase": "AU legal search",
    },
}


def _strip_angle_prefix(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^(Pitch|Offer|Partner pitch|Enterprise pitch|Channel partner|Integration or OEM):\s*",
               "", t, flags=re.IGNORECASE)
    return t.strip()


def _short(text: str, max_len: int = 140) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rsplit(" ", 1)[0] + "…"


def _domain(website: str) -> str:
    w = website.strip().lower().rstrip("/")
    w = re.sub(r"^https?://(www\.)?", "", w)
    return w.split("/")[0] if w else ""


def load_agencies_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("agency_name", "").strip():
                continue
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def build_sequence(
    row: Dict[str, str],
    sender_name: str,
    sender_title: str,
    cta_url: str,
    calendar_url: str,
) -> Dict[str, Any]:
    vertical = row.get("vertical") or "legal"
    vc = VERTICAL_COPY.get(vertical, VERTICAL_COPY["legal"])
    agency = row["agency_name"]
    website = row.get("website", "")
    notes = row.get("notes", "")
    hq = row.get("hq_region", "")
    leadership = row.get("leadership_snapshot", "")
    hooks = row.get("portfolio_public_hooks", "")
    services = row.get("core_services_tagged", "")
    ai_signals = row.get("ai_geo_answer_engine_signals", "")
    angle = _strip_angle_prefix(row.get("gemflush_outreach_angle", ""))
    wikidata_angle = row.get("wikidata_knowledge_graph_angle", "").strip()
    source_date = row.get("enrichment_source_date", "")

    notes_short = _short(notes, 120)
    angle_sentence = angle if angle else (
        f"we'd explore how GemFlush could add comparative AI-discoverability reporting for "
        f"accounts you already run in {vc['vertical_phrase']}."
    )
    wiki_sentence = (
        wikidata_angle
        if wikidata_angle
        else (
            "Structured open knowledge (e.g., Wikidata-aligned entity work) is one lever we "
            "often map when clients care about ambiguous brands and YMYL trust signals."
        )
    )

    # --- Email 1 ---
    subj_a = f"{agency} — AI visibility layer for your {vc['client_noun']}?"
    subj_b = f"Entity + AI-surface reporting (GemFlush × {agency})"

    body_1 = f"""Hi {{{{first_name}}}},

I am reaching out because {agency} is clearly focused on {_short(notes, 100)} — i.e., buyers who already invest in performance marketing and SEO.

GemFlush (gemflush.com) is a B2B visibility-audit product: **objective, comparative** signals for how businesses show up in AI-assisted discovery and related surfaces versus competitors — useful when “blue links” are no longer the whole story, especially for {vc['client_noun']}.

Why you specifically: {angle_sentence}

Knowledge-graph angle: {_short(wiki_sentence, 220)}

We are not pitching a rip-and-replace. Typical fits are **white-label audits**, a **data layer** strategists reuse in QBRs, or an **API-friendly** complement to the stack you already sell.

If it is worth 15 minutes, I can share a one-pager or a sample partner workflow. You can also grab context here: {cta_url}
{f"Book time here: {calendar_url}" if calendar_url else ""}

Best,
{sender_name}
{sender_title}

P.S. The bullets above come from **public research only** ({_short(source_date, 80) if source_date else "verify before citing in outbound"}). We are **not** claiming to have run a live GemFlush audit on your site unless we explicitly say so in a later thread.

---
Unsubscribe: reply "unsubscribe"
"""

    # --- Email 2 (follow-up) ---
    subj_2a = f"Follow-up: GemFlush + {agency} ({_domain(website)})"
    subj_2b = f"One angle: { _short(ai_signals, 50) or 'AI search + entities' }"

    leadership_line = (
        f"Public leadership notes we have on file: {_short(leadership, 160)}"
        if leadership
        else "If you point me to the right owner (partnerships / SEO product), I will keep this tight."
    )
    hooks_line = (
        f"\nPortfolio hooks (verify before naming in mail): {_short(hooks, 200)}"
        if hooks
        else ""
    )

    body_2 = f"""Hi {{{{first_name}}}},

Circling back once on GemFlush + {agency}.

{leadership_line}{hooks_line}

Services tag snapshot from our sheet: {_short(services, 160) if services else "SEO/digital — details on your site."}

If **{ _short(ai_signals, 120) if ai_signals else "AI Overviews / LLM citation" }** is on your roadmap for {vc['client_noun']}, GemFlush is meant to make that **measurable** (comparative, evidence-first) without forcing a new CMS.

Reply with a “yes” and I will send a concise partner outline + sample deliverable structure.

Best,
{sender_name}
"""

    # --- Email 3 (break-up) ---
    subj_3a = f"Closing the loop — GemFlush × {agency}"
    subj_3b = f"Last note + checklist ({agency})"

    body_3 = f"""Hi {{{{first_name}}}},

Last email from me on this thread.

If timing was wrong, no problem. If helpful, here is a **free, no-call** takeaway you can use internally: when clients ask whether they “show up in AI,” separate **(a)** classic rankings from **(b)** entity clarity + **(c)** comparative benchmarks versus named competitors. GemFlush is built around (b)+(c) with exportable framing for agencies.

Overview: {cta_url}

Thanks for the work you do in {vc['vertical_phrase']} — {hq if hq else "your market"}.

Best,
{sender_name}
"""

    return {
        "merge_fields_expected": ["first_name", "last_name", "email", "company_name"],
        "merge_field_hints": {
            "company_name": agency,
            "first_name": "REQUIRED_APOLLO_OR_MANUAL",
            "email": "REQUIRED_APOLLO_OR_MANUAL",
        },
        "emails": [
            {
                "step": 1,
                "delay_days_after_previous": 0,
                "subject_a": subj_a,
                "subject_b": subj_b,
                "body": body_1.strip(),
            },
            {
                "step": 2,
                "delay_days_after_previous": 4,
                "subject_a": subj_2a,
                "subject_b": subj_2b.strip(),
                "body": body_2.strip(),
            },
            {
                "step": 3,
                "delay_days_after_previous": 5,
                "subject_a": subj_3a,
                "subject_b": subj_3b,
                "body": body_3.strip(),
            },
        ],
    }


def build_campaign(
    rows: List[Dict[str, str]],
    *,
    sender_name: str,
    sender_title: str,
    cta_url: str,
    calendar_url: str,
    source_csv: str,
) -> Dict[str, Any]:
    contacts = []
    for i, row in enumerate(rows):
        seq = build_sequence(row, sender_name, sender_title, cta_url, calendar_url)
        contacts.append(
            {
                "contact_id": f"seo_agency_{i+1:03d}",
                "vertical": row.get("vertical", ""),
                "agency_name": row["agency_name"],
                "website": row.get("website", ""),
                "domain": _domain(row.get("website", "")),
                "research_notes": row.get("notes", ""),
                "hq_region": row.get("hq_region", ""),
                "leadership_snapshot": row.get("leadership_snapshot", ""),
                "portfolio_public_hooks": row.get("portfolio_public_hooks", ""),
                "core_services_tagged": row.get("core_services_tagged", ""),
                "ai_geo_signals": row.get("ai_geo_answer_engine_signals", ""),
                "gemflush_outreach_angle": row.get("gemflush_outreach_angle", ""),
                "wikidata_angle": row.get("wikidata_knowledge_graph_angle", ""),
                "enrichment_source_date": row.get("enrichment_source_date", ""),
                "status": "needs_contact_email_apollo_or_manual",
                **seq,
            }
        )

    return {
        "campaign_id": "gemflush_seo_agency_partner_2026q2",
        "product": "GemFlush — AI-assisted visibility / comparative discoverability audits (B2B SaaS)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "csv": source_csv,
            "disclaimer": "Research-only rows; verify hooks and names before sending. No Apollo/API data in this artifact.",
        },
        "sender_defaults": {
            "name": sender_name,
            "title": sender_title,
            "cta_url": cta_url,
            "calendar_url": calendar_url or None,
        },
        "sequence_template": [
            {"step": 1, "delay_days_after_previous": 0},
            {"step": 2, "delay_days_after_previous": 4},
            {"step": 3, "delay_days_after_previous": 5},
        ],
        "contacts": contacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GemFlush SEO-agency partner campaign from CSV.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "data" / "outreach" / "seo_vertical_agencies.csv",
        help="Path to enriched agency CSV",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "outreach" / "campaigns" / "seo_vertical_agencies_campaign.json",
        help="Output JSON path",
    )
    parser.add_argument("--sender-name", default=os.getenv("GEMFLUSH_OUTREACH_SENDER_NAME", "[Your name]"))
    parser.add_argument("--sender-title", default=os.getenv("GEMFLUSH_OUTREACH_SENDER_TITLE", "GemFlush"))
    parser.add_argument(
        "--cta-url",
        default=os.getenv("GEMFLUSH_CAMPAIGN_URL", "https://gemflush.com"),
    )
    parser.add_argument(
        "--calendar-url",
        default=os.getenv("GEMFLUSH_CALENDAR_URL", ""),
    )
    args = parser.parse_args()

    if not args.csv.is_file():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    rows = load_agencies_csv(args.csv)
    campaign = build_campaign(
        rows,
        sender_name=args.sender_name,
        sender_title=args.sender_title,
        cta_url=args.cta_url,
        calendar_url=args.calendar_url,
        source_csv=(
            str(args.csv.relative_to(ROOT))
            if str(args.csv).startswith(str(ROOT))
            else str(args.csv)
        ),
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(campaign['contacts'])} contacts to {args.out}")


if __name__ == "__main__":
    main()
