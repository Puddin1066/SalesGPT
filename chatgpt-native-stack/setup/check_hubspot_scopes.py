"""
Check HubSpot API key scopes.

Verifies which scopes are available on the current API key.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv('.env.local')


def check_scopes():
    """Check available scopes on HubSpot API key."""
    
    api_key = os.getenv('HUBSPOT_API_KEY') or os.getenv('HUBSPOT_PAT')
    if not api_key:
        print("❌ Error: HUBSPOT_API_KEY or HUBSPOT_PAT not found")
        return False
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Checking HubSpot API key scopes...\n")
    
    # Get access token info
    url = f"{base_url}/oauth/v1/access-tokens/{api_key}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        scopes = data.get('scopes', [])
        
        print(f"✅ API Key Valid")
        print(f"   Hub ID: {data.get('hub_id')}")
        print(f"   App ID: {data.get('app_id')}")
        print(f"\n📋 Available Scopes ({len(scopes)}):")
        
        for scope in sorted(scopes):
            print(f"   - {scope}")
        
        # Check required scopes
        required_scopes = [
            'crm.schemas.contacts.write',
            'crm.objects.contacts.read',
            'crm.objects.contacts.write',
        ]
        
        optional_scopes = [
            'crm.lists.read',
            'crm.lists.write',
            'marketing-email.send',
            'forms',
            'content',
        ]
        
        print(f"\n🎯 Required Scopes:")
        missing_required = []
        for scope in required_scopes:
            if scope in scopes:
                print(f"   ✅ {scope}")
            else:
                print(f"   ❌ {scope} - MISSING")
                missing_required.append(scope)
        
        print(f"\n💡 Optional Scopes:")
        missing_optional = []
        for scope in optional_scopes:
            if scope in scopes:
                print(f"   ✅ {scope}")
            else:
                print(f"   ⚠️  {scope} - Not available")
                missing_optional.append(scope)
        
        if missing_required:
            print(f"\n⚠️  Missing Required Scopes!")
            print(f"\n💡 Next steps:")
            print(f"   1. Go to HubSpot → Settings → Integrations → Private Apps")
            print(f"   2. Edit your Private App")
            print(f"   3. Add missing scopes: {', '.join(missing_required)}")
            print(f"   4. Generate new access token")
            print(f"   5. Update .env.local with new token")
            print(f"\n   See: setup/configure_hubspot_scopes.md for details")
            return False
        else:
            print(f"\n✅ All required scopes are available!")
            if missing_optional:
                print(f"\n💡 Optional scopes missing:")
                print(f"   {', '.join(missing_optional)}")
                print(f"   (These enable additional automation features)")
            return True
            
    except requests.exceptions.RequestException as e:
        # If this endpoint doesn't work, try a different approach
        print(f"⚠️  Cannot check scopes via API (endpoint may not be available)")
        print(f"\n💡 Try creating a property to test scopes:")
        print(f"   python3 chatgpt-native-stack/setup/create_hubspot_properties.py")
        print(f"\n   If you see 403 Forbidden errors, you need to add scopes:")
        print(f"   See: setup/configure_hubspot_scopes.md")
        return False


if __name__ == "__main__":
    success = check_scopes()
    sys.exit(0 if success else 1)

