"""
A.S.S.C.H. Assembly - Main Orchestrator

Daily cron or manual CLI execution.
Orchestrates the full pipeline: Apollo → Smartlead → SalesGPT → HubSpot
"""
import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from services.apollo.apollo_agent import ApolloAgent
from services.outbound.smartlead_agent import SmartleadAgent
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper
from services.scheduler.cal_scheduler import CalScheduler
from services.crm.hubspot_agent import HubSpotAgent
from services.visibility.gemflush_agent import GEMflushAgent
from services.competitor.competitor_agent import CompetitorAgent
from services.scoring.geo_scorer import GEOScorer
from state.state_manager import StateManager


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
    
    def __init__(
        self,
        apollo: ApolloAgent,
        smartlead: SmartleadAgent,
        salesgpt: SalesGPTWrapper,
        scheduler: CalScheduler,
        crm: HubSpotAgent,
        visibility: GEMflushAgent,
        competitor: CompetitorAgent,
        scorer: GEOScorer,
        state: StateManager,
        ab_manager=None,
        apollo_ab=None
    ):
        """
        Initialize orchestrator with injected dependencies.
        
        Args:
            apollo: Apollo agent for lead sourcing
            smartlead: Smartlead agent for email delivery
            salesgpt: SalesGPT wrapper for reply generation
            scheduler: Cal scheduler for booking links
            crm: HubSpot agent for CRM management
            visibility: GEMflush agent for visibility audits
            competitor: Competitor agent for competitive analysis
            scorer: GEO scorer for lead scoring
            state: State manager for persistence
        """
        self.apollo = apollo
        self.smartlead = smartlead
        self.salesgpt = salesgpt
        self.scheduler = scheduler
        self.crm = crm
        self.visibility = visibility
        self.competitor = competitor
        self.scorer = scorer
        self.state = state
        
        # Analytics services (optional - for A/B testing)
        self.ab_manager = ab_manager
        self.apollo_ab = apollo_ab
        
        # Configuration (will be loaded from settings via container)
        self.campaign_name = "ASSCH Outreach"  # Default, can be overridden
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
        
        # Step 1: Pull leads from Apollo (with A/B testing if available)
        print("1️⃣ Fetching leads from Apollo...")
        
        # Use Apollo A/B testing if available
        if self.apollo_ab:
            apollo_config = self.apollo_ab.get_next_config_to_test()
            params = apollo_config.to_apollo_params()
            print(f"   Using A/B config: {apollo_config.to_code()}")
            
            leads = self.apollo.search_leads(
                geography=apollo_config.geography_value or geography,
                specialty=apollo_config.specialty or specialty,
                min_employees=params["min_employees"],
                max_employees=params["max_employees"],
                has_website=params["has_website"],
                limit=lead_limit
            )
            
            # Tag leads with apollo_config_code
            apollo_config_code = apollo_config.to_code()
            for lead in leads:
                lead.metadata["apollo_config_code"] = apollo_config_code
        else:
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
        # Prepare lead data with email content for Smartlead UI review
        # Email content will be visible in Smartlead dashboard for review
        lead_data = []
        for lead in scored_leads:
            # Get email content if it was generated (for manual review flow)
            # In automated flow, emails are generated per lead
            lead_entry = {
                "email": lead.email,
                "first_name": lead.name.split()[0] if lead.name else "",
                "last_name": " ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                "custom_fields": {
                    "company_name": lead.company_name,
                    "website": lead.website,
                    "specialty": lead.specialty,
                    "location": lead.location,
                    "score": str(lead.metadata.get("score", 0)),
                    # Add email content so it's visible in Smartlead UI for review
                    # Note: In automated flow, subject/body come from sequences
                    # These custom fields allow viewing generated email content in Smartlead dashboard
                    "email_subject": lead.metadata.get("email_subject", ""),
                    "email_body": lead.metadata.get("email_body", ""),
                    "lead_score": str(lead.metadata.get("score", 0)),
                    "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                }
            }
            lead_data.append(lead_entry)
        
        success = self.smartlead.add_leads_to_campaign(
            self.campaign_id,
            lead_data
        )
        
        if success:
            print(f"✅ Added {len(lead_data)} leads to campaign")
            
            # Update lead states - store ALL valuable data from Apollo search (NO additional API calls)
            # This includes: name, email, title, LinkedIn URL, employee count, organization ID, score
            # Note: Enrichment methods (enrich_person/enrich_organization) cost 1 credit each
            #       and should only be used for high-value leads (e.g., score >= 15 or "interested" status)
            current_timestamp = datetime.now().isoformat()
            
            # Compute ELM scores and assign variants if A/B testing is enabled
            for lead in scored_leads:
                # Check if lead already exists to preserve first_seen timestamp
                existing_lead = self.state.get_lead_state(lead.email)
                first_seen = existing_lead.get("first_seen", current_timestamp) if existing_lead else current_timestamp
                
                # Compute ELM route if A/B testing enabled
                elaboration_score = None
                persuasion_route = None
                variant_code = None
                
                if self.ab_manager:
                    elaboration_score, persuasion_route = self._compute_elaboration_score(lead)
                    variant = self.ab_manager.assign_variant(
                        lead.email,
                        {
                            "persuasion_route": persuasion_route,
                            "score": lead.metadata.get("score", 0)
                        }
                    )
                    variant_code = variant.to_code()
                
                self.state.set_lead_status(
                    lead.email,
                    status="idle",
                    metadata={
                        # Basic contact info
                        "name": lead.name,
                        "email": lead.email,
                        "company_name": lead.company_name,
                        "website": lead.website,
                        "location": lead.location,
                        "specialty": lead.specialty,
                        # Apollo identifiers (for tracking and future API calls)
                        "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                        "apollo_organization_id": lead.metadata.get("apollo_organization_id", ""),
                        # Person professional info
                        "title": lead.metadata.get("title", ""),
                        "linkedin_url": lead.metadata.get("linkedin_url", ""),
                        # Person contact & location
                        "person_phone": lead.metadata.get("person_phone", ""),
                        "person_city": lead.metadata.get("person_city", ""),
                        "person_state": lead.metadata.get("person_state", ""),
                        "person_country": lead.metadata.get("person_country", ""),
                        "person_postal_code": lead.metadata.get("person_postal_code", ""),
                        # Organization details
                        "organization_name": lead.metadata.get("organization_name", ""),
                        "organization_website": lead.metadata.get("organization_website", ""),
                        "organization_phone": lead.metadata.get("organization_phone", ""),
                        "employee_count": lead.metadata.get("employee_count", 0),
                        "organization_industry": lead.metadata.get("organization_industry", ""),
                        "organization_city": lead.metadata.get("organization_city", ""),
                        "organization_state": lead.metadata.get("organization_state", ""),
                        "organization_country": lead.metadata.get("organization_country", ""),
                        "organization_postal_code": lead.metadata.get("organization_postal_code", ""),
                        # Quality score
                        "score": lead.metadata.get("score", 0),
                        # Campaign tracking
                        "campaign_id": self.campaign_id,
                        # A/B Testing (if enabled)
                        "variant_code": variant_code,
                        "apollo_config_code": lead.metadata.get("apollo_config_code"),
                        "persuasion_route": persuasion_route,
                        "elaboration_score": elaboration_score,
                        # Timestamp tracking (preserve first_seen if lead already exists)
                        "first_seen": first_seen,
                        "last_updated": current_timestamp,
                        # Apollo timestamps
                        "apollo_updated_at": lead.metadata.get("apollo_updated_at", ""),
                        "organization_updated_at": lead.metadata.get("organization_updated_at", ""),
                    }
                )
                
                # Also update direct database columns for A/B testing
                if variant_code or lead.metadata.get("apollo_config_code"):
                    update_data = {}
                    if variant_code:
                        update_data["variant_code"] = variant_code
                    if lead.metadata.get("apollo_config_code"):
                        update_data["apollo_config_code"] = lead.metadata.get("apollo_config_code")
                    if persuasion_route:
                        update_data["persuasion_route"] = persuasion_route
                    if elaboration_score is not None:
                        update_data["elaboration_score"] = elaboration_score
                    
                    if update_data:
                        self.state.update_lead_state(lead.email, update_data)
        else:
            print("❌ Failed to add leads to campaign")
        
        # Step 5: Create contacts in HubSpot with full Apollo data
        print("\n5️⃣ Creating HubSpot contacts with full Apollo data...")
        for lead in scored_leads[:20]:  # Limit to avoid rate limits
            # Extract first/last name
            name_parts = lead.name.split() if lead.name else []
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            contact_id = self.crm.create_contact(
                email=lead.email,
                first_name=first_name,
                last_name=last_name,
                company=lead.company_name,
                website=lead.website,
                phone=lead.metadata.get("person_phone", ""),
                title=lead.metadata.get("title", ""),
                linkedin_url=lead.metadata.get("linkedin_url", ""),
                city=lead.metadata.get("person_city", ""),
                state=lead.metadata.get("person_state", ""),
                country=lead.metadata.get("person_country", ""),
                postal_code=lead.metadata.get("person_postal_code", ""),
                additional_properties={
                    # Store Apollo IDs for future reference
                    "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                    "apollo_organization_id": lead.metadata.get("apollo_organization_id", ""),
                    # Organization details
                    "organization_phone": lead.metadata.get("organization_phone", ""),
                    "employee_count": str(lead.metadata.get("employee_count", 0)),
                    "organization_industry": lead.metadata.get("organization_industry", ""),
                    "organization_city": lead.metadata.get("organization_city", ""),
                    "organization_state": lead.metadata.get("organization_state", ""),
                    "organization_country": lead.metadata.get("organization_country", ""),
                    # Lead scoring
                    "lead_score": str(lead.metadata.get("score", 0)),
                    "specialty": lead.specialty,
                }
            )
            
            if contact_id:
                self.state.update_lead_state(
                    lead.email,
                    {"hubspot_contact_id": contact_id}
                )
        
        print("✅ Pipeline complete!")
        print("\n📧 Emails will be sent via Smartlead sequences")
        print("🔄 Reply handling via webhook (see webhook_handler.py)")
    
    def _setup_elm_sequences(self, campaign_id: int, playbook_path: Optional[str] = None):
        """
        Set up ELM progression sequences (emails 2-4) for a campaign.
        
        Args:
            campaign_id: Campaign ID
            playbook_path: Optional path to playbook JSON
        """
        import json
        from pathlib import Path
        
        # Load playbook
        if playbook_path is None:
            playbook_path = os.path.join(
                os.path.dirname(__file__),
                "examples",
                "elm_email_playbook.json"
            )
        
        with open(playbook_path, "r") as f:
            playbook = json.load(f)
        
        progression = playbook.get("sequence_progression", {})
        from salesgpt.config import get_settings
        settings = get_settings()
        from_name = settings.smartlead_from_name
        
        # Email 2: Reciprocity
        email_2 = progression.get("email_2", {})
        if email_2.get("purpose"):
            subject = email_2.get("subject_template", "").format(
                company_name="{{company_name}}"
            )
            body = email_2.get("body_template", "").format(
                lead_name="{{first_name}}",
                company_name="{{company_name}}",
                competitor_name="{{competitor_name}}",
                from_name=from_name
            )
            self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=subject,
                body=body,
                delay_days=email_2.get("delay_days", 3)
            )
        
        # Email 3: Commitment
        email_3 = progression.get("email_3", {})
        if email_3.get("purpose"):
            subject = email_3.get("subject_template", "").format(
                company_name="{{company_name}}"
            )
            body = email_3.get("body_template", "").format(
                lead_name="{{first_name}}",
                company_name="{{company_name}}",
                from_name=from_name
            )
            self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=subject,
                body=body,
                delay_days=email_3.get("delay_days", 5)
            )
        
        # Email 4: Authority + Social Proof
        email_4 = progression.get("email_4", {})
        if email_4.get("purpose"):
            subject = email_4.get("subject_template", "").format(
                company_name="{{company_name}}"
            )
            body = email_4.get("body_template", "").format(
                lead_name="{{first_name}}",
                company_name="{{company_name}}",
                location="{{location}}",
                from_name=from_name
            )
            self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=subject,
                body=body,
                delay_days=email_4.get("delay_days", 7)
            )
    
    async def _ensure_campaign(self, use_elm_sequences: bool = False) -> int:
        """
        Ensure campaign exists, create if not.
        
        Args:
            use_elm_sequences: If True, set up ELM progression sequences (emails 2-4)
        
        Returns:
            Campaign ID
        """
        # Check if campaign exists (simplified - in production, query API)
        # For now, create new campaign
        
        # Get settings from container (will be injected via settings)
        from salesgpt.config import get_settings
        settings = get_settings()
        
        from_email = settings.smartlead_from_email
        from_name = settings.smartlead_from_name
        reply_to = settings.smartlead_reply_to or from_email
        
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
        
        # Add sequences based on mode
        if campaign_id:
            if use_elm_sequences:
                # ELM sequences: Email 1 is personalized per lead (handled in campaign)
                # Emails 2-4 follow ELM progression
                self._setup_elm_sequences(campaign_id)
            else:
                # Legacy: Add initial sequence
                # Default templates - can be moved to settings if needed
                subject = "Quick question about your clinic's visibility"
                body = (
                    "Hi {{first_name}},\n\nI noticed {{company_name}} and wanted to share "
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
                followup_subject = "Following up on visibility"
                followup_body = (
                    "Hi {{first_name}},\n\nJust wanted to follow up on my previous message. "
                    "I'd love to show you how we can improve {{company_name}}'s patient "
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
        company_name = lead_state.get("company_name", "") if lead_state else ""
        
        # Generate reply with SalesGPT
        reply_data = self.salesgpt.generate_reply(
            email_body=email_body,
            sender_name=sender_name,
            sender_email=sender_email,
            conversation_history=conversation_history,
            company_name=company_name
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
            
            # Update HubSpot to "booked" with ELM tracking
            if lead_state and lead_state.get("hubspot_contact_id"):
                self.crm.update_pipeline_stage(
                    lead_state["hubspot_contact_id"],
                    "booked"
                )
                # Optionally add custom properties for ELM tracking
                # Note: Requires HubSpot custom properties to be set up
                # self.crm.update_contact_properties(
                #     lead_state["hubspot_contact_id"],
                #     {
                #         "elm_route": lead_state.get("persuasion_route", "unknown"),
                #         "elm_elaboration_score": lead_state.get("elaboration_score", 0)
                #     }
                # )
            
            # Update state with outcome tracking
            self.state.set_lead_status(
                sender_email,
                "booked",
                metadata={
                    "reply_intent": intent,
                    "outcome": "booked",
                    "outcome_timestamp": datetime.now().isoformat()
                }
            )
            
        elif intent in ["curious", "neutral"]:
            # Inject GEMflush evidence
            if company_name:
                from salesgpt.config import get_settings
                settings = get_settings()
                competitor = settings.default_competitor
                evidence = self.visibility.get_competitor_comparison(
                    clinic_id=company_name,
                    competitor_name=competitor
                )
                
                if "error" not in evidence:
                    evidence_text = self.visibility.format_evidence_message(evidence)
                    reply_body = f"{reply_body}\n\n{evidence_text}"
            
            # Update state with outcome tracking
            self.state.set_lead_status(
                sender_email,
                "engaged",
                metadata={
                    "reply_intent": intent,
                    "outcome": "engaged",
                    "outcome_timestamp": datetime.now().isoformat()
                }
            )
            
        elif intent == "objection":
            # Handle objection with evidence
            if company_name:
                from salesgpt.config import get_settings
                settings = get_settings()
                competitor = settings.default_competitor
                evidence = self.visibility.get_competitor_comparison(
                    clinic_id=company_name,
                    competitor_name=competitor
                )
                
                if "error" not in evidence:
                    evidence_text = self.visibility.format_evidence_message(
                        evidence,
                        include_full_audit=True
                    )
                    reply_body = f"{reply_body}\n\n{evidence_text}"
            
            # Update state with outcome tracking
            self.state.set_lead_status(
                sender_email,
                "engaged",
                metadata={
                    "reply_intent": intent,
                    "outcome": "objection_handled",
                    "outcome_timestamp": datetime.now().isoformat()
                }
            )
        
        # Send reply via Smartlead
        success = self.smartlead.send_reply(thread_id, reply_body)
        
        if success:
            # Add agent reply to history
            self.state.add_conversation_message(thread_id, reply_body, sender="agent")
            print(f"✅ Reply sent successfully")
        else:
            print(f"❌ Failed to send reply")
    
    def _compute_elaboration_score(self, lead) -> Tuple[float, str]:
        """
        Compute ELM elaboration score and route selection.
        
        Based on Elaboration Likelihood Model:
        - Motivation: Title authority, decision-making power
        - Ability: Business maturity, employee count
        - Opportunity: Website presence, digital sophistication
        
        Args:
            lead: Lead object with metadata
            
        Returns:
            Tuple of (elaboration_score 0-100, route: "central" or "peripheral")
        """
        score = 0.0
        
        # Motivation (0-40 points)
        title = lead.metadata.get("title", "").lower()
        if any(word in title for word in ["owner", "ceo", "founder", "president"]):
            score += 30.0  # High authority
        elif any(word in title for word in ["director", "manager", "partner"]):
            score += 20.0  # Medium authority
        elif any(word in title for word in ["marketing", "growth", "strategy"]):
            score += 15.0  # Relevant role
        
        # Ability (0-35 points)
        emp_count = lead.metadata.get("employee_count", 0)
        if 10 <= emp_count <= 50:
            score += 25.0  # Sweet spot - mature but not too large
        elif 5 <= emp_count < 10:
            score += 15.0  # Growing
        elif emp_count > 50:
            score += 10.0  # Large org - may have bureaucracy
        
        # Opportunity (0-25 points)
        if lead.website and lead.website.startswith("http"):
            score += 25.0  # Has website = digital presence
        
        # Route selection: central if score >= 60, peripheral otherwise
        route = "central" if score >= 60.0 else "peripheral"
        
        return (min(score, 100.0), route)
    
    async def enrich_lead_fully_mocked(
        self,
        lead
    ) -> Dict:
        """
        Fully mocked enrichment - no external API calls.
        Generates competitors, competitive analysis, and email.
        
        Args:
            lead: Lead object
            
        Returns:
            Enriched lead dictionary with competitor, analysis, email, and geo_score
        """
        # 1. Generate mock competitors using CompetitorAgent
        competitors = self.competitor.generate_mock_competitors(
            company_name=lead.company_name,
            location=lead.location,
            specialty=lead.specialty,
            count=3
        )
        
        # 2. Pick best competitor to reference
        best_competitor = self.competitor.find_best_competitor(competitors)
        
        # 3. Get competitive analysis using CompetitorAgent
        analysis_obj = self.competitor.get_competitive_analysis(
            clinic_id=lead.company_name,
            competitor=best_competitor
        )
        
        # Convert to dict for SalesGPT
        analysis = {
            "lead_score": analysis_obj.lead_score,
            "competitor_score": analysis_obj.competitor_score,
            "gap": analysis_obj.gap,
            "gap_percentage": analysis_obj.gap_percentage,
            "referral_multiplier": analysis_obj.referral_multiplier,
            "competitor_name": analysis_obj.competitor_name,
            "competitor_has_kg": analysis_obj.competitor_has_kg,
            "competitor_kg_url": analysis_obj.competitor_kg_url,
            "competitor_kg_qid": analysis_obj.competitor_kg_qid
        }
        
        # 4. Compute ELM route (needed for email generation)
        elaboration_score, persuasion_route = self._compute_elaboration_score(lead)
        
        # 5. Determine disclaimer mode (all competitor/KG data is mocked)
        copy_disclaimer_mode = {
            "simulated_competitor_data": True,
            "simulated_kg_presence": True,
            "simulated_audit_data": True
        }
        
        # 6. Generate personalized email with SalesGPT using ELM route
        email = self.salesgpt.generate_initial_email(
            route=persuasion_route,
            lead_name=lead.name,
            company_name=lead.company_name,
            location=lead.location,
            specialty=lead.specialty,
            competitive_analysis=analysis,
            disclaimer_mode=copy_disclaimer_mode
        )
        
        # 7. Calculate GEO score using GEOScorer
        geo_score = self.scorer.score_lead(
            lead=lead,
            visibility_score=analysis_obj.lead_score
        )
        
        return {
            "lead": lead,
            "competitor": {
                "name": best_competitor.name,
                "location": best_competitor.location,
                "specialty": best_competitor.specialty,
                "has_kg": best_competitor.has_kg,
                "wikidata_url": best_competitor.wikidata_url,
                "wikidata_qid": best_competitor.wikidata_qid
            },
            "analysis": analysis,
            "email": email,
            "geo_score": geo_score,
            "elaboration_score": elaboration_score,
            "persuasion_route": persuasion_route,
            "copy_disclaimer_mode": copy_disclaimer_mode
        }
    
    async def run_gemflush_campaign_with_competitors(
        self,
        geography: str = "United States",
        specialty: str = "Dental",
        lead_limit: int = 100,
        target_users: int = 50,
        min_geo_score: float = 50.0
    ):
        """
        GEMflush campaign with mocked competitor research and SalesGPT email generation.
        
        Args:
            geography: Target geography
            specialty: Medical specialty filter
            lead_limit: Maximum leads to source
            target_users: Target number of users to acquire
            min_geo_score: Minimum GEO score to qualify lead
        """
        print("🎯 GEMflush User Acquisition Campaign")
        print("=" * 50)
        
        # 1. Source leads
        leads = self.apollo.search_leads(
            geography=geography,
            specialty=specialty,
            limit=lead_limit
        )
        
        if not leads:
            print("❌ No leads found")
            return
        
        print(f"✅ Found {len(leads)} leads")
        
        # 2. Score leads
        scored_leads = self.apollo.score_leads(leads)
        
        # 3. Enrich with mocked competitor data and generate emails
        print("\n🔍 Enriching leads with competitor research (mocked)...")
        enriched = []
        
        for lead in scored_leads:
            try:
                enriched_lead = await self.enrich_lead_fully_mocked(lead)
                if enriched_lead:
                    enriched.append(enriched_lead)
            except Exception as e:
                print(f"⚠️ Failed to enrich {lead.email}: {e}")
                continue
        
        print(f"✅ Enriched {len(enriched)} leads")
        
        # 4. Filter by GEO score
        qualified = [
            e for e in enriched
            if e["geo_score"] >= min_geo_score
        ]
        
        # Sort by GEO score and take top N
        qualified = sorted(qualified, key=lambda x: x["geo_score"], reverse=True)[:target_users]
        
        print(f"✅ {len(qualified)} leads qualified (GEO score >= {min_geo_score})")
        
        # 5. Create campaign with ELM sequences
        campaign_id = await self._ensure_campaign(use_elm_sequences=True)
        if not campaign_id:
            print("❌ Failed to create campaign")
            return
        
        # 6. Add leads with SalesGPT-generated emails
        print("\n📧 Adding leads to campaign with personalized emails...")
        
        # Prepare all lead data
        all_leads_data = []
        sequences_added = 0
        
        for item in qualified:
            lead = item["lead"]
            email_content = item["email"]
            
            # Add sequence with personalized email for this lead
            # Note: Smartlead may require sequences to be added before leads
            # or may support per-lead email customization through other means
            sequence_id = self.smartlead.add_sequence(
                campaign_id=campaign_id,
                subject=email_content["subject"],
                body=email_content["body"],
                delay_days=0
            )
            
            if sequence_id:
                sequences_added += 1
            
            # Prepare lead data
            lead_data = {
                "email": lead.email,
                "first_name": lead.name.split()[0] if lead.name else "",
                "last_name": " ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                "company_name": lead.company_name
            }
            all_leads_data.append(lead_data)
            
            # Store data for reply handling (including ELM routing data)
            self.state.update_lead_state(
                lead.email,
                {
                    "audit_data": item["analysis"],
                    "competitor": item["competitor"],
                    "campaign_id": campaign_id,
                    "personalized_email": email_content,
                    "sequence_id": sequence_id,
                    "persuasion_route": item.get("persuasion_route", "peripheral"),
                    "elaboration_score": item.get("elaboration_score", 0.0),
                    "copy_disclaimer_mode": item.get("copy_disclaimer_mode", {}),
                    "email_variant": "elm_initial",  # Track variant for A/B testing
                    "email_sent_timestamp": datetime.now().isoformat()
                }
            )
        
        # Add all leads to campaign
        success = self.smartlead.add_leads_to_campaign(
            campaign_id=campaign_id,
            leads=all_leads_data
        )
        
        if success:
            print(f"✅ Added {len(qualified)} leads with personalized emails")
            print(f"   Created {sequences_added} personalized email sequences")
        else:
            print("❌ Failed to add leads to campaign")
        
        # 7. Create HubSpot contacts (optional)
        for item in qualified[:20]:
            lead = item["lead"]
            self.crm.create_contact(
                email=lead.email,
                first_name=lead.name.split()[0] if lead.name else "",
                last_name=" ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                company=lead.company_name,
                website=lead.website
            )
        
        print(f"\n📊 Campaign Summary:")
        print(f"   - Leads: {len(qualified)}")
        print(f"   - Emails: SalesGPT-generated with competitor references")
        print(f"   - LLM Cost: ~${len(qualified) * 0.01:.2f} (GPT-3.5)")
        print(f"   - Reply Handling: SalesGPT (existing)")


async def main():
    """Main entry point for CLI execution."""
    import argparse
    from salesgpt.config import get_settings
    from salesgpt.container import ServiceContainer
    
    # Load settings
    settings = get_settings()
    
    parser = argparse.ArgumentParser(description="A.S.S.C.H. Assembly Orchestrator")
    parser.add_argument(
        "--campaign",
        type=str,
        choices=["daily", "gemflush-competitors"],
        default="daily",
        help="Campaign type to run"
    )
    parser.add_argument(
        "--geography",
        type=str,
        default=settings.default_geography,
        help="Target geography"
    )
    parser.add_argument(
        "--specialty",
        type=str,
        default=settings.default_specialty,
        help="Medical specialty"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum leads to process"
    )
    parser.add_argument(
        "--target-users",
        type=int,
        default=settings.gemflush_campaign_target_users,
        help="Target number of users (for gemflush-competitors campaign)"
    )
    parser.add_argument(
        "--min-geo-score",
        type=float,
        default=settings.gemflush_min_geo_score,
        help="Minimum GEO score to qualify lead (for gemflush-competitors campaign)"
    )
    
    args = parser.parse_args()
    
    # Initialize container and get orchestrator
    container = ServiceContainer(settings)
    orchestrator = container.orchestrator
    
    if args.campaign == "gemflush-competitors":
        await orchestrator.run_gemflush_campaign_with_competitors(
            geography=args.geography,
            specialty=args.specialty,
            lead_limit=args.limit,
            target_users=args.target_users,
            min_geo_score=args.min_geo_score
        )
    else:
        await orchestrator.run_daily_pipeline(
            geography=args.geography,
            specialty=args.specialty,
            lead_limit=args.limit
        )


if __name__ == "__main__":
    asyncio.run(main())
