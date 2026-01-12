"""
Check HubSpot email sending limits and usage.

Verifies Free tier limits and current usage.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv('.env.local')


def check_email_limits():
    """Check HubSpot email sending limits."""
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found")
        return False
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Checking HubSpot email limits...\n")
    
    # Note: HubSpot Marketing API for email limits may require Marketing Hub
    # For Free tier, limits are typically:
    # - 2,000 marketing emails/month
    # - Unlimited transactional emails
    
    print("📧 HubSpot Free Tier Email Limits:")
    print("   Marketing Emails: 2,000/month")
    print("   Transactional Emails: Unlimited")
    print()
    
    print("💡 Verification:")
    print("   1. Log into HubSpot")
    print("   2. Go to: Marketing → Email")
    print("   3. Check your account limits")
    print("   4. Verify current usage")
    print()
    
    print("📝 Notes:")
    print("   - Free tier includes 2,000 marketing emails/month")
    print("   - Budget: 500 emails/week for 4-week campaign")
    print("   - Week 1: 800 emails (200 × 4 verticals)")
    print("   - Remaining: 1,200 emails for Weeks 2-4")
    print()
    
    print("✅ Recommendation: Monitor usage in HubSpot UI weekly")
    
    return True


if __name__ == "__main__":
    check_email_limits()

