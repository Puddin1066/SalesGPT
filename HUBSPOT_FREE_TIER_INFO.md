# HubSpot Free Tier - API Access Information

## ✅ Good News: No Paid Subscription Required!

**Private Apps and API access tokens work on FREE HubSpot accounts.**

## What's Available on Free Tier

### ✅ Available Features:
- **Private Apps** - Can create and use Private Apps
- **API Access Tokens** - Can generate and use access tokens
- **OAuth 2.0** - Can use OAuth authentication
- **API Access** - Full API access to CRM objects

### ⚠️ Rate Limits (Free/Starter Accounts):
- **100 requests per 10 seconds**
- **250,000 requests per day**

### 📈 Higher Tier Limits (Professional/Enterprise):
- **150 requests per 10 seconds**
- **500,000 requests per day**

## Your Token Issue

The "expired token" error you're seeing is **NOT** because of your account tier. It's because:

1. **The token itself is expired/invalid**
2. **The token was never properly regenerated**
3. **The token format might be incorrect**

## What You Need to Do

1. **Go to Private Apps** (works on free tier):
   - https://app.hubspot.com/settings/integrations/private-apps

2. **Create/Regenerate Private App:**
   - Create a new Private App OR
   - Click existing app → Auth tab → **Regenerate token**

3. **Copy the NEW token:**
   - Must be different from the old one
   - Should be 100+ characters

4. **Update .env:**
   ```bash
   python3 update_hubspot_token.py
   ```

## Free Tier Limitations

While you can use API tokens on free tier, some features require paid plans:

- **UI Extensions** - Require Enterprise subscription
- **Advanced features** - Some require paid tiers
- **Higher rate limits** - Paid tiers have higher limits

But for **basic API access** (contacts, deals, etc.), **free tier is sufficient**.

## References

- [HubSpot API Usage Guidelines](https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines)
- [Private Apps Documentation](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview)



