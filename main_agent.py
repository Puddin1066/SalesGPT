"""
A.S.S.C.H. Assembly - Main Orchestrator

Daily cron or manual CLI execution.
Orchestrates the full pipeline: Apollo → Smartlead → SalesGPT → HubSpot
"""
import os
import asyncio
import json
from typing import List, Dict
from dotenv import load_dotenv

from services.apollo import ApolloAgent
from services.outbound import SmartleadAgent
from services.salesgpt import SalesGPTWrapper
from services.scheduler import CalScheduler
from services.crm import HubSpotAgent
from services.visibility import GEMflushAgent
from state import StateManager


class ASSCHOrchestrator:
    """
    Main orchestrator for A.S.S.C.H. Assembly.
    
    Pipeline:
    1. Pull 20-50 new leads via Apollo → score by specialty & location
    2. POST leads into Smartlead → emails auto-sequenced
    3. Webhook catches reply events from Smartlead
    4. Smartlead → calls SalesGPT with thread history
    5. SalesGPT checks sentiment → intent
    6. If "interested" → returns booking link
    7. If "objection" → turns visibility results into value
    8. Booked call → send to HubSpot
    9. HubSpot status updates → feed Smartlead prioritization
    """
    
    def __init__(self):
        """Initialize orchestrator with all services."""
        load_dotenv(".env.local")
        
        # Initialize services
        self.apollo = ApolloAgent()
        self.smartlead = SmartleadAgent()
        self.salesgpt = SalesGPTWrapper()
        self.scheduler = CalScheduler()
        self.crm = HubSpotAgent()
        self.visibility = GEMflushAgent()
        self.state = StateManager()
        
        # Configuration
        self.campaign_name = os.getenv("SMARTLEAD_CAMPAIGN_NAME", "ASSCH Outreach")
        self.campaign_id = None
    
    async def run_daily_pipeline(
        self,
        geography: str,
        specialty: str,
        lead_limit: int = 50
    ):
        """
        Run the daily lead sourcing and outreach pipeline.
        
        Args:
            geography: Target geography (e.g., "New York, NY")
            specialty: Medical specialty filter
            lead_limit: Maximum leads to process
        """
        print(f"🚀 Starting A.S.S.C.H. Assembly pipeline...")
        print(f"📍 Geography: {geography}")
        print(f"🏥 Specialty: {specialty}")
        print(f"📊 Lead Limit: {lead_limit}\n")
        
        # Step 1: Pull leads from Apollo
        print("1️⃣ Fetching leads from Apollo...")
        leads = self.apollo.search_leads(
            geography=geography,
            specialty=specialty,
            limit=lead_limit
        )
        
        if not leads:
            print("❌ No leads found. Exiting.")
            return
        
        print(f"✅ Found {len(leads)} leads")
        
        # Step 2: Score leads
        print("\n2️⃣ Scoring leads...")
        scored_leads = self.apollo.score_leads(leads)
        print(f"✅ Scored {len(scored_leads)} leads")
        
        # Step 3: Create/Get Smartlead campaign
        print("\n3️⃣ Setting up Smartlead campaign...")
        self.campaign_id = await self._ensure_campaign()
        
        if not self.campaign_id:
            print("❌ Failed to create campaign. Exiting.")
            return
        
        print(f"✅ Campaign ID: {self.campaign_id}")
        
        # Step 4: Add leads to Smartlead
        print("\n4️⃣ Adding leads to Smartlead...")
        lead_data = [
            {
                "email": lead.email,
                "first_name": lead.name.split()[0] if lead.name else "",
                "last_name": " ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                "custom_fields": {
                    "clinic_name": lead.clinic_name,
                    "website": lead.website,
                    "specialty": lead.specialty,
                    "location": lead.location,
                    "score": lead.metadata.get("score", 0),
                }
            }
            for lead in scored_leads
        ]
        
        success = self.smartlead.add_leads_to_campaign(
            self.campaign_id,
            lead_data
        )
        
        if success:
            print(f"✅ Added {len(lead_data)} leads to campaign")
            
            # Update lead states
            for lead in scored_leads:
                self.state.set_lead_status(
                    lead.email,
                    status="idle",
                    metadata={
                        "clinic_name": lead.clinic_name,
                        "website": lead.website,
                        "specialty": lead.specialty,
                        "campaign_id": self.campaign_id,
                    }
                )
        else:
            print("❌ Failed to add leads to campaign")
        
        # Step 5: Create contacts in HubSpot
        print("\n5️⃣ Creating HubSpot contacts...")
        for lead in scored_leads[:20]:  # Limit to avoid rate limits
            contact_id = self.crm.create_contact(
                email=lead.email,
                first_name=lead.name.split()[0] if lead.name else "",
                last_name=" ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                company=lead.clinic_name,
                website=lead.website
            )
            
            if contact_id:
                self.state.update_lead_state(
                    lead.email,
                    {"hubspot_contact_id": contact_id}
                )
        
        print("✅ Pipeline complete!")
        print("\n📧 Emails will be sent via Smartlead sequences")
        print("🔄 Reply handling via webhook (see webhook_handler.py)")
    
    async def _ensure_campaign(self) -> int:
        """
        Ensure campaign exists, create if not.
        
        Returns:
            Campaign ID
        """
        # Check if campaign exists (simplified - in production, query API)
        # For now, create new campaign
        
        from_email = os.getenv("SMARTLEAD_FROM_EMAIL")
        from_name = os.getenv("SMARTLEAD_FROM_NAME", "ASSCH Team")
        reply_to = os.getenv("SMARTLEAD_REPLY_TO", from_email)
        
        # Get mailbox IDs
        mailboxes = self.smartlead.get_mailboxes()
        mailbox_ids = [mb["id"] for mb in mailboxes[:3]]  # Use first 3 mailboxes
        
        if not mailbox_ids:
            print("⚠️ No mailboxes available. Using default.")
            mailbox_ids = [1]  # Fallback
        
        campaign_id = self.smartlead.create_campaign(
            name=self.campaign_name,
            from_email=from_email,
            from_name=from_name,
            reply_to=reply_to,
            mailbox_ids=mailbox_ids
        )
        
        # Add initial sequence
        if campaign_id:
            subject = os.getenv(
                "SMARTLEAD_INITIAL_SUBJECT",
                "Quick question about your clinic's visibility"
            )
            body = os.getenv(
                "SMARTLEAD_INITIAL_BODY",
                "Hi {{first_name}},\n\nI noticed {{clinic_name}} and wanted to share "
                "something that might interest you.\n\nWould you be open to a "
                "brief conversation?\n\nBest,\n{{from_name}}"
            )
            
            self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=subject,
                body=body,
                delay_days=0
            )
            
            # Add follow-up sequence
            followup_subject = os.getenv(
                "SMARTLEAD_FOLLOWUP_SUBJECT",
                "Following up on visibility"
            )
            followup_body = os.getenv(
                "SMARTLEAD_FOLLOWUP_BODY",
                "Hi {{first_name}},\n\nJust wanted to follow up on my previous message. "
                "I'd love to show you how we can improve {{clinic_name}}'s patient "
                "acquisition.\n\nBest,\n{{from_name}}"
            )
            
            self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=followup_subject,
                body=followup_body,
                delay_days=3
            )
        
        return campaign_id
    
    async def handle_reply(
        self,
        thread_id: str,
        sender_email: str,
        sender_name: str,
        email_body: str
    ):
        """
        Handle incoming email reply.
        
        Args:
            thread_id: Email thread ID
            sender_email: Sender email address
            sender_name: Sender name
            email_body: Email body text
        """
        print(f"\n📧 Processing reply from {sender_email}...")
        
        # Get conversation history
        conversation_history = self.state.get_conversation_history(thread_id)
        
        # Add user message to history
        self.state.add_conversation_message(thread_id, email_body, sender="user")
        
        # Get lead state
        lead_state = self.state.get_lead_state(sender_email)
        clinic_name = lead_state.get("clinic_name", "") if lead_state else ""
        
        # Generate reply with SalesGPT
        reply_data = self.salesgpt.generate_reply(
            email_body=email_body,
            sender_name=sender_name,
            sender_email=sender_email,
            conversation_history=conversation_history,
            clinic_name=clinic_name
        )
        
        intent = reply_data["intent"]
        reply_body = reply_data["body"]
        
        print(f"🎯 Intent: {intent}")
        
        # Handle based on intent
        if intent == "interested":
            # Send booking link
            booking_link = self.scheduler.get_booking_link(
                lead_name=sender_name,
                lead_email=sender_email
            )
            confirmation = self.scheduler.generate_confirmation_message(booking_link)
            reply_body = f"{reply_body}\n\n{confirmation}"
            
            # Update HubSpot to "booked"
            if lead_state and lead_state.get("hubspot_contact_id"):
                self.crm.update_pipeline_stage(
                    lead_state["hubspot_contact_id"],
                    "booked"
                )
            
            self.state.set_lead_status(sender_email, "booked")
            
        elif intent in ["curious", "neutral"]:
            # Inject GEMflush evidence
            if clinic_name:
                competitor = os.getenv("DEFAULT_COMPETITOR", "local competitors")
                evidence = self.visibility.get_competitor_comparison(
                    clinic_id=clinic_name,
                    competitor_name=competitor
                )
                
                if "error" not in evidence:
                    evidence_text = self.visibility.format_evidence_message(evidence)
                    reply_body = f"{reply_body}\n\n{evidence_text}"
            
            self.state.set_lead_status(sender_email, "engaged")
            
        elif intent == "objection":
            # Handle objection with evidence
            if clinic_name:
                competitor = os.getenv("DEFAULT_COMPETITOR", "local competitors")
                evidence = self.visibility.get_competitor_comparison(
                    clinic_id=clinic_name,
                    competitor_name=competitor
                )
                
                if "error" not in evidence:
                    evidence_text = self.visibility.format_evidence_message(
                        evidence,
                        include_full_audit=True
                    )
                    reply_body = f"{reply_body}\n\n{evidence_text}"
            
            self.state.set_lead_status(sender_email, "engaged")
        
        # Send reply via Smartlead
        success = self.smartlead.send_reply(thread_id, reply_body)
        
        if success:
            # Add agent reply to history
            self.state.add_conversation_message(thread_id, reply_body, sender="agent")
            print(f"✅ Reply sent successfully")
        else:
            print(f"❌ Failed to send reply")


async def main():
    """Main entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A.S.S.C.H. Assembly Orchestrator")
    parser.add_argument(
        "--geography",
        type=str,
        default=os.getenv("DEFAULT_GEOGRAPHY", "New York, NY"),
        help="Target geography"
    )
    parser.add_argument(
        "--specialty",
        type=str,
        default=os.getenv("DEFAULT_SPECIALTY", "Dermatology"),
        help="Medical specialty"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum leads to process"
    )
    
    args = parser.parse_args()
    
    orchestrator = ASSCHOrchestrator()
    await orchestrator.run_daily_pipeline(
        geography=args.geography,
        specialty=args.specialty,
        lead_limit=args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())
