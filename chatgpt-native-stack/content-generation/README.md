# Content Generation - Fully Automated

Generate all marketing content using OpenAI API. No manual ChatGPT interaction needed!

## Quick Start

### Generate Everything (One Command)

```bash
cd /Users/JJR/SalesGPT
python3 chatgpt-native-stack/content-generation/generate_all_content.py
```

**What it does:**
- Generates 12 email sequences (3 emails × 4 verticals)
- Generates 8 landing pages (2 variants × 4 verticals)
- Saves all files automatically
- **Time: 2-3 minutes** (vs 4-6 hours manual)

---

## Individual Scripts

### 1. Generate Email Sequences

```bash
python3 chatgpt-native-stack/content-generation/generate_emails.py
```

**Output:** 12 files in `email-content/`
- `medical_email_1.txt` (subject A, subject B, body)
- `medical_email_2.txt`
- `medical_email_3.txt`
- (repeat for legal, realestate, agencies)

**Format:**
```
{{subject line A}}
{{subject line B}}

{{email body with {{firstname}}, {{company}}, {{city}} tokens}}
```

**Used by:** `gemflush_campaign.py` (reads these files for campaigns)

---

### 2. Generate Landing Pages

```bash
python3 chatgpt-native-stack/content-generation/generate_landing_pages.py
```

**Output:** 8 files in `content-generation/output/landing-pages/`
- `medical_landing_page_a.md` (audit-focused)
- `medical_landing_page_b.md` (demo-focused)
- (repeat for legal, realestate, agencies)

**Format:** Markdown with sections:
- Hero headline
- Hero subheadline
- Problem/benefits points
- How it works
- Social proof
- CTA

**Used by:** You (copy/paste into HubSpot landing page builder)

---

## Requirements

### 1. OpenAI API Key

Add to your `.env.local`:

```bash
OPENAI_API_KEY=sk-proj-...
```

**Cost Estimate:**
- 12 emails @ ~500 tokens each = ~6,000 tokens
- 8 landing pages @ ~1,500 tokens each = ~12,000 tokens
- Total: ~18,000 tokens = **$0.20 - $0.30** per run (GPT-4 Turbo)

### 2. Python OpenAI Library

```bash
pip3 install openai
```

Or add to requirements.txt:
```
openai>=1.0.0
```

---

## How It Works

### Architecture

```
generate_all_content.py
         │
         ├─ generate_emails.py
         │  ├─ Calls OpenAI API
         │  ├─ 12 API calls (one per email)
         │  └─ Saves to email-content/
         │
         └─ generate_landing_pages.py
            ├─ Calls OpenAI API
            ├─ 8 API calls (one per page)
            └─ Saves to output/landing-pages/
```

### Content Generation Flow

```python
# For each vertical and email/page:
1. Load vertical-specific prompts (medical, legal, etc.)
2. Create OpenAI API request with prompt
3. Call GPT-4 Turbo via OpenAI API
4. Parse and format response
5. Save to file in correct format
6. Repeat for next piece of content
```

### Prompts Used

**Emails:**
- Email 1: Problem-focused, evidence-driven, 150 words
- Email 2: Case study follow-up, social proof, 175 words
- Email 3: Breakup email, FOMO or helpful, 125 words

**Landing Pages:**
- Variant A: Audit-focused, "Get Your Free Audit" CTA
- Variant B: Demo-focused, "Book 15-Min Demo" CTA

**Personalization:**
- Emails include: `{{firstname}}`, `{{company}}`, `{{city}}`
- Landing pages include vertical-specific stats and pain points

---

## Customization

### Edit Prompts

Prompts are in the script files:

**Emails:** `generate_emails.py` - lines 40-120
**Landing Pages:** `generate_landing_pages.py` - lines 40-120

**To customize:**
1. Edit the prompt strings
2. Adjust tone, length, or focus
3. Re-run generation script

### Change Model

Default: `gpt-4-turbo-preview`

To use different model:
```python
# In generate_emails.py or generate_landing_pages.py
model="gpt-4o"  # or "gpt-3.5-turbo" (cheaper)
```

**Model costs (per 1K tokens):**
- GPT-4 Turbo: $0.01 input, $0.03 output
- GPT-4o: $0.005 input, $0.015 output
- GPT-3.5 Turbo: $0.0005 input, $0.0015 output

---

## Output Files

### Email Content (`email-content/`)

