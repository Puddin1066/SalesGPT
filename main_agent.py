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
                "Quick question about {{clinic_name}}'s AI visibility"
            )
            body = os.getenv(
                "SMARTLEAD_INITIAL_BODY",
                "Hi {{first_name}},\n\nI noticed {{clinic_name}} specializes in {{specialty}} and thought you might be interested in how our AI visibility platform helps similar clinics:\n\n• Publish your clinic to knowledge graphs to actively raise AI visibility\n• Improve discoverability in AI-powered patient searches (ChatGPT, Google AI, etc.)\n• See how you compare to competitors in your area\n• Get actionable insights to boost patient acquisition\n\nWould you be open to a quick 15-min demo?\n\nBest,\n{{from_name}}"
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
                "Following up on AI visibility for {{clinic_name}}"
            )
            followup_body = os.getenv(
                "SMARTLEAD_FOLLOWUP_BODY",
                "Hi {{first_name}},\n\nJust wanted to follow up. Our AI visibility platform helps clinics like {{clinic_name}} actively raise their AI visibility through knowledge graph publishing, understand their competitive positioning, and improve patient discovery.\n\nI can show you a quick demo of how knowledge graph publishing works - would 15 minutes this week work?\n\nBest,\n{{from_name}}"
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
        
        # Handle based on intent - SaaS-specific flows
        if intent == "demo_request":
            # Send demo booking link
            booking_link = self.scheduler.get_booking_link(
                lead_name=sender_name,
                lead_email=sender_email
            )
            demo_message = (
                f"Great! I'd love to show you how our AI visibility platform works. "
                f"Please book a time that works for you:\n\n{booking_link}\n\n"
                f"During the demo, I'll show you:\n"
                f"• How knowledge graph publishing actively raises your AI visibility\n"
                f"• Your clinic's current visibility score\n"
                f"• How you compare to competitors\n"
                f"• Actionable insights to improve patient discovery\n\n"
                f"Looking forward to speaking with you!"
            )
            reply_body = f"{reply_body}\n\n{demo_message}"
            
            # Update HubSpot to "demo_scheduled"
            if lead_state and lead_state.get("hubspot_contact_id"):
                self.crm.update_pipeline_stage(
                    lead_state["hubspot_contact_id"],
                    "demo_scheduled"
                )
            
            self.state.set_lead_status(sender_email, "demo_scheduled")
            
        elif intent == "trial_request":
            # Send trial link (if you have a trial system)
            trial_link = os.getenv("TRIAL_SIGNUP_LINK", "")
            if trial_link:
                trial_message = (
                    f"Perfect! You can start a free trial here: {trial_link}\n\n"
                    f"The trial includes:\n"
                    f"• Full visibility audit\n"
                    f"• Competitor comparison\n"
                    f"• Actionable recommendations\n\n"
                    f"I'll follow up in a few days to see how it's going!"
                )
                reply_body = f"{reply_body}\n\n{trial_message}"
            else:
                # Fallback to demo if no trial link
                booking_link = self.scheduler.get_booking_link(
                    lead_name=sender_name,
                    lead_email=sender_email
                )
                reply_body = f"{reply_body}\n\nI'd love to show you how it works in a demo. Book a time here: {booking_link}"
            
            self.state.set_lead_status(sender_email, "trial")
            
        elif intent == "pricing_question":
            # Send pricing information
            pricing_page = os.getenv("PRICING_PAGE_URL", "")
            pricing_message = (
                f"Great question! Our AI visibility platform is priced based on clinic size and needs. "
                f"You can see our pricing here: {pricing_page if pricing_page else 'our website'}\n\n"
                f"Most clinics see ROI within 30-60 days through knowledge graph publishing and "
                f"increased patient discovery. "
                f"I'm happy to discuss which plan would work best for {{clinic_name}} - would a quick call work?"
            )
            reply_body = f"{reply_body}\n\n{pricing_message}"
            
            self.state.set_lead_status(sender_email, "pricing_discussion")
            
        elif intent == "interested":
            # Send demo booking link
            booking_link = self.scheduler.get_booking_link(
                lead_name=sender_name,
                lead_email=sender_email
            )
            confirmation = self.scheduler.generate_confirmation_message(booking_link)
            reply_body = f"{reply_body}\n\n{confirmation}"
            
            # Update HubSpot to "demo_scheduled"
            if lead_state and lead_state.get("hubspot_contact_id"):
                self.crm.update_pipeline_stage(
                    lead_state["hubspot_contact_id"],
                    "demo_scheduled"
                )
            
            self.state.set_lead_status(sender_email, "demo_scheduled")
            
        elif intent in ["curious", "neutral"]:
            # Inject GEMflush evidence (AI visibility insights)
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
            # Handle objection with evidence + ROI focus
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
                    # Add ROI context for pricing objections
                    roi_message = (
                        f"\n\nMost clinics see a 15-30% increase in patient discovery within "
                        f"the first 60 days through knowledge graph publishing, which typically "
                        f"pays for the platform many times over. "
                        f"I'd be happy to show you a quick ROI calculation - would that help?"
                    )
                    reply_body = f"{reply_body}\n\n{evidence_text}{roi_message}"
            
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
