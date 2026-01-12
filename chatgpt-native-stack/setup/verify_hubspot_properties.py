"""
Verify HubSpot custom properties exist.

Checks if all required custom properties are created in HubSpot.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv('.env.local')


def verify_properties():
    """Verify all required HubSpot properties exist."""
    
    # Required properties
    required_properties = [
        'vertical',
        'gemflush_email_sent',
        'gemflush_variant',
        'gemflush_email_subject',
        'gemflush_last_campaign_date',
        'gemflush_sender_email'
    ]
    
    # Get API key
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found in .env.local")
        return False
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Get all contact properties
    url = f"{base_url}/crm/v3/properties/contacts"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Get property names
        existing_properties = {prop['name'] for prop in data.get('results', [])}
        
        print("🔍 Checking HubSpot custom properties...\n")
        
        missing = []
        found = []
        
        for prop_name in required_properties:
            if prop_name in existing_properties:
                print(f"✅ {prop_name} - Found")
                found.append(prop_name)
            else:
                print(f"❌ {prop_name} - Missing")
                missing.append(prop_name)
        
        print(f"\n📊 Summary:")
        print(f"   Found: {len(found)}/{len(required_properties)}")
        print(f"   Missing: {len(missing)}/{len(required_properties)}")
        
        if missing:
            print(f"\n⚠️  Missing properties: {', '.join(missing)}")
            print(f"\n💡 Next steps:")
            print(f"   1. See setup/hubspot_properties_guide.md for instructions")
            print(f"   2. Create missing properties in HubSpot UI")
            print(f"   3. Run this script again to verify")
            return False
        else:
            print(f"\n✅ All required properties exist!")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking properties: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Error response: {e.response.text}")
        return False


if __name__ == "__main__":
    success = verify_properties()
    sys.exit(0 if success else 1)

