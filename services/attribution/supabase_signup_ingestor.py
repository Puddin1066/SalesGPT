"""
Supabase Signup Ingestor.

Pulls recent signups from Supabase Auth (auth.users) and marks matching leads
in the SalesGPT state DB as free signups (by email match).

Design:
- Read-only against Supabase, write to SalesGPT DB.
- Idempotent: only sets free_signup_at if missing.
- Safe for free-tier ramp: can be run as a cron job.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, text


@dataclass(frozen=True)
class SupabaseSignup:
    email: str
    created_at: datetime


class SupabaseSignupIngestor:
    def __init__(self, supabase_database_url: str, state_manager):
        self.supabase_database_url = supabase_database_url
        self.state = state_manager

    def fetch_recent_signups(self, days_back: int = 30, limit: int = 5000) -> List[SupabaseSignup]:
        """
        Fetch recent auth.users signups from Supabase.

        Notes:
        - Requires a DB user with SELECT access to auth.users (Supabase service role / elevated role).
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

        engine = create_engine(self.supabase_database_url, pool_pre_ping=True)
        query = text(
            """
            SELECT email, created_at
            FROM auth.users
            WHERE email IS NOT NULL
              AND created_at >= :cutoff
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )

        signups: List[SupabaseSignup] = []
        with engine.connect() as conn:
            rows = conn.execute(query, {"cutoff": cutoff, "limit": limit}).fetchall()

        for email, created_at in rows:
            if not email:
                continue
            # created_at may be tz-aware or naive depending on driver
            if isinstance(created_at, datetime) and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            signups.append(SupabaseSignup(email=email.strip().lower(), created_at=created_at))

        return signups

    def sync_recent_signups(self, days_back: int = 30, limit: int = 5000) -> Tuple[int, int]:
        """
        Mark matching leads in SalesGPT DB with free_signup_at.

        Returns:
            (matched_count, updated_count)
        """
        signups = self.fetch_recent_signups(days_back=days_back, limit=limit)
        matched = 0
        updated = 0

        for s in signups:
            lead = self.state.get_lead_state(s.email)
            if not lead:
                continue
            matched += 1

            if lead.get("free_signup_at"):
                continue

            self.state.update_lead_state(
                s.email,
                {
                    "free_signup_at": s.created_at,
                    "status": lead.get("status") or "signed_up",
                },
            )
            updated += 1

        return matched, updated


