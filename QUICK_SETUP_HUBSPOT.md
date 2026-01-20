# Quick Setup: HubSpot Personal Access Key

## What You Need

1. **Personal Access Key** from HubSpot
2. **`.env` file** in repository root with `HUBSPOT_API_KEY`

## Setup Steps (2 minutes)

### 1. Get Your Personal Access Key

```bash
# Option 1: Via HubSpot UI (Recommended)
# Go to: https://app.hubspot.com/settings/integrations/private-apps
# Create Private App → Auth tab → Copy Access Token

# Option 2: Via HubSpot CLI
npm install -g @hubspot/cli
hs account auth
# Follow prompts to get your Personal Access Key
```

### 2. Add to .env File

Create or edit `.env` in the repository root:

```env
HUBSPOT_API_KEY=your-personal-access-key-here
```

### 3. Verify Setup

```bash
python3 verify_hubspot_token.py
```

Expected output:
```
✅ SUCCESS! Token is valid and working
```

## Required Scopes

When creating your Private App, ensure these scopes are enabled:
- ✅ `crm.objects.contacts.read`
- ✅ `crm.objects.contacts.write`
- ✅ `crm.objects.deals.read`
- ✅ `crm.objects.deals.write`

## That's It!

The code will automatically:
- Read `HUBSPOT_API_KEY` from `.env`
- Use it for API authentication
- Handle all HubSpot CRM operations

## Troubleshooting

**Token expired?**
```bash
# Regenerate token in HubSpot UI, then:
python3 verify_hubspot_token.py
```

**Need help?**
See `HUBSPOT_PERSONAL_ACCESS_KEY_SETUP.md` for detailed instructions.



