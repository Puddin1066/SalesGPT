"""
Background Queue Builder.

Continuously sources leads, generates emails, creates HubSpot entries.
Runs as background worker to keep review queue populated.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
import os
from services.apollo.apollo_agent import ApolloAgent, Lead
from services.salesgpt.salesgpt_wrapper import SalesGPTWrapper
from services.crm.hubspot_agent import HubSpotAgent
from services.analytics import ABTestManager, ApolloABManager
from services.competitor.competitor_agent import CompetitorAgent
from services.visibility.gemflush_agent import GEMflushAgent
from services.scoring.geo_scorer import GEOScorer
from state.state_manager import StateManager
from services.segmentation.labeling import infer_market, infer_persona
from services.outbound.landing_urls import build_market_landing_url


class BackgroundQueueBuilder:
    """
    Background worker that continuously builds email review queue.
    
    Continuously sources leads, generates personalized emails with A/B testing,
    creates HubSpot entries, and stores everything in database for manual review.
    """
    
    def __init__(
        self,
        apollo: ApolloAgent,
        salesgpt: SalesGPTWrapper,
        hubspot: HubSpotAgent,
        state_manager: StateManager,
        ab_manager: ABTestManager,
        apollo_ab: ApolloABManager,
        competitor: Optional[CompetitorAgent] = None,
        visibility: Optional[GEMflushAgent] = None,
        scorer: Optional[GEOScorer] = None
    ):
        """
        Initialize Background Queue Builder.
        
        Args:
            apollo: Apollo agent for lead sourcing
            salesgpt: SalesGPT wrapper for email generation
            hubspot: HubSpot agent for CRM operations
            state_manager: State manager for database operations
            ab_manager: AB test manager for email variants
            apollo_ab: Apollo AB manager for search configs
            competitor: Competitor agent (optional, will create if None)
            visibility: GEMflush agent (optional, will create if None)
            scorer: GEO scorer (optional, will create if None)
        """
        self.apollo = apollo
        self.salesgpt = salesgpt
        self.hubspot = hubspot
        self.state = state_manager
        self.ab_manager = ab_manager
        self.apollo_ab = apollo_ab
        
        # Initialize optional services if not provided
        if visibility is None:
            from salesgpt.config import get_settings
            settings = get_settings()
            visibility = GEMflushAgent(
                api_key=settings.gemflush_api_key,
                api_base_url=settings.gemflush_api_url,
                use_real_api=settings.gemflush_use_real_api
            )
        
        if competitor is None:
            competitor = CompetitorAgent(visibility_agent=visibility)
        
        if scorer is None:
            scorer = GEOScorer()
        
        self.competitor = competitor
        self.visibility = visibility
        self.scorer = scorer
    
    async def run(
        self,
        geography: str,
        specialty: str,
        batch_size: int = 50,
        min_score: int = 10
    ):
        """
        Run continuous queue building loop.
        
        Args:
            geography: Target geography (e.g., "New York, NY")
            specialty: Medical specialty filter
            batch_size: Number of leads to process per batch
            min_score: Minimum lead score to process
        """
        print(f"🚀 Background Queue Builder Started")
        print(f"📍 Geography: {geography}")
        print(f"🏥 Specialty: {specialty}")
        print(f"📊 Batch Size: {batch_size}")
        print(f"🎯 Min Score: {min_score}\n")
        
        iteration = 0
        
        while True:
            iteration += 1
            print(f"\n━━━ Batch #{iteration} ━━━\n")
            
            # Check queue size
            pending_count = self.state.count_leads_by_status("pending_review")
            
            if pending_count < 20:
                print(f"📋 Queue low ({pending_count}), fetching leads...")
                
                # Get next Apollo config to test
                apollo_config = self.apollo_ab.get_next_config_to_test()
                params = apollo_config.to_apollo_params()
                
                print(f"🔍 Testing Apollo Config: {apollo_config.to_code()}")
                print(f"   - Geography: {apollo_config.geography_strategy.value}")
                print(f"   - Employee Range: {apollo_config.employee_range.value}")
                print(f"   - Title Strategy: {apollo_config.title_strategy.value}")
                print(f"   - Website Required: {apollo_config.require_website}")
                
                # Search Apollo with config
                leads = self.apollo.search_leads(
                    geography=apollo_config.geography_value or geography,
                    specialty=apollo_config.specialty or specialty,
                    min_employees=params["min_employees"],
                    max_employees=params["max_employees"],
                    has_website=params["has_website"],
                    limit=batch_size
                )
                
                if not leads:
                    print("⚠️  No leads found. Waiting 5 minutes...")
                    await asyncio.sleep(300)
                    continue
                
                print(f"✅ Found {len(leads)} leads")
                
                # Score leads
                scored_leads = self.apollo.score_leads(leads)
                
                # Process each lead
                processed = 0
                for lead in scored_leads:
                    if lead.metadata.get("score", 0) < min_score:
                        continue
                    
                    try:
                        # Process lead: generate email, create HubSpot, store
                        await self._process_lead(lead, apollo_config)
                        processed += 1
                    except Exception as e:
                        print(f"⚠️  Error processing {lead.email}: {e}")
                        continue
                
                print(f"✅ Processed {processed} leads, added to queue")
            else:
                print(f"✅ Queue sufficient ({pending_count} pending). Waiting 5 minutes...")
            
            # Wait before next iteration
            await asyncio.sleep(300)  # 5 minutes
    
    async def _process_lead(
        self,
        lead: Lead,
        apollo_config
    ) -> Optional[Dict]:
        """
        Process single lead: generate email, create HubSpot entry, store.
        
        Args:
            lead: Lead object from Apollo
            apollo_config: ApolloSearchConfig used to source this lead
            
        Returns:
            Dictionary with processed lead data or None
        """
        # 1. Compute ELM route
        elaboration_score, persuasion_route = self._compute_elaboration_score(lead)
        
        # 2. Generate competitor data
        competitors = self.competitor.generate_mock_competitors(
            company_name=lead.company_name,
            location=lead.location,
            specialty=lead.specialty,
            count=3
        )
        
        best_competitor = self.competitor.find_best_competitor(competitors)
        
        # 3. Get competitive analysis
        analysis_obj = self.competitor.get_competitive_analysis(
            clinic_id=lead.company_name,
            competitor=best_competitor
        )
        
        # Convert to dict
        evidence = {
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
        
        # 4. Assign email variant
        variant = self.ab_manager.assign_variant(
            lead.email,
            {
                "persuasion_route": persuasion_route,
                "score": lead.metadata.get("score", 0)
            }
        )
        
        # 5. Generate email with variant
        lead_dict = {
            "name": lead.name,
            "company_name": lead.company_name,
            "location": lead.location,
            "specialty": lead.specialty,
            "email": lead.email,
            "website": lead.website
        }

        # Segmentation labels (market + persona)
        title = lead.metadata.get("title", "") if lead.metadata else ""
        market = infer_market(lead.specialty, title=title, company_name=lead.company_name)
        persona = infer_persona(title)

        # Landing URL for Email 2+ (Email 1 should remain linkless for deliverability)
        landing_base = os.getenv("GEMFLUSH_LANDING_BASE_URL", "https://www.gemflush.com")
        utm_campaign = f"cold_{market}_{(lead.specialty or 'niche').lower().replace(' ', '_')}"
        landing_url = build_market_landing_url(
            base_url=landing_base,
            market=market,
            utm_source="cold_email",
            utm_campaign=utm_campaign,
            utm_content=email["variant_code"],
        )
        
        competitor_dict = {
            "name": best_competitor.name,
            "location": best_competitor.location,
            "specialty": best_competitor.specialty,
            "has_kg": best_competitor.has_kg,
            "wikidata_url": best_competitor.wikidata_url,
            "wikidata_qid": best_competitor.wikidata_qid
        }
        
        # 5. Generate email with variant (must be done before HubSpot contact creation)
        email = self.ab_manager.generate_email_from_variant(
            variant=variant,
            salesgpt_wrapper=self.salesgpt,
            lead=lead_dict,
            evidence=evidence,
            competitor=competitor_dict
        )
        
        # 6. Create HubSpot contact with email content
        name_parts = lead.name.split() if lead.name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        contact_id = self.hubspot.create_contact(
            email=lead.email,
            first_name=first_name,
            last_name=last_name,
            company=lead.company_name,
            website=lead.website,
            phone=lead.metadata.get("person_phone"),
            title=lead.metadata.get("title"),
            linkedin_url=lead.metadata.get("linkedin_url"),
            city=lead.metadata.get("person_city"),
            state=lead.metadata.get("person_state"),
            country=lead.metadata.get("person_country"),
            postal_code=lead.metadata.get("person_postal_code"),
            additional_properties={
                # Apollo data
                "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                "apollo_organization_id": lead.metadata.get("apollo_organization_id", ""),
                # Lead scoring
                "lead_score": str(lead.metadata.get("score", 0)),
                "specialty": lead.specialty,
                "employee_count": str(lead.metadata.get("employee_count", 0)),
                # Email content (custom properties for HubSpot UI)
                "email_subject": email["subject"],
                "email_body": email["body"],
                "email_variant": email["variant_code"],
                "persuasion_route": persuasion_route,
                "elaboration_score": str(elaboration_score),
            }
        )
        
        # 7. Create HubSpot deal
        deal_id = None
        if contact_id:
            deal_id = self.hubspot.create_deal(
                contact_id=contact_id,
                deal_name=f"{lead.company_name} - GEMflush Implementation",
                amount=5000.00,
                stage="idle"
            )
        
        # 8. Store in database with all metadata
        self.state.set_lead_status(
            lead.email,
            "pending_review",
            metadata={
                # Basic info
                "name": lead.name,
                "email": lead.email,
                "company_name": lead.company_name,
                "website": lead.website,
                "location": lead.location,
                "specialty": lead.specialty,
                "market": market,
                "persona": persona,
                "landing_url": landing_url,
                # Apollo data
                "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                "apollo_organization_id": lead.metadata.get("apollo_organization_id", ""),
                "title": lead.metadata.get("title", ""),
                "linkedin_url": lead.metadata.get("linkedin_url", ""),
                "person_phone": lead.metadata.get("person_phone", ""),
                "person_city": lead.metadata.get("person_city", ""),
                "person_state": lead.metadata.get("person_state", ""),
                "person_country": lead.metadata.get("person_country", ""),
                "person_postal_code": lead.metadata.get("person_postal_code", ""),
                "organization_name": lead.metadata.get("organization_name", ""),
                "organization_website": lead.metadata.get("organization_website", ""),
                "organization_phone": lead.metadata.get("organization_phone", ""),
                "employee_count": lead.metadata.get("employee_count", 0),
                "organization_industry": lead.metadata.get("organization_industry", ""),
                "organization_city": lead.metadata.get("organization_city", ""),
                "organization_state": lead.metadata.get("organization_state", ""),
                "organization_country": lead.metadata.get("organization_country", ""),
                "organization_postal_code": lead.metadata.get("organization_postal_code", ""),
                # Scoring
                "score": lead.metadata.get("score", 0),
                # A/B testing
                "variant_code": email["variant_code"],
                "apollo_config_code": apollo_config.to_code(),
                "persuasion_route": persuasion_route,
                "elaboration_score": elaboration_score,
                # Email content
                "email_subject": email["subject"],
                "email_body": email["body"],
                "email_generated_at": datetime.now().isoformat(),
                "email_sequence_step": 1,
                # Evidence
                "evidence": evidence,
                "competitor": competitor_dict,
                # HubSpot
                "hubspot_contact_id": contact_id,
                "hubspot_deal_id": deal_id,
                # Timestamps
                "first_seen": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        )
        
        # Also update direct columns in database
        self.state.update_lead_state(
            lead.email,
            {
                "variant_code": email["variant_code"],
                "apollo_config_code": apollo_config.to_code(),
                "persuasion_route": persuasion_route,
                "elaboration_score": elaboration_score,
                "email_subject": email["subject"],
                "email_body": email["body"],
                "email_generated_at": datetime.now(),
                "market": market,
                "persona": persona,
                "hubspot_contact_id": contact_id
            }
        )
        
        return {
            "email": lead.email,
            "variant_code": email["variant_code"],
            "apollo_config_code": apollo_config.to_code(),
            "hubspot_contact_id": contact_id
        }
    
    def _compute_elaboration_score(self, lead: Lead) -> tuple:
        """
        Compute ELM elaboration score and route selection.
        
        Args:
            lead: Lead object with metadata
            
        Returns:
            Tuple of (elaboration_score 0-100, route: "central" or "peripheral")
        """
        score = 0.0
        
        # Motivation (0-40 points)
        title = lead.metadata.get("title", "").lower()
        if any(word in title for word in ["owner", "ceo", "founder", "president"]):
            score += 30.0
        elif any(word in title for word in ["director", "manager", "partner"]):
            score += 20.0
        elif any(word in title for word in ["marketing", "growth", "strategy"]):
            score += 15.0
        
        # Ability (0-35 points)
        emp_count = lead.metadata.get("employee_count", 0)
        if 10 <= emp_count <= 50:
            score += 25.0
        elif 5 <= emp_count < 10:
            score += 15.0
        elif emp_count > 50:
            score += 10.0
        
        # Opportunity (0-25 points)
        if lead.website and lead.website.startswith("http"):
            score += 25.0
        
        # Route selection
        route = "central" if score >= 60.0 else "peripheral"
        
        return (min(score, 100.0), route)

