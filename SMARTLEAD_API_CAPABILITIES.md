# Smartlead API Capabilities & Limitations

## ✅ What Works via API

### Confirmed Working Endpoints

1. **GET `/client`** ✅
   - Status: 200 OK
   - Returns: Account/client information
   - Use: Verify API key and account status

2. **GET `/campaigns`** ✅
   - Status: 200 OK
   - Returns: List of existing campaigns
   - Use: List all campaigns, check if campaign exists

### Authentication ✅
- **Method**: Query parameter (`?api_key=...`)
- **Status**: Working correctly
- **Base URL**: `https://server.smartlead.ai/api/v1`

### Rate Limits
- **Limit**: 60 requests per 60 seconds
- **Headers**: `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-reset`
- **Batching**: Up to 350 leads per upload

---

## ⚠️ What Requires Dashboard Setup

### Endpoints Returning 404

1. **POST `/campaigns`** ❌
   - Status: 404 Not Found
   - **Workaround**: Create campaigns via Smartlead dashboard
   - **Reason**: May require plan upgrade or initial dashboard setup

2. **GET `/mailboxes`** ❌
   - Status: 404 Not Found
   - **Workaround**: Add mailboxes via dashboard (Settings → Mailboxes)
   - **Reason**: Mailboxes must be configured in dashboard first

3. **POST `/campaigns/{id}/sequences`** ⚠️
   - **Status**: Unknown (requires existing campaign)
   - **Workaround**: Add sequences via dashboard or after campaign creation

4. **POST `/campaigns/{id}/leads`** ⚠️
   - **Status**: Unknown (requires existing campaign)
   - **Workaround**: Add leads via dashboard or after campaign creation

---

## 🔄 Hybrid Approach (Recommended)

Since some operations require dashboard setup, use a **hybrid approach**:

### Step 1: Dashboard Setup (Required First)
1. **Add Mailboxes**
   - Go to https://app.smartlead.ai
   - Settings → Mailboxes
   - Add your sending email accounts
   - Wait for warm-up

2. **Create Initial Campaign** (if API doesn't work)
   - Dashboard → Campaigns → Create Campaign
   - Set up basic campaign settings
   - Note the Campaign ID

### Step 2: API Operations (After Dashboard Setup)
1. **List Campaigns**
   ```python
   from services.outbound.smartlead_agent import SmartleadAgent
   agent = SmartleadAgent()
   campaigns = requests.get(
       'https://server.smartlead.ai/api/v1/campaigns',
       params={'api_key': agent.api_key}
   ).json()
   ```

2. **Add Leads to Campaign** (if endpoint works)
   ```python
   agent.add_leads_to_campaign(campaign_id, leads)
   ```

3. **Monitor Campaigns**
   ```python
   # Use GET /campaigns to check status
   ```

---

## 📋 Setup Checklist

### Via Dashboard (Required)
- [ ] Activate API access in account settings
- [ ] Add mailboxes (Settings → Mailboxes)
- [ ] Wait for mailbox warm-up to complete
- [ ] Create initial campaign (if API creation fails)
- [ ] Configure webhook URL (Settings → Webhooks)

### Via API (After Dashboard Setup)
- [x] Verify API key authentication
- [x] List existing campaigns
- [ ] Add leads to campaigns (test after campaign exists)
- [ ] Add sequences (test after campaign exists)
- [ ] Monitor campaign status

---

## 🛠️ Current Workaround Script

Since campaign creation via API returns 404, use this workflow:

1. **Create campaign manually in dashboard**
2. **Get campaign ID from dashboard**
3. **Use API to add leads and sequences**

Or use the setup script which will:
- Check if campaigns exist
- Guide you to create in dashboard if needed
- Help configure sequences and leads via API once campaign exists

---

## 🔍 Testing Endpoints

To test which endpoints work with your account:

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('SMARTLEAD_API_KEY')
base = 'https://server.smartlead.ai/api/v1'

# Test endpoint
endpoint = '/campaigns'
response = requests.get(f'{base}{endpoint}', params={'api_key': api_key})
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
```

---

## 💡 Recommendations

1. **Start with Dashboard**
   - Set up mailboxes and initial campaign in dashboard
   - This ensures everything is properly configured

2. **Use API for Automation**
   - Once setup is complete, use API for:
     - Adding leads in bulk
     - Monitoring campaign status
     - Managing sequences (if endpoints work)

3. **Check Plan Limitations**
   - Some API features may require specific plan tiers
   - Contact Smartlead support if endpoints don't work

4. **Monitor Rate Limits**
   - Stay under 60 requests/minute
   - Use batch operations when possible

---

## 📞 Next Steps

1. **Complete Dashboard Setup**
   - Add mailboxes
   - Create initial campaign
   - Configure webhooks

2. **Test API Endpoints**
   - Verify which endpoints work after dashboard setup
   - Some endpoints may become available after initial configuration

3. **Use Hybrid Approach**
   - Dashboard for setup and configuration
   - API for automation and bulk operations

---

**Last Updated:** January 18, 2026  
**API Key Status:** ✅ Valid  
**Authentication:** ✅ Working  
**Campaign Creation:** ⚠️ Requires dashboard (API returns 404)

