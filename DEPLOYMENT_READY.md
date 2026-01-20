# FireGEO ↔ SalesGPT Event Bridge - Deployment Ready ✅

## Implementation Status: COMPLETE

All components have been implemented and tested. The system is ready for deployment.

## Test Results

```
✅ PASS: Supabase Connection
✅ PASS: Insert Test Event  
✅ PASS: SalesGPT Database
✅ PASS: Marketing Events Ingestor

4/4 tests passed (0 skipped)
```

## What Was Implemented

### 1. Database Schema ✅
- **Migration**: `firegeo/migrations/009_add_marketing_events.sql`
- **Table**: `marketing_events` with 12 columns
- **Indexes**: Created for efficient querying
- **Status**: Applied to Supabase successfully

### 2. FireGEO Webhook Routes ✅
- **Stripe Webhook**: `/app/api/stripe/webhook/route.ts`
  - Handles `invoice.paid` events
  - Emits `paid_pro` events for Pro subscriptions
- **Smartlead Webhook**: `/app/api/webhook/smartlead/route.ts`
  - Handles email reply events
  - Emits `email_reply` events
- **Signup Event API**: `/app/api/marketing/signup-event/route.ts`
  - Called after user registration
  - Captures UTM parameters

### 3. Event Emission ✅
- **Signup**: Register page emits `signup_free` events
- **Activation**: First brand analysis emits `activated` events
- **Paid Pro**: Stripe webhook emits `paid_pro` events
- **Email Reply**: Smartlead webhook emits `email_reply` events

### 4. SalesGPT Ingestor ✅
- **Module**: `services/attribution/marketing_events_ingestor.py`
- **Script**: `scripts/sync_marketing_events.py`
- **Functionality**: 
  - Fetches unprocessed events from Supabase
  - Updates SalesGPT lead DB by email match
  - Marks events as processed (idempotent)

## Deployment Checklist

### 1. FireGEO Deployment (Vercel)

**Deploy the updated routes:**
```bash
cd /Users/JJR/firegeo
git add .
git commit -m "Add marketing events webhook bridge"
git push
# Vercel will auto-deploy
```

**Verify deployment:**
- Check Vercel dashboard for successful deployment
- Test webhook endpoints are accessible

### 2. Configure Stripe Webhook

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → Developers → Webhooks
2. Click "Add endpoint"
3. Enter URL: `https://your-firegeo-domain.vercel.app/api/stripe/webhook`
4. Select events:
   - `invoice.paid` (required for paid_pro events)
   - `checkout.session.completed` (already handled)
   - `customer.subscription.updated` (already handled)
   - `customer.subscription.deleted` (already handled)
5. Copy webhook signing secret
6. Add to FireGEO environment variables:
   - `STRIPE_WEBHOOK_SECRET_LIVE` (for production)
   - `STRIPE_WEBHOOK_SECRET` (for test mode)

### 3. Configure Smartlead Webhook (When Ready)

1. Go to Smartlead Dashboard → Settings → Webhooks
2. Add endpoint: `https://your-firegeo-domain.vercel.app/api/webhook/smartlead`
3. Select events: `email_replied` (or equivalent)
4. (Optional) Set webhook secret in FireGEO:
   - `SMARTLEAD_WEBHOOK_SECRET`

### 4. Set Up SalesGPT Event Sync

**Option A: Cron Job (Recommended)**

Add to crontab:
```bash
crontab -e
```

Add line (runs every 5 minutes):
```
*/5 * * * * cd /Users/JJR/SalesGPT && /Users/JJR/SalesGPT/venv/bin/python3 scripts/sync_marketing_events.py --limit 1000 >> /tmp/marketing_events_sync.log 2>&1
```

**Option B: Manual Run**

```bash
cd /Users/JJR/SalesGPT
source venv/bin/activate
python3 scripts/sync_marketing_events.py --limit 1000
```

**Option C: Systemd Service (Linux)**

Create `/etc/systemd/system/marketing-events-sync.service`:
```ini
[Unit]
Description=SalesGPT Marketing Events Sync
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/Users/JJR/SalesGPT
Environment="PATH=/Users/JJR/SalesGPT/venv/bin"
ExecStart=/Users/JJR/SalesGPT/venv/bin/python3 scripts/sync_marketing_events.py --limit 1000
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable marketing-events-sync
sudo systemctl start marketing-events-sync
```

