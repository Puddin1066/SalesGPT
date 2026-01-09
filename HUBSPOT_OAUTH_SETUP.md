# HubSpot OAuth 2.0 Setup Guide

Follow these steps to set up OAuth 2.0 authentication for HubSpot API.

## Prerequisites

1. A HubSpot account
2. Access to create apps in HubSpot Developer account

## Step 1: Create a HubSpot App

1. Go to: https://developers.hubspot.com/apps
2. Click **"Create app"**
3. Give your app a name (e.g., "SalesGPT Integration")
4. Click **"Create app"**

## Step 2: Configure OAuth Settings

1. In your app settings, go to the **"Auth"** tab
2. Note your **Client ID** and **Client Secret** (you'll need these)
3. Set your **Redirect URI** (e.g., `http://localhost:8080/callback` for testing, or your production URL)
   - For local testing: `http://localhost:8080/callback`
   - Must use `https` in production (IP addresses not supported)
4. In the **"Scopes"** section, select the required permissions:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - (Optional) `crm.schemas.custom.read` (if using Operations Hub)

## Step 3: Get Authorization Code

1. Build your authorization URL:
   ```
   https://app.hubspot.com/oauth/authorize?
   client_id=YOUR_CLIENT_ID&
   scope=crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.deals.read%20crm.objects.deals.write&
   redirect_uri=YOUR_REDIRECT_URI
   ```

   Replace:
   - `YOUR_CLIENT_ID` with your actual Client ID
   - `YOUR_REDIRECT_URI` with your redirect URI (URL-encoded, e.g., `http%3A%2F%2Flocalhost%3A8080%2Fcallback`)

2. Open this URL in your browser
3. Select your HubSpot account
4. Click **"Grant access"**
5. You'll be redirected to your redirect_uri with a `code` parameter:
   ```
   http://localhost:8080/callback?code=xxxx-xxxx-xxxx
   ```
6. Copy the `code` value from the URL

## Step 4: Generate Initial Tokens

Use Python to generate your initial access and refresh tokens:

```python
from services.crm.hubspot_agent import HubSpotAgent

# Replace with your actual values
client_id = "your-client-id"
client_secret = "your-client-secret"
authorization_code = "code-from-redirect-url"
redirect_uri = "http://localhost:8080/callback"

tokens = HubSpotAgent.generate_initial_tokens(
    client_id=client_id,
    client_secret=client_secret,
    authorization_code=authorization_code,
    redirect_uri=redirect_uri
)

if tokens:
    print(f"Access Token: {tokens.get('access_token')}")
    print(f"Refresh Token: {tokens.get('refresh_token')}")
    print(f"Expires in: {tokens.get('expires_in')} seconds")
else:
    print("Failed to generate tokens")
```

## Step 5: Update .env File

Add these variables to your `.env` file:

```env
HUBSPOT_CLIENT_ID=your-client-id-here
HUBSPOT_CLIENT_SECRET=your-client-secret-here
HUBSPOT_REFRESH_TOKEN=your-refresh-token-here
```

**Important:** 
- Never commit your `.env` file to version control
- The refresh token is used to automatically get new access tokens
- Access tokens expire (typically 1800 seconds / 30 minutes)
- The code will automatically refresh tokens when needed

## Step 6: Test the Connection

Run the test script:

```bash
python3 test_hubspot_connection.py
```

You should see:
```
✅ HubSpot API connection test PASSED!
```

## Troubleshooting

### "Invalid authorization code"
- Make sure you copied the entire code from the redirect URL
- The code expires quickly (usually within 10 minutes)
- Generate a new code if it expired

### "Invalid redirect_uri"
- The redirect_uri must exactly match what's configured in your app settings
- Make sure it's URL-encoded in the authorization URL

### "Insufficient scopes"
- Make sure you selected the required scopes in your app settings
- The scopes in the authorization URL must match app settings

### Token refresh fails
- Verify your Client ID and Client Secret are correct
- Check that the refresh token hasn't been revoked
- Make sure your app is still installed in the HubSpot account

## Quick Reference

- **HubSpot Apps**: https://developers.hubspot.com/apps
- **OAuth Guide**: https://developers.hubspot.com/docs/api-reference/auth-oauth-v1/guide
- **OAuth Working Guide**: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth
- **Scopes Reference**: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/scopes

