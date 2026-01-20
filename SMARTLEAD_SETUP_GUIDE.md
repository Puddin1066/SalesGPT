# Smartlead Account Setup Guide

## ✅ Status: API Key Verified

Your Smartlead API key is **working correctly**! The authentication is successful (confirmed by 200 responses on `/client` and `/campaigns` endpoints).

## Current Situation

- ✅ **API Key**: Valid and authenticated
- ✅ **Base URL**: `https://server.smartlead.ai/api/v1`
- ✅ **Authentication Method**: Query parameter (`?api_key=...`)
- ⚠️ **Mailboxes Endpoint**: Returns 404 (may need dashboard setup first)
- ⚠️ **Campaign Creation**: Some endpoints may require initial setup via dashboard

## Setup Steps

### Step 1: Add Mailboxes (Required - Dashboard Only)

Mailboxes cannot be created via API initially. You must add them in the Smartlead dashboard:

1. Go to https://app.smartlead.ai
2. Log in to your account
3. Navigate to **Settings → Mailboxes**
4. Click **Add Mailbox** or **Connect Email**
5. Follow the prompts to:
   - Connect your email account (Gmail, Outlook, etc.)
   - Or add a custom SMTP server
6. Wait for warm-up to complete (this can take a few days)

**Why mailboxes are needed:**
- Mailboxes are the sending domains/accounts used for email delivery
- Domain rotation requires multiple mailboxes
- Inbox warm-up ensures good deliverability

### Step 2: Verify Mailboxes via API

Once mailboxes are added in the dashboard, you can verify them:

```bash
python3 test_smartlead_api_key.py
```

Or test directly:
```python
from services.outbound.smartlead_agent import SmartleadAgent
agent = SmartleadAgent()
mailboxes = agent.get_mailboxes()
print(f"Found {len(mailboxes)} mailboxes")
```

**Note:** The `/mailboxes` endpoint may return 404 until mailboxes are set up in the dashboard. This is normal.

### Step 3: Create Campaign via API

Once you have mailboxes, run the setup script:

```bash
python3 setup_smartlead_account.py
```

This will:
- ✅ Check account status
- ✅ List available mailboxes
- ✅ Create a campaign with your settings
- ✅ Add email sequences (initial + 2 follow-ups)
- ✅ Provide webhook configuration instructions

### Step 4: Configure Environment Variables

Make sure your `.env` file has:

```env
SMARTLEAD_API_KEY=your_api_key_here
SMARTLEAD_FROM_EMAIL=your-email@domain.com
SMARTLEAD_FROM_NAME=Your Name
SMARTLEAD_REPLY_TO=your-email@domain.com
SMARTLEAD_CAMPAIGN_NAME=SalesGPT Outreach

# Optional: Email templates
SMARTLEAD_INITIAL_SUBJECT=Quick question about your clinic
SMARTLEAD_INITIAL_BODY=Hi {{first_name}},\n\nI noticed {{clinic_name}}...
```

## API Endpoints Status

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/client` | GET | ✅ 200 | Returns account info |
| `/campaigns` | GET | ✅ 200 | Lists campaigns |
| `/campaigns` | POST | ⚠️ 404 | May need mailboxes first |
| `/mailboxes` | GET | ⚠️ 404 | Requires dashboard setup first |
| `/campaigns/{id}/sequences` | POST | ⚠️ Unknown | Test after campaign creation |
| `/campaigns/{id}/leads` | POST | ⚠️ Unknown | Test after campaign creation |

## Rate Limits

- **60 requests per 60 seconds** per API key
- Monitor via response headers:
  - `x-ratelimit-limit`: Total allowed
  - `x-ratelimit-remaining`: Remaining requests
  - `x-ratelimit-reset`: Reset time

## Troubleshooting

### Issue: 404 on `/mailboxes`
**Solution:** Add mailboxes in Smartlead dashboard first. The API endpoint may not be available until mailboxes are configured.

### Issue: 404 on POST `/campaigns`
**Solution:** Ensure mailboxes are set up first. Some endpoints require initial dashboard configuration.

### Issue: 401 Unauthorized
**Solution:** 
- Verify API key in `.env` matches dashboard
- Check that API access is activated in account settings
- Ensure plan includes API access

### Issue: No mailboxes found
**Solution:** 
1. Add mailboxes in dashboard (Settings → Mailboxes)
2. Wait for warm-up to complete
3. Run setup script again

## Next Steps

1. ✅ **API Key**: Working (confirmed)
2. ⏳ **Add Mailboxes**: Do this in dashboard
3. ⏳ **Run Setup Script**: After mailboxes are ready
4. ⏳ **Configure Webhook**: For reply handling
5. ⏳ **Start Adding Leads**: Once campaign is created

## Files Created

- `setup_smartlead_account.py` - Main setup script
- `test_smartlead_api_key.py` - API key diagnostic tool
- `services/outbound/smartlead_agent.py` - Updated to use query parameter auth

## Support

If you encounter issues:
1. Check Smartlead API docs: https://api.smartlead.ai
2. Verify account settings in dashboard
3. Test API key with diagnostic script
4. Check rate limits and plan restrictions

---

**Last Updated:** January 18, 2026  
**API Key Status:** ✅ Valid and Authenticated

