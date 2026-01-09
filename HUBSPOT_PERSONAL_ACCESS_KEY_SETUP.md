# HubSpot Personal Access Key Setup Guide

This guide shows how to set up HubSpot API access using a Personal Access Key (PAK) for this repository.

## What is a Personal Access Key?

A Personal Access Key is a user-level authentication token that allows you to access HubSpot APIs. It's similar to a Private App token but tied to your user account rather than an app.

## Step 1: Generate a Personal Access Key

### Option A: Via HubSpot UI

1. Go to: https://app.hubspot.com/settings/integrations/private-apps
2. Click **"Create a private app"**
3. Provide a name (e.g., "SalesGPT Integration")
4. In the **"Scopes"** tab, select the required permissions:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - (Optional) `crm.schemas.custom.read` (if using Operations Hub)
5. Click **"Create app"**
6. Go to the **"Auth"** tab
7. Click **"Show token"** to reveal your Personal Access Key
8. **Copy this key** - you'll need it for the next step

### Option B: Via HubSpot CLI (if already installed)

```bash
# Install HubSpot CLI if not already installed
npm install -g @hubspot/cli

# Authenticate with HubSpot
hs account auth

# When prompted, you can either:
# 1. Open HubSpot to copy your personal access key
# 2. Enter an existing personal access key
```

The CLI will store the key in `~/.hscli/config.yml`, but for this repo, we'll use it in the `.env` file.

## Step 2: Add to .env File

Add your Personal Access Key to the `.env` file in the repository root:

```bash
# HubSpot API Configuration
HUBSPOT_API_KEY=your-personal-access-key-here
```

**Important:**
- Never commit the `.env` file to version control
- The `.env` file should already be in `.gitignore`
- Keep your Personal Access Key secure

## Step 3: Verify the Setup

Run the verification script to test your connection:

```bash
python3 verify_hubspot_token.py
```

You should see:
```
✅ SUCCESS! Token is valid and working
   📊 Can access CRM contacts
   ✅ HubSpotAgent initialized successfully
```

## Step 4: Test the Integration

Test the full HubSpot integration:

```bash
python3 test_hubspot_connection.py
```

## Troubleshooting

### "Token is expired or invalid"

1. Go back to: https://app.hubspot.com/settings/integrations/private-apps
2. Find your Private App
3. Go to the "Auth" tab
4. Click "Regenerate token"
5. Copy the new token
6. Update `HUBSPOT_API_KEY` in your `.env` file
7. Run `python3 verify_hubspot_token.py` again

### "Insufficient permissions"

1. Go to your Private App settings
2. Click on the app name
3. Go to the "Scopes" tab
4. Ensure these scopes are enabled:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
5. Save changes
6. Test again

### "HUBSPOT_API_KEY not found"

1. Make sure you have a `.env` file in the repository root
2. Check that the file contains: `HUBSPOT_API_KEY=your-token-here`
3. Make sure there are no extra spaces or quotes around the token
4. Run `python3 verify_hubspot_token.py` to verify

## Quick Reference

- **Private Apps**: https://app.hubspot.com/settings/integrations/private-apps
- **HubSpot CLI Docs**: https://developers.hubspot.com/docs/developer-tooling/local-development/hubspot-cli/personal-access-key
- **API Authentication**: https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview

## Environment Variable

The code expects the Personal Access Key in the `.env` file as:

```env
HUBSPOT_API_KEY=your-personal-access-key-here
```

The `HubSpotAgent` class will automatically:
- Read `HUBSPOT_API_KEY` from environment
- Use it for Bearer token authentication
- Handle API requests to HubSpot CRM endpoints

## Security Best Practices

1. **Never commit tokens to git** - Always use `.env` file
2. **Rotate tokens regularly** - Regenerate tokens periodically
3. **Use minimal scopes** - Only grant permissions you need
4. **Store securely** - Keep your `.env` file secure and backed up
5. **Monitor usage** - Check HubSpot for unusual API activity

