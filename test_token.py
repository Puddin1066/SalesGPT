#!/usr/bin/env python3
"""
Quick test script to verify a HubSpot token before updating .env

Usage:
    python3 test_token.py YOUR_TOKEN_HERE
    # or
    python3 test_token.py  # will prompt for token
"""
import sys
import requests

def test_token(token: str):
    """Test if a HubSpot token works."""
    if not token:
        print("❌ No token provided")
        return False
    
    token = token.strip()
    print(f"🔑 Testing token: {token[:20]}...{token[-10:]}")
    print(f"   Length: {len(token)} characters")
    print()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            params={"limit": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ SUCCESS! Token is valid and working!")
            data = response.json()
            print(f"   📊 Can access CRM contacts")
            if "results" in data:
                print(f"   📝 Contacts available in account")
            return True
        else:
            print(f"❌ FAILED - Status Code: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('message', str(error))}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("Paste your new HubSpot token to test:")
        token = input("Token: ").strip()
    
    success = test_token(token)
    if success:
        print("\n" + "="*50)
        print("✅ Token is valid! You can now update .env:")
        print("   python3 update_hubspot_token.py")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ Token is invalid. Please get a new token from:")
        print("   https://app.hubspot.com/settings/integrations/private-apps")
        print("="*50)
    
    sys.exit(0 if success else 1)

