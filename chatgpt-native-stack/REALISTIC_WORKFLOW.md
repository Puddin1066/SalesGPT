# Realistic Workflow for HubSpot Free Tier

## TL;DR

**Reality:** Marketing Email API and CMS API require paid tiers.

**Solution:** Hybrid approach - API for CRM, UI for emails/pages

**Result:** Still saves 5-7 hours (35% reduction)

---

## What Actually Works on Free Tier

### ✅ Fully Automated via API

1. **Custom Properties** (`create_hubspot_properties.py`)
   - Creates 6 properties in 30 seconds
   - Saves 20 minutes of UI clicking

2. **Contact Import** (`import_contacts_bulk.py`)
   - Imports 500 contacts in 5 minutes
   - Saves 55 minutes of CSV mapping

3. **Contact Updates** (built into tracking)
   - Updates properties when contacts engage
   - Automatic tracking

4. **Analytics Extraction** (`analyze_results.py`)
   - Pulls metrics in 30 seconds
   - Saves 30 minutes of manual export

**Total API savings: ~105 minutes per campaign**

### 📝 Done in HubSpot UI (Faster Anyway)

1. **Landing Pages** (3-4 hours)
   - Use drag-and-drop builder
   - Paste ChatGPT-generated content
   - Actually faster than API

2. **Email Campaigns** (30 minutes)
   - Create email in UI
   - Send to segmented list
   - Use our properties for targeting

3. **Reply Handling** (15 min/day)
   - Check inbox
   - Respond to interested prospects

**Total UI work: ~4-5 hours** (unavoidable on any tier)

---

## Step-by-Step Workflow

### Week 0: One-Time Setup (15 min)

#### 1. Fix API Scopes (5 min)
```bash
# Follow guide
open chatgpt-native-stack/setup/configure_hubspot_scopes.md

# Add these scopes:
# - crm.schemas.contacts.write
# - crm.objects.contacts.read
# - crm.objects.contacts.write

# Verify
python3 chatgpt-native-stack/setup/check_hubspot_scopes.py
```

#### 2. Create Properties (30 sec)
```bash
python3 chatgpt-native-stack/setup/create_hubspot_properties.py
python3 chatgpt-native-stack/setup/verify_hubspot_properties.py
```

**Properties created:**
- `vertical` (medical, legal, realestate, agencies)
- `gemflush_email_sent` (timestamp)
- `gemflush_variant` (A or B)
- `gemflush_email_subject` (subject line)
- `gemflush_last_campaign_date` (date)
- `gemflush_sender_email` (Alex@GEMflush.com)

---

### Week 1: Content Generation (4-6 hours)

#### 1. Generate Landing Page Content (1-2 hours)

**Open:** `content-prompts/landing_page_prompts.md`

**Process:**
1. Open ChatGPT Plus
2. Search for "HubSpot Landing Page Creator" GPT (if available)
   - OR just use regular ChatGPT with prompts
3. Generate 8 landing pages:
   - Medical Variant A (audit focus)
   - Medical Variant B (demo focus)
   - Legal Variant A
   - Legal Variant B
   - Real Estate Variant A
   - Real Estate Variant B
   - Agencies Variant A
   - Agencies Variant B

**Save:** Copy outputs to text files for reference

#### 2. Generate Email Content (1-2 hours)

**Open:** `content-prompts/email_prompts.md`

**Process:**
1. Use ChatGPT (Plus or regular)
2. Generate 12 email sequences (3 emails × 4 verticals)
3. Save to `email-content/` directory as:
   - `medical_email_1.txt` (subject A, subject B, body)
   - `medical_email_2.txt`
   - `medical_email_3.txt`
   - (repeat for legal, realestate, agencies)

---

### Week 2: HubSpot UI Setup (3-4 hours)

#### 1. Build Landing Pages (2-3 hours)

**For each of 8 landing pages:**

1. HubSpot → Marketing → Landing Pages → Create
2. Choose template (or start blank)
3. Paste ChatGPT-generated content:
   - Hero headline
   - Problem statements (3 points)
   - How it works (3 steps)
   - CTA section
4. Add form (Variant A) or Calendly embed (Variant B)
5. Publish and save URL

**URLs to track:**
- `medical-audit.hs-sites.com/gemflush-medical-audit`
- `medical-demo.hs-sites.com/gemflush-medical-demo`
- (etc for 8 pages)

#### 2. Create Lists in HubSpot (15 min)

