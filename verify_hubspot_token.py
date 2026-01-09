#!/usr/bin/env python3
"""
Automatically verify HubSpot Personal Access Key or Private App token from .env file.

This script:
1. Reads HUBSPOT_API_KEY from .env (works with Personal Access Keys or Private App tokens)
2. Tests the connection
3. Provides clear next steps if token is invalid
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_token():
    """Verify HubSpot API token from .env file."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    if not api_key:
        print("❌ HUBSPOT_API_KEY not found in .env file")
        print("\nTo set up a Personal Access Key or Private App token:")
        print("1. Go to: https://app.hubspot.com/settings/integrations/private-apps")
        print("2. Create a new Private App (or use existing)")
        print("3. Go to 'Auth' tab and copy the Access Token")
        print("4. Add to .env: HUBSPOT_API_KEY=your-token-here")
        print("\nSee HUBSPOT_PERSONAL_ACCESS_KEY_SETUP.md for detailed instructions")
        return False
    
    print(f"🔑 Found API key in .env: {api_key[:15]}...{api_key[-10:]}")
    print(f"   Length: {len(api_key)} characters")
    print("\n🔍 Testing connection...")
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(
            f"{base_url}/crm/v3/objects/contacts",
            headers=headers,
            params={"limit": 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print("✅ SUCCESS! Token is valid and working")
        print(f"   📊 Can access CRM contacts")
        if "results" in data:
            print(f"   📝 Contacts available in account")
        
        # Test HubSpotAgent initialization
        try:
            from services.crm import HubSpotAgent
            agent = HubSpotAgent()
            print(f"   ✅ HubSpotAgent initialized successfully")
        except Exception as e:
            print(f"   ⚠️  HubSpotAgent initialization issue: {e}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_json = e.response.json()
            error_detail = error_json.get("message", str(error_json))
        except:
            error_detail = e.response.text
        
        if e.response.status_code == 401:
            print("❌ Token is expired or invalid")
            print(f"   Error: {error_detail}")
            print("\n" + "="*60)
            print("NEXT STEPS - Regenerate Personal Access Key/Token:")
            print("="*60)
            print("\n1. Go to: https://app.hubspot.com/settings/integrations/private-apps")
            print("2. Find your Private App (or create a new one)")
            print("3. Click on the app name")
            print("4. Go to the 'Auth' tab")
            print("5. Click 'Show token' or 'Regenerate token'")
            print("6. Copy the new Access Token")
            print("7. Update .env file:")
            print(f"   HUBSPOT_API_KEY=your-new-token-here")
            print("8. Run this script again to verify:")
            print("   python3 verify_hubspot_token.py")
            return False
        elif e.response.status_code == 403:
            print("⚠️  Token works but insufficient permissions")
            print(f"   Error: {error_detail}")
            print("\nUpdate your Private App scopes to include:")
            print("  - crm.objects.contacts.read")
            print("  - crm.objects.contacts.write")
            return False
        else:
            print(f"❌ HTTP Error {e.response.status_code}: {error_detail}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = verify_token()
    sys.exit(0 if success else 1)

