"""
Marketing Events Ingestor.

Pulls unprocessed events from Supabase marketing_events table and updates
SalesGPT lead DB with conversion signals (signup_free, paid_pro, email_reply, activated).

Design:
- Read-only against Supabase, write to SalesGPT DB.
- Idempotent: only processes events where processed_at IS NULL.
- Marks events as processed after successful update.
- Safe for free-tier ramp: can be run as a cron job.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from salesgpt.models.database import Lead
from salesgpt.db.connection import DatabaseManager


def fix_supabase_url(url: str) -> str:
    """Remove pgbouncer parameter and fix password encoding in Supabase connection string."""
    if not url:
        return url
    from urllib.parse import quote
    parsed = urlparse(url)
    
    # Fix password encoding if it contains special characters
    if '@' in parsed.netloc:
        auth, hostport = parsed.netloc.rsplit('@', 1)
        if ':' in auth:
            user, passwd = auth.split(':', 1)
            # URL-encode the password (handles @ and other special chars)
            passwd_encoded = quote(passwd, safe='')
            new_netloc = f'{user}:{passwd_encoded}@{hostport}'
        else:
            new_netloc = parsed.netloc
    else:
        new_netloc = parsed.netloc
    
    # Remove pgbouncer from query
    query_params = parse_qs(parsed.query)
    query_params.pop('pgbouncer', None)
    new_query = urlencode(query_params, doseq=True)
    
    new_url = urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return new_url


@dataclass(frozen=True)
class MarketingEvent:
    id: str
    email: str
    event_type: str
    occurred_at: datetime
    market: Optional[str]
    niche: Optional[str]
    persona: Optional[str]
    variant_code: Optional[str]
    apollo_config_code: Optional[str]
    source: Optional[str]
    payload: Optional[dict]


class MarketingEventsIngestor:
    def __init__(self, supabase_database_url: str, db_manager: DatabaseManager):
        self.supabase_database_url = supabase_database_url
        self.db_manager = db_manager

    def fetch_unprocessed_events(self, limit: int = 1000) -> List[MarketingEvent]:
        """
        Fetch unprocessed marketing events from Supabase.
        
        Notes:
        - Only fetches events where processed_at IS NULL.
        - Orders by occurred_at ASC to process oldest first.
        """
        # Fix connection string (remove pgbouncer, encode password)
        db_url = fix_supabase_url(self.supabase_database_url)
        engine = create_engine(db_url, pool_pre_ping=True)
        
        query = text("""
            SELECT 
                id,
                email,
                event_type,
                occurred_at,
                market,
                niche,
                persona,
                variant_code,
                apollo_config_code,
                source,
                payload
            FROM marketing_events
            WHERE processed_at IS NULL
            ORDER BY occurred_at ASC
            LIMIT :limit
        """)

        events: List[MarketingEvent] = []
        with engine.connect() as conn:
            rows = conn.execute(query, {"limit": limit}).fetchall()

        for row in rows:
            # Handle timezone-aware timestamps
            occurred_at = row.occurred_at
            if isinstance(occurred_at, datetime) and occurred_at.tzinfo is None:
                occurred_at = occurred_at.replace(tzinfo=timezone.utc)
            
            events.append(MarketingEvent(
                id=str(row.id),
                email=row.email.strip().lower(),
                event_type=row.event_type,
                occurred_at=occurred_at,
                market=row.market,
                niche=row.niche,
                persona=row.persona,
                variant_code=row.variant_code,
                apollo_config_code=row.apollo_config_code,
                source=row.source,
                payload=row.payload if row.payload else None,
            ))

        return events

    def mark_event_processed(self, event_id: str) -> None:
        """Mark an event as processed by setting processed_at timestamp."""
        # Fix connection string (remove pgbouncer, encode password)
        db_url = fix_supabase_url(self.supabase_database_url)
        engine = create_engine(db_url, pool_pre_ping=True)
        
        query = text("""
            UPDATE marketing_events
            SET processed_at = NOW()
            WHERE id = :event_id
        """)
        
        with engine.connect() as conn:
            conn.execute(query, {"event_id": event_id})
            conn.commit()

    def update_lead_from_event(self, event: MarketingEvent) -> bool:
        """
        Update SalesGPT lead DB based on marketing event.
        
        Returns:
            True if lead was found and updated, False otherwise.
        """
        with self.db_manager.session() as session:
            # Find lead by email (case-insensitive)
            lead = session.query(Lead).filter(
                Lead.email.ilike(event.email)
            ).first()

            if not lead:
                # Lead not found - this is expected for organic signups
                return False

            updated = False

            # Handle different event types
            if event.event_type == 'signup_free':
                if not lead.free_signup_at:
                    lead.free_signup_at = event.occurred_at
                    updated = True
                    # Also update market/persona if provided
                    if event.market and not lead.market:
                        lead.market = event.market
                    if event.persona and not lead.persona:
                        lead.persona = event.persona
                    if event.variant_code and not lead.variant_code:
                        lead.variant_code = event.variant_code
                    if event.apollo_config_code and not lead.apollo_config_code:
                        lead.apollo_config_code = event.apollo_config_code

            elif event.event_type == 'paid_pro':
                if not lead.paid_pro_at:
                    lead.paid_pro_at = event.occurred_at
                    updated = True
                    # Extract payment details from payload
                    if event.payload:
                        if 'price_id' in event.payload:
                            lead.paid_pro_price_id = event.payload['price_id']
                        if 'invoice_id' in event.payload:
                            lead.paid_pro_invoice_id = event.payload['invoice_id']
                        if 'amount_paid' in event.payload:
                            # Convert from cents to dollars if needed
                            amount = event.payload['amount_paid']
                            if isinstance(amount, int) and amount > 1000:
                                # Likely in cents, convert to dollars
                                lead.paid_pro_amount = amount / 100.0
                            else:
                                lead.paid_pro_amount = float(amount)

            elif event.event_type == 'email_reply':
                if not lead.reply_received_at:
                    lead.reply_received_at = event.occurred_at
                    updated = True
                    # Optionally extract intent from payload if available
                    if event.payload and 'reply_intent' in event.payload:
                        lead.reply_intent = event.payload['reply_intent']

            elif event.event_type == 'activated':
                # Activation is a leading indicator but doesn't directly update lead status
                # Could be used for analytics/segmentation
                pass

            # Session context manager will commit automatically if no exception
            return updated

    def sync_events(self, limit: int = 1000) -> Tuple[int, int, int]:
        """
        Sync unprocessed marketing events into SalesGPT lead DB.
        
        Returns:
            Tuple of (events_processed, leads_updated, events_not_found)
        """
        events = self.fetch_unprocessed_events(limit=limit)
        
        processed = 0
        updated = 0
        not_found = 0

        for event in events:
            try:
                # Try to update lead
                lead_updated = self.update_lead_from_event(event)
                
                if lead_updated:
                    updated += 1
                else:
                    # Lead not found - this is OK for organic signups
                    not_found += 1
                
                # Mark event as processed regardless of whether lead was found
                # (prevents re-processing)
                self.mark_event_processed(event.id)
                processed += 1
                
            except Exception as e:
                # Log error but continue processing other events
                print(f"Error processing event {event.id}: {e}")
                # Don't mark as processed if there was an error
                continue

        return (processed, updated, not_found)