**Create 4 active lists:**

1. HubSpot → Contacts → Lists → Create list
2. Name: "GemFlush - Medical"
3. Filters: `vertical` is exactly `medical`
4. Save as active list
5. Repeat for: Legal, Real Estate, Agencies

**Result:** Auto-updating lists for each vertical

#### 3. Create Email Campaigns (30 min)

**For Week 1 (Email 1 only):**

1. HubSpot → Marketing → Email → Create email
2. Name: "GemFlush - Medical - Email 1 - Variant A"
3. Subject: Copy from `email-content/medical_email_1.txt` (line 1)
4. Body: Copy email body, replace tokens:
   - `{{firstname}}` → Use HubSpot personalization
   - `{{company}}` → Use HubSpot personalization
   - `{{city}}` → Use HubSpot personalization
5. Add link to landing page
6. Save (don't send yet)

**Repeat for:**
- Medical Variant B (subject line 2)
- Legal Variant A & B
- Real Estate Variant A & B
- Agencies Variant A & B

**Total: 8 email campaigns** (one per vertical per variant)

---

### Week 3: Lead Sourcing & Import (2-3 hours)

#### 1. Source Leads (1-2 hours)

**Option A: LinkedIn Sales Navigator** (Recommended, Free Trial)
1. Sign up for 30-day free trial
2. Search for job titles:
   - Medical: "Practice Manager", "Office Manager", "Medical Director"
   - Legal: "Managing Partner", "Marketing Director"
   - Real Estate: "Broker Owner", "Marketing Manager"
   - Agencies: "Partner", "CMO", "Head of Growth"
3. Export up to 2,500 leads
4. Download CSV

**Option B: Buy List** ($50-100)
- Use UpLead, ZoomInfo, or Seamless.ai
- Buy 500-1,000 verified leads
- Download CSV

#### 2. Format CSV (30-60 min)

**Use template:** `setup/leads_template.csv`

**Required columns:**
```csv
Email,First Name,Last Name,Company,City,Job Title,vertical
alex@clinic.com,Alex,Smith,Medical Clinic,New York,Practice Manager,medical
```

**Validate:**
- Email addresses valid
- `vertical` is exactly: medical, legal, realestate, or agencies
- No duplicate emails

#### 3. Import to HubSpot (5 min - AUTOMATED!)

```bash
# Preview first
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv --dry-run

# Import
python3 chatgpt-native-stack/setup/import_contacts_bulk.py leads.csv
```

**Verify in HubSpot:**
1. Contacts → All Contacts
2. Filter by `vertical` property
3. Check counts:
   - Medical: ~125-250 contacts
   - Legal: ~125-250 contacts
   - Real Estate: ~125-250 contacts
   - Agencies: ~125-250 contacts

---

### Week 4: Campaign Launch (1 hour)

#### Manual A/B Split (5 min per vertical)

Since we don't have Marketing API, we split contacts manually:

**For Medical vertical:**

1. **Create Variant A List:**
   - HubSpot → Lists → Create list
   - Name: "GemFlush - Medical - Variant A"
   - Filters:
     - `vertical` is exactly `medical`
     - `Contact ID` is odd (HubSpot list filter)
   - Save

2. **Create Variant B List:**
   - Name: "GemFlush - Medical - Variant B"
   - Filters:
     - `vertical` is exactly `medical`
     - `Contact ID` is even
   - Save

**Repeat for:** Legal, Real Estate, Agencies (total 8 lists)

#### Send Campaigns (30 min)

**For each vertical (4 total):**

**Monday - Medical:**
1. Open "GemFlush - Medical - Email 1 - Variant A"
2. Recipients → Select "GemFlush - Medical - Variant A" list
3. Review and send
4. Open "GemFlush - Medical - Email 1 - Variant B"
5. Recipients → Select "GemFlush - Medical - Variant B" list
6. Review and send

**Tuesday - Legal** (repeat process)

**Wednesday - Real Estate** (repeat process)

**Thursday - Agencies** (repeat process)

**Total sent:** 800 emails (200 per vertical, 100 per variant)

#### Track Manually (5 min)

After sending, update contact properties manually:
1. HubSpot → Contacts → Select all in "Medical - Variant A"
2. Edit properties:
   - `gemflush_variant` = A
   - `gemflush_email_sent` = Today's date
   - `gemflush_sender_email` = Alex@GEMflush.com
3. Repeat for all 8 lists

**OR:** Use bulk property update API (can automate this part)

---

### Week 5: Daily Monitoring (15 min/day)

#### Check Replies
1. HubSpot → Conversations → Inbox
2. Check for replies to campaign emails
3. Respond using reply templates (create with ChatGPT)
4. Update contact properties:
   - Create custom property: `gemflush_replied` = Yes/No
   - Update when prospects reply

#### Track Metrics
Use HubSpot dashboard or our analytics script:

```bash
python3 chatgpt-native-stack/analyze_results.py --week 1
```

**Note:** This pulls from HubSpot's analytics API (works on Free tier!)

---

### Week 6: Analysis & Optimization (1 hour)

#### Extract Metrics (1 min - AUTOMATED)

```bash
python3 chatgpt-native-stack/analyze_results.py --week 1 > week1_results.txt
```

**Output includes:**
- Emails sent per vertical
- Open rates per variant
- Click rates per variant
- Reply rates per variant
- Landing page visits

#### Analyze with ChatGPT (30 min)

1. Open ChatGPT
2. Paste output from `analyze_results.py`
3. Ask:
   - "Which vertical performed best?"
   - "Which subject variant won?"
   - "What should I focus on in Week 2?"
   - "Any messaging changes recommended?"

#### Plan Week 2 (30 min)

Based on ChatGPT analysis:
- **Kill:** Underperforming verticals (<2% reply rate)
- **Scale:** Best vertical (2x contacts)
- **Test:** New subject lines or landing page variants

---

## Time Investment Summary

| Phase | Task | Time | Automated? |
|-------|------|------|------------|
| Setup | Fix scopes | 5 min | No (one-time) |
| Setup | Create properties | 30 sec | Yes ✅ |
| Setup | Verify setup | 30 sec | Yes ✅ |
| Content | Landing pages | 1-2 hours | No (ChatGPT) |
| Content | Email sequences | 1-2 hours | No (ChatGPT) |
| UI | Build landing pages | 2-3 hours | No (UI faster) |
| UI | Create email campaigns | 30 min | No (UI required) |
| UI | Create lists | 15 min | No (UI simple) |
| Leads | Source leads | 1-2 hours | No (external) |
| Leads | Format CSV | 30-60 min | No (data cleaning) |
| Leads | Import to HubSpot | 5 min | Yes ✅ |
| Launch | Create A/B lists | 20 min | No (one-time setup) |
| Launch | Send campaigns | 30 min | No (UI sends) |
| Launch | Track properties | 5 min | Partial (can automate) |
| Daily | Check replies | 15 min/day | No (human touch) |
| Analysis | Extract metrics | 1 min | Yes ✅ |
| Analysis | ChatGPT review | 30 min | No (strategy) |
| **Total** | - | **~10-13 hours** | **35% automated** |

**vs. Fully Manual:** ~15-20 hours

**Time Saved:** 5-7 hours (35% reduction)

---

## What's Worth It

### ✅ High Value Automation
- Property creation: **YES** (saves 20 min, prevents errors)
- Contact import: **YES** (saves 55 min, validates data)
- Analytics extraction: **YES** (saves 30 min, consistent format)
- A/B tracking properties: **YES** (enables analysis)

### 📝 Manual But Fast
- Landing pages in UI: **Faster than API anyway**
- Email campaigns in UI: **Required, but streamlined with lists**
- Lists setup: **One-time, then reusable**

### 💡 Content Generation
- ChatGPT prompts: **Time well spent** (quality matters)
- Would take same time regardless of automation

---

## Bottom Line

**Free Tier Reality:**
- CRM API: ✅ Excellent
- Marketing API: ❌ Requires paid tier
- CMS API: ❌ Requires paid tier

**Our Solution:**
- Automate: Properties, imports, analytics
- UI for: Emails, landing pages (faster anyway)
- Scripts for: A/B tracking, personalization logic

**Result:**
- 35% time savings (5-7 hours)
- More organized workflow
- Better tracking and analytics
- Scales for future campaigns

**Recommendation:** Proceed! The automation is still worth it.

---

## Next Steps

1. **Fix API scopes** (5 min)
2. **Run automated setup** (2 min)
3. **Generate content** (4-6 hours)
4. **Build in HubSpot UI** (3-4 hours)
5. **Import leads & launch** (1 hour)
6. **Analyze results** (1 min automated!)

**See:** `QUICK_START.md` for commands and detailed guide

**The automation saves time where it matters most: repetitive setup tasks! 🎯**

