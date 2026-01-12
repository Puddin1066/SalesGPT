# Email Content Directory

This directory stores ChatGPT-generated email content for GemFlush campaigns.

## File Naming Convention

Files should be named: `{vertical}_email_{number}.txt`

Examples:
- `medical_email_1.txt` - Medical vertical, first email
- `legal_email_2.txt` - Legal vertical, second email (follow-up)
- `realestate_email_3.txt` - Real Estate vertical, third email (breakup)

## File Format

Each file should contain:
1. **First line:** Subject line variant A
2. **Second line:** Subject line variant B
3. **Remaining lines:** Email body template (with personalization tokens)

Example:
```
{{firstname}}, your competitors are showing up in ChatGPT
Quick question about {{company}}'s AI visibility

Hi {{firstname}},

I noticed {{company}} is a {{industry}} practice in {{city}}.

According to a recent study, 64% of patients now use ChatGPT to research medical providers before booking—but most local practices aren't showing up at all.

When I searched "best {{specialty}} near {{city}}" in ChatGPT, your practice wasn't mentioned. Your competitors were.

Curious how {{company}} ranks in AI search results?

Best,
[Your name]
```

## Personalization Tokens

Use these tokens in your email templates:
- `{{firstname}}` or `{{contact.firstname}}` - Contact's first name
- `{{company}}` or `{{contact.company}}` - Company name
- `{{city}}` or `{{contact.city}}` - City
- `{{jobtitle}}` - Job title

These will be replaced automatically by the campaign script.

## Generating Content

Use **HubSpot Marketing Email GPT** in ChatGPT to generate email content:

1. Open ChatGPT
2. Search for "HubSpot Marketing Email" GPT
3. Use prompts like:

```
Create evidence-driven cold email for medical clinics.

Product: GemFlush - AI Visibility Audit
Target: Practice Managers at medical clinics

Email 1 (Initial Outreach):
- Subject: 2 variants (problem-focused, curiosity-focused)
- Body: 150 words max, evidence-driven
- Include stat about AI search adoption
- Personalization: {{firstname}}, {{company}}, {{city}}
- CTA: Link to landing page

Tone: Professional, data-backed, not salesy
Format: Plain text for HubSpot
```

4. Save output in the format specified above

