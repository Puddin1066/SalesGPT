# How to Get a NEW HubSpot Personal Access Key

## Important: Deactivating/Reactivating ≠ New Token

**Deactivating and reactivating a Private App does NOT generate a new token** - it just enables/disables the same token.

## To Get a NEW Token, You Must:

### Option 1: Regenerate Token (Recommended)

1. Go to: https://app.hubspot.com/settings/integrations/private-apps
2. Click on your **Private App name** (not just activate/deactivate)
3. Go to the **"Auth"** tab
4. Look for one of these options:
   - **"Regenerate token"** button
   - **"Show token"** → then **"Regenerate"**
   - **"Reset token"** or **"Generate new token"**
5. Click to regenerate
6. **Copy the NEW token** (it will be different from the old one)
7. **Important**: The old token will stop working immediately

### Option 2: Delete and Recreate Private App

If there's no "Regenerate" option:

1. Go to: https://app.hubspot.com/settings/integrations/private-apps
2. Find your Private App
3. Click the **three dots (⋯)** or **Delete** button
4. Confirm deletion
5. Click **"Create a private app"** again
6. Use the same name or a new name
7. Set the same scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
8. Click **"Create app"**
9. Go to **"Auth"** tab
10. Click **"Show token"**
11. Copy the **NEW token**

## Verify You Have a New Token

Compare the tokens:
**REDACTED**: HubSpot token removed.
- **New token** should be **completely different**

If they're the same, you didn't regenerate - you just activated the old one.

## After Getting New Token

1. Update `.env`:
   ```bash
   python3 update_hubspot_token.py YOUR_NEW_TOKEN
   ```

2. Verify it works:
   ```bash
   python3 verify_hubspot_token.py
   ```

## Troubleshooting

**"I don't see a Regenerate button"**
- Some HubSpot accounts may not have this option
- Use Option 2: Delete and recreate the app

**"The token looks the same"**
- Make sure you're copying from the "Auth" tab, not just viewing the app
- Try deleting and recreating the app

**"Token still doesn't work"**
- Make sure you copied the ENTIRE token (100+ characters)
- Check for extra spaces or line breaks
- Verify the scopes are correct



