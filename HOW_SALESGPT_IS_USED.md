# 🤖 How SalesGPT is Used in the System

## Overview

SalesGPT is the **AI brain** of the system. It's used for two main purposes:
1. **Generating initial cold emails** (personalized, evidence-driven)
2. **Handling email replies** (intent analysis, contextual responses)

---

## 🎯 Two Main Use Cases

### 1. **Initial Email Generation** (Outbound)

SalesGPT generates personalized cold emails when leads are first processed.

**When it's called:**
- During `BackgroundQueueBuilder` workflow
- When processing new leads from Apollo
- Before emails are sent via Smartlead

**What it does:**
- Generates personalized email content
- Incorporates competitive analysis data
- Follows ELM (Elaboration Likelihood Model) persuasion routes
- Creates subject lines and email bodies

**Code location:** `workflows/background_queue_builder.py`

### 2. **Reply Handling** (Inbound)

SalesGPT analyzes and responds to email replies from leads.

**When it's called:**
- When Smartlead webhook receives a reply
- Automatically via `webhook_handler.py`
- After lead responds to initial email

**What it does:**
- Classifies intent (interested, objection, curious, neutral)
- Generates contextual responses
- Determines conversation stage
- Provides booking links or evidence as needed

**Code location:** `webhook_handler.py` → `main_agent.py` → `SalesGPTWrapper`

---

## 📧 Use Case 1: Generating Initial Emails

### Flow Diagram

```
Apollo Lead → Background Queue Builder
    ↓
Competitive Analysis (GEMflush)
    ↓
ELM Score Calculation
    ↓
A/B Variant Assignment
    ↓
SalesGPT.generate_initial_email()  ← YOU ARE HERE
    ↓
Email Content (subject + body)
    ↓
HubSpot Contact (with email content)
    ↓
Database Storage (pending_review)
    ↓
Dashboard Review
    ↓
Smartlead Send
```

### Code Example

**File:** `workflows/background_queue_builder.py`

```python
# 1. Get competitive analysis
evidence = {
    "lead_score": 65,
    "competitor_score": 85,
    "gap_percentage": 20,
    "competitor_name": "Competitor A",
    "referral_multiplier": 2.5
}

# 2. Assign A/B variant
variant = self.ab_manager.assign_variant(lead.email, {...})

# 3. Generate email using SalesGPT
email = self.ab_manager.generate_email_from_variant(
    variant=variant,
    salesgpt_wrapper=self.salesgpt,  # ← SalesGPT used here
    lead=lead_dict,
    evidence=evidence,
    competitor=competitor_dict
)

# Result: email["subject"] and email["body"]
```

### What SalesGPT Does

**Method:** `SalesGPTWrapper.generate_initial_email()`

1. **Loads ELM playbook** - Gets persuasion route configuration
2. **Builds context** - Combines lead info + competitive analysis
3. **Generates email body** - Uses GPT to create personalized content
4. **Generates subject line** - Creates compelling subject from patterns
5. **Injects disclaimers** - Adds required disclaimers based on route

**Key Features:**
- ✅ **ELM-compliant** - Follows central/peripheral persuasion routes
- ✅ **Evidence-driven** - Incorporates competitive analysis
- ✅ **Personalized** - Uses lead name, company, location, specialty
- ✅ **A/B tested** - Different variants for different lead types

### Example Output

```python
{
    "subject": "Sarah, Competitor A is getting 2.5x more ChatGPT referrals",
    "body": "Hello Sarah,\n\nI noticed that Competitor A Dermatology in New York...",
    "route": "central",
    "competitor_referenced": "Competitor A"
}
```

---

## 💬 Use Case 2: Handling Email Replies

### Flow Diagram

```
Lead Replies to Email
    ↓
Smartlead Webhook (POST /webhook/smartlead)
    ↓
Webhook Handler (webhook_handler.py)
    ↓
Orchestrator.handle_reply()
    ↓
SalesGPT.generate_reply()  ← YOU ARE HERE
    ↓
Intent Classification
    ↓
Response Generation
    ↓
Action Determination
    ↓
Send Reply via Smartlead
    ↓
Update HubSpot Pipeline
```

### Code Example

**File:** `main_agent.py`

```python
async def handle_reply(
    self,
    thread_id: str,
    sender_email: str,
    sender_name: str,
    email_body: str
):
    # 1. Get conversation history
    conversation_history = self.state.get_conversation_history(thread_id)
    
    # 2. Generate reply using SalesGPT
    reply_data = self.salesgpt.generate_reply(  # ← SalesGPT used here
        email_body=email_body,
        sender_name=sender_name,
        sender_email=sender_email,
        conversation_history=conversation_history,
        company_name=company_name
    )
    
    # 3. Get intent and response
    intent = reply_data["intent"]  # "interested", "objection", "curious", etc.
    reply_body = reply_data["body"]
    
    # 4. Handle based on intent
    if intent == "interested":
        # Add booking link
        booking_link = self.scheduler.generate_booking_link(...)
        reply_body += f"\n\nBook a call: {booking_link}"
    elif intent == "objection":
        # Add evidence
        evidence = self.visibility.get_audit(...)
        reply_body += f"\n\nHere's the data: {evidence}"
```

### What SalesGPT Does

**Method:** `SalesGPTWrapper.generate_reply()`

1. **Injects context** - Adds company info and evidence to conversation
2. **Adds user message** - Processes incoming email
3. **Determines conversation stage** - Introduction → Close
4. **Classifies intent** - interested, objection, curious, neutral, not_interested
5. **Generates reply** - Uses GPT to create contextual response
6. **Determines action** - send_booking_link, send_evidence, provide_info

**Key Features:**
- ✅ **Context-aware** - Uses full conversation history
- ✅ **Intent classification** - Understands what lead wants
- ✅ **Stage-aware** - Adapts to conversation progression
- ✅ **Evidence injection** - Can add GEMflush data when needed

### Intent Classification

SalesGPT classifies replies into 5 categories:

1. **"interested"** → Send booking link
2. **"objection"** → Provide evidence (GEMflush audit)
3. **"curious"** → Provide information
4. **"neutral"** → Engage with value
5. **"not_interested"** → Respectful exit

### Example Output

```python
{
    "body": "Thanks for your interest! I'd be happy to show you...",
    "intent": "interested",
    "action": "send_booking_link",
    "conversation_stage": "value_proposition"
}
```

---

## 🔧 Technical Implementation

### SalesGPTWrapper Class

**File:** `services/salesgpt/salesgpt_wrapper.py`

**Key Methods:**

1. **`generate_initial_email()`**
   - Generates cold emails with ELM routing
   - Incorporates competitive analysis
   - Follows A/B test variants

2. **`generate_reply()`**
   - Handles email replies
   - Classifies intent
   - Generates contextual responses

3. **`classify_intent()`**
   - Analyzes email content
   - Determines lead intent
   - Returns classification

4. **`get_conversation_context()`**
   - Retrieves conversation history
   - Maintains context across messages

### Integration Points

**1. Background Queue Builder**
```python
# workflows/background_queue_builder.py
email = self.ab_manager.generate_email_from_variant(
    variant=variant,
    salesgpt_wrapper=self.salesgpt,  # ← SalesGPT integration
    lead=lead_dict,
    evidence=evidence
)
```

**2. Webhook Handler**
```python
# webhook_handler.py → main_agent.py
reply_data = self.salesgpt.generate_reply(
    email_body=email_body,
    sender_name=sender_name,
    conversation_history=conversation_history
)
```

**3. Service Container**
```python
# salesgpt/container.py
self._salesgpt = SalesGPTWrapper(
    config_path=self.settings.salesgpt_config_path,
    model_name=self.settings.gpt_model,
    verbose=self.settings.salesgpt_verbose
)
```

---

## 📊 Conversation Stages

SalesGPT tracks conversation progression through 7 stages:

1. **Introduction** - Initial contact
2. **Qualification** - Understanding needs
3. **Value Proposition** - Presenting solution
4. **Objection Handling** - Addressing concerns
5. **Close** - Finalizing deal
6. **End** - Conversation complete

**How it's used:**
- SalesGPT determines current stage
- Adapts response style to stage
- Progresses conversation forward

---

## 🎯 ELM (Elaboration Likelihood Model) Integration

SalesGPT uses ELM to determine persuasion route:

### Central Route (High ELM Score)
- **When**: Lead has high elaboration score (75+)
- **Approach**: Evidence-heavy, logical, data-driven
- **Email style**: Detailed competitive analysis, numbers, facts

### Peripheral Route (Low ELM Score)
- **When**: Lead has low elaboration score (<75)
- **Approach**: Simple, social proof, emotional
- **Email style**: Short, simple, social cues

**How it works:**
```python
# Calculate ELM score
elaboration_score, persuasion_route = self._compute_elaboration_score(lead)

# Generate email based on route
email = self.salesgpt.generate_initial_email(
    route=persuasion_route,  # "central" or "peripheral"
    lead_name=lead.name,
    competitive_analysis=evidence,
    ...
)
```

---

## 🔄 Complete Flow Example

### Scenario: Lead replies "I'm interested, tell me more"

```
1. Smartlead receives reply
   ↓
2. Webhook fires → webhook_handler.py
   ↓
3. Orchestrator.handle_reply() called
   ↓
4. SalesGPT.generate_reply() called
   ├─ Classifies intent: "interested"
   ├─ Determines stage: "value_proposition"
   ├─ Generates reply: "Great! I'd be happy to show you..."
   └─ Action: "send_booking_link"
   ↓
5. Booking link added to reply
   ↓
6. Reply sent via Smartlead
   ↓
7. HubSpot pipeline updated: "engaged" → "booked"
   ↓
8. Database updated with reply tracking
```

---

## 📝 Configuration

### Agent Configuration

**File:** `examples/example_agent_setup.json`

```json
{
  "salesperson_name": "ASSCH Team",
  "salesperson_role": "Sales Representative",
  "company_name": "GEMflush",
  "company_business": "AI visibility optimization for medical practices",
  "conversation_purpose": "Book a call to discuss GEMflush visibility audit",
  "conversation_type": "call"
}
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...  # For GPT model
SALESGPT_CONFIG_PATH=examples/example_agent_setup.json

# Optional
GPT_MODEL=gpt-3.5-turbo-0613  # Model to use
SALESGPT_USE_TOOLS=true  # Enable/disable tools
SALESGPT_VERBOSE=false  # Enable verbose logging
```

---

## ✅ Summary

**SalesGPT is used for:**

1. **Generating initial emails** (outbound)
   - Personalized cold emails
   - ELM-compliant persuasion
   - Evidence-driven content
   - A/B test variants

2. **Handling replies** (inbound)
   - Intent classification
   - Contextual responses
   - Conversation stage tracking
   - Action determination

**Key Features:**
- ✅ Context-aware (uses conversation history)
- ✅ Intent classification (5 categories)
- ✅ ELM routing (central/peripheral)
- ✅ Evidence injection (GEMflush data)
- ✅ Stage-aware (7 conversation stages)

**Integration Points:**
- Background Queue Builder (email generation)
- Webhook Handler (reply processing)
- Service Container (initialization)

SalesGPT is the **AI engine** that makes emails intelligent, personalized, and contextually appropriate! 🚀

---

## 🔬 Advanced Usage Patterns

### Pattern 1: Custom Email Generation with Variants

**Scenario:** Generate email with specific A/B test variant

```python
from services.analytics.ab_test_manager import ABTestManager, EmailVariant, SubjectVariant, BodyStructure, EvidenceLevel, CTAVariant
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper

# Initialize
ab_manager = ABTestManager(state_manager)
salesgpt = SalesGPTWrapper()

# Create specific variant
variant = EmailVariant(
    subject_variant=SubjectVariant.COMPETITOR_MENTION,
    body_structure=BodyStructure.EVIDENCE_FIRST,
    evidence_level=EvidenceLevel.FULL,
    cta_variant=CTAVariant.DIRECT_BOOKING,
    personalization_level="high",
    email_length="medium"
)

# Generate email
email = ab_manager.generate_email_from_variant(
    variant=variant,
    salesgpt_wrapper=salesgpt,
    lead={
        "name": "Dr. Sarah Smith",
        "company_name": "Smith Dermatology",
        "location": "New York, NY",
        "specialty": "Dermatology"
    },
    evidence={
        "lead_score": 65,
        "competitor_score": 85,
        "gap_percentage": 20,
        "referral_multiplier": 2.5,
        "competitor_name": "Competitor A",
        "competitor_has_kg": True
    }
)
```

### Pattern 2: Reply Handling with Evidence Injection

**Scenario:** Handle objection by injecting GEMflush evidence

