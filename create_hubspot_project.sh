#!/bin/bash
# Script to create HubSpot project non-interactively

echo "Creating HubSpot project..."

# Create project with automated responses
{
    echo "SalesGPT-Integration"  # Project name
    echo ""                       # Accept default folder location
    echo "1"                     # Select template option 1 (CRM getting started with private apps)
} | hs project create --platform-version 2025.1

if [ -d "SalesGPT-Integration" ]; then
    echo "✅ Project created successfully!"
    echo "Project location: $(pwd)/SalesGPT-Integration"
else
    echo "❌ Project creation may have failed or needs manual input"
    echo "Try running manually: hs project create --platform-version 2025.1"
fi



