# Quick Start Guide

## ✅ Implementation Status

All automation scripts are ready! HubSpot API connection verified.

**Next Steps:**
1. Generate content using ChatGPT GPTs (manual)
2. Source/import leads to HubSpot (manual)
3. Run campaigns using scripts (automated)

## Step-by-Step Setup

### 1. ✅ HubSpot API Connection (COMPLETE)

Your HubSpot credentials are configured:
- `HUBSPOT_PAT` ✅
- `HS_CLIENT_ID` ✅
- `HS_CLIENT_SECRET` ✅

Test: `python3 chatgpt-native-stack/test_hubspot_connection.py`

### 2. Generate Landing Pages (ChatGPT)

**Use HubSpot Landing Page Creator GPT:**

1. Open ChatGPT
2. Search for "HubSpot Landing Page Creator" GPT
3. Generate 2 variants per vertical (8 total):
   - Medical: Variant A (Audit-focused), Variant B (Demo-focused)
   - Legal: Variant A, Variant B
   - Real Estate: Variant A, Variant B
   - Agencies: Variant A, Variant B

4. Build in HubSpot UI:
   - Marketing → Landing Pages → Create
   - Paste ChatGPT-generated copy
   - Add forms (Variant A) or Calendly (Variant B)
   - Publish and note URLs

**Time:** ~2-3 hours for all 8 pages

### 3. Generate Email Content (ChatGPT)

**Use HubSpot Marketing Email GPT:**

1. Open ChatGPT
2. Search for "HubSpot Marketing Email" GPT
3. Generate email sequences for each vertical

**Example prompt:**
```
Create evidence-driven cold email for medical clinics.

Product: GemFlush - AI Visibility Audit
Target: Practice Managers

Email 1 (Initial Outreach):
- Subject: 2 variants (problem-focused, curiosity-focused)
- Body: 150 words max, evidence-driven
- Include stat about AI search adoption
- Personalization: {{firstname}}, {{company}}, {{city}}
- CTA: Link to landing page

Tone: Professional, data-backed, not salesy
```

4. Save email content in `email-content/` directory:
   - Format: See `email-content/README.md`
   - Files: `medical_email_1.txt`, `legal_email_1.txt`, etc.

**Time:** ~1 hour for all 4 verticals

### 4. Source and Import Leads

**Option A: LinkedIn Sales Navigator (Free Trial)**
1. Sign up for 30-day free trial
2. Search for job titles per vertical
3. Export leads (up to 2,500 in trial)
4. Import to HubSpot CRM

**Option B: Buy Lead List ($50-100 one-time)**
1. Use UpLead, ZoomInfo, or Seamless.ai
2. Buy 500-1000 verified leads per vertical
3. Import CSV to HubSpot

**Import Steps:**
1. HubSpot → Contacts → Import
2. Upload CSV
3. Map columns (email, firstname, lastname, company, city, jobtitle)
4. Add custom property: `vertical` (medical, legal, realestate, agencies)
5. Import

**Time:** 1-2 hours (or 40+ hours if manual research)

### 5. Run Campaigns (Automated)

**Week 1: Test All 4 Verticals**

```bash
# Monday: Medical
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical medical \
  --email 1 \
  --count 200

# Tuesday: Legal
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical legal \
  --email 1 \
  --count 200

# Wednesday: Real Estate
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical realestate \
  --email 1 \
  --count 200

# Thursday: Agencies
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical agencies \
  --email 1 \
  --count 200
```

**Friday: Analyze Results**

```bash
python3 chatgpt-native-stack/analyze_results.py --week 1
```

Copy output and paste into ChatGPT for analysis.

### 6. Follow-Up Emails (Manual or Script)

**After 3 days (Day 4):**

Send Email 2 to non-responders:

```bash
# Re-run script with email 2 content
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical medical \
  --email 2 \
  --count 150  # Non-responders only
```

Or send manually via HubSpot UI.

## Notes

### HubSpot Free Email Sending

**Important:** HubSpot Free tier email sending works, but:
- Limited to 2,000 emails/month
- Scripts track contacts in CRM
- Actual sending may require HubSpot Marketing API access
- Alternative: Use HubSpot UI for manual sending if API sending is limited

**Current Implementation:**
- Scripts prepare emails and track in HubSpot CRM
- Custom properties track: `gemflush_email_sent`, `gemflush_variant`
- Check HubSpot UI for actual sending options

### Next Steps After Week 1

1. **Run ChatGPT analysis** on Week 1 results
2. **Identify top 2 verticals** (best reply rates)
3. **Plan Week 2 tests** (email body variants, landing page tests)
4. **Scale winners, pause losers**

## Files Created

✅ `gemflush_campaign.py` - Main campaign script
✅ `analyze_results.py` - Metrics export for ChatGPT
✅ `test_hubspot_connection.py` - Connection test
✅ `email-content/README.md` - Email format guide
✅ `README.md` - Full documentation

## Support

See `README.md` for detailed documentation.

For issues:
1. Check HubSpot API connection: `python3 test_hubspot_connection.py`
2. Verify email content format: `email-content/README.md`
3. Check HubSpot UI for actual email sending capabilities

