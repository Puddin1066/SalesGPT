"""
Database models for SalesGPT.

This module contains both the original models (BedrockCustomModel, etc.)
and the new database models.
"""
# Import original models from parent module
import sys
from pathlib import Path

# Import original models.py content
_models_file = Path(__file__).parent.parent / "models.py"
if _models_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("salesgpt.models_original", _models_file)
    if spec and spec.loader:
        models_original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_original)
        # Re-export original models
        BedrockCustomModel = models_original.BedrockCustomModel
        __all__ = ["BedrockCustomModel", "Base", "Lead", "Conversation", "ConversationMessage", "Campaign"]
    else:
        # Fallback: import from parent
        from salesgpt.models import BedrockCustomModel
        __all__ = ["BedrockCustomModel", "Base", "Lead", "Conversation", "ConversationMessage", "Campaign"]
else:
    # If models.py doesn't exist, just export database models
    __all__ = ["Base", "Lead", "Conversation", "ConversationMessage", "Campaign"]

# Import database models
from salesgpt.models.database import Base, Lead, Conversation, ConversationMessage, Campaign

