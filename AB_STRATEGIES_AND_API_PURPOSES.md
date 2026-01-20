# 📊 A/B Strategies Recording & API Integration Purposes

## Part 1: How A/B Strategies Are Recorded and Documented

### 🗄️ Database Storage

A/B testing strategies are recorded in the **SQLite database** (can be upgraded to PostgreSQL) with the following structure:

#### Email Variant Storage

**Table**: `leads`  
**Columns**:
- `variant_code` (String, indexed) - Stores the complete variant identifier
- `persuasion_route` (String) - "central" or "peripheral" 
- `elaboration_score` (Float) - ELM score (0-100)
- `email_subject` (Text) - Generated subject line
- `email_body` (Text) - Generated email body
- `email_generated_at` (DateTime) - When variant was assigned
- `email_sent_at` (DateTime) - When email was sent
- `reply_received_at` (DateTime) - When reply was received
- `reply_intent` (String) - "interested", "objection", "curious", etc.

**Variant Code Format**:
```
{subject}-{body}-{evidence}-{cta}-{personalization}-{length}
```

**Example**: `competitor-evidence-full-direct-high-medium`

This means:
- **Subject**: Competitor mention
- **Body**: Evidence-first structure
- **Evidence**: Full competitive analysis
- **CTA**: Direct booking request
- **Personalization**: High (full name, company, location)
- **Length**: Medium (100-150 words)

#### Apollo Configuration Storage

**Table**: `leads`  
**Columns**:
- `apollo_config_code` (String, indexed) - Stores the Apollo search config identifier

**Config Code Format**:
```
{geography_strategy}-{employee_range}-{title_strategy}-{website_requirement}
```

**Example**: `city-small-decision-web`

This means:
- **Geography**: City-specific search
- **Employee Range**: Small (5-15 employees)
- **Title Strategy**: Decision makers (CEO, Owner, Director, etc.)
- **Website**: Required (has_website = true)

### 📝 Code-Level Documentation

#### 1. Variant Assignment Logic

**File**: `services/analytics/ab_test_manager.py`

```python
class EmailVariant:
    """Email variant configuration."""
    subject_variant: SubjectVariant      # competitor, question, value, etc.
    body_structure: BodyStructure        # evidence, problem, story, question
    evidence_level: EvidenceLevel        # full, minimal, none
    cta_variant: CTAVariant             # direct, soft, value, two_step
    personalization_level: str           # high, medium, low
    email_length: str                    # short, medium, long
    
    def to_code(self) -> str:
        """Generate variant code for storage."""
        return f"{self.subject_variant.value}-{self.body_structure.value}-..."
```

#### 2. Apollo Config Logic

**File**: `services/analytics/apollo_ab_manager.py`

```python
@dataclass
class ApolloSearchConfig:
    """Apollo search configuration for A/B testing."""
    geography_strategy: GeographyStrategy    # city, metro, state, multi
    geography_value: str                     # "New York, NY"
    employee_range: EmployeeRangeStrategy     # micro, small, medium, large
    title_strategy: TitleStrategy            # c_level, owners, decision, broad
    require_website: bool                     # True/False
    specialty: str                           # "Dermatology"
    
    def to_code(self) -> str:
        """Generate config code for storage."""
        website_code = "web" if self.require_website else "noweb"
        return f"{self.geography_strategy.value}-{self.employee_range.value}-..."
```

### 📊 Analytics & Tracking

#### Performance Metrics Storage

**File**: `services/analytics/metrics_tracker.py`

Metrics are calculated on-demand from the database:

```python
def get_variant_performance(self, variant_code: str, days_back: int = 30):
    """
    Calculate performance metrics for a variant.
    
    Returns:
        {
            "variant_code": "competitor-evidence-full-direct-high-medium",
            "sent_count": 150,
            "reply_rate": 12.5,
            "positive_reply_rate": 8.3,
            "booking_rate": 5.0,
            "close_rate": 2.5
        }
    """
```

#### Multi-Armed Bandit Algorithm

