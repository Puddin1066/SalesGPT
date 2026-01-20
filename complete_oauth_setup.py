#!/usr/bin/env python3
"""
Complete OAuth setup for HubSpot using Client ID and Secret.

This script helps you:
1. Build the authorization URL
2. Get authorization code
3. Exchange for access and refresh tokens
"""
import os
import sys
from dotenv import load_dotenv
from services.crm.hubspot_agent import HubSpotAgent

load_dotenv()

def main():
    client_id = os.getenv("HUBSPOT_CLIENT_ID")
    client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ HUBSPOT_CLIENT_ID and HUBSPOT_CLIENT_SECRET must be set in .env")
        return False
    
    print("="*60)
    print("HubSpot OAuth Setup")
    print("="*60)
    print(f"\n✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: {'*' * 20}...")
    print()
    
    # Get redirect URI
    redirect_uri = input("Enter your Redirect URI (from app settings, e.g., http://localhost:3000/callback): ").strip()
    if not redirect_uri:
        print("❌ Redirect URI is required")
        return False
    
    # Build authorization URL
    scopes = "crm.objects.contacts.read crm.objects.contacts.write crm.objects.deals.read crm.objects.deals.write"
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={client_id}&"
        f"scope={scopes.replace(' ', '%20')}&"
        f"redirect_uri={redirect_uri.replace(':', '%3A').replace('/', '%2F')}"
    )
    
    print("\n" + "="*60)
    print("Step 1: Authorize the App")
    print("="*60)
    print("\n1. Open this URL in your browser:")
    print(f"\n{auth_url}\n")
    print("2. Select your HubSpot account")
    print("3. Click 'Grant access'")
    print("4. You'll be redirected to your redirect_uri with a 'code' parameter")
    print("5. Copy the 'code' value from the URL")
    print()
    
    auth_code = input("Enter the authorization code from the redirect URL: ").strip()
    if not auth_code:
        print("❌ Authorization code is required")
        return False
    
    print("\n" + "="*60)
    print("Step 2: Generate Tokens")
    print("="*60)
    print("\nGenerating access and refresh tokens...")
    
    tokens = HubSpotAgent.generate_initial_tokens(
        client_id=client_id,
        client_secret=client_secret,
        authorization_code=auth_code,
        redirect_uri=redirect_uri
    )
    
    if not tokens:
        print("❌ Failed to generate tokens")
        print("\nCommon issues:")
        print("  - Authorization code expired (get a new one)")
        print("  - Redirect URI doesn't match app settings")
        print("  - Client ID or Secret incorrect")
        return False
    
    print("✅ Tokens generated successfully!")
    print(f"\nAccess Token: {tokens.get('access_token', '')[:50]}...")
    print(f"Refresh Token: {tokens.get('refresh_token', '')[:50]}...")
    print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds")
    
    print("\n" + "="*60)
    print("Step 3: Update .env File")
    print("="*60)
    print("\nAdd/update these in your .env file:")
    print(f"HUBSPOT_CLIENT_ID={client_id}")
    print(f"HUBSPOT_CLIENT_SECRET={client_secret}")
    print(f"HUBSPOT_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
    print("\nThe access token will be automatically refreshed when needed.")
    
    # Optionally write to .env
    write_env = input("\nUpdate .env file automatically? (y/n): ").strip().lower()
    if write_env == 'y':
        env_path = '.env'
        try:
            # Read existing .env
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
            
            # Remove old HubSpot OAuth vars if they exist
            lines = env_content.split('\n')
            filtered_lines = [
                line for line in lines
                if not line.startswith('HUBSPOT_CLIENT_ID=')
                and not line.startswith('HUBSPOT_CLIENT_SECRET=')
                and not line.startswith('HUBSPOT_REFRESH_TOKEN=')
                and not line.startswith('HUBSPOT_API_KEY=')  # Remove old API key if using OAuth
            ]
            
            # Add new vars
            filtered_lines.append(f"HUBSPOT_CLIENT_ID={client_id}")
            filtered_lines.append(f"HUBSPOT_CLIENT_SECRET={client_secret}")
            filtered_lines.append(f"HUBSPOT_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(filtered_lines))
            
            print(f"✅ Updated {env_path}")
        except Exception as e:
            print(f"❌ Failed to write to .env: {e}")
            print("Please add the variables manually.")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nTest the connection:")
    print("  python3 test_hubspot_connection.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



