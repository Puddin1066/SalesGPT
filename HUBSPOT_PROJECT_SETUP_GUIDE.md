# Complete HubSpot Project Setup Guide

Based on: [Creating Private Apps with Projects](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/build-with-projects/create-private-apps-with-projects#create-a-private-app-within-a-project)

## Prerequisites

✅ HubSpot CLI installed (v7.11.2)  
⏳ HubSpot CLI authenticated (need to do this)

## Step 1: Authenticate HubSpot CLI

```bash
hs account auth
```

**You'll be prompted to:**

1. **Choose authentication method:**
   - "Open HubSpot to copy your personal access key" (opens browser)
   - "Enter existing personal access key" (paste directly)

2. **Get Personal Access Key:**
   - Go to: https://app.hubspot.com/settings/integrations/private-apps
   - Create Private App → Auth tab → Copy token
   - Or use existing token

3. **Paste the token** when prompted

**Result:** CLI config saved to `~/.hscli/config.yml`

## Step 2: Create the Project

```bash
hs project create --platform-version 2025.1
```

**Prompts:**
1. **Project name:** Enter name (e.g., "SalesGPT-Integration")
2. **Folder location:** Confirm directory (default: current directory)
3. **Template:** Select **"CRM getting started with private apps"**

**Result:** Project created with structure:

```
your-project-name/
├── hsproject.json
└── src/
    └── app/
        ├── app.json              # App configuration
        ├── app.functions/        # Serverless functions
        │   ├── example-function.js
        │   ├── package.json
        │   └── serverless.json
        ├── extensions/           # UI extensions
        │   ├── example-card.json
        │   ├── Example.jsx
        │   └── package.json
        └── webhooks/             # Webhook configs
            └── webhook.json
```

## Step 3: Configure App Scopes

Edit `src/app/app.json`:

```json
{
  "name": "SalesGPT Integration",
  "description": "HubSpot integration for SalesGPT",
  "uid": "salesgpt_integration",
  "scopes": [
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.deals.read",
    "crm.objects.deals.write"
  ],
  "public": false,
  "extensions": {
    "crm": {
      "cards": []
    }
  },
  "webhooks": {
    "file": "./webhooks/webhooks.json"
  }
}
```

**Important scopes for this repo:**
- `crm.objects.contacts.read`
- `crm.objects.contacts.write`
- `crm.objects.deals.read`
- `crm.objects.deals.write`

## Step 4: Upload Project to HubSpot

```bash
cd your-project-name
hs project upload
```

**This will:**
- Validate project files
- Build the app
- Upload to HubSpot
- Create private app in your account
- Auto-deploy if successful

## Step 5: Get Access Token

After upload:

1. **Go to HubSpot:**
   - Navigate to **Development** → **Legacy apps**
   - Click your app name

2. **Get token:**
   - Go to **Auth** tab
   - Copy the **Access Token**

3. **Update .env:**
   ```bash
   python3 update_hubspot_token.py
   # Paste your token
   ```

4. **Verify:**
   ```bash
   python3 verify_hubspot_token.py
   ```

## Project Features

The created project includes:

### Serverless Functions
- Located in `app.functions/`
- Can be used for UI extension backends
- Includes HubSpot Node.js client library

### UI Extensions
- Located in `extensions/`
- React-based components
- Custom CRM cards
- **Note:** Requires Enterprise subscription for standard accounts

### Webhooks
- Located in `webhooks/`
- Configure webhook subscriptions
- Update `targetUrl` to your backend

## For This Repository

**If you just need API access:**
- The project method works, but is more complex
- Simpler: Just get token from UI
- Both give you the same access token

**If you want to build extensions:**
- Use the project method
- Better structure and logging
- Supports serverless functions

## Quick Reference

```bash
# 1. Authenticate
hs account auth

# 2. Create project
hs project create --platform-version 2025.1
# Select: "CRM getting started with private apps"

# 3. Configure (edit src/app/app.json)

# 4. Upload
cd your-project-name
hs project upload

# 5. Get token from HubSpot UI
# Development → Legacy apps → Your app → Auth tab

# 6. Update .env
python3 update_hubspot_token.py
```

## Troubleshooting

**"Config file not found"**
- Run `hs account auth` first

**"Authentication failed"**
- Make sure you copied the entire Personal Access Key
- Token should be 100+ characters

**"Project upload failed"**
- Check `app.json` syntax
- Verify scopes are valid
- Check HubSpot account permissions

## References

- [Creating Private Apps with Projects](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/build-with-projects/create-private-apps-with-projects#create-a-private-app-within-a-project)
- [HubSpot CLI Documentation](https://developers.hubspot.com/docs/developer-tooling/local-development/hubspot-cli/install-the-cli)



