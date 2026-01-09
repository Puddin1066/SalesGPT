#!/bin/bash
# Automated HubSpot app creation via CLI

echo "Creating HubSpot app via CLI..."

# Create project with automated responses
# Responses: App name, select App, Private distribution, Static token, no features
{
    echo "SalesGPT-Integration"  # Project name
    echo ""                       # Accept default folder
    echo "1"                     # Select App (option 1)
    echo "1"                     # Select Private distribution
    echo "1"                     # Select Static token (not OAuth)
    echo ""                       # No features (just press enter or deselect all)
} | hs project create 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Project created successfully!"
    echo "Next steps:"
    echo "1. cd SalesGPT-Integration"
    echo "2. hs project upload"
    echo "3. hs project open (to get access token)"
else
    echo ""
    echo "⚠️  Project creation may need manual input"
    echo "Try running manually: hs project create"
fi

