import os
import sys

# Ensure we use the venv
print(f"Python version: {sys.version}")

try:
    from salesgpt.agents import SalesGPT
    from langchain_community.chat_models import ChatLiteLLM
    print("✅ Successfully imported SalesGPT and ChatLiteLLM")
except ImportError as e:
    print(f"❌ Failed to import dependencies: {e}")
    sys.exit(1)

print("✅ Environment setup looks good!")