```python
# In main_agent.py handle_reply()
reply_data = self.salesgpt.generate_reply(
    email_body="This seems expensive, what's the ROI?",
    sender_name="Dr. Smith",
    sender_email="sarah@example.com",
    conversation_history=history,
    company_name="Smith Dermatology",
    evidence_data={
        "competitor_name": "Competitor A",
        "delta_score": -20,  # 20% less visible
        "referral_multiplier": 2.5
    }
)

# SalesGPT will automatically inject evidence into reply
# Reply will include: "Quick insight: Your clinic shows 20% less visibility..."
```

### Pattern 3: ELM Route Selection

**Scenario:** Generate email based on lead's elaboration score

```python
# Calculate ELM score
elaboration_score, persuasion_route = self._compute_elaboration_score(lead)

# Generate email with route-specific playbook
email = self.salesgpt.generate_initial_email(
    route=persuasion_route,  # "central" or "peripheral"
    lead_name=lead.name,
    company_name=lead.company_name,
    location=lead.location,
    specialty=lead.specialty,
    competitive_analysis=evidence,
    disclaimer_mode={
        "simulated_competitor_data": True,
        "simulated_kg_presence": True,
        "simulated_audit_data": True
    }
)

# Central route: Evidence-heavy, 200-250 words, detailed numbers
# Peripheral route: Simple, 100-150 words, heuristic cues
```

---

## 📚 Real-World Examples

### Example 1: High-Value Lead (Central Route)

**Lead Profile:**
- Name: Dr. Sarah Smith
- Company: Smith Dermatology
- Location: New York, NY
- Score: 18/20 (high value)
- ELM Score: 85 (central route)

**Generated Email:**
```
Subject: Sarah, Competitor A Dermatology is getting 2.5x more ChatGPT referrals

Body:
Hello Sarah,

I noticed that Competitor A Dermatology in New York is currently outperforming 
Smith Dermatology in terms of AI visibility and patient referrals from ChatGPT. 
Based on our simulated preview audit, they have approximately 2.5x more visibility 
in GPT-based patient searches.

The mechanism: Competitor A has a Wikidata knowledge graph presence, which 
significantly boosts their AI search visibility. Your clinic shows an estimated 
20% visibility gap compared to them.

I can show you the full 1-page audit report on a 15-minute call. Would you be 
open to a quick review?

Best regards,
ASSCH Team

Note: This competitive analysis is based on a simulated preview audit. Full 
verification requires your participation.
```

**Characteristics:**
- ✅ Evidence-heavy (numbers, percentages, multipliers)
- ✅ Explains mechanism (Wikidata KG)
- ✅ Specific CTA (15-minute call)
- ✅ Includes disclaimers
- ✅ 200+ words

### Example 2: Low-Value Lead (Peripheral Route)

**Lead Profile:**
- Name: Dr. John Doe
- Company: Doe Clinic
- Location: Boston, MA
- Score: 12/20 (medium value)
- ELM Score: 45 (peripheral route)

**Generated Email:**
```
Subject: Quick question about Doe Clinic's visibility

Body:
Hi John,

Quick question - have you noticed how AI search is changing how patients find 
medical practices?

We help dermatology clinics like yours improve their AI visibility. Similar 
practices in Boston have seen great results.

Would you be open to a quick 15-minute walkthrough?

Best,
ASSCH Team
```

**Characteristics:**
- ✅ Simple and short (100-150 words)
- ✅ Heuristic cues (social proof, authority)
- ✅ Single clear CTA
- ✅ Conversational tone
- ✅ No detailed numbers

### Example 3: Reply Handling - Interested Lead

**Incoming Reply:**
```
"Hi, I'm interested in learning more. Can we schedule a call?"
```

**SalesGPT Processing:**
1. **Intent Classification:** "interested"
2. **Conversation Stage:** "value_proposition" → "close"
3. **Generated Reply:**
```
Great! I'd be happy to show you the full audit and discuss how we can help 
Smith Dermatology improve its AI visibility.

Book a 15-minute call here: https://cal.com/assch/smith-dermatology

Looking forward to speaking with you!
```

4. **Action:** `send_booking_link`
5. **HubSpot Update:** Pipeline stage → "booked"

### Example 4: Reply Handling - Objection

**Incoming Reply:**
```
"This seems expensive. What's the ROI? We're on a tight budget."
```

