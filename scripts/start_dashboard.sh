#!/bin/bash
# Start Streamlit Dashboard

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project directory
cd "$PROJECT_DIR"

# Run Streamlit
streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost

