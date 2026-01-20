# Create HubSpot Private App Project - Step by Step

## Prerequisites

1. ✅ HubSpot CLI installed (v7.11.2 - you have this)
2. ⏳ HubSpot CLI authenticated (need to do this first)

## Step 1: Authenticate HubSpot CLI

Before creating a project, you need to authenticate:

```bash
hs account auth
```

This will prompt you to:
1. **Choose authentication method:**
   - "Open HubSpot to copy your personal access key" (recommended)
   - "Enter existing personal access key"

2. **If you choose "Open HubSpot":**
   - Browser will open to HubSpot
   - Copy your Personal Access Key
   - Paste it into the terminal

3. **If you choose "Enter existing":**
   - Paste your Personal Access Key directly

**Note:** You can get a Personal Access Key from:
- https://app.hubspot.com/settings/integrations/private-apps
- Create Private App → Auth tab → Copy token

## Step 2: Create the Project

Once authenticated, create the project:

```bash
hs project create --platform-version 2025.1
```

**Prompts you'll see:**
1. **Project name:** Enter a name (e.g., "SalesGPT-Integration")
2. **Folder location:** Confirm or change the directory
3. **Template selection:** Choose "CRM getting started with private apps"

## Step 3: Project Structure

After creation, you'll have:

```
your-project-name/
├── hsproject.json
└── src/
    └── app/
        ├── app.json          # App configuration
        ├── app.functions/    # Serverless functions
        ├── extensions/       # UI extensions
        └── webhooks/         # Webhook configs
```

## Step 4: Configure App

Edit `src/app/app.json` to set:
- **name:** Your app name
- **scopes:** Required permissions
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.objects.deals.read`
  - `crm.objects.deals.write`

## Step 5: Upload to HubSpot

```bash
cd your-project-name
hs project upload
```

This will:
- Validate your project
- Build the app
- Upload to HubSpot
- Create the private app in your account

## Step 6: Get Access Token

After upload:

1. Go to HubSpot: **Development → Legacy apps**
2. Click your app name
3. Go to **Auth** tab
4. Copy the **Access Token**
5. Add to `.env`: `HUBSPOT_API_KEY=your-token-here`

## Alternative: Skip Project, Just Get Token

If you just need the access token (not building extensions):

**Faster method:**
1. Go to: https://app.hubspot.com/settings/integrations/private-apps
2. Create Private App
3. Copy token from Auth tab
4. Add to `.env`

This gives you the same token without creating a project.

## Next Steps

After getting your token:
```bash
python3 update_hubspot_token.py
python3 verify_hubspot_token.py
```



