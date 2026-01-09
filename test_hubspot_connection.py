#!/usr/bin/env python3
"""
Test HubSpot API connection.

Supports both OAuth 2.0 and Private App access tokens.
Verifies that authentication is working correctly.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_hubspot_connection():
    """Test HubSpot API connection with a simple API call."""
    # Check for OAuth credentials
    client_id = os.getenv("HUBSPOT_CLIENT_ID")
    client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
    refresh_token = os.getenv("HUBSPOT_REFRESH_TOKEN")
    
    # Check for Private App token
    api_key = os.getenv("HUBSPOT_API_KEY")
    
    auth_method = None
    token = None
    
    if client_id and client_secret and refresh_token:
        auth_method = "OAuth 2.0"
        print("🔐 Authentication method: OAuth 2.0")
        print(f"   Client ID: {client_id[:10]}...")
        print(f"   Refresh token: {refresh_token[:10]}...")
        
        # Try to refresh access token
        print("\n   🔄 Refreshing OAuth access token...")
        try:
            response = requests.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            print(f"   ✅ OAuth token refreshed successfully")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ OAuth token refresh failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Error: {error_data.get('message', e.response.text)}")
                except:
                    print(f"   Error: {e.response.text}")
            return False
    elif api_key:
        auth_method = "Private App Access Token"
        token = api_key
        print("🔐 Authentication method: Private App Access Token")
        print(f"   Token: {api_key[:10]}...{api_key[-4:]}")
        print(f"   Length: {len(api_key)} characters")
    else:
        print("❌ ERROR: No HubSpot authentication configured")
        print("\n   Configure one of the following:")
        print("   1. Private App (simpler, single account):")
        print("      - Set HUBSPOT_API_KEY in .env file")
        print("      - Get from: https://app.hubspot.com/settings/integrations/private-apps")
        print("\n   2. OAuth 2.0 (for multi-account apps):")
        print("      - Set HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, HUBSPOT_REFRESH_TOKEN")
        print("      - See: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth")
        return False
    
    if not token:
        print("❌ No valid access token available")
        return False
    
    print("\n🔍 Testing HubSpot API connection...")
    
    base_url = "https://api.hubapi.com"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Test 1: Get account information using v3 API
    print("\n1️⃣ Testing: Get account information (v3 API)...")
    try:
        response = requests.get(
            f"{base_url}/crm/v3/objects/contacts",
            headers=headers,
            params={"limit": 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"   ✅ Success! Connected to HubSpot account")
        print(f"   📊 Can access CRM contacts")
        if "results" in data:
            print(f"   📝 Sample contacts available: {len(data.get('results', []))}")
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_json = e.response.json()
            error_detail = error_json.get("message", str(error_json))
        except:
            error_detail = e.response.text
        
        if e.response.status_code == 401:
            print(f"   ❌ Authentication failed")
            print(f"   Error: {error_detail}")
            
            if auth_method == "OAuth 2.0":
                print(f"\n   💡 OAuth token may be expired or invalid")
                print(f"      - Verify your refresh token is valid")
                print(f"      - Check that your app has the required scopes")
                print(f"      - See: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide")
                print(f"      - To get initial tokens, use HubSpotAgent.generate_initial_tokens()")
                print(f"        with the authorization code from the OAuth redirect")
            else:
                print(f"\n   💡 Private App token may be expired or invalid")
                print(f"      1. Go to https://app.hubspot.com/settings/integrations/private-apps")
                print(f"      2. Regenerate the access token for your Private App")
                print(f"      3. Update HUBSPOT_API_KEY in your .env file")
                print(f"      4. Ensure scopes include: crm.objects.contacts.read")
            return False
        elif e.response.status_code == 403:
            print(f"   ⚠️  Authentication works but insufficient permissions")
            print(f"   Error: {error_detail}")
            print(f"\n   💡 Ensure your app has CRM read permissions")
        else:
            print(f"   ❌ HTTP Error {e.response.status_code}: {error_detail}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    # Test 2: Test HubSpotAgent initialization
    print("\n2️⃣ Testing: HubSpotAgent initialization...")
    try:
        from services.crm import HubSpotAgent
        agent = HubSpotAgent()
        print(f"   ✅ HubSpotAgent initialized successfully")
        print(f"   🌐 Base URL: {agent.base_url}")
        print(f"   🔐 Using OAuth: {agent.use_oauth}")
        print(f"   🔐 Authorization header set: {'Bearer' in agent.headers.get('Authorization', '')}")
    except ValueError as e:
        print(f"   ❌ Initialization failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*50)
    print("✅ HubSpot API connection test PASSED!")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_hubspot_connection()
    sys.exit(0 if success else 1)
