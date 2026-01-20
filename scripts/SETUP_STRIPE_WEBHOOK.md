# Setting Up Stripe Webhook via API

## Quick Setup

Use the script to automatically create/update the Stripe webhook endpoint:

```bash
cd /Users/JJR/SalesGPT
source venv/bin/activate
python3 scripts/setup_stripe_webhook.py --url https://your-firegeo-domain.vercel.app/api/stripe/webhook
```

Replace `your-firegeo-domain.vercel.app` with your actual FireGEO Vercel deployment URL.

## Find Your FireGEO URL

1. **Check Vercel Dashboard:**
   - Go to https://vercel.com/dashboard
   - Find your FireGEO project
   - Copy the deployment URL (e.g., `firegeo-iota.vercel.app`)

2. **Or check environment:**
   ```bash
   cd /Users/JJR/firegeo
   grep NEXT_PUBLIC_APP_URL .env.local
   ```

## Example

```bash
# For production
python3 scripts/setup_stripe_webhook.py --url https://gemflush.com/api/stripe/webhook

# For Vercel preview
python3 scripts/setup_stripe_webhook.py --url https://firegeo-iota.vercel.app/api/stripe/webhook
```

## What It Does

1. ✅ Checks if webhook endpoint already exists
2. ✅ Creates new endpoint if it doesn't exist
3. ✅ Updates existing endpoint if it does exist
4. ✅ Configures required events:
   - `invoice.paid` (for paid_pro events)
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. ✅ Displays webhook secret for FireGEO environment variables

## After Running

The script will output a webhook secret. Add it to FireGEO environment variables:

**In Vercel Dashboard or `.env.local`:**
```
STRIPE_WEBHOOK_SECRET_LIVE=whsec_...
```

## Verify Setup

1. Check Stripe Dashboard → Developers → Webhooks
2. Verify endpoint is listed and active
3. Test by completing a test checkout
4. Check FireGEO logs for webhook events

## Troubleshooting

**Error: "STRIPE_API_KEY not configured"**
- Add `STRIPE_API_KEY=sk_live_...` to `.env.local`

**Error: "Invalid API key"**
- Make sure you're using the correct key (live vs test)
- Check key format starts with `sk_live_` or `sk_test_`

**Webhook not receiving events**
- Verify URL is publicly accessible
- Check FireGEO deployment is live
- Verify webhook secret matches in FireGEO

