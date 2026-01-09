# ⚡ Quick HubSpot UI Setup

## 🎯 Yes! HubSpot UI Can Be Used for Email Review

The code now automatically sends email content to HubSpot as custom properties!

## ✅ What You Get

- ✅ All contacts created in HubSpot
- ✅ Email subject and body stored in HubSpot
- ✅ Email variant and A/B test data
- ✅ Lead scores and ELM data
- ✅ All visible in HubSpot UI

## 🚀 Quick Setup (2 Steps)

### Step 1: Create Custom Properties in HubSpot

Go to: **HubSpot Settings** → **Properties** → **Contact Properties** → **Create property**

Create these properties:
- `email_subject` (Single-line text)
- `email_body` (Multi-line text)  
- `email_variant` (Single-line text)
- `persuasion_route` (Single-select: central, peripheral)
- `elaboration_score` (Number)

### Step 2: Run Queue Builder

```bash
python3 scripts/start_queue_builder.py
```

Contacts will be created in HubSpot with email content ready to review!

## 📧 How to Use

1. Open HubSpot → Contacts
2. Filter: `email_subject` is not empty
3. Review emails in contact records
4. All email content visible in custom properties

## 🎉 Done!

You can now review all emails directly in HubSpot UI!
