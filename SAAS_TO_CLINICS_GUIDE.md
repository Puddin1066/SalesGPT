# Selling SaaS to Clinics - Configuration Guide

## Current Issue

The system is currently configured with **marketing/SEO messaging** ("clinic visibility", "patient acquisition") which works if you're selling marketing SaaS, but not if you're selling other SaaS products to clinics.

## What Needs to Change

### 1. **Value Proposition Messaging**

**Current (Marketing SaaS)**:
- "Improve your clinic's visibility"
- "Patient acquisition"
- GEMflush audit scores

**Needs to be configurable for different SaaS types**:

#### Practice Management SaaS
- "Reduce admin time by X hours/week"
- "Automate patient scheduling and reminders"
- "Integrate with your EMR system"

#### Billing/Revenue Cycle SaaS
- "Increase collections by X%"
- "Reduce claim denials"
- "Automate insurance verification"

#### Telemedicine SaaS
- "Expand patient reach"
- "Reduce no-shows with virtual visits"
- "HIPAA-compliant video consultations"

#### Patient Engagement SaaS
- "Improve patient satisfaction scores"
- "Automate appointment reminders"
- "Reduce missed appointments by X%"

#### Marketing/SEO SaaS (Current)
- "Improve clinic visibility"
- "Patient acquisition"
- GEMflush audits

### 2. **Email Templates - SaaS-Focused**

The templates need to be configurable based on SaaS product type. Here are examples:

#### Practice Management SaaS Template
```
Subject: Quick question about {{clinic_name}}'s operations

Hi {{first_name}},

I noticed {{clinic_name}} specializes in {{specialty}} and thought you might 
be interested in how [YourSaaS] helps similar clinics:

• Reduce admin time by 10+ hours/week with automated scheduling
• Integrate seamlessly with [EMR system]
• Improve patient satisfaction with automated reminders

Would you be open to a quick 15-min demo?

Best,
{{from_name}}
```

#### Billing SaaS Template
```
Subject: Quick question about {{clinic_name}}'s revenue cycle

Hi {{first_name}},

I noticed {{clinic_name}} and wanted to share how [YourSaaS] helps clinics 
like yours:

• Increase collections by 15-25%
• Reduce claim denials with automated verification
• Get paid faster with real-time insurance checks

Happy to show you how it works in a quick demo.

Best,
{{from_name}}
```

### 3. **Intent Handling - SaaS-Specific**

Current intents are too generic. For SaaS to clinics, we need:

- **demo_request** → Send demo booking link
- **pricing_question** → Send pricing + ROI calculator
- **integration_question** → Send integration docs (EMR, billing systems)
- **trial_request** → Send trial signup link
- **security/compliance** → Send HIPAA/SOC2 docs
- **objection** → Handle specific objections (cost, complexity, time to implement)
- **interested** → Send demo + case study

### 4. **Tools - Replace GEMflush with SaaS Tools**

**If selling Marketing/SEO SaaS**: Keep GEMflush
**If selling other SaaS**: Replace with:

- **Demo Scheduler**: Book demos with pre-qualification
- **Trial Manager**: Generate trial links, track signups
- **ROI Calculator**: Calculate time/cost savings for clinics
- **Integration Checker**: Check EMR/billing system compatibility
- **Case Study Selector**: Match case studies by specialty/clinic size
- **Compliance Docs**: HIPAA, SOC2 documentation

### 5. **SalesGPT Configuration**

The SalesGPT agent needs to be configured with SaaS product information:

```python
sales_agent = SalesGPT.from_llm(
    llm=llm,
    use_tools=True,
    product_catalog="saas_product_catalog.txt",  # Features, integrations, pricing
    salesperson_name="Alex",
    salesperson_role="Account Executive",
    company_name="YourSaaS",
    company_business='''[YourSaaS] is a [type] SaaS platform that helps 
    healthcare clinics [key benefit]. We help clinics:
    • [Benefit 1]
    • [Benefit 2]
    • [Benefit 3]
    
    We integrate with [EMR systems, billing systems, etc.] and serve 
    clinics from [size range] employees.'''
)
```

## Implementation Plan

### Step 1: Make Value Props Configurable

Add SaaS product type configuration:

