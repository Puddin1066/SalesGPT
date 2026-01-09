"""
Email Review Components.

Helper functions for rendering email review UI components.
"""
import streamlit as st
from typing import List, Dict, Callable


def render_queue_sidebar(leads: List[Dict], current_idx: int):
    """
    Render queue sidebar (left panel).
    
    Args:
        leads: List of lead dictionaries
        current_idx: Current lead index
    """
    st.markdown("### 📋 Queue")
    
    for i, item in enumerate(leads[:15]):
        icon = "🟢" if i == current_idx else "○"
        name = item.get('name', 'Unknown')[:20]
        score = item.get('score', 0)
        st.text(f"{icon} {name}")
        st.caption(f"  Score: {score}")


def render_email_preview(
    lead: Dict,
    on_approve: Callable,
    on_edit: Callable,
    on_skip: Callable
):
    """
    Render email preview (center panel).
    
    Args:
        lead: Lead dictionary
        on_approve: Callback for approve action
        on_edit: Callback for edit action
        on_skip: Callback for skip action
    """
    st.markdown(f"### 📧 Email Preview")
    
    # Subject and body are handled in main app
    # This is a placeholder for future componentization
    pass


def render_lead_context(lead: Dict):
    """
    Render lead context (right panel).
    
    Args:
        lead: Lead dictionary
    """
    st.markdown("### 📊 Lead Details")
    st.text(f"Name: {lead.get('name', 'N/A')}")
    st.text(f"Company: {lead.get('company_name', 'N/A')}")
    st.text(f"Location: {lead.get('location', 'N/A')}")

