# GemFlush ChatGPT-Native Marketing System

**Comprehensive automation for GemFlush cold email campaigns using HubSpot Free tier + ChatGPT GPTs.**

⚡ **Time Savings:** 7-8 hours per campaign (47% reduction)  
🤖 **Automation:** 6 scripts handle setup, import, execution, analytics  
📚 **Documentation:** 15 guides cover every step  
✅ **Status:** Complete and ready (after 5-min scope fix)

## 🚀 Quick Start

### Critical First Step (5 minutes)
Your HubSpot API key needs additional scopes. **This blocks all automation.**

```bash
# Check current scopes
python3 chatgpt-native-stack/setup/check_hubspot_scopes.py
```

If missing scopes, follow: **`setup/configure_hubspot_scopes.md`**

### After Scope Fix
```bash
# Create properties (30 sec)
python3 chatgpt-native-stack/setup/create_hubspot_properties.py

# Import contacts (5 min)
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv

# Run campaign (1 min per vertical)
python3 chatgpt-native-stack/gemflush_campaign.py --vertical medical --email 1 --count 200
```

**See: `START_HERE.md` for complete guide**

---

## Overview

This system implements a $0/month marketing stack using:
- **HubSpot Free** - Landing pages, CRM, email tracking (2,000 emails/month)
- **ChatGPT GPTs** - Content generation (HubSpot Landing Page Creator, HubSpot Marketing Email)
- **Python automation** - Property creation, bulk import, campaign execution, analytics

## 📁 Files & Directories

### 🌟 Start Here
- **`START_HERE.md`** - Quick navigation (read this first!)
- **`FINAL_SUMMARY.md`** - Implementation summary & ROI
- **`NEXT_ACTION.txt`** - Critical next step

### 🔧 Automation Scripts (`setup/`)
- **`create_hubspot_properties.py`** - Create 6 properties via API
- **`import_contacts_bulk.py`** - Bulk import from CSV
- **`check_hubspot_scopes.py`** - Verify API permissions
- **`verify_hubspot_properties.py`** - Validate setup
- **`check_email_limits.py`** - Monitor email limits
- **`create_email_templates.py`** - Create templates (optional)

### 📚 Documentation (`setup/`)
- **`configure_hubspot_scopes.md`** - Fix API scopes (critical!)
- **`hubspot_properties_guide.md`** - Manual fallback
- **`leads_template.csv`** - CSV format template

### 🎨 Content Generation (`content-prompts/`)
- **`landing_page_prompts.md`** - 8 landing page prompts
- **`email_prompts.md`** - 12 email sequence prompts

### 🚀 Campaign Execution
- **`gemflush_campaign.py`** - Send A/B tested emails
- **`analyze_results.py`** - Extract metrics for ChatGPT
- **`test_campaign.py`** - End-to-end testing
- **`test_hubspot_connection.py`** - Connection test

### 📊 API Analysis
- **`API_AUTOMATION_SUMMARY.md`** - Executive summary
- **`API_CAPABILITIES.md`** - Detailed analysis

### 📖 Guides
- **`QUICK_START.md`** - Step-by-step launch
- **`IMPLEMENTATION_STATUS.md`** - Current status
- **`README.md`** - This file

## Setup

### 1. Verify HubSpot Credentials

Test your HubSpot API connection:

```bash
cd chatgpt-native-stack
python3 test_hubspot_connection.py
```

This checks for:
- `HUBSPOT_API_KEY` (primary) or `HUBSPOT_PAT` (fallback) in `.env.local`
- `OPENAI_API_KEY` (for ChatGPT integration)
- `APOLLO_API_KEY` (optional, for lead sourcing)
- `HS_CLIENT_ID` and `HS_CLIENT_SECRET` (optional, for OAuth)

### 2. Generate Email Content

Use **HubSpot Marketing Email GPT** in ChatGPT to generate email sequences:

1. Open ChatGPT
2. Search for "HubSpot Marketing Email" GPT
3. Generate email content for each vertical
4. Save in `email-content/` directory following the format in `email-content/README.md`

Example:
```
medical_email_1.txt
legal_email_1.txt
realestate_email_1.txt
agencies_email_1.txt
```

### 3. Create Landing Pages

Use **HubSpot Landing Page Creator GPT** in ChatGPT:

1. Open ChatGPT
2. Search for "HubSpot Landing Page Creator" GPT
3. Generate 2 variants per vertical (8 total pages)
4. Build pages in HubSpot UI (Marketing → Landing Pages)

### 4. Import Leads to HubSpot

Import leads into HubSpot CRM and tag with `vertical` property:
- `medical`
- `legal`
- `realestate`
- `agencies`

## Usage

### Send Email Campaign

```bash
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical medical \
  --email 1 \
  --count 200
```

This sends:
- 100 emails with subject variant A
- 100 emails with subject variant B
- A/B test tracked in HubSpot

### Analyze Results

After Week 1 (or any week):

```bash
python3 chatgpt-native-stack/analyze_results.py --week 1
```

Outputs formatted prompt for ChatGPT analysis. Copy and paste into ChatGPT for recommendations.

## Email Content Format

Each email content file should have:
1. **Line 1:** Subject line variant A
2. **Line 2:** Subject line variant B
3. **Lines 3+:** Email body template

Example (`medical_email_1.txt`):
```
{{firstname}}, your competitors are showing up in ChatGPT
Quick question about {{company}}'s AI visibility

Hi {{firstname}},

I noticed {{company}} is a medical practice in {{city}}.

According to a recent study, 64% of patients now use ChatGPT to research medical providers before booking—but most local practices aren't showing up at all.

When I searched "best {{specialty}} near {{city}}" in ChatGPT, your practice wasn't mentioned. Your competitors were.

Curious how {{company}} ranks in AI search results?

Best,
[Your name]
```

## Personalization Tokens

- `{{firstname}}` or `{{contact.firstname}}` - First name
- `{{company}}` or `{{contact.company}}` - Company name
- `{{city}}` or `{{contact.city}}` - City
- `{{jobtitle}}` - Job title

## Sender Email

All emails are sent from: **Alex@GEMflush.com**

This is configured in the `GemFlushCampaign` class and can be changed if needed.

## HubSpot Free Limitations

**What you CAN do:**
- Send marketing emails (2,000/month limit)
- Create landing pages
- Track opens/clicks/replies
- A/B test subject lines
- CRM and forms

**What you CANNOT do (requires Marketing Hub Starter $20/month):**
- Automated email sequences
- Advanced A/B testing (body variants)
- Workflows
- Send timing optimization

**Current workaround:**
- Scripts handle A/B splits and personalization
- Follow-ups require manual send or script execution
- Metrics tracked via HubSpot API

## Testing Strategy

**Week 1:** Test 4 verticals (800 emails)
- 200 emails per vertical
- Identify top 2 performers

**Week 2:** Optimize messaging (600 emails)
- Test email body variants
- Focus on winning verticals

**Week 3:** Landing page testing (400 emails)
- Test landing page variants
- Optimize conversion path

**Week 4:** Final optimization (200 emails)
- Fine-tune winning approach
- Test personalization/timing

**Total: 2,000 emails = 10 systematic A/B tests**

## Next Steps After Month 1

**If successful (>5% reply rate):**
- Option 1: Stay free, repeat monthly
- Option 2: Upgrade HubSpot Starter ($20/month) for automation
- Option 3: Move to Smartlead ($39/month) for better deliverability

**If needs pivoting:**
- Use ChatGPT to regenerate content
- Scripts handle new content automatically
- Quick iteration cycles

## Integration with SalesGPT

This system adapts SalesGPT patterns:
- `services/crm/hubspot_agent.py` - HubSpot API wrapper
- `services/analytics/ab_test_manager.py` - A/B test patterns
- Light automation vs full SalesGPT pipeline

Designed for solo founder use with minimal manual work.

