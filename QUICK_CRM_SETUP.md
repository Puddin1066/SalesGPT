# Quick HubSpot CRM Setup Guide

## 🎯 Goal
Set up HubSpot CRM tracking so your pipeline automatically:
- Creates contacts for all leads
- Tracks pipeline stages (idle → engaged → booked → closed)
- Creates deals for interested leads

## ⚡ Quick Setup (3 Steps)

### Step 1: Install the App
1. **Project should be open in your browser** (just opened it)
2. **Click on `salesgpt_integration`** (the app component, not the project)
3. **Go to "Distribution" tab**
4. **Click "Install now"**
5. **Authorize the app** (review permissions, click "Connect app")

### Step 2: Get Access Token
1. **Go to "Auth" tab** (after installation)
2. **Click "Show token" or "Copy"**
3. **Copy the entire Access Token** (100+ characters)

### Step 3: Update .env File

**Option A: Use the update script (easiest)**
```bash
cd /Users/JJR/SalesGPT
python3 update_hubspot_token.py YOUR_TOKEN_HERE
```

**Option B: Manual edit**
```bash
# Edit .env file
# Set: HUBSPOT_API_KEY=your-token-here
```

### Step 4: Verify It Works
```bash
python3 verify_hubspot_token.py
```

Expected output: `✅ SUCCESS! Token is valid and working`

## ✅ What Happens Next

Once set up, your pipeline will automatically:

1. **When leads are generated:**
   - Creates HubSpot contacts automatically
   - Stores contact IDs for tracking

2. **When leads reply:**
   - Updates pipeline stage based on intent:
     - "interested" → "booked"
     - "curious/neutral" → "engaged"
     - "objection" → "engaged"

3. **In HubSpot UI:**
   - See all leads in Contacts
   - Track pipeline in Deals
   - View reports and metrics

## 🔍 Verify CRM Tracking

After setup, test it:

```bash
python3 -c "
from services.crm import HubSpotAgent
agent = HubSpotAgent()
contact_id = agent.create_contact(
    email='test@example.com',
    first_name='Test',
    last_name='User',
    company='Test Company'
)
print(f'✅ Contact created: {contact_id}')
"
```

Then check HubSpot → Contacts to see the test contact.

## 📊 View Your CRM Data

- **Contacts:** HubSpot → Contacts (all leads)
- **Deals:** HubSpot → Deals (pipeline stages)
- **Reports:** HubSpot → Reports (metrics)

## 🆘 Troubleshooting

**Token not working?**
- Make sure app is **installed** (not just created)
- Token should be from "Auth" tab (100+ chars)
- Run: `python3 verify_hubspot_token.py`

**Can't find Distribution tab?**
- Make sure you clicked on the **app** (`salesgpt_integration`)
- Not the project page, but the app component page

**Contacts not creating?**
- Verify token: `python3 verify_hubspot_token.py`
- Check HubSpot → Contacts to see if they're there
- Check code logs for errors

## 🎉 Done!

Once verified, your CRM tracking is live. Every time you run the pipeline, HubSpot will automatically track all leads and their progression through your sales funnel.



