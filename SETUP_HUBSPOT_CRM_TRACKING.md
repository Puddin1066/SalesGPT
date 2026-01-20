# Setup HubSpot CRM Tracking - Step by Step

## Overview

This guide will help you set up HubSpot CRM tracking for your SalesGPT pipeline. Once configured, HubSpot will automatically:
- Create contacts for all leads
- Track pipeline stages (idle → engaged → booked → closed)
- Create deals for interested leads
- Provide full sales visibility

## Prerequisites

✅ HubSpot app created: `salesgpt_integration`  
✅ App deployed: Build #1 succeeded  
⏳ App installed: **Need to do this**  
⏳ Access token: **Need to get this**

## Step 1: Install the HubSpot App

1. **Open the project in HubSpot:**
   ```bash
   cd SalesGPT-Integration
   hs project open
   ```
   Or manually navigate to: HubSpot → Development → Projects → SalesGPT-Integration

2. **Click on the app:**
   - In the project page, click on `salesgpt_integration` (the app component)

3. **Go to Distribution tab:**
   - Click the "Distribution" tab (next to "Overview", "Auth", etc.)

4. **Install the app:**
   - Click "Install now" button
   - Review the permissions (contacts read/write, deals read/write)
   - Click "Connect app" or "Authorize"

5. **Wait for installation:**
   - The app should install successfully
   - You'll see a confirmation message

## Step 2: Get the Access Token

1. **Go to Auth tab:**
   - After installation, click the "Auth" tab

2. **Copy the Access Token:**
   - You should see an "Access Token" field
   - Click "Show token" or "Copy" button
   - Copy the entire token (should be 100+ characters)

3. **Save it somewhere temporarily:**
   - You'll need to paste it into `.env` file

## Step 3: Update Environment Variables

1. **Open your `.env` file:**
   ```bash
   cd /Users/JJR/SalesGPT
   # Edit .env file
   ```

2. **Update HUBSPOT_API_KEY:**
   ```env
   # HubSpot CRM
   HUBSPOT_API_KEY=your-new-access-token-here
   ```
   
   **Important:**
   - Replace `your-new-access-token-here` with the token you copied
   - Remove or comment out the old `HUBSPOT_API_KEY` line
   - Remove or comment out `HUBSPOT_PAT` if it exists

3. **Save the file**

## Step 4: Verify the Connection

1. **Test the connection:**
   ```bash
   python3 verify_hubspot_token.py
   ```

2. **Expected output:**
   ```
   ✅ SUCCESS! Token is valid and working
   ```

3. **If it fails:**
   - Double-check the token was copied correctly
   - Make sure there are no extra spaces
   - Verify the app is installed

## Step 5: Test CRM Tracking

1. **Test creating a contact:**
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
   print(f'Contact created: {contact_id}')
   "
   ```

2. **Check in HubSpot:**
   - Go to HubSpot → Contacts
   - You should see the test contact

## Step 6: Verify Integration in Pipeline

The CRM tracking is already integrated into your pipeline. It will automatically:

1. **When leads are generated** (in `main_agent.py`):
   - Creates HubSpot contacts for all leads
   - Stores contact IDs for tracking

2. **When leads reply** (in `handle_reply`):
   - Updates pipeline stage based on intent:
     - "interested" → "booked"
     - "curious/neutral" → "engaged"
     - "objection" → "engaged"

3. **Pipeline stages tracked:**
   - `idle` → Initial state
   - `engaged` → Lead responded
   - `booked` → Call scheduled
   - `closed` → Deal won/lost

## Step 7: View Your CRM Data

1. **In HubSpot UI:**
   - Go to HubSpot → Contacts (see all leads)
   - Go to HubSpot → Deals (see pipeline)
   - Go to HubSpot → Reports (see metrics)

2. **Pipeline visibility:**
   - See how many leads are in each stage
   - Track conversion rates
   - Monitor deal progression

## Troubleshooting

### Token not working?
- Make sure app is installed (not just created)
- Verify token is from "Auth" tab (not old API key)
- Check token length (should be 100+ characters)

### Can't find Distribution tab?
- Make sure you clicked on the app component (`salesgpt_integration`)
- Not the project page, but the app page

### App won't install?
- Check that you have proper HubSpot permissions
- Verify the app build succeeded
- Try refreshing the page

### Contacts not creating?
- Check token is valid: `python3 verify_hubspot_token.py`
- Verify scopes include `crm.objects.contacts.write`
- Check HubSpot API logs for errors

## Quick Reference

**Install app:**
```bash
cd SalesGPT-Integration && hs project open
# Then: Click app → Distribution tab → Install now
```

**Get token:**
```
Click app → Auth tab → Copy Access Token
```

**Update .env:**
```env
HUBSPOT_API_KEY=your-token-here
```

**Verify:**
```bash
python3 verify_hubspot_token.py
```

## What Gets Tracked

Once set up, HubSpot will automatically track:

- ✅ **All leads** as contacts
- ✅ **Pipeline stages** (idle → engaged → booked → closed)
- ✅ **Deals** for interested leads
- ✅ **Email interactions** (via contact records)
- ✅ **Conversion metrics** (via reports)

## Next Steps

After setup:
1. Run your pipeline: `python3 main_agent.py`
2. Check HubSpot → Contacts to see leads
3. Monitor pipeline stages as leads progress
4. Use HubSpot reports for sales analytics



