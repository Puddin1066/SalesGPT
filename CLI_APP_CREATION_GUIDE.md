# Creating HubSpot App with CLI - Step by Step

## Quick Start Method

```bash
hs get-started
```

**When prompted:**
1. Select: **App** (not CMS assets)
2. Follow the prompts to create a demo app

## Full Setup Method

```bash
hs project create
```

**When prompted, make these selections:**

### Step 1: Base Contents
- Select: **App**

### Step 2: Distribution
- Select: **Private** (or "Specific accounts")
- This limits the app to your account only

### Step 3: Authentication
- Select: **Static token** (not OAuth)
- Static token is simpler for single-account use
- OAuth is only needed for multi-account apps

### Step 4: Features
- Press **spacebar** to deselect all features
- Or select **None** if available
- You don't need:
  - ❌ Card (UI extension)
  - ❌ App Function (serverless)
  - ❌ Settings (app settings page)
  - ❌ Webhooks
  - ❌ Custom Workflow Action

**Why no features?** You just need API access, not UI extensions.

### Step 5: Project Details
- **Project name:** Enter a name (e.g., "SalesGPT-Integration")
- **Folder location:** Accept default or specify

## After Project Creation

### 1. Upload to HubSpot

```bash
cd your-project-name
hs project upload
```

This will:
- Validate your project
- Build the app
- Upload to HubSpot
- Create the app in your account

### 2. Get Your Access Token

**Option A: Using CLI**
```bash
hs project open
```
This opens the project in your browser, then:
- Click your app name
- Go to **Auth** tab
- Copy the **Access Token**

**Option B: Direct URL**
- Go to: HubSpot → Development → Projects
- Click your project name
- Click your app UID
- Go to **Auth** tab
- Copy the **Access Token**

### 3. Update .env

```bash
python3 update_hubspot_token.py
```

Paste your access token when prompted.

### 4. Verify

```bash
python3 verify_hubspot_token.py
```

## Configuration for Static Token

If you selected "Static token" authentication, the app will have:
- A single access token (no OAuth flow needed)
- Token doesn't expire (unless regenerated)
- Perfect for single-account integrations

## Troubleshooting

### "Config file not found"
- Run `hs account auth` first
- You already did this, so you should be good!

### "Project creation failed"
- Make sure you're in the right directory
- Check CLI version: `hs --version` (should be 7.6.0+)

### "Can't find access token"
- Make sure you uploaded the project: `hs project upload`
- Check the Auth tab in HubSpot
- For static token, it should be visible immediately

## Quick Reference

```bash
# 1. Create project
hs project create
# Select: App → Private → Static token → No features

# 2. Upload
cd project-name
hs project upload

# 3. Get token
hs project open
# Or: HubSpot → Development → Projects → Your app → Auth tab

# 4. Update .env
python3 update_hubspot_token.py

# 5. Verify
python3 verify_hubspot_token.py
```

## Alternative: Legacy Private App (Simpler)

If the CLI method seems too complex, you can still use the simpler UI method:
- Go to: https://app.hubspot.com/settings/integrations/private-apps
- Create Private App → Get token

Both methods give you the same access token!

