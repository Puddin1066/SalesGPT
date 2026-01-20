# Apollo Data Storage Guide

This document explains where all Apollo contact data is stored in the SalesGPT framework.

## Overview

All Apollo data from `search_leads()` is captured and stored in **two locations**:
1. **StateManager** (JSON files) - Local persistence for application state
2. **HubSpot CRM** - Cloud-based CRM for sales pipeline management

**Important**: All data is captured from the initial Apollo search - **NO additional API calls or credits required**.

## Storage Locations

### 1. StateManager (`state/lead_states.json`)

**Location**: `./state/lead_states.json`

**Purpose**: Local JSON file storage for application state, conversation tracking, and lead metadata.

**Data Stored**:
- **Basic Contact Info**
  - `name`, `email`, `company_name`, `website`, `location`, `specialty`
  
- **Apollo Identifiers**
  - `apollo_person_id` - Apollo's unique person ID
  - `apollo_organization_id` - Apollo's unique organization ID
  
- **Person Professional Info**
  - `title` - Job title
  - `linkedin_url` - LinkedIn profile URL
  
- **Person Contact & Location**
  - `person_phone` - Phone number
  - `person_city`, `person_state`, `person_country`, `person_postal_code`
  
- **Organization Details**
  - `organization_name`, `organization_website`, `organization_phone`
  - `employee_count` - Estimated number of employees
  - `organization_industry` - Industry classification
  - `organization_city`, `organization_state`, `organization_country`, `organization_postal_code`
  
- **Quality & Tracking**
  - `score` - Lead quality score (0-20+)
  - `campaign_id` - Smartlead campaign ID
  - `first_seen` - First time lead was discovered
  - `last_updated` - Last update timestamp
  - `apollo_updated_at` - Apollo's last update timestamp
  - `organization_updated_at` - Organization last update timestamp

**Access**: Via `StateManager` class methods:
```python
from state import StateManager

state = StateManager()
lead_data = state.get_lead_state("email@example.com")
```

### 2. HubSpot CRM

**Location**: HubSpot Cloud (via API)

**Purpose**: Cloud-based CRM for sales pipeline management, deal tracking, and team collaboration.

**Data Stored**:
- **Standard Contact Properties**
  - `email`, `firstname`, `lastname`
  - `company` - Company name
  - `website` - Website URL
  - `phone` - Phone number
  - `jobtitle` - Job title
  - `linkedin` - LinkedIn URL
  - `city`, `state`, `country`, `zip` - Location data

- **Custom Properties** (stored as additional_properties)
  - `apollo_person_id` - Apollo person ID
  - `apollo_organization_id` - Apollo organization ID
  - `organization_phone` - Organization phone
  - `employee_count` - Number of employees
  - `organization_industry` - Industry
  - `organization_city`, `organization_state`, `organization_country` - Org location
  - `lead_score` - Quality score
  - `specialty` - Medical specialty

**Access**: Via HubSpot web interface or API:
```python
from services.crm import HubSpotAgent

crm = HubSpotAgent()
contact = crm.get_contact_by_email("email@example.com")
```

## Data Flow

```
Apollo API (search_leads)
    ↓
ApolloAgent extracts ALL available fields
    ↓
    ├─→ StateManager (JSON file) - Full data storage
    └─→ HubSpot CRM - Contact creation with all fields
```

## What Data is Available from Apollo?

The `mixed_people/search` endpoint returns:

### Person Fields
- `id` - Apollo person ID ✅ Stored
- `first_name`, `last_name` ✅ Stored
- `email` ✅ Stored
- `title` ✅ Stored
- `linkedin_url` ✅ Stored
- `phone_numbers[]` ✅ Stored (first number)
- `city`, `state`, `country`, `postal_code` ✅ Stored
- `updated_at` ✅ Stored

### Organization Fields
- `id` - Apollo organization ID ✅ Stored
- `name` ✅ Stored
- `website_url` ✅ Stored
- `primary_phone` ✅ Stored
- `estimated_num_employees` ✅ Stored
- `industry` ✅ Stored
- `city`, `state`, `country`, `postal_code` ✅ Stored
- `updated_at` ✅ Stored

## Credit Usage

| Operation | API Calls | Credits |
|----------|-----------|---------|
| `search_leads()` | 1 | Plan-dependent (may be free) |
| **Storing all data** | **0** | **0** ✅ |
| `enrich_person()` (optional) | +1 | 1 credit per person |
| `enrich_organization()` (optional) | +1 | 1 credit per org |

**All data storage happens with ZERO additional API calls** - we capture everything from the initial search response.

## Enrichment (Optional - Costs Credits)

For deeper data (phone numbers, social profiles, company financials), use enrichment methods:

```python
# Enrich high-value leads only (costs 2 credits: 1 person + 1 org)
if lead.metadata.get("score", 0) >= 15:
    enriched_lead = apollo.enrich_lead(lead)
    # enriched_lead contains: phone, social profiles, company details, etc.
```

## Best Practices

1. **All search data is stored** - No need to re-fetch basic info
2. **Use enrichment selectively** - Only for high-value leads (score ≥ 15)
3. **StateManager for app state** - Use for conversation history, lead status
4. **HubSpot for sales pipeline** - Use for CRM, deals, team collaboration
5. **Apollo IDs stored** - Use `apollo_person_id` and `apollo_organization_id` for future API calls

## File Locations

- **StateManager**: `./state/lead_states.json`
- **HubSpot**: Cloud-based (accessible via API or web UI)
- **Code**: 
  - Apollo extraction: `services/apollo/apollo_agent.py`
  - State storage: `main_agent.py` (lines 145-189)
  - HubSpot storage: `main_agent.py` (lines 193-230)
  - HubSpot agent: `services/crm/hubspot_agent.py`

## Summary

✅ **All available Apollo data is captured and stored**
✅ **Zero additional API calls required**
✅ **Data stored in both StateManager (local) and HubSpot (cloud)**
✅ **Ready for sales pipeline management and team collaboration**



