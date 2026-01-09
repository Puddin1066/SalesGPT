# OAuth vs Static Token - What You Need

## Current Situation

Your app is configured as **"static" token** type, but you have:
- ✅ Client ID: `73b4dd33-849e-49f6-80e4-591c8deea23b`
- ✅ Client Secret: (saved in .env)

## Two Options

### Option 1: Use Static Token (Simpler) ⭐

**What you need:**
- Access Token (from Auth tab, after installing app)

**Steps:**
1. Go to **Distribution** tab
2. Click **"Install now"**
3. After install, go back to **Auth** tab
4. Copy the **Access Token**
5. Update `.env`: `HUBSPOT_API_KEY=your-access-token`

**Pros:**
- ✅ Simpler
- ✅ No OAuth flow needed
- ✅ Token doesn't expire (unless regenerated)

### Option 2: Switch to OAuth (More Complex)

**What you need:**
- ✅ Client ID (you have)
- ✅ Client Secret (you have)
- ❌ Refresh Token (need to get via OAuth flow)

**Steps:**
1. **Update app config to OAuth:**
   - Change `app-hsmeta.json`: `"type": "oauth"`
   - Add `redirectUrls`
   - Redeploy: `hs project upload`

2. **Complete OAuth flow:**
   - Build authorization URL
   - User authorizes
   - Get authorization code
   - Exchange for refresh token

3. **Update .env:**
   ```
   HUBSPOT_CLIENT_ID=73b4dd33-849e-49f6-80e4-591c8deea23b
   HUBSPOT_CLIENT_SECRET=your-secret
   HUBSPOT_REFRESH_TOKEN=your-refresh-token
   ```

**Pros:**
- ✅ Better for multi-account apps
- ✅ Tokens auto-refresh
- ✅ More secure for production

## Recommendation

**For single-account use (your case):**
- Use **Static Token** (Option 1)
- Just install app → Get access token → Done!

**For multi-account or production:**
- Use **OAuth** (Option 2)
- Complete OAuth flow → Get refresh token

## Quick Decision

**Just need API access?** → Static Token (install app, get token)

**Building for multiple accounts?** → OAuth (complete OAuth flow)

Both work! Choose based on your needs.

