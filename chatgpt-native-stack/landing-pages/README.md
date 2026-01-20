# 🚀 GemFlush Landing Pages

**Rich, conversion-optimized landing pages for each market vertical.**

## ✅ What's Been Built

All **8 landing pages** have been built and are ready to deploy:

### Markets & Variants
- 🏥 **Medical Clinics** (Variant A: Audit-focused, Variant B: Demo-focused)
- ⚖️ **Legal Firms** (Variant A: Audit-focused, Variant B: Demo-focused)
- 🏘️ **Real Estate** (Variant A: Audit-focused, Variant B: Demo-focused)
- 🚀 **Marketing Agencies** (Variant A: Audit-focused, Variant B: Demo-focused)

### Features
✅ Modern, mobile-responsive design  
✅ Conversion-optimized layout  
✅ Market-specific branding (colors, messaging, CTAs)  
✅ Lead capture forms  
✅ Social proof sections  
✅ Problem-solution-CTA flow  
✅ Fast loading (pure HTML/CSS)  

---

## 📂 File Structure

```
landing-pages/
├── builder.py              # Generates HTML from markdown
├── deploy_hubspot.py       # Deploy to HubSpot (requires CMS Hub)
├── deploy_netlify.py       # Deploy to Netlify (free, instant)
├── README.md              # This file
└── output/
    └── html/
        ├── medical_landing_page_a.html
        ├── medical_landing_page_b.html
        ├── legal_landing_page_a.html
        ├── legal_landing_page_b.html
        ├── realestate_landing_page_a.html
        ├── realestate_landing_page_b.html
        ├── agencies_landing_page_a.html
        └── agencies_landing_page_b.html
```

---

## 🚀 Quick Start - Deploy Now!

### Option 1: Netlify (Recommended - Fast & Free)

**Easiest:** Drag & Drop
```bash
# 1. Open https://app.netlify.com
# 2. Click "Add new site" → "Deploy manually"
# 3. Drag the "output/html" folder
# 4. Get your live URL in seconds!
```

**Advanced:** CLI Deployment
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy all pages
python3 landing-pages/deploy_netlify.py
```

### Option 2: HubSpot (If you have CMS Hub)

```bash
# Requires HubSpot CMS Hub (paid)
python3 landing-pages/deploy_hubspot.py
```

### Option 3: View Locally

```bash
# Open any HTML file in your browser
open landing-pages/output/html/medical_landing_page_a.html
```

---

## 🎨 Customization

### Update Content

The pages are generated from markdown files in:
```
content-generation/output/landing-pages/
```

To rebuild after changes:
```bash
python3 landing-pages/builder.py
```

### Update Branding (Colors, CTAs)

Edit `builder.py`:
```python
MARKET_CONFIG = {
    'medical': {
        'color_primary': '#0066CC',    # Change colors
        'color_secondary': '#00A3E0',
        'cta_primary': 'Get Your Free AI Audit',  # Change CTAs
    },
    # ... other markets
}
```

Then rebuild:
```bash
python3 landing-pages/builder.py
```

---

## 📊 Tracking & Analytics

### Add HubSpot Tracking

Replace in each HTML file:
```html
<!-- Find this line at bottom of HTML -->
<script type="text/javascript" id="hs-script-loader" 
        async defer src="//js.hs-scripts.com/YOUR_HUB_ID.js"></script>

<!-- Replace YOUR_HUB_ID with your actual HubSpot ID -->
```

### Add Google Analytics

Add before `</head>`:
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

---

## 📝 Connect Forms to HubSpot

### Option 1: HubSpot Forms API (Recommended)

1. Create form in HubSpot: Marketing → Forms → Create
2. Get form ID from URL
3. Replace form in HTML:

```html
<!-- Replace existing form div with: -->
<div id="hubspot-form"></div>
<script charset="utf-8" type="text/javascript" src="//js.hsforms.net/forms/v2.js"></script>
<script>
  hbspt.forms.create({
    region: "na1",
    portalId: "YOUR_PORTAL_ID",
    formId: "YOUR_FORM_ID"
  });
