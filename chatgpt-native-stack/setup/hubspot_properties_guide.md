# HubSpot Custom Properties Setup Guide

This guide helps you create the required custom properties in HubSpot for the GemFlush campaign.

## Required Properties

Create these 6 custom contact properties in HubSpot:

### 1. vertical (Single-line text)
- **Label:** Vertical
- **Internal Name:** `vertical`
- **Field Type:** Single-line text
- **Values:** `medical`, `legal`, `realestate`, `agencies`
- **Purpose:** Segment contacts by target vertical
- **Required:** Yes

### 2. gemflush_email_sent (Date/Time)
- **Label:** GemFlush Email Sent
- **Internal Name:** `gemflush_email_sent`
- **Field Type:** Date picker (with time)
- **Purpose:** Track when email was sent
- **Required:** No

### 3. gemflush_variant (Single-line text)
- **Label:** GemFlush Variant
- **Internal Name:** `gemflush_variant`
- **Field Type:** Single-line text
- **Values:** `A`, `B`
- **Purpose:** Track A/B test variant
- **Required:** No

### 4. gemflush_email_subject (Single-line text)
- **Label:** GemFlush Email Subject
- **Internal Name:** `gemflush_email_subject`
- **Field Type:** Single-line text
- **Purpose:** Store sent email subject line
- **Required:** No

### 5. gemflush_last_campaign_date (Date)
- **Label:** GemFlush Last Campaign Date
- **Internal Name:** `gemflush_last_campaign_date`
- **Field Type:** Date picker (date only)
- **Purpose:** Track last campaign date
- **Required:** No

### 6. gemflush_sender_email (Single-line text)
- **Label:** GemFlush Sender Email
- **Internal Name:** `gemflush_sender_email`
- **Field Type:** Single-line text
- **Purpose:** Track sender email (Alex@GEMflush.com)
- **Required:** No

## Step-by-Step Instructions

### How to Create Properties in HubSpot:

1. **Log into HubSpot**
   - Go to https://app.hubspot.com

2. **Navigate to Properties**
   - Click Settings (gear icon in top right)
   - Go to: **Properties** → **Contact Properties**

3. **Create Each Property**
   - Click **"Create property"** button
   - Fill in the details from the list above:
     - **Label:** User-facing name
     - **Internal name:** API name (usually auto-generated from label)
     - **Field type:** Select from dropdown
     - **Description:** Optional (you can add "For GemFlush campaign tracking")
   - Click **"Create"** or **"Save"**

4. **Repeat for All 6 Properties**
   - Create each property one at a time
   - Total time: ~15-20 minutes

## Verification

After creating all properties, verify they exist:

1. Go to **Contacts** → **Create contact**
2. Check that all 6 custom properties appear in the form
3. Or use the verification script: `verify_hubspot_properties.py`

## Notes

- **Internal names** must match exactly (case-sensitive)
- Properties will be created as **contact properties** (not company properties)
- All properties except `vertical` are optional (campaign script handles missing properties gracefully)
- Properties can be edited later if needed

## Troubleshooting

**Property doesn't appear:**
- Check you created it as a **Contact Property** (not Company Property)
- Verify internal name matches exactly (case-sensitive)
- Refresh HubSpot page

**Property exists but script can't find it:**
- Check internal name matches exactly
- Verify property is active (not archived)
- Check API permissions (Private App needs proper scopes)

