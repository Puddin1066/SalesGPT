"""
Cal.com Scheduler Service.

Generates booking links for interested leads.
"""
import os
from typing import Optional


class CalScheduler:
    """
    Cal.com booking link generator.
    
    Critical design: Atomic service - single responsibility.
    Single outcome: Return booking link for lead.
    """
    
    def __init__(self, booking_link: Optional[str] = None):
        """
        Initialize Cal Scheduler.
        
        Args:
            booking_link: Cal.com booking link (defaults to CAL_BOOKING_LINK env var)
        """
        self.booking_link = booking_link or os.getenv("CAL_BOOKING_LINK")
        if not self.booking_link:
            raise ValueError("CAL_BOOKING_LINK not found in environment")
    
    def get_booking_link(
        self,
        lead_name: Optional[str] = None,
        lead_email: Optional[str] = None
    ) -> str:
        """
        Get booking link for a lead.
        
        Args:
            lead_name: Lead's name (optional, for pre-fill)
            lead_email: Lead's email (optional, for pre-fill)
            
        Returns:
            Booking link URL
        """
        # If Cal.com supports pre-fill parameters, add them here
        # For now, return base link
        return self.booking_link
    
    def generate_confirmation_message(self, booking_link: str) -> str:
        """
        Generate confirmation message with booking link.
        
        Args:
            booking_link: Booking link URL
            
        Returns:
            Formatted confirmation message
        """
        return (
            f"Great! I'd love to show you how we can improve your clinic's "
            f"visibility. Please book a time that works for you:\n\n"
            f"{booking_link}\n\n"
            f"Looking forward to speaking with you!"
        )
