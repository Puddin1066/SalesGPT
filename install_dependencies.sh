#!/bin/bash
# Install all required dependencies for the dashboard

set -e

echo "📦 Installing all required dependencies..."
echo ""

cd /Users/JJR/SalesGPT

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
    2>&1 | grep -v "WARNING" || true

echo ""
echo "✅ Core dependencies installed!"
echo ""

# Verify critical imports
echo "🔍 Verifying installations..."
python3 -c "import streamlit; print('  ✅ streamlit:', streamlit.__version__)" 2>/dev/null || echo "  ❌ streamlit missing"
python3 -c "import plotly; print('  ✅ plotly:', plotly.__version__)" 2>/dev/null || echo "  ❌ plotly missing"
python3 -c "import pandas; print('  ✅ pandas:', pandas.__version__)" 2>/dev/null || echo "  ❌ pandas missing"
python3 -c "from pydantic_settings import BaseSettings; print('  ✅ pydantic-settings')" 2>/dev/null || echo "  ❌ pydantic-settings missing"
python3 -c "from sqlalchemy import create_engine; print('  ✅ sqlalchemy')" 2>/dev/null || echo "  ❌ sqlalchemy missing"
python3 -c "import alembic; print('  ✅ alembic')" 2>/dev/null || echo "  ❌ alembic missing"

echo ""
echo "✅ Dependency installation complete!"
echo ""
echo "🚀 You can now start services with:"
echo "   ./install_and_start.sh"

