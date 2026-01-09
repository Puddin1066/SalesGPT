# 🎯 Using HubSpot UI CRM for Email Review

Yes! **HubSpot UI can absolutely be used** to review all custom emails and contacts. Here's how to set it up and use it.

---

## ✅ What's Currently Working

### Current HubSpot Integration:
- ✅ Creates contacts in HubSpot with all lead data
- ✅ Creates deals associated with contacts
- ✅ Updates pipeline stages (idle → engaged → booked → closed)
- ✅ Stores Apollo data, lead scores, specialty, etc.

### What's Missing (Now Fixed):
- ✅ Email subject and body are now stored as **custom properties** in HubSpot
- ✅ Email variant, persuasion route, elaboration score stored
- ✅ All email content visible in HubSpot UI

---

## 🔧 Setting Up Custom Properties in HubSpot

Before the emails will show properly, you need to create custom properties in HubSpot:

### Step 1: Create Custom Properties in HubSpot UI

1. Go to **HubSpot Settings** → **Properties** → **Contact Properties**
2. Click **"Create property"**
3. Create these custom properties:

| Property Name | Internal Name | Field Type | Description |
|--------------|---------------|------------|-------------|
| Email Subject | `email_subject` | Single-line text | Subject line of generated email |
| Email Body | `email_body` | Multi-line text | Full email body content |
| Email Variant | `email_variant` | Single-line text | A/B test variant code |
| Persuasion Route | `persuasion_route` | Single-select | Central or Peripheral |
| Elaboration Score | `elaboration_score` | Number | ELM score (0-100) |
| Lead Score | `lead_score` | Number | Lead quality score |
| Apollo Person ID | `apollo_person_id` | Single-line text | Apollo person identifier |
| Apollo Org ID | `apollo_organization_id` | Single-line text | Apollo organization identifier |
| Specialty | `specialty` | Single-line text | Medical specialty |

### Step 2: Configure Property Visibility

Make sure these properties are visible in:
- ✅ Contact record view
- ✅ Contact list view (optional columns)
- ✅ Deal record view (if needed)

---

## 📧 How Email Content Appears in HubSpot

### In Contact Record:

When you open a contact in HubSpot, you'll see:

1. **Standard Properties Tab:**
   - Email, Name, Company, Title, etc.
   - Phone, Address, LinkedIn

2. **Custom Properties Section:**
   - **Email Subject**: The generated email subject line
   - **Email Body**: Full email content (scrollable)
   - **Email Variant**: A/B test variant (e.g., "variant_1")
   - **Persuasion Route**: Central or Peripheral
   - **Elaboration Score**: 0-100 score
   - **Lead Score**: Overall lead quality

3. **Timeline/Activity:**
   - Deal created
   - Pipeline stage updates
   - Email sent events (if integrated with Smartlead)

### In Contact Lists:

You can add custom columns:
- Email Subject
- Email Variant
- Lead Score
- Persuasion Route

This allows you to see email content directly in list view!

---

## 🚀 Using HubSpot UI for Email Review Workflow

### Recommended Workflow:

1. **Background Queue Builder** creates contacts with email content
2. **Open HubSpot UI** → Contacts
3. **Filter by Custom Property**: `email_subject` is not empty
4. **Review emails** in the contact records
5. **Update pipeline stage** in HubSpot (e.g., "idle" → "engaged")
6. **Send email** via Smartlead (or mark as "ready to send")

### Alternative: HubSpot Workflows

You can set up HubSpot workflows to:
- Auto-tag contacts with email content
- Send notifications when new emails are generated
- Create tasks for email review
- Update deal stages based on email status

---

## 🔄 Updating Existing Contacts with Email Content

If you already have contacts in HubSpot, you can update them with email content:

### Option 1: Via Code (Automatic)

The updated code now automatically:
1. Creates contact with email content in custom properties
2. Updates existing contacts if they already exist

### Option 2: Via HubSpot API (Manual)

```python
from services.crm.hubspot_agent import HubSpotAgent

hubspot = HubSpotAgent()

# Update contact with email content
hubspot.update_contact_properties(
    contact_id="12345678",
    properties={
        "email_subject": "Quick question about Company Inc.",
        "email_body": "Hi John,\n\nI noticed...",
        "email_variant": "variant_1",
        "persuasion_route": "central",
        "elaboration_score": "85.5"
    }
)
```

### Option 3: Via HubSpot UI (Manual)

