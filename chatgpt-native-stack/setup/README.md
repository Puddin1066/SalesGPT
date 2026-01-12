# Setup Guide for GemFlush Campaign

This directory contains setup guides and templates for launching the GemFlush campaign.

## Files

- **`hubspot_properties_guide.md`** - Step-by-step guide to create custom properties in HubSpot
- **`verify_hubspot_properties.py`** - Script to verify all required properties exist
- **`leads_template.csv`** - CSV template for importing leads

## Quick Start

### 1. Verify HubSpot Properties

Before running campaigns, verify all custom properties exist:

```bash
python3 chatgpt-native-stack/setup/verify_hubspot_properties.py
```

If properties are missing, follow the guide:
- See `hubspot_properties_guide.md` for step-by-step instructions
- Create properties in HubSpot UI
- Run verification script again

### 2. Prepare Leads CSV

Use `leads_template.csv` as a template for your leads:

1. Replace example rows with real lead data
2. Ensure required columns are present:
   - Email (required)
   - First Name
   - Last Name
   - Company
   - City
   - Job Title
   - vertical (must be: medical, legal, realestate, or agencies)
3. Save as CSV
4. Import to HubSpot (Contacts → Import)

### 3. Next Steps

After setup is complete:
1. Generate email content using HubSpot Marketing Email GPT
2. Generate landing pages using HubSpot Landing Page Creator GPT
3. Run first test campaign
4. See main README.md for full workflow

