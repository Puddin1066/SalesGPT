# Getting Access Token from Static Token App

## What You See on Auth Page

On your HubSpot Auth page, you see:
- ✅ **Client ID:** `73b4dd33-849e-49f6-80e4-591c8deea23b`
- ✅ **Client Secret:** (masked)
- ❌ **Access Token:** Not visible yet

## For Static Token Apps

**Important:** Even though the app uses "Static token" auth, you still need to **install the app** to generate the access token.

### Step 1: Install the App

1. **Go to Distribution tab** (next to Auth tab)
2. **Under "Standard install"** section
3. **Click "Install now"**
4. **Review permissions** and click "Connect app"

OR

1. Go to: HubSpot → Development → Projects → SalesGPT-Integration
2. Click "salesgpt_integration" app
3. Go to **"Distribution"** tab
4. Click **"Install now"** under Standard install

### Step 2: Get Access Token After Installation

After installing, the **Access Token** will be available:

**Option A: Via Connected Apps**
1. Go to: HubSpot → Settings → Integrations → Connected Apps
2. Find "SalesGPT Integration"
3. Click on it
4. Copy the **Access Token**

**Option B: Via Development → Projects**
1. Go to: Development → Projects → SalesGPT-Integration
2. Click "salesgpt_integration"
3. Go to **"Auth"** tab
4. The **Access Token** should now be visible (after installation)

### Step 3: Update .env

```bash
python3 update_hubspot_token.py
```

Paste the Access Token when prompted.

## Alternative: Use OAuth Instead

If you prefer to use OAuth (you already have Client ID/Secret):

1. **Add to .env:**
   ```
   HUBSPOT_CLIENT_ID=73b4dd33-849e-49f6-80e4-591c8deea23b
   HUBSPOT_CLIENT_SECRET=your-client-secret
   ```

2. **Get Refresh Token:**
   - Build OAuth authorization URL
   - Complete OAuth flow
   - Get refresh token
   - Add: `HUBSPOT_REFRESH_TOKEN=...`

3. **Code will use OAuth** instead of static token

## Recommendation

**For simplicity:** Install the app → Get static access token → Use it

**For OAuth:** Complete OAuth flow → Get refresh token → Use OAuth

Both work! Static token is simpler for single-account use.