</script>
```

### Option 2: Netlify Forms (Free)

Already configured if you use `deploy_netlify.py`! 

Form submissions go to: Netlify Dashboard → Forms

### Option 3: Direct API Integration

See `deploy_hubspot.py` for programmatic form creation.

---

## 🧪 A/B Testing

### Test Variant A vs Variant B

**Netlify:**
```bash
# Deploy both variants
# Use Netlify Split Testing feature
# Dashboard → Split Testing → Configure
```

**HubSpot:**
```bash
# Both variants deployed as separate pages
# Use HubSpot A/B testing:
# Marketing → Landing Pages → Select page → Test
```

**Manual:**
```bash
# Split traffic 50/50 in email campaigns:
# - 50% get link to variant A
# - 50% get link to variant B
# Track conversions in HubSpot
```

---

## 🔗 Get Live URLs

After deployment:

### Netlify
Your URLs will be:
```
https://your-site-name.netlify.app/medical_landing_page_a.html
https://your-site-name.netlify.app/legal_landing_page_a.html
https://your-site-name.netlify.app/realestate_landing_page_a.html
https://your-site-name.netlify.app/agencies_landing_page_a.html
```

### Custom Domain (Recommended)
```
https://medical.gemflush.com  → medical_landing_page_a.html
https://legal.gemflush.com    → legal_landing_page_a.html
https://realestate.gemflush.com → realestate_landing_page_a.html
https://agencies.gemflush.com → agencies_landing_page_a.html
```

Setup in Netlify: Domain Settings → Add custom domain

---

## 🎯 Integration with Email Campaigns

Update your email templates to include live landing page URLs:

```python
# In email content files (email-content/*.txt)
# Replace placeholders:
[Link to landing page] → https://medical.gemflush.com

# Or in gemflush_campaign.py:
landing_page_urls = {
    'medical': 'https://medical.gemflush.com',
    'legal': 'https://legal.gemflush.com',
    'realestate': 'https://realestate.gemflush.com',
    'agencies': 'https://agencies.gemflush.com'
}
```

---

## 📈 Conversion Optimization Checklist

- [ ] Deploy pages to Netlify/HubSpot
- [ ] Add tracking codes (HubSpot + Google Analytics)
- [ ] Connect forms to HubSpot
- [ ] Test form submissions
- [ ] Set up custom domain (optional)
- [ ] Add pages to email campaigns
- [ ] Set up A/B tests
- [ ] Monitor conversion rates
- [ ] Iterate based on data

---

## 🚨 Troubleshooting

**Forms not submitting?**
- Check HubSpot form ID is correct
- Verify portal ID in embed code
- Test form in browser console

**Pages not loading?**
- Check HTML files exist in output/html/
- Verify deployment completed successfully
- Check browser console for errors

**Want to rebuild pages?**
```bash
python3 landing-pages/builder.py
```

---

## 🎓 Next Steps

1. **Deploy immediately:** `python3 landing-pages/deploy_netlify.py`
2. **Get live URLs** from Netlify dashboard
3. **Update email campaigns** with landing page links
4. **Set up A/B tests** to optimize conversion
5. **Monitor results** in HubSpot analytics

---

## 💡 Pro Tips

**For Maximum Conversions:**
- Test both A and B variants for each market
- Use market-specific URLs (medical.gemflush.com)
- Add testimonials from real customers when available
- Monitor time-on-page and bounce rate
- Iterate based on data, not assumptions

**For Fast Iteration:**
- Use Netlify for instant deploys (no approval needed)
- Keep markdown content in Git for version control
- A/B test everything (headlines, CTAs, images)
- Use heatmaps (Hotjar) to see user behavior

---

## 📞 Support

**Issues with deployment?**
- Check: `DEPLOYMENT_GUIDE.md`
- HubSpot docs: https://developers.hubspot.com/docs/cms
- Netlify docs: https://docs.netlify.com

**Questions about customization?**
- See: `builder.py` for all configuration options
- Edit: `MARKET_CONFIG` dictionary for branding

---

**Ready to launch? Let's get those pages live! 🚀**

```bash
python3 landing-pages/deploy_netlify.py
```


