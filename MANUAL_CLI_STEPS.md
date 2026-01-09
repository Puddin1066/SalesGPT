# Manual CLI Steps to Complete

## Current Status

✅ Project created: `SalesGPT-Integration`  
⏳ App component needs to be added

## Complete These Steps in Your Terminal

### Step 1: Add App to Project

```bash
cd SalesGPT-Integration
hs project add
```

**When prompted:**
1. **Distribution:** Use arrow keys to select **"Privately"** → Press Enter
2. **Authentication:** Select **"Static Auth"** (first option) → Press Enter  
3. **Features:** Press Enter (no features needed)

### Step 2: Upload to HubSpot

```bash
hs project upload
```

This will:
- Validate your project
- Build the app
- Upload to HubSpot
- Create the app in your account

### Step 3: Get Access Token

**Option A: Using CLI**
```bash
hs project open
```
This opens the project in your browser, then:
- Click your app name/UID
- Go to **Auth** tab
- Copy the **Access Token**

**Option B: Direct URL**
- Go to: HubSpot → Development → Projects
- Click "SalesGPT-Integration" project
- Click your app UID
- Go to **Auth** tab
- Copy the **Access Token**

### Step 4: Update .env

```bash
cd /Users/JJR/SalesGPT
python3 update_hubspot_token.py
```

Paste your access token when prompted.

### Step 5: Verify

```bash
python3 verify_hubspot_token.py
```

## Alternative: Simpler UI Method

If the CLI steps seem too complex:

1. **Go to:** https://app.hubspot.com/settings/integrations/private-apps
2. **Click:** "Create a private app"
3. **Set scopes:** contacts.read, contacts.write, deals.read, deals.write
4. **Get token:** Auth tab → Copy token
5. **Update .env:** `python3 update_hubspot_token.py`

**This gives you the same token in 2 minutes!**

## Recommendation

For your use case (just API access), the **UI method is faster and simpler**. The CLI method is better if you plan to build extensions or serverless functions later.

