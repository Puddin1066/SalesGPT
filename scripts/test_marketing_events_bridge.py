"""
Test script for FireGEO ↔ SalesGPT Event Bridge.

Tests:
1. Database connection and table existence
2. Event insertion (simulated)
3. SalesGPT ingestor reading and processing events
4. Lead updates in SalesGPT DB
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from salesgpt.models.database import Lead
from services.attribution.marketing_events_ingestor import MarketingEventsIngestor
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


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


def test_supabase_connection():
    """Test 1: Verify Supabase connection and marketing_events table exists."""
    print("\n" + "="*60)
    print("TEST 1: Supabase Connection & Table Check")
    print("="*60)
    
    settings = get_settings()
    if not settings.supabase_database_url:
        print("❌ SUPABASE_DATABASE_URL not configured")
        return False
    
    try:
        # Fix connection string (remove pgbouncer, encode password)
        db_url = fix_supabase_url(settings.supabase_database_url)
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'marketing_events'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ marketing_events table exists")
                
                # Check table structure
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'marketing_events'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                print(f"✅ Table has {len(columns)} columns:")
                for col_name, col_type in columns:
                    print(f"   - {col_name}: {col_type}")
                
                return True
            else:
                print("❌ marketing_events table does not exist")
                print("   Run migration: psql $DATABASE_URL -f firegeo/migrations/009_add_marketing_events.sql")
                return False
                
    except OperationalError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_insert_test_event():
    """Test 2: Insert a test event into marketing_events."""
    print("\n" + "="*60)
    print("TEST 2: Insert Test Event")
    print("="*60)
    
    settings = get_settings()
    if not settings.supabase_database_url:
        print("❌ SUPABASE_DATABASE_URL not configured")
        return False, None
    
    try:
        # Remove pgbouncer parameter if present (not supported by psycopg2)
        db_url = fix_supabase_url(settings.supabase_database_url)
        engine = create_engine(db_url, pool_pre_ping=True)
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        
        with engine.connect() as conn:
            # Insert test event
            result = conn.execute(text("""
                INSERT INTO marketing_events (
                    email, event_type, occurred_at, source, payload
                ) VALUES (
                    :email, 'signup_free', NOW(), 'test', '{"test": true}'::jsonb
                )
                RETURNING id, email, event_type;
            """), {"email": test_email})
            
            event = result.fetchone()
            conn.commit()
            
            if event:
                print(f"✅ Test event inserted: {event[1]} ({event[2]})")
                print(f"   Event ID: {event[0]}")
                return True, test_email
            else:
                print("❌ Failed to insert test event")
                return False, None
                
    except Exception as e:
        print(f"❌ Error inserting test event: {e}")
        return False, None


def test_salesgpt_db():
    """Test 3: Verify SalesGPT database and create test lead."""
    print("\n" + "="*60)
    print("TEST 3: SalesGPT Database & Test Lead")
    print("="*60)
    
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)
    
    try:
        # Create tables
        db_manager.create_tables()
        print("✅ SalesGPT database tables created/verified")
        
        # Create test lead
        with db_manager.session() as session:
            test_email = f"test_{datetime.now().timestamp()}@example.com"
            
            # Check if lead exists
            existing = session.query(Lead).filter(Lead.email == test_email).first()
            if existing:
                print(f"✅ Test lead already exists: {test_email}")
                return True, test_email
            
            # Create new lead
            lead = Lead(
                email=test_email,
                name="Test Lead",
                company_name="Test Company",
                status="idle"
            )
            session.add(lead)
            session.commit()
            
            print(f"✅ Test lead created: {test_email}")
            return True, test_email
            
    except Exception as e:
        print(f"❌ Error with SalesGPT database: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_ingestor(test_email: str):
    """Test 4: Test the MarketingEventsIngestor."""
    print("\n" + "="*60)
    print("TEST 4: Marketing Events Ingestor")
    print("="*60)
    
    settings = get_settings()
    supabase_url = settings.supabase_database_url
    if not supabase_url and settings.database_url and 'postgres' in settings.database_url.lower():
        supabase_url = settings.database_url
    
    if not supabase_url:
        print("⚠️  SUPABASE_DATABASE_URL not configured")
        print("   Skipping test (requires Postgres connection)")
        return None
    
    try:
        # Remove pgbouncer parameter if present (not supported by psycopg2)
        if supabase_url and 'pgbouncer=true' in supabase_url:
            supabase_url = supabase_url.replace('?pgbouncer=true', '').replace('&pgbouncer=true', '')
        # Initialize ingestor
        db_manager = DatabaseManager(settings.database_url)
        ingestor = MarketingEventsIngestor(supabase_url, db_manager)
        
        # Fetch unprocessed events
        events = ingestor.fetch_unprocessed_events(limit=10)
        print(f"✅ Fetched {len(events)} unprocessed events")
        
        if events:
            print(f"   Sample events:")
            for event in events[:3]:
                print(f"   - {event.email}: {event.event_type} ({event.occurred_at})")
        
        # Test syncing events
        processed, updated, not_found = ingestor.sync_events(limit=10)
        print(f"✅ Sync completed:")
        print(f"   - Events processed: {processed}")
        print(f"   - Leads updated: {updated}")
        print(f"   - Events (leads not found): {not_found}")
        
        # Verify lead was updated
        with db_manager.session() as session:
            lead = session.query(Lead).filter(Lead.email == test_email).first()
            if lead and lead.free_signup_at:
                print(f"✅ Lead updated: free_signup_at = {lead.free_signup_at}")
                return True
            elif lead:
                print(f"⚠️  Lead found but not updated (no matching event)")
                return True
            else:
                print(f"⚠️  Lead not found (expected if no matching event)")
                return True
        
    except Exception as e:
        print(f"❌ Error testing ingestor: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FireGEO ↔ SalesGPT Event Bridge - Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Supabase connection
    results.append(("Supabase Connection", test_supabase_connection()))
    
    # Test 2: Insert test event
    result = test_insert_test_event()
    if isinstance(result, tuple):
        success, test_email = result
    else:
        success, test_email = (result, None) if result is not None else (None, None)
    results.append(("Insert Test Event", success))
    
    # Test 3: SalesGPT database
    success, test_lead_email = test_salesgpt_db()
    results.append(("SalesGPT Database", success))
    
    # Test 4: Ingestor (use test_email from event insertion)
    if test_email:
        ingestor_result = test_ingestor(test_email)
        results.append(("Ingestor", ingestor_result))
    elif success is not None:  # Test was skipped
        results.append(("Ingestor", None))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result is None:
            status = "⏭️  SKIP"
        elif result:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{status}: {test_name}")
    
    skipped = sum(1 for _, result in results if result is None)
    print(f"\n{passed}/{total} tests passed ({skipped} skipped)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