1. Open contact in HubSpot
2. Edit properties
3. Fill in custom properties:
   - Email Subject
   - Email Body
   - Email Variant
   - etc.

---

## 📊 Viewing Emails in HubSpot Lists

### Create a Custom View:

1. Go to **Contacts** → **Create view**
2. Add columns:
   - Standard: Email, Company, Title
   - Custom: Email Subject, Email Variant, Lead Score
3. Add filters:
   - `email_subject` is not empty
   - `lead_score` is greater than 10
4. Save view as "**Emails Ready for Review**"

Now you can see all contacts with generated emails in one list!

---

## 🎯 Complete Workflow with HubSpot UI

### Step 1: Generate Leads & Emails

```bash
python3 scripts/start_queue_builder.py
```

This creates contacts in HubSpot with:
- ✅ All contact information
- ✅ Email subject and body in custom properties
- ✅ Email variant and A/B test data
- ✅ Lead scores and ELM data
- ✅ Associated deals

### Step 2: Review in HubSpot UI

1. Open **HubSpot** → **Contacts**
2. Filter: `email_subject` is not empty
3. Sort by: `lead_score` (descending)
4. Open each contact to review:
   - **Email Subject** (custom property)
   - **Email Body** (custom property - full content)
   - **Email Variant** (A/B test variant)
   - **Lead Score** (prioritization)
   - **Company** and **Title** (context)

### Step 3: Approve & Send

Option A: Update HubSpot Pipeline Stage
- Change deal stage: "idle" → "ready_to_send"
- This can trigger Smartlead integration

Option B: Use HubSpot + Smartlead Integration
- HubSpot workflow can automatically send to Smartlead
- Or manually export contacts and import to Smartlead

Option C: Use Dashboard (Hybrid Approach)
- Review in HubSpot UI
- Approve in custom dashboard
- Send via Smartlead

---

## 🔗 HubSpot + Smartlead Integration Options

### Option 1: HubSpot Native Integration (Recommended)

HubSpot has a native Smartlead integration:
1. Connect Smartlead app in HubSpot
2. Map custom properties (email_subject, email_body)
3. Create workflows to auto-send emails
4. Track email status back to HubSpot

### Option 2: Zapier/Make Integration

1. HubSpot contact created → Trigger
2. Extract email_subject and email_body
3. Send to Smartlead API
4. Update HubSpot with email status

### Option 3: Custom Webhook

Create a HubSpot workflow that:
1. Triggers on contact property change
2. Sends webhook to your backend
3. Your backend sends email via Smartlead
4. Updates HubSpot with send status

---

## 📝 Example: HubSpot Contact Record

When you open a contact, you'll see:

```
Contact: John Doe
Email: john@example.com
Company: Company Inc.
Title: Sales Manager

Custom Properties:
├── Email Subject: "Quick question about Company Inc."
├── Email Body: "Hi John,\n\nI noticed Company Inc. is focused on..."
├── Email Variant: "variant_1"
├── Persuasion Route: "central"
├── Elaboration Score: 85.5
├── Lead Score: 75
├── Specialty: "Sales"
└── Apollo Person ID: "apollo_123"

Associated Deal:
└── "Company Inc. - GEMflush Implementation" ($5,000)
    └── Stage: idle
```

---

## ✅ Benefits of Using HubSpot UI

1. **Familiar Interface**: Use HubSpot's native CRM
2. **Mobile Access**: Review emails on mobile app
3. **Team Collaboration**: Share contacts with team
4. **Workflows & Automation**: HubSpot native automation
5. **Reporting**: Built-in analytics and reports
6. **Integration Ecosystem**: Connect with other tools
7. **Contact History**: All interactions in one place

---

## 🎯 Quick Start Checklist

- [ ] Create custom properties in HubSpot UI
- [ ] Update code to send email content (✅ Already done)
- [ ] Run queue builder to populate HubSpot
- [ ] Set up HubSpot view for "Emails Ready for Review"
- [ ] Configure HubSpot workflows (optional)
- [ ] Connect Smartlead integration (optional)

---

## 📚 Next Steps

1. **Test the Integration**:
   ```bash
   python3 scripts/start_queue_builder.py
   # Check HubSpot → Contacts for new contacts with email content
   ```

2. **Customize Properties**: Add any additional custom properties you need

3. **Set Up Workflows**: Create HubSpot workflows for automation

4. **Integrate Smartlead**: Connect Smartlead for automated sending

---

**🎉 Yes, HubSpot UI can be your primary CRM interface for reviewing and managing all custom emails and contacts!**