**SalesGPT Processing:**
1. **Intent Classification:** "objection"
2. **Conversation Stage:** "objection_handling"
3. **Evidence Injection:** GEMflush audit data
4. **Generated Reply:**
```
I understand budget concerns. Let me show you the numbers:

Quick insight: Your clinic shows an estimated 20% less visibility than 
Competitor A in GPT-based patient searches. They're getting approximately 
2.5x more referrals from ChatGPT.

If you're losing even 2-3 patients per month to competitors due to visibility 
gaps, that's $6,000-$9,000 in monthly revenue. Our solution typically pays 
for itself within the first month.

I can show you the full audit with specific numbers for your practice. Would 
you be open to a quick 15-minute review?
```

5. **Action:** `send_evidence`
6. **HubSpot Update:** Pipeline stage → "engaged"

---

## 🛠️ Troubleshooting

### Issue 1: SalesGPT Not Generating Emails

**Symptoms:**
- `generate_initial_email()` returns empty body
- Error: "No response from SalesGPT"

**Solutions:**
1. **Check OpenAI API Key:**
   ```bash
   echo $OPENAI_API_KEY  # Should show your key
   ```

2. **Check Model Availability:**
   ```python
   # Verify model name is correct
   GPT_MODEL=gpt-3.5-turbo-0613  # or gpt-4
   ```

3. **Check Conversation History:**
   ```python
   # SalesGPT needs conversation history initialized
   sales_api.sales_agent.seed_agent()  # Must be called first
   ```

### Issue 2: Emails Not Personalized

**Symptoms:**
- Generic emails without lead-specific data
- Missing competitor names or evidence

**Solutions:**
1. **Verify Evidence Data:**
   ```python
   # Check evidence is passed correctly
   print(competitive_analysis)  # Should have competitor_name, gap_percentage, etc.
   ```

2. **Check Lead Data:**
   ```python
   # Ensure lead dict has all required fields
   lead = {
       "name": "Dr. Smith",  # Required
       "company_name": "Smith Clinic",  # Required
       "location": "New York, NY",  # Required
       "specialty": "Dermatology"  # Required
   }
   ```

### Issue 3: Intent Classification Not Working

**Symptoms:**
- All replies classified as "neutral"
- Wrong intent detected

**Solutions:**
1. **Improve Classification Logic:**
   ```python
   # Current: Keyword-based (simple)
   # Future: LLM-based classification (more accurate)
   
   # For now, check keywords are being detected
   body_lower = email_body.lower()
   if "interested" in body_lower or "yes" in body_lower:
       return "interested"
   ```

2. **Add Custom Keywords:**
   ```python
   # Add domain-specific keywords
   interested_keywords = ["yes", "interested", "tell me more", "schedule", "book", "call", "sounds good"]
   objection_keywords = ["expensive", "cost", "price", "budget", "can't afford", "too much", "ROI"]
   ```

### Issue 4: Conversation History Lost

**Symptoms:**
- SalesGPT doesn't remember previous messages
- Replies don't reference earlier conversation

**Solutions:**
1. **Check State Manager:**
   ```python
   # Verify conversation history is stored
   history = state_manager.get_conversation_history(thread_id)
   print(history)  # Should show previous messages
   ```

2. **Ensure History is Passed:**
   ```python
   # Always pass conversation history
   reply_data = salesgpt.generate_reply(
       email_body=email_body,
       conversation_history=history,  # ← Must include this
       ...
   )
   ```

---

## 💡 Best Practices

### 1. **Always Seed Agent Before Use**

```python
# ✅ Good
sales_api.sales_agent.seed_agent()  # Initialize conversation
email = salesgpt.generate_initial_email(...)

# ❌ Bad
email = salesgpt.generate_initial_email(...)  # May fail without seeding
```

### 2. **Pass Complete Context**

```python
# ✅ Good
email = salesgpt.generate_initial_email(
    route=persuasion_route,
    lead_name=lead.name,
    company_name=lead.company_name,
    location=lead.location,
    specialty=lead.specialty,
    competitive_analysis=evidence,  # Complete evidence
    disclaimer_mode=disclaimer_mode
)

# ❌ Bad
email = salesgpt.generate_initial_email(
    lead_name=lead.name  # Missing context
)
```

### 3. **Use ELM Routing Appropriately**

