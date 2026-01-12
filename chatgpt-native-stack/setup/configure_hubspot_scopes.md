# HubSpot API Scopes Configuration

## Issue

The HubSpot API key requires additional scopes to automate property creation and email sending.

**Current Error:**
```
403 Forbidden - Missing required scopes: crm.schemas.contacts.write
```

## Solution: Add Scopes to HubSpot Private App

### Step 1: Access HubSpot Private App Settings

1. Log into HubSpot
2. Click Settings (gear icon) → Integrations → Private Apps
3. Find your existing Private App (or create new one)
4. Click the app name to edit

### Step 2: Add Required Scopes

In the "Scopes" tab, enable these scopes:

#### CRM Scopes (Required for automation)
- ✅ `crm.schemas.contacts.write` - Create custom contact properties
- ✅ `crm.objects.contacts.read` - Read contact data
- ✅ `crm.objects.contacts.write` - Create/update contacts
- ✅ `crm.lists.read` - Read contact lists
- ✅ `crm.lists.write` - Create/update lists

#### Marketing Scopes (For email automation)
- ✅ `marketing-email.send` - Send marketing emails (if available on Free tier)
- ✅ `marketing.read` - Read marketing data
- ✅ `forms` - Access forms (for landing page forms)

#### Optional Scopes (Enhanced functionality)
- ✅ `content` - Access CMS content (landing pages - may require paid tier)
- ✅ `reports` - Access analytics reports

### Step 3: Generate New Access Token

1. After adding scopes, click "Show token"
2. Copy the new access token
3. Update your `.env.local` file:

```bash
HUBSPOT_API_KEY=pat_REDACTED
# OR
HUBSPOT_PAT=pat_REDACTED
```

### Step 4: Verify Scopes

Run the verification script to confirm scopes are correct:

```bash
python3 chatgpt-native-stack/setup/check_hubspot_scopes.py
```

### Step 5: Create Properties Automatically

Once scopes are added, run:

```bash
python3 chatgpt-native-stack/setup/create_hubspot_properties.py
```

## Free Tier Limitations

HubSpot Free tier has some API limitations:

### ✅ Fully Available (Free Tier)
- CRM object CRUD (contacts, companies, deals)
- Custom properties (via UI or API with correct scopes)
- Contact import/export
- Single-send transactional emails (API)
- Forms API
- Analytics/reports API

### ⚠️  Limited (Free Tier)
- **Marketing emails**: 2,000/month limit (available via UI, API may be restricted)
- **Landing pages**: Basic functionality (CMS API may require paid tier)
- **Workflows**: Not available on Free tier
- **Sequences**: Not available on Free tier

### ❌ Not Available (Free Tier)
- Marketing automation workflows
- Advanced CMS features
- A/B testing (native HubSpot - we handle this manually)
- Advanced reporting

## Workaround for API Limitations

If marketing email API is not available on Free tier:

### Option 1: Use Single-Send API (Transactional)
```python
# Send individual emails via transactional API
POST /marketing/v3/transactional/single-send
```

### Option 2: Use HubSpot UI for Bulk Sends
1. Import contacts with segmentation
2. Create email campaign in UI
3. Send to segmented lists
4. Track metrics via API

### Option 3: Hybrid Approach (Recommended)
- Use API for: Contact management, property updates, analytics
- Use UI for: Email sending, landing page creation
- Use ChatGPT for: Content generation, strategy analysis

## Summary

| Task | API Available? | Solution |
|------|----------------|----------|
| Create custom properties | ✅ Yes (with scopes) | Automated via API |
| Import contacts | ✅ Yes | Automated via API |
| Update contact properties | ✅ Yes | Automated via API |
| Send marketing emails | ⚠️  Limited | Use UI or transactional API |
| Create landing pages | ⚠️  Limited | Use UI (faster anyway) |
| Track email metrics | ✅ Yes | Automated via API |
| A/B testing | ❌ No (native) | Manual via our scripts |

## Next Steps

1. **Add scopes** to HubSpot Private App (5 minutes)
2. **Update** `.env.local` with new token
3. **Run** `create_hubspot_properties.py` to auto-create properties
4. **Use** hybrid approach: API for automation, UI for email/pages
5. **Proceed** with campaign launch

The automation will handle:
- ✅ Property creation
- ✅ Contact import
- ✅ Property tracking
- ✅ Metrics extraction

Manual tasks (faster in UI anyway):
- Landing page creation (2-3 hours)
- Email campaign setup (1 hour)
- Reply handling (15 min/day)

