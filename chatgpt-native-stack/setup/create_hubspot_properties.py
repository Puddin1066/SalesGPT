"""
Automatically create HubSpot custom properties via API.

Uses HubSpot Properties API to create all required custom contact properties.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv('.env.local')


def create_property(api_key: str, property_config: dict) -> bool:
    """Create a single HubSpot property."""
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/crm/v3/properties/contacts"
    
    try:
        response = requests.post(url, headers=headers, json=property_config)
        
        # 409 means property already exists - that's OK
        if response.status_code == 409:
            print(f"   ℹ️  {property_config['name']} - Already exists (skipping)")
            return True
        
        response.raise_for_status()
        print(f"   ✅ {property_config['name']} - Created successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {property_config['name']} - Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"      Details: {json.dumps(error_data, indent=6)}")
            except:
                print(f"      Response: {e.response.text}")
        return False


def create_all_properties():
    """Create all required HubSpot custom properties."""
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found in .env.local")
        return False
    
    print("🚀 Creating HubSpot custom properties via API...\n")
    
    # Define all properties
    properties = [
        {
            "name": "vertical",
            "label": "Vertical",
            "type": "string",
            "fieldType": "text",
            "groupName": "contactinformation",
            "description": "Target vertical for GemFlush campaign (medical, legal, realestate, agencies)",
            "formField": True
        },
        {
            "name": "gemflush_email_sent",
            "label": "GemFlush Email Sent",
            "type": "datetime",
            "fieldType": "date",
            "groupName": "contactinformation",
            "description": "Timestamp when GemFlush email was sent",
            "formField": False
        },
        {
            "name": "gemflush_variant",
            "label": "GemFlush Variant",
            "type": "string",
            "fieldType": "text",
            "groupName": "contactinformation",
            "description": "A/B test variant (A or B)",
            "formField": False
        },
        {
            "name": "gemflush_email_subject",
            "label": "GemFlush Email Subject",
            "type": "string",
            "fieldType": "text",
            "groupName": "contactinformation",
            "description": "Subject line of sent email",
            "formField": False
        },
        {
            "name": "gemflush_last_campaign_date",
            "label": "GemFlush Last Campaign Date",
            "type": "date",
            "fieldType": "date",
            "groupName": "contactinformation",
            "description": "Date of last campaign contact",
            "formField": False
        },
        {
            "name": "gemflush_sender_email",
            "label": "GemFlush Sender Email",
            "type": "string",
            "fieldType": "text",
            "groupName": "contactinformation",
            "description": "Sender email address (Alex@GEMflush.com)",
            "formField": False
        }
    ]
    
    success_count = 0
    for prop_config in properties:
        if create_property(api_key, prop_config):
            success_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Created/Verified: {success_count}/{len(properties)}")
    
    if success_count == len(properties):
        print(f"\n✅ All properties ready!")
        print(f"\n💡 Next steps:")
        print(f"   1. Verify properties: python3 chatgpt-native-stack/setup/verify_hubspot_properties.py")
        print(f"   2. Continue with content generation")
        return True
    else:
        print(f"\n⚠️  Some properties could not be created")
        print(f"   Check errors above and retry")
        return False


if __name__ == "__main__":
    success = create_all_properties()
    sys.exit(0 if success else 1)