```python
SAAS_PRODUCT_TYPES = {
    "practice_management": {
        "value_props": [
            "Reduce admin time by 10+ hours/week",
            "Automate patient scheduling",
            "Integrate with EMR systems"
        ],
        "use_gemflush": False,
        "tools": ["demo_scheduler", "trial_manager", "roi_calculator", "integration_checker"]
    },
    "billing": {
        "value_props": [
            "Increase collections by 15-25%",
            "Reduce claim denials",
            "Automate insurance verification"
        ],
        "use_gemflush": False,
        "tools": ["demo_scheduler", "roi_calculator", "integration_checker"]
    },
    "marketing_seo": {
        "value_props": [
            "Improve clinic visibility",
            "Patient acquisition",
            "Competitive positioning"
        ],
        "use_gemflush": True,  # Keep GEMflush for marketing SaaS
        "tools": ["demo_scheduler", "gemflush_audit"]
    },
    # ... other types
}
```

### Step 2: Update Email Templates

Make templates configurable by SaaS product type in `.env.local`:

```bash
SAAS_PRODUCT_TYPE=practice_management  # or billing, marketing_seo, etc.

# Practice Management Templates
SMARTLEAD_INITIAL_SUBJECT=Quick question about {{clinic_name}}'s operations
SMARTLEAD_INITIAL_BODY=Hi {{first_name}},\n\nI noticed {{clinic_name}} specializes in {{specialty}} and thought you might be interested in how [YourSaaS] helps similar clinics reduce admin time by 10+ hours/week with automated scheduling.\n\nWould you be open to a quick 15-min demo?\n\nBest,\n{{from_name}}

# Or Billing Templates
# SMARTLEAD_INITIAL_SUBJECT=Quick question about {{clinic_name}}'s revenue cycle
# SMARTLEAD_INITIAL_BODY=...
```

### Step 3: Update Intent Handling

Enhance intent classification for SaaS-specific intents:

```python
def classify_saas_intent(email_body: str) -> str:
    body_lower = email_body.lower()
    
    # SaaS-specific intents
    if any(word in body_lower for word in ["demo", "show me", "see how it works"]):
        return "demo_request"
    
    if any(word in body_lower for word in ["trial", "try it", "test"]):
        return "trial_request"
    
    if any(word in body_lower for word in ["price", "cost", "pricing", "how much"]):
        return "pricing_question"
    
    if any(word in body_lower for word in ["integrate", "works with", "compatible", "emr"]):
        return "integration_question"
    
    if any(word in body_lower for word in ["hipaa", "compliant", "security", "soc2"]):
        return "security_question"
    
    # ... existing intents
```

### Step 4: Conditional GEMflush Usage

Only use GEMflush if selling marketing/SEO SaaS:

```python
# In main_agent.py handle_reply()
if intent in ["curious", "neutral"]:
    product_type = os.getenv("SAAS_PRODUCT_TYPE", "practice_management")
    
    if product_type == "marketing_seo":
        # Use GEMflush for marketing SaaS
        evidence = self.visibility.get_competitor_comparison(...)
    else:
        # Use SaaS-specific tools
        if intent == "curious":
            # Send case study or ROI calculator
            case_study = self.get_case_study_by_specialty(specialty)
            reply_body += f"\n\n{case_study}"
        elif intent == "pricing_question":
            # Send ROI calculator
            roi_link = self.roi_calculator.generate_link(clinic_size)
            reply_body += f"\n\n{roi_link}"
```

## Quick Fixes for Current System

If you want to quickly adapt the current system:

1. **Update email templates** in `.env.local`:
   - Change "visibility" → your SaaS value prop
   - Change "patient acquisition" → your SaaS benefit

2. **Update SalesGPT config** (`examples/example_agent_setup.json`):
   - Update `company_business` with your SaaS description
   - Update `product_catalog` with your SaaS features

3. **Make GEMflush optional**:
   - Only use if selling marketing/SEO SaaS
   - Otherwise, replace with demo/trial/ROI tools

4. **Enhance intent classification**:
   - Add SaaS-specific intents (demo, trial, pricing, integration)

## What SaaS Product Are You Selling?

To properly configure this, I need to know:

1. **What type of SaaS?** (Practice Management, Billing, Telemedicine, Marketing, etc.)
2. **Key value props?** (Time savings, cost reduction, compliance, etc.)
3. **Key integrations?** (EMR systems, billing systems, etc.)
4. **Target clinic size?** (Small practices, large clinics, etc.)
5. **Main objections?** (Cost, complexity, implementation time, etc.)

Once I know this, I can:
- Update email templates with your value props
- Configure SalesGPT with your product info
- Set up appropriate tools (demo, trial, ROI calculator, etc.)
- Make GEMflush optional/conditional
- Enhance intent handling for your SaaS

Would you like me to make these changes? What SaaS product are you selling to clinics?
