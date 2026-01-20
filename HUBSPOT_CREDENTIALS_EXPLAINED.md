# HubSpot Credentials Explained

## Two Authentication Methods

### Method 1: Static Token (What We Set Up) ⭐

**For the app we just created, you need:**
- ✅ **Access Token** (from Auth tab)
- ❌ NOT Client ID/Secret

**What to get:**
1. Go to your app's Auth tab
2. Copy the **"Access Token"** (not Client ID/Secret)
3. Add to `.env`: `HUBSPOT_API_KEY=your-access-token`

### Method 2: OAuth 2.0 (More Complex)

**If you want to use OAuth, you need:**
- ✅ Client ID
- ✅ Client Secret  
- ✅ Refresh Token (requires OAuth flow)

**What you have:**
- ✅ Client ID (saved to .env)
- ✅ Client Secret (saved to .env)
- ❌ Refresh Token (still needed)

**To get Refresh Token:**
1. Build OAuth authorization URL
2. User authorizes app
3. Get authorization code
4. Exchange code for access + refresh tokens

## For Your Current Setup

**Since we created a Static Token app:**
- You **don't need** Client ID/Secret
- You **just need** the Access Token from Auth tab

**However, if you want to use OAuth instead:**
- You have Client ID ✅
- You have Client Secret ✅
- You still need Refresh Token ❌

## Recommendation

**For simplicity:** Use Static Token (Method 1)
- Get Access Token from Auth tab
- Add to `.env`: `HUBSPOT_API_KEY=token`
- Done!

**If you want OAuth:** You'll need to complete the OAuth flow to get a refresh token.

## Current Status

Your app supports **both methods**:
- Static token: Just need `HUBSPOT_API_KEY`
- OAuth: Need `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET`, `HUBSPOT_REFRESH_TOKEN`

Choose one method - you don't need both!



