#!/usr/bin/env python3
"""
Generate HubSpot OAuth tokens from authorization code.

Usage:
    python3 generate_hubspot_tokens.py \
        --client-id YOUR_CLIENT_ID \
        --client-secret YOUR_CLIENT_SECRET \
        --auth-code AUTHORIZATION_CODE \
        --redirect-uri http://localhost:8080/callback
"""
import argparse
import sys
from services.crm.hubspot_agent import HubSpotAgent

def main():
    parser = argparse.ArgumentParser(
        description="Generate HubSpot OAuth access and refresh tokens"
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="OAuth Client ID from HubSpot app settings"
    )
    parser.add_argument(
        "--client-secret",
        required=True,
        help="OAuth Client Secret from HubSpot app settings"
    )
    parser.add_argument(
        "--auth-code",
        required=True,
        help="Authorization code from OAuth redirect URL"
    )
    parser.add_argument(
        "--redirect-uri",
        required=True,
        help="Redirect URI (must match app settings)"
    )
    
    args = parser.parse_args()
    
    print("Generating HubSpot OAuth tokens...")
    print(f"Client ID: {args.client_id[:10]}...")
    print(f"Redirect URI: {args.redirect_uri}")
    print()
    
    tokens = HubSpotAgent.generate_initial_tokens(
        client_id=args.client_id,
        client_secret=args.client_secret,
        authorization_code=args.auth_code,
        redirect_uri=args.redirect_uri
    )
    
    if not tokens:
        print("❌ Failed to generate tokens")
        print("\nCommon issues:")
        print("  - Authorization code may have expired (generate a new one)")
        print("  - Redirect URI doesn't match app settings")
        print("  - Client ID or Client Secret is incorrect")
        sys.exit(1)
    
    print("✅ Tokens generated successfully!")
    print()
    print("="*60)
    print("Add these to your .env file:")
    print("="*60)
    print(f"HUBSPOT_CLIENT_ID={args.client_id}")
    print(f"HUBSPOT_CLIENT_SECRET={args.client_secret}")
    print(f"HUBSPOT_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
    print()
    print(f"Access token expires in: {tokens.get('expires_in', 'N/A')} seconds")
    print("(Access tokens are automatically refreshed, so you only need the refresh token)")
    print()
    print("After updating .env, test with:")
    print("  python3 test_hubspot_connection.py")

if __name__ == "__main__":
    main()