```
email-content/
├── medical_email_1.txt
├── medical_email_2.txt
├── medical_email_3.txt
├── legal_email_1.txt
├── legal_email_2.txt
├── legal_email_3.txt
├── realestate_email_1.txt
├── realestate_email_2.txt
├── realestate_email_3.txt
├── agencies_email_1.txt
├── agencies_email_2.txt
└── agencies_email_3.txt
```

**Format:**
```
Subject Variant A
Subject Variant B

Email body with {{personalization}} tokens.

Best,
Alex
```

### Landing Pages (`output/landing-pages/`)

```
output/landing-pages/
├── medical_landing_page_a.md
├── medical_landing_page_b.md
├── legal_landing_page_a.md
├── legal_landing_page_b.md
├── realestate_landing_page_a.md
├── realestate_landing_page_b.md
├── agencies_landing_page_a.md
└── agencies_landing_page_b.md
```

**Format:** Markdown with sections

---

## Integration with Campaign Scripts

### Automatic Usage

```bash
# 1. Generate content
python3 chatgpt-native-stack/content-generation/generate_all_content.py

# 2. Run campaign (automatically uses generated emails)
python3 chatgpt-native-stack/gemflush_campaign.py \
  --vertical medical \
  --email 1 \
  --count 200
```

**Campaign script automatically:**
- Reads `email-content/medical_email_1.txt`
- Parses subject lines A & B
- Personalizes body with contact data
- Sends A/B split (100 each variant)

**No manual steps needed!**

---

## Time Comparison

### Manual (ChatGPT Plus UI)
- Open browser
- Find GPT
- Copy prompts
- Generate one by one
- Copy/paste to files
- **Time: 4-6 hours**

### Automated (This Script)
- Run one command
- Script handles all API calls
- All files generated automatically
- **Time: 2-3 minutes**

**Time saved: ~4-6 hours** (98% reduction)

---

## Cost Analysis

### Per Generation Run

**OpenAI API:**
- 20 pieces of content @ ~1,000 tokens avg
- Total: ~40,000 tokens (input + output)
- Cost: **$0.30 - $0.50** per run (GPT-4 Turbo)

**Annual (4 campaigns):**
- 4 runs × $0.40 avg = **$1.60/year**

### vs. Manual ChatGPT Plus

**ChatGPT Plus:**
- $20/month × 12 = **$240/year**
- Still need to copy/paste manually (4-6 hours)

**OpenAI API:**
- $1.60/year for content generation
- **Fully automated** (2-3 minutes)

**Savings: $238.40/year + 16-24 hours of time**

---

## Troubleshooting

### Error: "OPENAI_API_KEY not found"

```bash
# Add to .env.local
echo 'OPENAI_API_KEY=sk-proj-...' >> .env.local

# Verify
grep OPENAI_API_KEY .env.local
```

### Error: "No module named 'openai'"

```bash
pip3 install openai
```

### Error: "Rate limit exceeded"

OpenAI API has rate limits. If you hit them:
- Wait 60 seconds
- Re-run script (it will skip already generated files)
- Or upgrade OpenAI API tier

### Generated Content Quality Issues

**Adjust prompts:**
1. Edit `generate_emails.py` or `generate_landing_pages.py`
2. Modify prompt text (tone, length, focus)
3. Re-run generation

**Try different model:**
- GPT-4o: Better quality, slightly cheaper
- GPT-3.5: Much cheaper, lower quality

---

## Next Steps

### After Content Generation

1. **Review Generated Content**
   ```bash
   # Check emails
   ls -la email-content/
   cat email-content/medical_email_1.txt
   
   # Check landing pages
   ls -la content-generation/output/landing-pages/
   cat content-generation/output/landing-pages/medical_landing_page_a.md
   ```

2. **Build Landing Pages**
   - Open HubSpot → Marketing → Landing Pages
   - Copy/paste generated markdown into page builder
   - Publish (8 pages total)

3. **Run Campaigns**
   ```bash
   # Campaign automatically uses generated emails
   python3 chatgpt-native-stack/gemflush_campaign.py \
     --vertical medical \
     --email 1 \
     --count 200
   ```

---

## Summary

✅ **Fully automated** content generation
✅ **OpenAI API** powered (GPT-4 Turbo)
✅ **2-3 minutes** vs 4-6 hours manual
✅ **$0.30-0.50** per run vs $20/month ChatGPT Plus
✅ **Integrated** with campaign scripts
✅ **Customizable** prompts and models

**No manual ChatGPT interaction needed!**

Run: `generate_all_content.py` and you're done! 🚀


