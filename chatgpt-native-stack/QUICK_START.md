# Quick Start Guide - GemFlush Campaign Launch

## ✅ Pre-Flight Checklist

Before launching campaigns, complete these setup steps:

### 0. Add HubSpot API Scopes ⚠️  CRITICAL (5 min)

**This is a blocker - must be done first!**

```bash
# Check current scopes
python3 chatgpt-native-stack/setup/check_hubspot_scopes.py
```

If missing `crm.schemas.contacts.write` scope:
1. Follow guide: `setup/configure_hubspot_scopes.md`
2. Add required scopes in HubSpot UI (5 min)
3. Update `.env.local` with new token
4. Verify with script above

### 1. Verify HubSpot Connection ✅
```bash
python3 chatgpt-native-stack/test_hubspot_connection.py
```
**Status:** ✅ Complete (already tested)

### 2. Create HubSpot Custom Properties (AUTOMATED - 1 min)
```bash
# Create properties automatically via API
python3 chatgpt-native-stack/setup/create_hubspot_properties.py

# Verify properties created
python3 chatgpt-native-stack/setup/verify_hubspot_properties.py
```

**No manual UI work needed!** (Once scopes are added)

### 3. Check Email Limits
```bash
python3 chatgpt-native-stack/setup/check_email_limits.py
```
Then verify in HubSpot UI: Marketing → Email

---

## 🚀 Launch Steps

### Phase 1: Content Generation (Day 1-2)

**1. Generate Landing Pages (1-2 hours)**
- Use prompts in: `content-prompts/landing_page_prompts.md`
- Generate 8 landing pages (2 variants × 4 verticals)
- Build in HubSpot UI: Marketing → Landing Pages

**2. Generate Email Content (1-2 hours)**
- Use prompts in: `content-prompts/email_prompts.md`
- Generate 12 email sequences (3 emails × 4 verticals)
- Save in `email-content/` directory

**3. Build Landing Pages (2-3 hours)**
- Create pages in HubSpot UI using generated copy
- Add forms (Variant A) or Calendly (Variant B)
- Publish and note URLs

### Phase 2: Lead Sourcing (Day 2-3)

**1. Source Leads (1-2 hours)**
- Option A: LinkedIn Sales Navigator trial (recommended, free)
- Option B: Buy lead list ($50-100)
- Target: 500-1,000 leads (125-250 per vertical)

**2. Prepare CSV (30-60 min)**
- Use template: `setup/leads_template.csv`
- Format: Email, First Name, Last Name, Company, City, Job Title, vertical
- Values for vertical: medical, legal, realestate, agencies

**3. Import to HubSpot (AUTOMATED - 5 min)**
```bash
# Preview import (dry run)
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv --dry-run

# Import contacts
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv
```

**No manual CSV import needed!** Script handles bulk upload via API.

### Phase 3: First Test Campaign (Day 3-4)

**1. Run Test Campaign**
```bash
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical realestate \
  --email 1 \
  --count 200
```

**2. Verify Results**
- Check HubSpot → Marketing → Email
- Verify properties set on contacts
- Monitor for replies

### Phase 4: Week 1 Full Campaign (Days 4-7)

**Run campaigns for all 4 verticals:**
```bash
# Medical
python3 chatgpt-native-stack/gemflush_campaign.py --vertical medical --email 1 --count 200

# Legal
python3 chatgpt-native-stack/gemflush_campaign.py --vertical legal --email 1 --count 200

# Agencies
python3 chatgpt-native-stack/gemflush_campaign.py --vertical agencies --email 1 --count 200
```

**Daily:**
- Check HubSpot inbox for replies (15 min/day)
- Respond to replies using templates

### Phase 5: Week 1 Analysis (Day 8)

**1. Export Metrics**
```bash
python3 chatgpt-native-stack/analyze_results.py --week 1
```

**2. Analyze with ChatGPT**
- Paste output into ChatGPT
- Get recommendations for Week 2

---

## 📚 Resources

- **Setup Guide:** `setup/README.md`
- **Properties Guide:** `setup/hubspot_properties_guide.md`
- **Landing Page Prompts:** `content-prompts/landing_page_prompts.md`
- **Email Prompts:** `content-prompts/email_prompts.md`
- **Main README:** `README.md`
- **Full Plan:** See plan file for detailed timeline

---

## ⚡ Quick Commands

```bash
# Check API scopes (CRITICAL - do first!)
python3 chatgpt-native-stack/setup/check_hubspot_scopes.py

# Test connection
python3 chatgpt-native-stack/test_hubspot_connection.py

# Create properties automatically
python3 chatgpt-native-stack/setup/create_hubspot_properties.py

# Verify properties
python3 chatgpt-native-stack/setup/verify_hubspot_properties.py

# Check email limits
python3 chatgpt-native-stack/setup/check_email_limits.py

# Import contacts (dry run first)
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv --dry-run
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv

# Run campaign
python3 chatgpt-native-stack/gemflush_campaign.py --vertical medical --email 1 --count 200

# Analyze results
python3 chatgpt-native-stack/analyze_results.py --week 1
```

---

## 🎯 Success Criteria (After Week 1)

- ✅ 800 emails sent (200 × 4 verticals)
- ✅ >3% overall reply rate
- ✅ >1% positive reply rate
- ✅ 5+ demos booked
- ✅ 1 vertical clearly outperforming

---

**Ready? Start with Phase 1: Content Generation!**

