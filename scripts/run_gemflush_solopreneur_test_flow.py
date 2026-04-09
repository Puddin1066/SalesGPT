#!/usr/bin/env python3
"""
End-to-end GemFlush outreach test for a single contact (no Apollo).

1) MOCK enrichment from CLI / seed profile (clearly labeled; not live API data).
2) Composes a plain-text email tailored to the persona.
3) Sends via first available transport:
   - Zoho Mail API when USE_ZOHO_STACK=true and OAuth is configured (and not USE_MOCK_APIS)
   - Gmail SMTP when GMAIL_MAIL + GMAIL_APP_PASSWORD are set

Use --dry-run to print only (no send).

Example:
  python scripts/run_gemflush_solopreneur_test_flow.py --dry-run
  python scripts/run_gemflush_solopreneur_test_flow.py \\
    --to j.jayround@gmail.com --first-name J \\
    --persona "solo entrepreneur focused on AI/IP therapeutic development"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_env_file(path: Path, *, override: bool = False) -> None:
    """Minimal KEY=VALUE loader so we work without python-dotenv installed."""
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


# .env.local wins over .env (match common tooling)
load_env_file(ROOT / ".env", override=False)
load_env_file(ROOT / ".env.local", override=True)

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env.local", override=True)
    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass


def mock_enrich_profile(
    *,
    email: str,
    first_name: str,
    persona: str,
    company_hint: str,
    website: str,
) -> Dict[str, Any]:
    """Synthetic enrichment for pipeline testing — NOT Apollo or live scrapers."""
    return {
        "enrichment_source": "MOCK_MANUAL_SEED",
        "enriched_at": datetime.now(timezone.utc).isoformat(),
        "email": email,
        "first_name": first_name,
        "persona_summary": persona,
        "company_name": company_hint or "Independent / stealth therapeutic venture",
        "website": website or "",
        "signals_used": [
            "User-supplied: solo operator",
            "User-supplied: AI + IP + therapeutic development focus",
            "Inferred: high-stakes discovery (investors, partners, acquirers) increasingly use AI assistants",
        ],
        "gemflush_hypothesis": (
            "Objective visibility vs named comparables (peers, programs, hubs) on AI-assisted "
            "surfaces may matter as much as classic SEO for capital and partnership conversations."
        ),
    }


def compose_email(
    profile: Dict[str, Any],
    *,
    sender_name: str,
    sender_title: str,
    cta_url: str,
    reply_to: str,
) -> Tuple[str, str]:
    fn = profile["first_name"] or "there"
    company = profile.get("company_name") or "your work"
    default_stealth = "Independent / stealth therapeutic venture"
    if company == default_stealth:
        subject_focus = "your AI/IP therapeutic work"
    else:
        subject_focus = company

    subject = f"{fn}, quick question — AI-visible footprint for {subject_focus}?"

    reply_line = reply_to if reply_to and "@" in reply_to else "this address (reply above)"

    sig_second = (
        ""
        if (sender_title.lower() == sender_name.lower() or not sender_title.strip())
        else f"\n{sender_title}"
    )

    body = f"""Hi {fn},

I'm writing because you're building in a corner of biotech where credibility and discoverability compound: AI-driven therapeutic development plus IP — and often, as a solo founder, you're the brand people need to find.

GemFlush (gemflush.com) is a B2B visibility-audit product. It focuses on objective, comparative signals: how a business or program shows up in AI-assisted discovery and related surfaces versus competitors or peer narratives — not vanity rankings, but evidence you can use in investor updates, partner conversations, and web positioning.

Why this might matter for you: when someone asks an assistant for background on a modality, a program, or "who is working on X," answers skew toward entities that are unambiguous and well-represented in open and structured contexts. For therapeutics, that overlaps with how orgs, assets, and people are disambiguated — the same class of problem GemFlush helps teams measure before they pour months into content.

I'm not claiming we've audited your properties; this is a single, direct note to see if a short benchmark (you vs a handful of comps you care about) would be useful. If yes, reply with your priority comparison set (2–3 names or links) and I'll keep the first pass tight.

More context: {cta_url}

Best,
{sender_name}{sig_second}

(Reply to: {reply_line})

