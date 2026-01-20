# FireGEO ↔ SalesGPT Event Bridge - Implementation Complete

## Summary

The event bridge architecture has been fully implemented. FireGEO (hosted on Vercel) now acts as the public webhook receiver for Stripe and Smartlead, writing normalized events into a dedicated Supabase `marketing_events` table. SalesGPT polls this table to update its local lead database with conversion signals.

## What Was Implemented

### 1. Supabase Database Schema ✅

**Migration:** `/Users/JJR/firegeo/migrations/009_add_marketing_events.sql`
- Created `marketing_events` table with all required fields
- Added indexes for efficient querying (`processed_at`, `event_type + occurred_at`, `email`)
- Schema added to Drizzle ORM in `/Users/JJR/firegeo/lib/db/schema.ts`

### 2. FireGEO Webhook Routes ✅

**Stripe Webhook:** `/Users/JJR/firegeo/app/api/stripe/webhook/route.ts`
- Enhanced existing webhook to handle `invoice.paid` events
- Detects Pro price ID (`price_1SobzBQg9yJEawqIFl1VSm5u` or from env)
- Extracts customer email and emits `paid_pro` events to `marketing_events`

**Smartlead Webhook:** `/Users/JJR/firegeo/app/api/webhook/smartlead/route.ts`
- New route to receive Smartlead email reply webhooks
- Optional HMAC signature verification (if `SMARTLEAD_WEBHOOK_SECRET` is set)
- Emits `email_reply` events to `marketing_events`

### 3. Signup & Activation Events ✅

**Signup Event API:** `/Users/JJR/firegeo/app/api/marketing/signup-event/route.ts`
- API route to emit `signup_free` events
- Extracts UTM parameters from URL/cookies for attribution

**Register Page:** `/Users/JJR/firegeo/app/register/page.tsx`
- Updated to call signup event API after successful registration
- Captures UTM parameters for attribution

**Activation Event:** `/Users/JJR/firegeo/app/api/brand-monitor/analyses/route.ts`
- Detects first brand analysis creation
- Emits `activated` event when user creates their first analysis

### 4. Marketing Events Service ✅

**Utility Service:** `/Users/JJR/firegeo/lib/marketing/events.ts`
- `insertMarketingEvent()` - Centralized function to insert events
- `extractUTMParams()` - Extracts UTM parameters from URLs/cookies
- Handles all event types: `signup_free`, `activated`, `paid_pro`, `email_reply`

### 5. SalesGPT Event Ingestor ✅

**Ingestor:** `/Users/JJR/SalesGPT/services/attribution/marketing_events_ingestor.py`
- Reads unprocessed events from `marketing_events` table (`processed_at IS NULL`)
- Updates SalesGPT lead DB by email match:
  - `signup_free` → sets `free_signup_at`, updates `market`, `persona`, `variant_code`
  - `paid_pro` → sets `paid_pro_at`, `paid_pro_price_id`, `paid_pro_invoice_id`, `paid_pro_amount`
  - `email_reply` → sets `reply_received_at`, optionally `reply_intent`
- Marks events as processed (`processed_at = NOW()`) for idempotency

**Sync Script:** `/Users/JJR/SalesGPT/scripts/sync_marketing_events.py`
- Command-line script to run the ingestor
- Usage: `python3 scripts/sync_marketing_events.py --limit 1000`

## Operational Setup Required

### 1. Run Database Migration

Apply the marketing_events table migration to Supabase:

```bash
# Option 1: Using psql
psql $DATABASE_URL -f /Users/JJR/firegeo/migrations/009_add_marketing_events.sql

# Option 2: Using Supabase SQL Editor
# Copy contents of 009_add_marketing_events.sql and run in Supabase dashboard
```

### 2. Configure Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-firegeo-domain.vercel.app/api/stripe/webhook`
3. Select events:
   - `invoice.paid` (required for paid_pro events)
   - `checkout.session.completed` (already handled)
   - `customer.subscription.updated` (already handled)
   - `customer.subscription.deleted` (already handled)
4. Copy webhook signing secret to FireGEO environment:
   - `STRIPE_WEBHOOK_SECRET_LIVE` (for production)
   - `STRIPE_WEBHOOK_SECRET` (for test mode)

### 3. Configure Smartlead Webhook (When Ready)

1. Go to Smartlead Dashboard → Settings → Webhooks
2. Add endpoint: `https://your-firegeo-domain.vercel.app/api/webhook/smartlead`
3. Select events:
   - `email_replied` (or equivalent)