**File**: `services/analytics/apollo_ab_manager.py`

Uses **Upper Confidence Bound (UCB)** algorithm to optimize Apollo config selection:

```python
def select_config(self) -> ApolloSearchConfig:
    """
    Select Apollo config using multi-armed bandit (UCB).
    
    Balances exploration (trying new configs) vs exploitation (using best configs).
    """
```

### 📋 Documentation Files

1. **`docs/AB_TESTING_GUIDE.md`** - Complete guide to A/B testing system
2. **`DASHBOARD_UI_VERIFICATION.md`** - UI verification including A/B test views
3. **Database Schema** - `salesgpt/models/database.py` - Full schema documentation

### 🔍 Querying A/B Test Data

#### SQL Queries

```sql
-- Get all leads by variant
SELECT email, variant_code, reply_rate, booking_rate 
FROM leads 
WHERE variant_code = 'competitor-evidence-full-direct-high-medium';

-- Get all leads by Apollo config
SELECT email, apollo_config_code, status 
FROM leads 
WHERE apollo_config_code = 'city-small-decision-web';

-- Performance by variant
SELECT 
    variant_code,
    COUNT(*) as sent_count,
    COUNT(CASE WHEN reply_received_at IS NOT NULL THEN 1 END) as replies,
    COUNT(CASE WHEN booked_at IS NOT NULL THEN 1 END) as bookings
FROM leads
WHERE email_sent_at IS NOT NULL
GROUP BY variant_code;
```

#### Python API

```python
# Get variant performance
metrics = metrics_tracker.get_variant_performance("competitor-evidence-full-direct-high-medium", days_back=30)

# Get Apollo config performance
apollo_perf = apollo_ab_manager.get_config_performance("city-small-decision-web", days_back=30)

# Get all leads by variant
leads = state_manager.get_leads_by_variant("competitor-evidence-full-direct-high-medium")
```

---

## Part 2: Purpose of Each API Integration

### 🔍 **1. Apollo.io** - Lead Sourcing & Enrichment

**Purpose**: Find and qualify potential customers

**What It Does**:
- ✅ **Searches for leads** by geography, specialty, employee count, title
- ✅ **Enriches lead data** with contact info, LinkedIn profiles, company details
- ✅ **Scores leads** based on relevance (website presence, title, employee count)
- ✅ **Provides metadata** (person_id, organization_id, phone, location, etc.)

**Key Methods**:
- `search_leads()` - Main search function (may consume credits depending on plan)
- `enrich_person()` - Enrich single person (1 credit per match)
- `enrich_organization()` - Enrich single organization (1 credit per enrichment)

**Credit Usage**:
- Search: Varies by plan (some plans include free searches)
- Enrichment: **1 credit per person/organization** (only used for high-value leads)

**Integration Point**: `services/apollo/apollo_agent.py`

**Data Flow**:
```
Apollo API → Lead Data → Scoring Algorithm → Qualified Leads → Database
```

---

### 📧 **2. Smartlead.ai** - Email Delivery Platform

**Purpose**: Actually send emails and manage email infrastructure

**What It Does**:
- ✅ **Sends emails** via SMTP (actual email delivery)
- ✅ **Inbox warm-up** - Ensures emails don't go to spam
- ✅ **Domain rotation** - Uses multiple sending domains to avoid spam filters
- ✅ **Email sequences** - Automated follow-ups (initial + 2 follow-ups)
- ✅ **Reply handling** - Webhooks for incoming replies
- ✅ **Delivery tracking** - Open rates, reply rates, bounce rates
- ✅ **Bounce/spam management** - Handles delivery issues

**Key Methods**:
- `create_campaign()` - Create email campaign
- `add_sequence()` - Add email sequence to campaign
- `add_leads_to_campaign()` - Add leads to campaign for sending

**What It Does NOT Do**:
- ❌ **NOT a CRM** - Doesn't manage contacts or deals
- ❌ **NOT for review** - Doesn't provide email review interface
- ❌ **NOT for analytics** - Basic tracking only

**Integration Point**: `services/outbound/smartlead_agent.py`

**Data Flow**:
```
Email Content → Smartlead Campaign → SMTP Delivery → Webhook (on reply) → SalesGPT
```

**Why It's Needed**: HubSpot cannot send emails. Smartlead provides the actual email delivery infrastructure.

---

### 🤖 **3. OpenAI / SalesGPT** - AI Email Generation & Reply Handling

**Purpose**: Generate intelligent, personalized emails and handle replies

**What It Does**:
- ✅ **Generates email content** - AI-powered personalized emails
- ✅ **Analyzes replies** - Determines intent (interested, objection, curious)
- ✅ **Generates responses** - Context-aware replies based on conversation history
- ✅ **Handles objections** - Provides evidence-based responses
- ✅ **Provides booking links** - For interested leads
- ✅ **ELM routing** - Central vs peripheral persuasion routes
- ✅ **Evidence injection** - Injects GEMflush audit data into emails

**Key Methods**:
- `generate_email()` - Generate personalized email with A/B variant
- `handle_reply()` - Analyze reply and generate response
- `classify_intent()` - Determine lead intent from reply

**Integration Point**: `services/salesgpt/salesgpt_wrapper.py`

**Data Flow**:
```
Lead Data + Evidence → SalesGPT → Email Content → Smartlead
Reply → SalesGPT → Intent Analysis → Response Generation → Smartlead
```

**Why It's Needed**: Provides agentic AI that HubSpot cannot - sophisticated email generation, intent analysis, and contextual responses.

---

### 🏢 **4. HubSpot** - CRM & Contact Management

**Purpose**: Manage contacts, track deals, and provide review interface

**What It Does**:
- ✅ **Stores contacts** - All leads stored as HubSpot contacts
- ✅ **Tracks pipeline stages** - Idle → Engaged → Booked → Closed
- ✅ **Manages deals** - Creates deals associated with contacts
- ✅ **Stores email content** - Email subject/body stored as custom properties
- ✅ **Provides review UI** - Review emails in HubSpot interface
- ✅ **Team collaboration** - Share contacts and deals with team
- ✅ **Sales reporting** - Track performance and pipeline health

**Key Methods**:
- `create_contact()` - Create new contact with email content
- `update_pipeline_stage()` - Update deal stage
- `create_deal()` - Create deal associated with contact
- `update_contact_properties()` - Update custom properties (email_subject, email_body, etc.)

**What It Does NOT Do**:
- ❌ **CANNOT send emails** - Not an email delivery platform
- ❌ **No inbox warm-up** - Doesn't handle email delivery infrastructure
- ❌ **No domain rotation** - Doesn't manage sending domains

**Integration Point**: `services/crm/hubspot_agent.py`

**Data Flow**:
```
Lead Data + Email Content → HubSpot Contact → Review in UI → Approve → Smartlead
Reply → HubSpot Pipeline Update (engaged → booked)
```

**Why It's Needed**: Provides CRM functionality that Smartlead cannot - contact management, deal tracking, team collaboration.

---

### 🔍 **5. GEMflush** - Visibility Audit & Evidence

**Purpose**: Provide competitive analysis data for email personalization

**What It Does**:
- ✅ **Visibility audits** - Analyzes clinic's online visibility
- ✅ **Competitor comparison** - Compares clinic to competitors
- ✅ **Gap analysis** - Identifies visibility gaps (e.g., "You're 40% less visible than Competitor X")
- ✅ **Evidence generation** - Provides data for email personalization

**Key Methods**:
- `get_audit()` - Get visibility audit for clinic
- `compare_competitor()` - Compare clinic to competitor

**Integration Point**: `services/visibility/gemflush_agent.py`

**Data Flow**:
```
Clinic Website → GEMflush API → Audit Data → Evidence → Email Content
```

**Why It's Needed**: Provides evidence-based personalization that makes emails more compelling and persuasive.

**Note**: Currently supports both real API and LLM-based simulation for testing.

---

### 📅 **6. Cal.com** - Booking & Scheduling

