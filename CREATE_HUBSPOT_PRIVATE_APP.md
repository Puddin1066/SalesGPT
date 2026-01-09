# How to Create a HubSpot Private App

**Based on:** [HubSpot Developer Platform Overview](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/overview)

## Two Methods Available

### Method 1: Legacy Private App (Recommended for API Access) ⭐

**Best for:** Just needing an access token for API calls (your use case)

- ✅ Simple and fast
- ✅ No CLI required
- ✅ Perfect for API-only access
- ✅ Still fully supported by HubSpot

### Method 2: 2025.2 Developer Platform App (For Full App Development)

**Best for:** Building apps with extensions, serverless functions, webhooks

- ✅ Latest platform features
- ✅ File-based build framework
- ✅ Requires HubSpot CLI
- ✅ More complex setup

**Note:** According to HubSpot docs: *"If you're less familiar with using the CLI and you only need an access token for a few HubSpot APIs, you may want to create a legacy private app."*

## Method 1: Legacy Private App (Recommended)

### Step-by-Step Guide

### Step 1: Navigate to Private Apps

1. **Log into HubSpot:**
   - Go to: https://app.hubspot.com
   - Sign in to your account

2. **Go to Settings:**
   - Click the **gear icon (⚙️)** in the top right
   - Or go directly to: https://app.hubspot.com/settings/integrations/private-apps

3. **Access Private Apps:**
   - In the left sidebar, go to **"Integrations"**
   - Click **"Private Apps"**

### Step 2: Create the Private App

1. **Click "Create a private app" button**
   - This is usually at the top right of the Private Apps page

2. **Enter App Details:**
   - **App name:** Enter a name (e.g., "SalesGPT Integration")
   - **Description:** (Optional) Add a description

3. **Click "Create app"**

### Step 3: Configure Scopes (Permissions)

1. **Go to the "Scopes" tab** (if not already there)

2. **Select the required scopes:**
   - ✅ `crm.objects.contacts.read` - Read contacts
   - ✅ `crm.objects.contacts.write` - Create/update contacts
   - ✅ `crm.objects.deals.read` - Read deals
   - ✅ `crm.objects.deals.write` - Create/update deals
   - (Optional) `crm.schemas.custom.read` - If using Operations Hub

3. **Click "Save"** or the app will auto-save

### Step 4: Get Your Access Token

1. **Go to the "Auth" tab**

2. **View your token:**
   - Click **"Show token"** or **"Copy token"**
   - The token will be displayed (100+ characters)

3. **Copy the entire token:**
   - Make sure you copy the complete token
   - It should be a long string (100+ characters)

### Step 5: Update Your .env File

1. **Use the helper script:**
   ```bash
   python3 update_hubspot_token.py
   ```
   Then paste your token when prompted.

2. **Or manually edit `.env`:**
   - Open `.env` file
   - Find: `HUBSPOT_API_KEY=...`
   - Replace with: `HUBSPOT_API_KEY=your-new-token-here`
   - Save the file

### Step 6: Verify It Works

```bash
python3 verify_hubspot_token.py
```

You should see:
```
✅ SUCCESS! Token is valid and working
```

## Visual Guide

```
HubSpot → Settings (⚙️) → Integrations → Private Apps
  ↓
Click "Create a private app"
  ↓
Enter name → Create app
  ↓
Go to "Scopes" tab → Select permissions → Save
  ↓
Go to "Auth" tab → Show token → Copy token
  ↓
Update .env file → Verify connection
```

## Important Notes

### Token Security
- **Never share your token publicly**
- **Don't commit `.env` to git**
- **Keep your token secure**

### Regenerating Tokens
- If you need a new token, go to **Auth tab → Regenerate token**
- The old token will stop working immediately
- Update `.env` with the new token

### App Management
- You can have multiple Private Apps
- Each app has its own token
- You can delete apps from the Auth tab

## Troubleshooting

### "I don't see Private Apps option"
- Make sure you're logged in as a Super Admin
- Some accounts may need to enable this feature
- Try: Settings → Integrations → Private Apps

### "I can't create an app"
- Free tier accounts can create Private Apps
- Make sure you have proper permissions
- Try refreshing the page

### "Token doesn't work"
- Make sure you copied the ENTIRE token
- Check for extra spaces or quotes
- Verify scopes are correct
- Try regenerating the token

## Method 2: 2025.2 Developer Platform App (Using CLI)

**Based on:** [Create a new app using the CLI](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app)

If you want to use the new developer platform with CLI:

### Quick Start (Easiest)

```bash
hs get-started
```

This creates a demo app with boilerplate code.

### Full Setup

```bash
hs project create
```

**When prompted, select:**
- **Base contents:** App
- **Distribution:** Private (or specific accounts) - since you only need one account
- **Auth:** Static token (not OAuth) - simpler for single account
- **Features:** None (or minimal) - you just need API access

### After Creation

1. **Upload to HubSpot:**
   ```bash
   cd your-project-name
   hs project upload
   ```

2. **Get Access Token:**
   - Run: `hs project open` (opens in browser)
   - Or go to: HubSpot → Development → Projects → Your app
   - Click **Auth** tab
   - Copy the **Access Token** (for static token) or get Client ID/Secret (for OAuth)

3. **Update .env:**
   ```bash
   python3 update_hubspot_token.py
   ```

### When to Use This Method

✅ Use if you want:
- Project-based structure
- Version control for app config
- Future extensibility (extensions, serverless functions)
- Better logging and debugging

❌ Skip if you:
- Just need API access (use Method 1 instead)
- Don't need extensions or serverless functions
- Want the simplest setup

**Note:** For just API access, Method 1 (Legacy Private App) is still simpler and faster.

## Accessing Legacy Apps

After creating a legacy private app, you can view it at:
- **HubSpot → Development → Legacy Apps**

This is where you'll find:
- Your app's access token
- API call logs
- App settings

## Quick Reference URLs

- **Private Apps (Legacy):** https://app.hubspot.com/settings/integrations/private-apps
- **Legacy Apps (New Location):** HubSpot → Development → Legacy Apps
- **HubSpot Settings:** https://app.hubspot.com/settings
- **HubSpot Login:** https://app.hubspot.com
- **Developer Platform Docs:** https://developers.hubspot.com/docs/apps/developer-platform/build-apps/overview

## After Creating the App

Once you have your token:

1. ✅ Update `.env` with the token
2. ✅ Verify: `python3 verify_hubspot_token.py`
3. ✅ Test: `python3 test_hubspot_connection.py`

Your HubSpot integration is ready to use!