---
Unsubscribe: reply "unsubscribe"
"""
    return subject.strip(), body.strip()


def save_artifact(profile: Dict[str, Any], subject: str, body: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "meta": {
            "artifact": "single_contact_test",
            "disclaimer": "Enrichment is MOCK/manual seed only.",
        },
        "profile": profile,
        "email": {"subject": subject, "body": body},
    }
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def try_zoho_primary_from_address() -> str:
    """
    When USE_ZOHO_STACK is enabled, infer sender from Zoho Mail GET /api/accounts
    if ZOHO_MAIL_FROM / OUTBOUND_FROM_EMAIL were not set.
    """
    if os.getenv("USE_ZOHO_STACK", "false").lower() != "true":
        return ""
    if os.getenv("USE_MOCK_APIS", "false").lower() == "true":
        return ""
    try:
        from services.outbound.zoho_mail_agent import ZohoMailAgent

        agent = ZohoMailAgent()
        if agent.access_token.startswith("mock"):
            return ""
        accounts = agent.list_accounts()
        if not accounts:
            return ""
        # Prefer configured account id match; else first account with an email
        want_id = (os.getenv("ZOHO_MAIL_ACCOUNT_ID") or "").strip()
        for acc in accounts:
            if want_id and str(acc.get("accountId", "")) != want_id:
                continue
            addr = (acc.get("primaryEmailAddress") or acc.get("emailAddress") or "").strip()
            if addr:
                return addr
        acc = accounts[0]
        return (acc.get("primaryEmailAddress") or acc.get("emailAddress") or "").strip()
    except Exception as e:
        print(f"Could not infer Zoho Mail from-address: {e}", file=sys.stderr)
        return ""


def send_zoho(subject: str, body: str, to_email: str, from_email: str) -> Tuple[bool, str]:
    from services.outbound.zoho_mail_agent import ZohoMailAgent

    use_mock = os.getenv("USE_MOCK_APIS", "false").lower() == "true"
    if use_mock:
        return False, "skipped: USE_MOCK_APIS=true (would not deliver a real message)"

    try:
        agent = ZohoMailAgent()
    except Exception as e:
        return False, f"zoho init failed: {e}"

    if agent.access_token.startswith("mock"):
        return False, "skipped: Zoho mock token"

    ok = agent.send_message(
        from_address=from_email,
        to_address=to_email,
        subject=subject,
        content=body,
        mail_format="plaintext",
    )
    return ok, "zoho_mail_api" if ok else "zoho send_message returned False"


def send_gmail_smtp(subject: str, body: str, to_email: str) -> Tuple[bool, str]:
    sender = os.getenv("GMAIL_MAIL", "").strip()
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not sender or not password:
        return False, "missing GMAIL_MAIL or GMAIL_APP_PASSWORD"

    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True, "gmail_smtp"
    except Exception as e:
        return False, f"gmail_smtp error: {e}"


def main() -> None:
    p = argparse.ArgumentParser(description="GemFlush single-contact test flow (mock enrich + send).")
    p.add_argument("--to", default="j.jayround@gmail.com", help="Recipient email")
    p.add_argument("--first-name", default="J", help="First name for greeting")
    p.add_argument(
        "--persona",
        default="Solo entrepreneur focused on AI/IP therapeutic development.",
        help="One-line persona (mock enrichment)",
    )
    p.add_argument("--company", default="", help="Optional company or project label")
    p.add_argument("--website", default="", help="Optional website URL")
    p.add_argument("--dry-run", action="store_true", help="Print only; do not send")
    p.add_argument(
        "--artifact",
        type=Path,
        default=ROOT / "data" / "outreach" / "campaigns" / "solopreneur_test_j_jayround.json",
        help="Write profile + email JSON here",
    )
    p.add_argument(
        "--from-email",
        default="",
        help="Override sender (must match Zoho mailbox or Gmail account used to send)",
    )
    args = p.parse_args()

    from_email = (
        args.from_email.strip()
        or os.getenv("OUTBOUND_FROM_EMAIL")
        or os.getenv("ZOHO_MAIL_FROM")
        or os.getenv("SMARTLEAD_FROM_EMAIL")
        or os.getenv("GMAIL_MAIL")
        or ""
    ).strip()
    if not from_email:
        from_email = try_zoho_primary_from_address()

    sender_name = (
        os.getenv("OUTBOUND_FROM_NAME")
        or os.getenv("ZOHO_MAIL_FROM_NAME")
        or os.getenv("SMARTLEAD_FROM_NAME")
        or "GemFlush"
    ).strip()
    sender_title = os.getenv("GEMFLUSH_OUTREACH_SENDER_TITLE", "GemFlush").strip()
    cta_url = os.getenv("GEMFLUSH_CAMPAIGN_URL", "https://gemflush.com").strip()
    reply_to = (
        os.getenv("OUTBOUND_REPLY_TO") or os.getenv("ZOHO_MAIL_REPLY_TO") or from_email
    ).strip()

    profile = mock_enrich_profile(
        email=args.to,
        first_name=args.first_name,
        persona=args.persona,
        company_hint=args.company,
        website=args.website,
    )
    subject, body = compose_email(
        profile,
        sender_name=sender_name,
        sender_title=sender_title,
        cta_url=cta_url,
        reply_to=reply_to,
    )

    save_artifact(profile, subject, body, args.artifact)

    if not args.dry_run and not from_email:
        print(
            "ERROR: No sender address. Set ZOHO_MAIL_FROM or OUTBOUND_FROM_EMAIL, "
            "or ensure USE_ZOHO_STACK=true with valid Zoho OAuth so the script can read "
            "primaryEmailAddress from Zoho Mail /api/accounts.",
            file=sys.stderr,
        )
        print("\nPreview below; artifact written for manual send if needed.\n")

    print("=== MOCK ENRICHMENT (not Apollo / not live scrape) ===")
    print(json.dumps(profile, indent=2))
    print("\n=== EMAIL ===")
    print(f"Subject: {subject}\n")
    print(body)
    print(f"\n=== Artifact: {args.artifact} ===")

    if args.dry_run:
        print("\nDry run: no send.")
        return

    if not from_email:
        sys.exit(1)

    use_zoho_stack = os.getenv("USE_ZOHO_STACK", "false").lower() == "true"
    if use_zoho_stack:
        ok, detail = send_zoho(subject, body, args.to, from_email)
        print(f"\nSend attempt (Zoho): ok={ok} detail={detail}")
        if ok:
            return
        print("Zoho did not send; trying Gmail SMTP if configured...", file=sys.stderr)

    ok, detail = send_gmail_smtp(subject, body, args.to)
    print(f"\nSend attempt (Gmail SMTP): ok={ok} detail={detail}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
