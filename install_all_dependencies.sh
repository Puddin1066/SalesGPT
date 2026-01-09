#!/bin/bash
# Install ALL dependencies needed for the platform

set -e

cd /Users/JJR/SalesGPT

echo "📦 Installing ALL dependencies for SalesGPT Email Platform..."
echo ""

# Core dependencies
python3 -m pip install --user --break-system-packages \
    streamlit \
    plotly \
    pandas \
    pydantic-settings \
    sqlalchemy \
    alembic \
    requests \
    fastapi \
    uvicorn \
    slowapi \
    langchain \
    langchain-core \
    langchain-community \
    langchain-openai \
    langchain-text-splitters \
    langchain-classic \
    litellm \
    chromadb \
    boto3 \
    aioboto3 \
    2>&1 | grep -v "WARNING" || true

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "🚀 Services are ready to start!"
echo ""
echo "Run: ./install_and_start.sh"

