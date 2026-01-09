# Install App and Get Access Token

## For Static Token Apps

For apps with **static token** authentication, you need to **install the app** first to generate the access token.

## Installation Steps

### Method 1: Via HubSpot UI (Recommended)

1. **Open the project in HubSpot:**
   ```bash
   cd SalesGPT-Integration
   hs project open
   ```
   This opens: https://app.hubspot.com/developer-projects/244348310/project/SalesGPT-Integration

2. **Go to Distribution tab:**
   - Click on **"salesgpt_integration"** (the app component)
   - Click the **"Distribution"** tab (next to Auth tab)

3. **Install the app:**
   - Under **"Standard install"** section
   - Click **"Install now"** button
   - Review the permissions/scopes
   - Check the box to authorize installing an unverified app
   - Click **"Connect app"**

4. **Get Access Token:**
   - After installation, go back to **"Auth"** tab
   - The **"Access Token"** should now be visible
   - Copy the entire access token

5. **Update .env:**
   ```bash
   cd /Users/JJR/SalesGPT
   python3 update_hubspot_token.py
   ```
   Paste the access token when prompted.

### Method 2: Direct URL

1. Go to: https://app.hubspot.com/developer-projects/244348310/project/SalesGPT-Integration
2. Click **"salesgpt_integration"**
3. Go to **"Distribution"** tab
4. Click **"Install now"**
5. Authorize the app
6. Go to **"Auth"** tab → Copy Access Token

## After Installation

Once installed, the app will:
- ✅ Generate an access token
- ✅ Appear in Settings → Integrations → Connected Apps
- ✅ Be ready for API calls

## Verify Installation

After installing and getting the token:

```bash
python3 verify_hubspot_token.py
```

You should see:
```
✅ SUCCESS! Token is valid and working
```

## Troubleshooting

**"Install now button not visible"**
- Make sure you're on the Distribution tab
- Check that you're viewing the app component (salesgpt_integration)
- Refresh the page

**"Access token still not visible"**
- Make sure you completed the installation
- Check Connected Apps: Settings → Integrations → Connected Apps
- The token should be in the app's Auth tab after installation

