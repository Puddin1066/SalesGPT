# Fix HubSpot API Connection - Step by Step

## Current Problem
❌ Token in `.env` is **expired/invalid**
**REDACTED**: HubSpot personal access key/token removed. Use your own token via env var (e.g. \1REDACTEDs: 401 Unauthorized
- Error: Token expired 20460 days ago

## Solution: Get a NEW Token

### Step 1: Get New Token from HubSpot

1. **Open HubSpot:**
   - Go to: https://app.hubspot.com/settings/integrations/private-apps
   - Or: Settings → Integrations → Private Apps

2. **Find Your Private App:**
   - Click on the **app name** (not just toggle on/off)
   - This opens the app details

3. **Go to Auth Tab:**
   - Click the **"Auth"** tab
   - You should see your access token

4. **Regenerate Token:**
   - Look for **"Regenerate token"** or **"Reset token"** button
   - Click it
   - **Important:** If you don't see a regenerate button, you need to:
     - Delete the existing Private App
     - Create a NEW Private App
     - Copy the token from the new app

5. **Copy the NEW Token:**
   - Click **"Show token"** if needed
   - Copy the **entire token** (should be 100+ characters)
   - **Make sure it's DIFFERENT from the old one!**

### Step 2: Update .env File

**Option A: Use the helper script (Easiest)**
```bash
python3 update_hubspot_token.py
# Then paste your new token when prompted
```

**Option B: Manual update**
1. Open `.env` file in your editor
2. Find this line:
   ```
**REDACTED**: Example command token removed (Authorization: Bearer REDACTED).
   ```
3. Replace with:
   ```
   \1REDACTEDs

```bash
python3 verify_hubspot_token.py
```

You should see:
```
✅ SUCCESS! Token is valid and working
   📊 Can access CRM contacts
   ✅ HubSpotAgent initialized successfully
```

## Troubleshooting

### "I don't see a Regenerate button"
- Delete the Private App
- Create a NEW Private App
- Copy the token from the new app

### "The token looks the same"
- Make sure you're copying from a NEW app or regenerated token
- The new token should be completely different

### "Still getting 401 error"
- Verify you copied the ENTIRE token (no truncation)
- Check for extra spaces or quotes in .env
- Make sure the token is on one line
- Try deleting and recreating the Private App

### "Token works but no permissions"
- Go to Private App → Scopes tab
- Enable these scopes:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.objects.deals.read`
  - `crm.objects.deals.write`

## Quick Checklist

- [ ] Opened HubSpot Private Apps page
- [ ] Clicked on Private App name (not just toggle)
- [ ] Went to "Auth" tab
- [ ] Regenerated token OR created new app
- [ ] Copied NEW token (different from old one)
- [ ] Updated `.env` file with new token
- [ ] Ran `python3 verify_hubspot_token.py`
- [ ] Got ✅ SUCCESS message

