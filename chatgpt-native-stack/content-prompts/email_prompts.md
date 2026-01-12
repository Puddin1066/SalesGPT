# Email Sequence Generation Prompts

Copy these prompts into ChatGPT with "HubSpot Marketing Email" GPT selected.

## Prompt Template (Use for each vertical × 3 emails)

### Email 1: Initial Outreach

```
Create evidence-driven cold email for [VERTICAL].

Product: GemFlush - AI Visibility Audit tool
Shows how businesses appear in ChatGPT/Claude/Gemini vs competitors

Target: [Practice Managers / Managing Partners / Broker Owners / CMOs]
Job Titles: [Practice Manager, Office Manager, Medical Director / Managing Partner, Marketing Director, Solo Practitioner / Broker Owner, Marketing Manager, Team Lead / Partner, CMO, Head of Growth]

Email 1 (Initial Outreach):
- Subject: 2 variants (problem-focused, curiosity-focused)
- Body: 150 words max, evidence-driven
- Include stat about AI search adoption in their industry
- Personalization: {{firstname}}, {{company}}, {{city}}
- CTA: Link to landing page

Tone: Professional, data-backed, not salesy
Format: Plain text for HubSpot
Output format: Subject variant A on first line, Subject variant B on second line, body below
```

### Email 2: Follow-up

```
Create follow-up email for [VERTICAL] cold email sequence.

Product: GemFlush - AI Visibility Audit tool

Email 2 (Follow-up):
- Subject: Social proof or competitor angle (2 variants)
- Body: Brief case study or example (175 words max)
- Reference similar businesses in their vertical
- CTA: "Want to see your audit?"

Tone: Professional, consultative
Format: Plain text for HubSpot
Output format: Subject variant A on first line, Subject variant B on second line, body below
```

### Email 3: Breakup

```
Create breakup email for [VERTICAL] cold email sequence.

Product: GemFlush - AI Visibility Audit tool

Email 3 (Breakup):
- Subject: Final touch (2 variants: FOMO or helpful resource)
- Body: Urgency or helpful framing (125 words max)
- Offer: Free audit or limited demo slots
- CTA: "Reply 'yes' for free audit" or strong CTA

Tone: Professional, helpful exit
Format: Plain text for HubSpot
Output format: Subject variant A on first line, Subject variant B on second line, body below
```

## Vertical-Specific Details

### Medical Clinics
- Replace `[VERTICAL]` with "medical clinics"
- Replace `[Practice Managers / ...]` with "Practice Managers, Office Managers, Medical Directors"
- Stats: "64% of patients use ChatGPT to research providers"
- Use case: Patient search behavior, local competition

### Legal Firms
- Replace `[VERTICAL]` with "legal firms"
- Replace `[Practice Managers / ...]` with "Managing Partners, Marketing Directors, Solo Practitioners"
- Stats: "Clients using ChatGPT for legal research"
- Use case: Client acquisition, practice area differentiation

### Real Estate Agencies
- Replace `[VERTICAL]` with "real estate agencies"
- Replace `[Practice Managers / ...]` with "Broker Owners, Marketing Managers, Team Leads"
- Stats: "Home buyers using AI tools for property search"
- Use case: Listing visibility, agent recruitment

### Marketing Agencies / VC Firms
- Replace `[VERTICAL]` with "marketing agencies and venture capital firms"
- Replace `[Practice Managers / ...]` with "Partners, CMOs, Heads of Growth"
- Stats: "Portfolio company performance tracking"
- Use case: Competitive intelligence, AI strategy

## File Saving Format

Save each email in `email-content/` directory as: `{vertical}_email_{number}.txt`

**File format:**
```
Subject Variant A
Subject Variant B

Email body here with {{personalization}} tokens.

- Alex
```

**Example files:**
- `medical_email_1.txt`
- `medical_email_2.txt`
- `medical_email_3.txt`
- `legal_email_1.txt`
- (repeat for all 12 emails: 4 verticals × 3 emails)

## Usage

1. Open ChatGPT Plus
2. Search for and select "HubSpot Marketing Email" GPT
3. Copy prompt above for Email 1
4. Replace `[VERTICAL]` and job titles with vertical-specific details
5. Paste into ChatGPT
6. Copy generated output
7. Save as `{vertical}_email_1.txt` in `email-content/` directory
8. Repeat for Email 2 and Email 3
9. Repeat for all 4 verticals

Total: 12 email files (4 verticals × 3 emails)