**Purpose**: Generate booking links for interested leads

**What It Does**:
- ✅ **Booking links** - Generates personalized booking URLs
- ✅ **Lead tracking** - Tracks which lead booked via URL parameters
- ✅ **Calendar integration** - Integrates with calendar for scheduling

**Integration Point**: `main_agent.py` (uses `CAL_BOOKING_LINK` env var)

**Data Flow**:
```
Interested Lead → SalesGPT → Booking Link → Lead Clicks → Calendar Booking
```

**Why It's Needed**: Automates the booking process when leads express interest.

---

## 🔄 How They Work Together

### Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    A.S.S.C.H. Assembly                         │
│     Apollo → Smartlead → SalesGPT → Cal.com → HubSpot          │
└─────────────────────────────────────────────────────────────────┘

1. Apollo
   ↓ Sources 20-50 leads
   ↓ Enriches with contact data
   ↓ Scores by relevance
   
2. Background Queue Builder
   ↓ Generates personalized emails (SalesGPT)
   ↓ Assigns A/B variants
   ↓ Creates HubSpot contacts (with email content)
   ↓ Stores in database (with variant_code, apollo_config_code)
   
3. HubSpot UI
   ↓ Review emails
   ↓ See lead scores, evidence, A/B test info
   ↓ Approve emails to send
   
4. Smartlead
   ↓ Actually SENDS emails (SMTP)
   ↓ Handles inbox warm-up
   ↓ Manages domain rotation
   ↓ Tracks delivery, opens, replies
   ↓ Sends webhooks when replies arrive
   
5. SalesGPT (via webhook)
   ↓ Processes replies
   ↓ Analyzes intent
   ↓ Generates intelligent responses
   ↓ Injects GEMflush evidence (if needed)
   ↓ Provides booking links (if interested)
   
6. HubSpot
   ↓ Updates pipeline stages (idle → engaged → booked)
   ↓ Tracks conversation history
   ↓ Manages deals
   
7. Cal.com
   ↓ Generates booking links
   ↓ Tracks bookings
```

---

## 📊 A/B Testing Integration

### How A/B Tests Are Recorded

1. **Email Variant Assignment**:
   - Lead email → Consistent hash → Variant assignment
   - Variant code stored in `variant_code` column
   - Email content generated based on variant
   - Content stored in `email_subject` and `email_body` columns

2. **Apollo Config Assignment**:
   - Multi-armed bandit (UCB) selects config
   - Config code stored in `apollo_config_code` column
   - Search performed with selected config

3. **Performance Tracking**:
   - Metrics calculated from database on-demand
   - Reply rates, booking rates, close rates per variant/config
   - Dashboard displays performance analytics

### Querying A/B Test Results

```python
# Get all leads with variant "competitor-evidence-full-direct-high-medium"
leads = state_manager.get_leads_by_variant("competitor-evidence-full-direct-high-medium")

# Get performance metrics
metrics = metrics_tracker.get_variant_performance("competitor-evidence-full-direct-high-medium", days_back=30)

# Get Apollo config performance
apollo_perf = apollo_ab_manager.get_config_performance("city-small-decision-web", days_back=30)
```

---

## 📝 Summary

### A/B Strategy Recording:
- ✅ **Database**: SQLite/PostgreSQL with indexed columns
- ✅ **Variant Codes**: Structured format for easy querying
- ✅ **Config Codes**: Structured format for Apollo configs
- ✅ **Analytics**: On-demand performance calculation
- ✅ **Documentation**: Code-level and guide documentation

### API Integration Purposes:
- **Apollo**: Lead sourcing and enrichment
- **Smartlead**: Email delivery infrastructure
- **SalesGPT**: AI email generation and reply handling
- **HubSpot**: CRM and contact management
- **GEMflush**: Evidence and competitive analysis
- **Cal.com**: Booking and scheduling

**All APIs work together** to create a complete sales automation pipeline that sources leads, generates personalized emails, sends them, handles replies, and tracks everything in a CRM.



