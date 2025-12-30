# AI Visibility SaaS - Setup Guide

## Overview

This system is now optimized for selling **AI Visibility SaaS** to healthcare clinics. The platform helps clinics:
- Improve discoverability in AI-powered patient searches
- Understand competitive positioning
- Get actionable insights to boost patient acquisition

## Key Changes Made

### 1. **SaaS-Focused Email Templates**

**Initial Email**:
- Focuses on AI visibility platform (not just "visibility")
- Highlights SaaS benefits: competitive insights, actionable recommendations
- Clear call-to-action: "15-min demo"

**Follow-up Email**:
- Emphasizes SaaS platform capabilities
- Professional, consultative tone
- Demo-focused CTA

### 2. **Enhanced Intent Classification**

Now recognizes SaaS-specific intents:
- **demo_request**: "Can I see a demo?"
- **trial_request**: "I'd like to try it"
- **pricing_question**: "How much does it cost?"
- **interested**: General interest
- **objection**: Pricing/concerns
- **curious**: Want more info
- **not_interested**: Opt-out

### 3. **SaaS-Specific Intent Handling**

**Demo Request** → Sends demo booking link with agenda
**Trial Request** → Sends trial signup link (if configured)
**Pricing Question** → Sends pricing page + ROI context
**Interested** → Routes to demo booking
**Objection** → Provides GEMflush evidence + ROI messaging
**Curious** → Provides GEMflush insights + platform info

### 4. **GEMflush Integration**

GEMflush is perfect for AI visibility SaaS - it provides:
- Visibility audit scores
- Competitor comparisons
- Evidence for email replies
- Competitive positioning data

## Configuration

### Required Environment Variables

Update `.env.local` with:

```bash
# SaaS-Specific Configuration
TRIAL_SIGNUP_LINK=https://your-saas.com/trial
PRICING_PAGE_URL=https://your-saas.com/pricing

# Email Templates (already updated for SaaS)
SMARTLEAD_INITIAL_SUBJECT=Quick question about {{clinic_name}}'s AI visibility
SMARTLEAD_INITIAL_BODY=Hi {{first_name}},\n\nI noticed {{clinic_name}} specializes in {{specialty}} and thought you might be interested in how our AI visibility platform helps similar clinics:\n\n• Improve discoverability in AI-powered patient searches\n• See how you compare to competitors in your area\n• Get actionable insights to boost patient acquisition\n\nWould you be open to a quick 15-min demo?\n\nBest,\n{{from_name}}

SMARTLEAD_FOLLOWUP_SUBJECT=Following up on AI visibility for {{clinic_name}}
SMARTLEAD_FOLLOWUP_BODY=Hi {{first_name}},\n\nJust wanted to follow up. Our AI visibility platform helps clinics like {{clinic_name}} understand their competitive positioning and improve patient discovery.\n\nI can show you a quick demo of how it works - would 15 minutes this week work?\n\nBest,\n{{from_name}}

# SalesGPT Configuration
SALESGPT_CONFIG_PATH=examples/example_ai_visibility_saas_setup.json
```

### SalesGPT Agent Configuration

Use `examples/example_ai_visibility_saas_setup.json` which includes:
- SaaS-focused company description
- AI visibility value propositions
- SaaS sales stages (trial → demo → close)
- Professional, consultative tone

## Pipeline Stages

The system now tracks SaaS-appropriate stages:

1. **prospect** → Initial outreach
2. **demo_scheduled** → Demo booked
3. **trial** → Trial signup
4. **engaged** → Active conversation
5. **pricing_discussion** → Pricing questions
6. **booked** → Demo completed, moving to close

## How It Works

### Daily Pipeline

1. **Apollo** finds clinics by specialty/location
2. **Smartlead** sends SaaS-focused email sequences
3. **Webhook** catches replies
4. **SalesGPT** classifies intent (demo/trial/pricing/etc.)
5. **Intent Handler** routes to appropriate action:
   - Demo request → Cal.com booking link
   - Trial request → Trial signup link
   - Pricing → Pricing page + ROI context
   - Objection → GEMflush evidence + ROI messaging
6. **HubSpot** tracks pipeline stages
7. **GEMflush** provides competitive insights

### Reply Handling Flow

```
Email Reply
    ↓
SalesGPT Classifies Intent
    ↓
Intent Handler Routes:
    ├─→ demo_request → Demo booking link
    ├─→ trial_request → Trial signup link  
    ├─→ pricing_question → Pricing page + ROI
    ├─→ objection → GEMflush evidence + ROI
    └─→ curious → GEMflush insights
    ↓
Reply Sent via Smartlead
    ↓
HubSpot Updated
```

## Value Propositions

The system now emphasizes SaaS benefits:

- **AI-Powered**: "Improve discoverability in AI-powered patient searches"
- **Competitive Insights**: "See how you compare to competitors"
- **Actionable**: "Get actionable insights to boost patient acquisition"
- **Easy Setup**: "Quick 15-min demo" (implies easy onboarding)
- **ROI Focus**: "Most clinics see ROI within 30-60 days"

## Next Steps

1. **Update `.env.local`** with your SaaS URLs (trial, pricing)
2. **Configure SalesGPT** to use `example_ai_visibility_saas_setup.json`
3. **Customize email templates** with your specific value props
4. **Set up Cal.com** booking link for demos
5. **Configure GEMflush** API (perfect for visibility SaaS!)
6. **Test the flow** with a small batch of leads

## Customization Options

### Add Your Own Value Props

Edit email templates in `.env.local`:
- Replace generic benefits with your specific features
- Add case studies or ROI stats
- Include specific integrations or capabilities

### Add More SaaS Tools

Consider adding:
- **ROI Calculator**: Interactive tool for clinics
- **Case Study Selector**: Match by specialty/clinic size
- **Integration Checker**: Check EMR/billing system compatibility
- **Trial Manager**: Track trial signups and conversions

### Enhance Intent Classification

Add more specific intents:
- `integration_question`: "Does it work with Epic/Athena?"
- `security_question`: "Is it HIPAA compliant?"
- `competitor_compare`: "How does this compare to CompetitorX?"

## Why This Works for AI Visibility SaaS

1. **GEMflush Integration**: Provides the exact data you need (visibility scores, competitor comparisons)
2. **SaaS Messaging**: Emphasizes platform, ROI, easy setup
3. **Demo-Focused**: Routes to demos (not just calls)
4. **Trial Support**: Can route to trial signups
5. **Competitive Insights**: Uses GEMflush data to show value
6. **Professional Tone**: Consultative, not pushy

The system is now optimized for selling AI visibility SaaS to clinics! 🚀
