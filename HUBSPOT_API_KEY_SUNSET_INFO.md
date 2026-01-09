# HubSpot API Key Sunset - Important Information

## What Happened?

According to [HubSpot's API Key Sunset announcement](https://developers.hubspot.com/changelog/upcoming-api-key-sunset):

- **July 15, 2022**: No new API keys could be created
- **November 30, 2022**: API keys were deprecated and no longer supported
- **Current**: API keys will NOT work - you MUST use Private Apps or OAuth 2.0

## Why Your Token Might Not Work

If you're using an **old API key** (created before July 15, 2022), it will:
- ❌ Return 401 errors
- ❌ Show "expired" or "invalid" errors
- ❌ Not work with HubSpot APIs

## What You Need Instead

### Option 1: Private App Access Token (Recommended for Single Account)

**What it is:**
- Static access token for a single HubSpot account
- Similar to old API keys but more secure
- Scoped permissions (granular control)

**How to get it:**
1. Go to: https://app.hubspot.com/settings/integrations/private-apps
2. Click "Create a private app"
3. Set scopes (permissions)
4. Go to "Auth" tab
5. Copy the "Access Token"

**How to use:**
```env
HUBSPOT_API_KEY=your-private-app-access-token
```

**Authentication:**
- Uses `Authorization: Bearer <token>` header
- Same as OAuth tokens

### Option 2: OAuth 2.0 (For Multi-Account Apps)

**What it is:**
- For apps used by multiple HubSpot accounts
- Better user experience
- Access tokens + refresh tokens

**How to set up:**
- See `HUBSPOT_OAUTH_SETUP.md`

## Key Differences

| Feature | Old API Keys (Deprecated) | Private App Tokens | OAuth 2.0 |
|---------|---------------------------|-------------------|-----------|
| **Status** | ❌ Deprecated (Nov 2022) | ✅ Active | ✅ Active |
| **Format** | Shorter, query param | 100+ chars, Bearer | 100+ chars, Bearer |
| **Scopes** | ❌ No scoping | ✅ Scoped | ✅ Scoped |
| **Multi-account** | ❌ No | ❌ No | ✅ Yes |
| **Auth Method** | Query parameter | Bearer header | Bearer header |

## Migration Guide

### If You Have an Old API Key:

1. **Don't try to use it** - it won't work
2. **Create a Private App** instead:
   - Go to Private Apps settings
   - Create new app
   - Get access token
3. **Update your code:**
   - Change from query param: `?hapikey=...`
   - To Bearer header: `Authorization: Bearer ...`
4. **Update .env:**
   ```env
   HUBSPOT_API_KEY=your-new-private-app-token
   ```

## Current Code Status

✅ **Good news:** The code in this repository already uses the **correct method**:
- Uses `Authorization: Bearer <token>` header
- Supports Private App tokens
- Supports OAuth 2.0
- No API key query parameters

❌ **The problem:** Your token might be:
- An old API key (won't work)
- An expired Private App token
- An invalid token

## Solution

1. **Get a NEW Private App access token:**
   - https://app.hubspot.com/settings/integrations/private-apps
   - Create/regenerate Private App
   - Copy access token

2. **Update .env:**
   ```env
   HUBSPOT_API_KEY=your-new-private-app-access-token
   ```

3. **Verify:**
   ```bash
   python3 verify_hubspot_token.py
   ```

## References

- [API Key Sunset Announcement](https://developers.hubspot.com/changelog/upcoming-api-key-sunset)
- [Private Apps Documentation](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview)
- [OAuth 2.0 Documentation](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth)

