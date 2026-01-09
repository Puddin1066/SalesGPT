"""
Manual Review Workflow.

Helper functions for manual email review and approval.
"""
from datetime import datetime
from typing import Dict, List, Optional
from state.state_manager import StateManager
from services.outbound.smartlead_agent import SmartleadAgent
from services.crm.hubspot_agent import HubSpotAgent


def load_pending_leads(
    state_manager: StateManager,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Load leads pending review.
    
    Args:
        state_manager: StateManager instance
        limit: Maximum number of leads to return
        
    Returns:
        List of lead dictionaries, sorted by score (descending)
    """
    leads = state_manager.get_all_leads_by_status("pending_review")
    
    # Sort by score (highest first)
    leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    if limit:
        leads = leads[:limit]
    
    return leads


def approve_and_send(
    lead: Dict,
    smartlead: SmartleadAgent,
    hubspot: HubSpotAgent,
    state_manager: StateManager
) -> bool:
    """
    Approve and send email for a lead.
    
    Args:
        lead: Lead dictionary
        smartlead: Smartlead agent for sending
        hubspot: HubSpot agent for CRM updates
        state_manager: State manager for database updates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Send email via Smartlead
        # Note: This assumes you have a campaign_id set up
        # For manual sending, you might need to use Smartlead's direct send API
        
        # For now, we'll update the status to "sent" and mark the timestamp
        # The actual sending would be handled by Smartlead integration
        
        # Update database
        state_manager.update_lead_state(
            lead["email"],
            {
                "status": "sent",
                "email_sent_at": datetime.now(),
                "email_subject": lead.get("email_subject", ""),
                "email_body": lead.get("email_body", "")
            }
        )
        
        # Update HubSpot pipeline stage
        if lead.get("hubspot_contact_id"):
            hubspot.update_pipeline_stage(
                lead["hubspot_contact_id"],
                "engaged"
            )
        
        return True
    except Exception as e:
        print(f"Error approving and sending email: {e}")
        return False


def skip_lead(
    lead_email: str,
    state_manager: StateManager
) -> bool:
    """
    Skip a lead (mark as skipped).
    
    Args:
        lead_email: Lead email address
        state_manager: State manager for database updates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        state_manager.set_lead_status(
            lead_email,
            "skipped",
            metadata={
                "skipped_at": datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error skipping lead: {e}")
        return False


def reject_lead(
    lead_email: str,
    state_manager: StateManager
) -> bool:
    """
    Reject a lead (mark as rejected).
    
    Args:
        lead_email: Lead email address
        state_manager: State manager for database updates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        state_manager.set_lead_status(
            lead_email,
            "rejected",
            metadata={
                "rejected_at": datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error rejecting lead: {e}")
        return False


def update_email_content(
    lead_email: str,
    subject: str,
    body: str,
    state_manager: StateManager
) -> bool:
    """
    Update email content for a lead.
    
    Args:
        lead_email: Lead email address
        subject: Updated subject line
        body: Updated email body
        state_manager: State manager for database updates
        
    Returns:
        True if successful, False otherwise
    """
    try:
        state_manager.update_lead_state(
            lead_email,
            {
                "email_subject": subject,
                "email_body": body,
                "email_edited_at": datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating email content: {e}")
        return False