```python
# ✅ Good - Match route to lead characteristics
if elaboration_score >= 75:
    route = "central"  # Evidence-heavy for high-engagement leads
else:
    route = "peripheral"  # Simple for low-engagement leads

# ❌ Bad - Same route for all leads
route = "central"  # May overwhelm low-engagement leads
```

### 4. **Handle Errors Gracefully**

```python
# ✅ Good
try:
    email = salesgpt.generate_initial_email(...)
except Exception as e:
    logger.error(f"Email generation failed: {e}")
    # Fallback to simple email
    email = {"subject": "Quick question", "body": "Hi..."}

# ❌ Bad
email = salesgpt.generate_initial_email(...)  # May crash if fails
```

### 5. **Monitor Conversation Stages**

```python
# ✅ Good - Track stage progression
stage = sales_api.sales_agent.current_conversation_stage
if stage == "close":
    # Add booking link
    reply += booking_link

# ❌ Bad - Same response for all stages
reply = salesgpt.generate_reply(...)  # Doesn't adapt to stage
```

---

## ⚡ Performance Considerations

### 1. **API Rate Limits**

**OpenAI Rate Limits:**
- GPT-3.5-turbo: 3,500 requests/minute
- GPT-4: 500 requests/minute

**Best Practice:**
- Batch email generation when possible
- Use async processing for replies
- Implement retry logic with exponential backoff

### 2. **Token Usage**

**Cost Optimization:**
- Use GPT-3.5-turbo for most emails (cheaper)
- Use GPT-4 only for complex replies
- Limit conversation history length (keep last 10 messages)

**Example:**
```python
# Limit conversation history
history = conversation_history[-10:]  # Last 10 messages only
reply = salesgpt.generate_reply(..., conversation_history=history)
```

### 3. **Caching**

**Cache Generated Emails:**
```python
# Cache emails for same lead + variant combination
cache_key = f"{lead.email}:{variant_code}"
if cache_key in email_cache:
    return email_cache[cache_key]
else:
    email = generate_email(...)
    email_cache[cache_key] = email
    return email
```

---

## 🎓 Learning Resources

### Understanding SalesGPT Architecture

1. **Core Components:**
   - `SalesGPT` (agents.py) - Main agent class
   - `SalesGPTAPI` (salesgptapi.py) - API wrapper
   - `SalesGPTWrapper` (salesgpt_wrapper.py) - Email-specific wrapper

2. **Conversation Management:**
   - Conversation history stored in database
   - Stage tracking (7 stages)
   - Context injection for personalization

3. **ELM Integration:**
   - Playbook: `examples/elm_email_playbook.json`
   - Route selection based on elaboration score
   - Persuasion principles applied per route

### Customization Points

1. **Modify Intent Classification:**
   - File: `services/salesgpt/salesgpt_wrapper.py`
   - Method: `classify_intent()`
   - Add domain-specific keywords

2. **Customize Email Generation:**
   - File: `services/salesgpt/salesgpt_wrapper.py`
   - Method: `generate_initial_email()`
   - Modify prompt templates

3. **Adjust ELM Playbook:**
   - File: `examples/elm_email_playbook.json`
   - Modify persuasion principles
   - Update structure rules

---

## 📊 Monitoring & Analytics

### Track SalesGPT Performance

```python
# Log email generation metrics
metrics = {
    "generation_time": time_taken,
    "token_count": tokens_used,
    "route": persuasion_route,
    "variant": variant_code,
    "success": True/False
}

# Track reply handling metrics
reply_metrics = {
    "intent": classified_intent,
    "stage": conversation_stage,
    "response_time": time_taken,
    "action_taken": action
}
```

### Dashboard Integration

SalesGPT metrics are automatically tracked in:
- **Email Analytics Tab** - Reply rates by intent
- **Optimization Tab** - AI recommendations
- **Database** - Conversation history and stages

---

## 🚀 Next Steps

1. **Test Email Generation:**
   ```bash
   python3 scripts/start_queue_builder.py
   ```

2. **Test Reply Handling:**
   - Send test email
   - Reply to trigger webhook
   - Check generated response

3. **Monitor Performance:**
   - Check dashboard analytics
   - Review intent classification accuracy
   - Optimize based on results

4. **Customize for Your Use Case:**
   - Modify ELM playbook
   - Adjust intent classification
   - Add domain-specific logic

---

**SalesGPT is the intelligent core that makes your email automation smart, personalized, and effective!** 🎯