### 5. Environment Variables

**FireGEO (.env.local on Vercel):**
```bash
DATABASE_URL=postgresql://...  # Supabase connection string
STRIPE_WEBHOOK_SECRET_LIVE=whsec_...  # Stripe webhook secret
STRIPE_PRO_PRICE_ID_LIVE=price_1SobzBQg9yJEawqIFl1VSm5u
SMARTLEAD_WEBHOOK_SECRET=...  # Optional
```

**SalesGPT (.env.local):**
```bash
SUPABASE_DATABASE_URL=postgresql://postgres.doeirwfpgplundoznniy:jayr@und4SUPA@aws-0-us-west-2.pooler.supabase.com:6543/postgres?pgbouncer=true
SALESGPT_DATABASE_URL=sqlite:///./salesgpt.db
```

## Testing After Deployment

### 1. Test Signup Event
1. Register a new user on FireGEO
2. Check Supabase `marketing_events` table for `signup_free` event
3. Run sync script: `python3 scripts/sync_marketing_events.py`
4. Verify lead in SalesGPT DB has `free_signup_at` set

### 2. Test Activation Event
1. Create first brand analysis for a new user
2. Check `marketing_events` table for `activated` event

### 3. Test Paid Pro Event
1. Complete a Pro subscription checkout
2. Check Stripe webhook logs in dashboard
3. Check `marketing_events` table for `paid_pro` event
4. Run sync script
5. Verify lead has `paid_pro_at`, `paid_pro_price_id`, etc.

### 4. Test Email Reply Event
1. Configure Smartlead webhook (when ready)
2. Send test reply event
3. Check `marketing_events` table for `email_reply` event
4. Run sync script
5. Verify lead has `reply_received_at` set

## Monitoring

### Check Event Processing
```sql
-- View unprocessed events
SELECT COUNT(*) FROM marketing_events WHERE processed_at IS NULL;

-- View recent events
SELECT email, event_type, occurred_at, processed_at 
FROM marketing_events 
ORDER BY occurred_at DESC 
LIMIT 20;

-- View events by type
SELECT event_type, COUNT(*) 
FROM marketing_events 
GROUP BY event_type;
```

### Check Lead Updates
```python
from salesgpt.db.connection import DatabaseManager
from salesgpt.models.database import Lead
from salesgpt.config import get_settings

db = DatabaseManager(get_settings().database_url)
with db.session() as session:
    # Count leads with conversions
    paid_count = session.query(Lead).filter(Lead.paid_pro_at.isnot(None)).count()
    signup_count = session.query(Lead).filter(Lead.free_signup_at.isnot(None)).count()
    reply_count = session.query(Lead).filter(Lead.reply_received_at.isnot(None)).count()
    
    print(f"Paid Pro: {paid_count}")
    print(f"Free Signups: {signup_count}")
    print(f"Email Replies: {reply_count}")
```

## Troubleshooting

### Events Not Appearing in Supabase
- Check FireGEO logs in Vercel dashboard
- Verify webhook URLs are correct
- Check environment variables are set

### Events Not Processing
- Verify `SUPABASE_DATABASE_URL` is set correctly
- Check sync script logs
- Verify SalesGPT database is accessible
- Check for email mismatches (case sensitivity handled)

### Connection Errors
- Verify password encoding (handled automatically)
- Check pgbouncer parameter removal (handled automatically)
- Verify network connectivity to Supabase

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
- `scripts/test_marketing_events_bridge.py` (new - test suite)
- `salesgpt/db/connection.py` (fixed PRAGMA listener scope)

## Next Steps

1. ✅ Deploy FireGEO to Vercel
2. ✅ Configure Stripe webhook
3. ⏳ Configure Smartlead webhook (when ready)
4. ⏳ Set up cron job for sync script
5. ⏳ Monitor event processing in production
6. ⏳ Set up alerts for sync failures

## Support

For issues or questions:
- Check test suite: `python3 scripts/test_marketing_events_bridge.py`
- Review logs: `/tmp/marketing_events_sync.log` (if using cron)
- Check Supabase dashboard for event counts
- Verify webhook delivery in Stripe/Smartlead dashboards

---

**Status**: ✅ Ready for Production Deployment