4. (Optional) Set webhook secret in FireGEO environment:
   - `SMARTLEAD_WEBHOOK_SECRET`

### 4. Set Up SalesGPT Poller

Run the sync script periodically (e.g., every 1-5 minutes via cron):

```bash
# Add to crontab (runs every 5 minutes)
*/5 * * * * cd /Users/JJR/SalesGPT && python3 scripts/sync_marketing_events.py --limit 1000
```

Or run manually:
```bash
cd /Users/JJR/SalesGPT
python3 scripts/sync_marketing_events.py --limit 1000
```

### 5. Environment Variables

**FireGEO (.env.local):**
```bash
DATABASE_URL=postgresql://...  # Supabase connection string
STRIPE_WEBHOOK_SECRET_LIVE=whsec_...  # Stripe webhook secret
STRIPE_PRO_PRICE_ID_LIVE=price_1SobzBQg9yJEawqIFl1VSm5u  # Pro price ID
SMARTLEAD_WEBHOOK_SECRET=...  # Optional, for Smartlead signature verification
```

**SalesGPT (.env.local):**
```bash
SUPABASE_DATABASE_URL=postgresql://...  # Supabase connection string (pooler URL)
SALESGPT_DATABASE_URL=sqlite:///./salesgpt.db  # SalesGPT local DB
```

## Event Flow

```
1. User signs up on FireGEO
   → POST /api/marketing/signup-event
   → INSERT marketing_events (event_type='signup_free')

2. User creates first brand analysis
   → POST /api/brand-monitor/analyses
   → INSERT marketing_events (event_type='activated')

3. User pays for Pro subscription
   → Stripe webhook → POST /api/stripe/webhook
   → INSERT marketing_events (event_type='paid_pro')

4. Lead replies to cold email
   → Smartlead webhook → POST /api/webhook/smartlead
   → INSERT marketing_events (event_type='email_reply')

5. SalesGPT poller runs
   → scripts/sync_marketing_events.py
   → SELECT * FROM marketing_events WHERE processed_at IS NULL
   → UPDATE leads table (free_signup_at, paid_pro_at, etc.)
   → UPDATE marketing_events SET processed_at = NOW()
```

## Testing

### Test Signup Event
1. Register a new user on FireGEO
2. Check `marketing_events` table for `signup_free` event
3. Run SalesGPT sync script
4. Verify lead in SalesGPT DB has `free_signup_at` set

### Test Activation Event
1. Create first brand analysis for a new user
2. Check `marketing_events` table for `activated` event

### Test Paid Pro Event
1. Complete a Pro subscription checkout
2. Check Stripe webhook logs
3. Check `marketing_events` table for `paid_pro` event
4. Run SalesGPT sync script
5. Verify lead has `paid_pro_at`, `paid_pro_price_id`, etc.

### Test Email Reply Event
1. Configure Smartlead webhook (when ready)
2. Send test reply event
3. Check `marketing_events` table for `email_reply` event
4. Run SalesGPT sync script
5. Verify lead has `reply_received_at` set

## Next Steps

1. ✅ Deploy FireGEO routes to Vercel
2. ✅ Run database migration
3. ✅ Configure Stripe webhook URL
4. ⏳ Configure Smartlead webhook URL (when ready to send emails)
5. ⏳ Set up cron job for SalesGPT poller
6. ⏳ Test end-to-end flow
7. ⏳ Monitor event processing in production

## Files Created/Modified

### FireGEO
- `migrations/009_add_marketing_events.sql` (new)
- `lib/db/schema.ts` (added marketingEvents table)
- `lib/marketing/events.ts` (new)
- `app/api/stripe/webhook/route.ts` (enhanced)
- `app/api/webhook/smartlead/route.ts` (new)
- `app/api/marketing/signup-event/route.ts` (new)
- `app/register/page.tsx` (added signup event emission)
- `app/api/brand-monitor/analyses/route.ts` (added activation event)

### SalesGPT
- `services/attribution/marketing_events_ingestor.py` (new)
- `scripts/sync_marketing_events.py` (new)

## Notes

- All events are idempotent (can be processed multiple times safely)
- Events are marked as processed to prevent duplicate processing
- Email matching is case-insensitive
- UTM parameters are captured for attribution
- The system gracefully handles leads not found (organic signups)

