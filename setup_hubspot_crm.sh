#!/bin/bash

# HubSpot CRM Tracking Setup Script

echo "🚀 HubSpot CRM Tracking Setup"
echo "=============================="
echo ""

# Step 1: Open project
echo "📂 Step 1: Opening HubSpot project..."
cd SalesGPT-Integration
hs project open

echo ""
echo "✅ Project opened in browser"
echo ""
echo "📋 Next steps (in browser):"
echo "   1. Click on 'salesgpt_integration' (the app component)"
echo "   2. Go to 'Distribution' tab"
echo "   3. Click 'Install now'"
echo "   4. Authorize the app"
echo "   5. Go to 'Auth' tab"
echo "   6. Copy the 'Access Token'"
echo ""
echo "After you get the token, run:"
echo "   python3 update_hubspot_token.py YOUR_TOKEN_HERE"
echo ""
echo "Or manually edit .env and set:"
echo "   HUBSPOT_API_KEY=your-token-here"
echo ""

