"""
Test Stripe webhook endpoint.

Sends a mock Stripe webhook event to test the FireGEO webhook endpoint.
"""

import argparse
import sys
import os
import json
import hmac
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env.local if it exists
env_file = project_root / '.env.local'
if env_file.exists():
    load_dotenv(env_file)

import stripe
from salesgpt.config import get_settings


def generate_stripe_signature(payload: bytes, secret: str, timestamp: int = None) -> str:
    """Generate Stripe webhook signature matching Stripe's format exactly."""
    if timestamp is None:
        timestamp = int(time.time())
    
    # Stripe signature format: timestamp + '.' + raw payload (as string)
    # The payload should be the raw JSON string, not bytes
    payload_str = payload.decode('utf-8')
    signed_payload = f"{timestamp}.{payload_str}"
    
    # Generate HMAC SHA256 signature
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Stripe signature format: t=timestamp,v1=signature
    return f"t={timestamp},v1={signature}"


def test_invoice_paid_webhook(webhook_url: str, webhook_secret: str, test_email: str = "test@example.com"):
    """Test invoice.paid webhook event."""
    
    # Create mock invoice.paid event
    event_data = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "type": "invoice.paid",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": f"in_test_{int(time.time())}",
                "object": "invoice",
                "amount_paid": 9900,  # $99 in cents
                "currency": "usd",
                "customer": f"cus_test_{int(time.time())}",
                "customer_email": test_email,
                "lines": {
                    "data": [
                        {
                            "price": {
                                "id": "price_1SobzBQg9yJEawqIFl1VSm5u"  # Pro price ID
                            }
                        }
                    ]
                },
                "subscription": f"sub_test_{int(time.time())}"
            }
        }
    }
    
    payload = json.dumps(event_data).encode('utf-8')
    signature = generate_stripe_signature(payload, webhook_secret)
    
    headers = {
        "Stripe-Signature": signature,
        "Content-Type": "application/json"
    }
    
    print(f"\n🧪 Testing Stripe webhook endpoint")
    print(f"   URL: {webhook_url}")
    print(f"   Event: invoice.paid")
    print(f"   Test Email: {test_email}")
    
    try:
        response = requests.post(webhook_url, data=payload, headers=headers, timeout=10)
        
        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:200]}")
        
        if response.status_code == 200:
            print(f"\n✅ Webhook test successful!")
            
            # Check if event was created in Supabase
            print(f"\n🔍 Checking if event was created in marketing_events...")
            from salesgpt.config import get_settings
            from services.attribution.marketing_events_ingestor import fix_supabase_url
            from sqlalchemy import create_engine, text
            
            settings = get_settings()
            if settings.supabase_database_url:
                db_url = fix_supabase_url(settings.supabase_database_url)
                engine = create_engine(db_url, pool_pre_ping=True)
                
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT id, email, event_type, occurred_at, processed_at
                        FROM marketing_events
                        WHERE email = :email
                        AND event_type = 'paid_pro'
                        ORDER BY occurred_at DESC
                        LIMIT 1
                    """), {"email": test_email.lower()})
                    
                    event = result.fetchone()
                    if event:
                        print(f"   ✅ Event found in marketing_events:")
                        print(f"      ID: {event[0]}")
                        print(f"      Email: {event[1]}")
                        print(f"      Type: {event[2]}")
                        print(f"      Occurred: {event[3]}")
                        print(f"      Processed: {event[4]}")
                    else:
                        print(f"   ⚠️  Event not found (may take a moment to appear)")
            
            return True
        else:
            print(f"\n❌ Webhook test failed")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error sending webhook: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Stripe webhook endpoint")
    parser.add_argument(
        "--url",
        type=str,
        default="https://gemflush.com/api/stripe/webhook",
        help="Webhook URL (default: https://gemflush.com/api/stripe/webhook)"
    )
    parser.add_argument(
        "--secret",
        type=str,
        help="Webhook secret (default: from WEBHOOK_SECRET_KEY env var)"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=f"test_{int(time.time())}@example.com",
        help="Test email address"
    )
    args = parser.parse_args()
    
    # Get webhook secret
    webhook_secret = args.secret or os.getenv("WEBHOOK_SECRET_KEY") or os.getenv("STRIPE_WEBHOOK_SECRET_LIVE") or os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        print("❌ Webhook secret not found")
        print("   Set WEBHOOK_SECRET_KEY, STRIPE_WEBHOOK_SECRET_LIVE, or STRIPE_WEBHOOK_SECRET")
        print("   Or use --secret flag")
        return 1
    
    if not webhook_secret.startswith("whsec_"):
        print(f"⚠️  Warning: Webhook secret should start with 'whsec_'")
        print(f"   Current value starts with: {webhook_secret[:6]}")
    
    success = test_invoice_paid_webhook(args.url, webhook_secret, args.email)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

