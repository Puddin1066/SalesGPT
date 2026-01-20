# Token vs Key: What You Need for HubSpot

## Short Answer: **They're the Same Thing!** ✅

Both "Personal Access Key" and "Private App Access Token" refer to the **same type of credential** - a long string (100+ characters) used for API authentication.

## Different Names, Same Thing

| HubSpot UI/CLI Name | What It Actually Is | Where to Get It |
|---------------------|---------------------|-----------------|
| **Personal Access Key** (CLI) | Access Token | `hs account auth` or Private Apps UI |
| **Private App Access Token** (UI) | Access Token | Private Apps → Auth tab |
| **Access Token** (OAuth) | Access Token | OAuth flow (different method) |

## For This Repository

You need **ONE** of these:

### Option 1: Private App Access Token (Simplest) ⭐ RECOMMENDED

**What to get:**
- Go to: https://app.hubspot.com/settings/integrations/private-apps
- Create Private App → **Auth tab** → Copy the **"Access Token"**
- This is a long string (100+ characters)

**What to put in .env:**
```env
HUBSPOT_API_KEY=your-access-token-here
```

**Note:** Even though HubSpot UI calls it "Access Token", the code uses `HUBSPOT_API_KEY` as the variable name. That's fine - it works!

### Option 2: Personal Access Key (via CLI)

**What to get:**
```bash
hs account auth
# Follow prompts to get Personal Access Key
```

**What to put in .env:**
```env
HUBSPOT_API_KEY=your-personal-access-key-here
```

**Note:** The CLI calls it "Personal Access Key", but it's the same type of credential.

## What the Code Expects

Looking at the code in `services/crm/hubspot_agent.py`:

```python
self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
```

The code expects:
- **Environment variable**: `HUBSPOT_API_KEY`
- **Value**: Any valid HubSpot access token (Personal Access Key or Private App Token)
- **Format**: Bearer token (100+ character string)

## Summary

✅ **You need:** One access token (called "key" or "token" - doesn't matter)  
✅ **Put it in:** `.env` file as `HUBSPOT_API_KEY=...`  
✅ **Get it from:** Private Apps UI (Auth tab) or HubSpot CLI  
✅ **Both work the same way** - they're just different names for the same credential type

## Quick Checklist

- [ ] Go to Private Apps: https://app.hubspot.com/settings/integrations/private-apps
- [ ] Create/Open Private App
- [ ] Go to "Auth" tab
- [ ] Copy the "Access Token" (or "Show token")
- [ ] Add to `.env`: `HUBSPOT_API_KEY=paste-token-here`
- [ ] Run: `python3 verify_hubspot_token.py`

That's it! The name doesn't matter - just get the token/key from the Auth tab and use it.



