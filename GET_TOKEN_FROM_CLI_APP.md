# Get Access Token from CLI-Created App

## ✅ App Successfully Created!

Your HubSpot app has been created and deployed:
- **Project:** SalesGPT-Integration
- **App UID:** salesgpt_integration
- **Account:** GEMflush_HS (244348310)
- **Status:** Deployed ✅

## Get Your Access Token

### Method 1: Using CLI (Easiest)

```bash
cd SalesGPT-Integration
hs project open
```

This will open the project in your browser. Then:
1. Click on **"salesgpt_integration"** (the app component)
2. Go to the **"Auth"** tab
3. Copy the **"Access Token"** (for static auth)

### Method 2: Direct URL

1. Go to: https://app.hubspot.com/developer-projects/244348310/project/SalesGPT-Integration
2. Click on **"salesgpt_integration"** in the component list
3. Go to **"Auth"** tab
4. Copy the **"Access Token"**

### Method 3: Via Development Menu

1. In HubSpot, go to **Development** → **Projects**
2. Click **"SalesGPT-Integration"**
3. Click **"salesgpt_integration"** (app UID)
4. Go to **"Auth"** tab
5. Copy the **"Access Token"**

## Update .env File

After getting your token:

```bash
cd /Users/JJR/SalesGPT
python3 update_hubspot_token.py
```

Paste your access token when prompted.

## Verify Connection

```bash
python3 verify_hubspot_token.py
```

You should see:
```
✅ SUCCESS! Token is valid and working
```

## App Configuration

Your app is configured with:
- **Distribution:** Private (single account)
- **Authentication:** Static token
- **Scopes:**
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.objects.deals.read`
  - `crm.objects.deals.write`
  - `oauth` (automatically added)

## Next Steps

1. ✅ Get access token (see above)
2. ✅ Update `.env` file
3. ✅ Verify connection
4. ✅ Start using HubSpot API!

Your HubSpot integration is ready! 🎉

