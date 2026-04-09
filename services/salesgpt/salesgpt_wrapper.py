"""
SalesGPT Wrapper - Reply agent model with context memory.

Integrates with existing SalesGPT to handle email replies.
Checks sentiment and intent, returns appropriate responses.
"""
import os
import json
from typing import Dict, List, Optional, Literal
from pathlib import Path
from salesgpt.agents import SalesGPT
from salesgpt.salesgptapi import SalesGPTAPI
from langchain_community.chat_models import ChatLiteLLM


class SalesGPTWrapper:
    """
    Wrapper around SalesGPT for email reply handling.
    
    Critical design: Atomic service - only operates when context exists.
    Single outcome: Generate contextually appropriate replies.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        model_name: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize SalesGPT Wrapper.
        
        Args:
            config_path: Path to agent config JSON
            model_name: LLM model name (defaults to GPT_MODEL env var)
            verbose: Enable verbose logging
        """
        self.config_path = config_path or os.getenv(
            "SALESGPT_CONFIG_PATH",
            "examples/example_agent_setup.json"
        )
        self.model_name = model_name or os.getenv("GPT_MODEL", "gpt-3.5-turbo-0613")
        self.verbose = verbose
        
        # Product-catalog RAG tools load Chroma + OpenAIEmbeddings (fragile with some openai/langchain-openai pairs).
        # Email reply flows do not need them; enable explicitly with SALESGPT_USE_TOOLS=true.
        use_tools = os.getenv("SALESGPT_USE_TOOLS", "false").lower() == "true"
        
        # Initialize SalesGPT API instance
        self.sales_api = SalesGPTAPI(
            config_path=self.config_path,
            verbose=verbose,
            model_name=self.model_name,
            use_tools=use_tools,
        )
    
    def classify_intent(
        self,
        email_body: str,
        conversation_history: List[str]
    ) -> Literal["interested", "objection", "curious", "neutral", "not_interested"]:
        """
        Classify email intent based on content.
        
        Args:
            email_body: Email body text
            conversation_history: Previous conversation messages
            
        Returns:
            Intent classification
        """
        # Use SalesGPT to analyze intent
        # In a real implementation, you'd use a separate classification chain
        # For now, simple keyword-based classification
        
        body_lower = email_body.lower()
        
        # Positive indicators
        if any(word in body_lower for word in ["yes", "interested", "tell me more", "schedule", "book", "call"]):
            return "interested"
        
        # Objection indicators
        if any(word in body_lower for word in ["expensive", "cost", "price", "budget", "can't afford", "too much"]):
            return "objection"
        
        # Curious indicators
        if any(word in body_lower for word in ["how", "what", "explain", "more info", "details"]):
            return "curious"
        
        # Negative indicators
        if any(word in body_lower for word in ["not interested", "unsubscribe", "remove", "stop"]):
            return "not_interested"
        
        return "neutral"
    
    def generate_reply(
        self,
        email_body: str,
        sender_name: str,
        sender_email: str,
        conversation_history: List[str],
        company_name: Optional[str] = None,
        evidence_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate a contextual reply using SalesGPT.
        
        Args:
            email_body: Incoming email body
            sender_name: Sender's name
            sender_email: Sender's email
            conversation_history: Previous conversation messages
            company_name: Company name for personalization
            evidence_data: GEMflush evidence data if available
            
        Returns:
            Dictionary with 'body', 'intent', and 'action' keys
        """
        # Inject background knowledge into the conversation history if not already present
        # This helps the LLM "know" the context before responding
        if company_name and not any(company_name in msg for msg in self.sales_api.sales_agent.conversation_history):
            background_msg = f"System: We are contacting {sender_name} from {company_name}."
            if evidence_data:
                evidence_text = self._format_evidence(evidence_data)
                background_msg += f" Current visibility audit: {evidence_text}"
            self.sales_api.sales_agent.conversation_history.append(background_msg)

        # Add user message to conversation
        self.sales_api.sales_agent.human_step(email_body)
        
        # Determine conversation stage
        self.sales_api.sales_agent.determine_conversation_stage()
        
        # Classify intent
        intent = self.classify_intent(email_body, conversation_history)
        
        # Generate reply
        response = self._run_async_safely(self.sales_api.do())
        
        reply_body = response.get("response", "")
        
        # Determine action based on intent
        action = "none"
        if intent == "interested":
            action = "send_booking_link"
        elif intent == "objection":
            action = "send_evidence"
        elif intent == "curious":
            action = "provide_info"
        
        return {
            "body": reply_body,
            "intent": intent,
            "action": action,
            "conversation_stage": response.get("conversational_stage", ""),
        }
    
    def _run_async_safely(self, coro):
        """
        Run async coroutine safely, handling both sync and async contexts.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            Result of the coroutine
        """
        import asyncio
        import inspect
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're already in an async context - create a task
            # Note: This is a workaround for testing - in production, this method
            # should ideally be async itself
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(coro)
    
    def _format_evidence(self, evidence_data: Dict) -> str:
        """
        Format GEMflush evidence data for insertion into reply.
        
        Args:
            evidence_data: Evidence dictionary from GEMflush
            
        Returns:
            Formatted evidence text
        """
        competitor = evidence_data.get("competitor_name", "competitors")
        delta = evidence_data.get("delta_score", 0)
        
        return (
            f"Quick insight: Your clinic shows {abs(delta)}% "
            f"{'more' if delta > 0 else 'less'} visibility than {competitor} "
            f"in GPT-based patient searches. I can show you the full audit "
            f"on a short call."
        )
    
    def should_send_booking_link(self, intent: str) -> bool:
        """
        Determine if booking link should be sent.
        
        Args:
            intent: Classified intent
            
        Returns:
            True if booking link should be sent
        """
        return intent == "interested"
    
    def get_conversation_context(self, thread_id: str) -> List[str]:
        """
        Retrieve conversation context for a thread.
        
        Args:
            thread_id: Email thread ID
            
        Returns:
            List of conversation messages
        """
        # In a real implementation, retrieve from state/ or database
        # For now, return empty list
        return []
    
    def generate_initial_email_with_competitor(
        self,
        lead_name: str,
        company_name: str,
        location: str,
        specialty: str,
        competitive_analysis: Dict
    ) -> Dict[str, str]:
        """
        Generate personalized initial cold email using SalesGPT.
        Email mentions specific local competitor with KG presence.
        
        Args:
            lead_name: Lead's name
            company_name: Company name
            location: Location/geography
            specialty: Medical specialty
            competitive_analysis: Competitive analysis dictionary
            
        Returns:
            Dictionary with 'subject', 'body', and 'competitor_referenced' keys
        """
        import asyncio
        
        # Build context from competitive analysis
        competitor_context = f"""
        Lead Information:
        - Name: {lead_name}
        - Company: {company_name}
        - Location: {location}
        - Specialty: {specialty}
        
        Competitive Analysis:
        - Their AI Visibility Score: {competitive_analysis['lead_score']}/100
        - {competitive_analysis['competitor_name']} Visibility Score: {competitive_analysis['competitor_score']}/100
        - Visibility Gap: {competitive_analysis['gap_percentage']}%
        - {competitive_analysis['competitor_name']} is getting approximately {competitive_analysis['referral_multiplier']}x more referrals from ChatGPT
        - Competitor has Wikidata Knowledge Graph: {competitive_analysis['competitor_has_kg']}
        """
        
        # Seed conversation at Introduction stage
        self.sales_api.sales_agent.seed_agent()
        
        # Inject competitor context
        prompt = f"""
        {competitor_context}
        
        Generate a personalized cold email that:
        1. Mentions {competitive_analysis['competitor_name']} specifically as a local competitor
        2. Notes they have {'Wikidata knowledge graph presence' if competitive_analysis['competitor_has_kg'] else 'significantly better AI visibility'}
        3. States they're getting approximately {competitive_analysis['referral_multiplier']}x more patient referrals from ChatGPT
        4. Suggests publishing to Wikidata knowledge graph with GEMflush to compete
        5. Keep it concise (150-200 words)
        6. Professional but direct
        7. Reference the specific location ({location})
        8. Make it personal and specific to their situation
        
        Generate the email body only (no subject line needed).
        """
        
        # Add to conversation history
        self.sales_api.sales_agent.conversation_history.append(prompt)
        
        # Generate email
        response = self._run_async_safely(self.sales_api.do())
        email_body = response.get("response", "")
        
        # Clean up response (remove any END_OF_TURN tags)
        email_body = email_body.replace("<END_OF_TURN>", "").replace("<END_OF_CALL>", "").strip()
        
        # Generate subject line
        subject = f"{lead_name.split()[0] if lead_name else 'Hi'}, {competitive_analysis['competitor_name']} is getting {competitive_analysis['referral_multiplier']}x more ChatGPT referrals"
        
        return {
            "subject": subject,
            "body": email_body,
            "competitor_referenced": competitive_analysis['competitor_name']
        }
    
    def _load_playbook(self, playbook_path: Optional[str] = None) -> Dict:
        """
        Load ELM email playbook configuration.
        
        Args:
            playbook_path: Path to playbook JSON (defaults to examples/elm_email_playbook.json)
            
        Returns:
            Playbook dictionary
        """
        if playbook_path is None:
            playbook_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "examples",
                "elm_email_playbook.json"
            )
        
        with open(playbook_path, "r") as f:
            return json.load(f)
    
    def _inject_disclaimer(
        self,
        email_body: str,
        route_config: Dict,
        disclaimer_mode: Dict
    ) -> str:
        """
        Inject appropriate disclaimers based on disclaimer mode.
        
        Args:
            email_body: Email body text
            route_config: Route-specific configuration from playbook
            disclaimer_mode: Dictionary with disclaimer flags
            
        Returns:
            Email body with disclaimers appended
        """
        disclaimers = []
        templates = route_config.get("disclaimer_templates", {})
        
        if disclaimer_mode.get("simulated_competitor_data"):
            disclaimers.append(templates.get("simulated_competitor", ""))
        
        if disclaimer_mode.get("simulated_kg_presence"):
            disclaimers.append(templates.get("simulated_kg", ""))
        
        if disclaimer_mode.get("simulated_audit_data"):
            disclaimers.append(templates.get("simulated_audit", ""))
        
        # Filter out empty disclaimers and join
        disclaimers = [d for d in disclaimers if d]
        
        if disclaimers:
            disclaimer_text = "\n\n" + " ".join(disclaimers)
            return email_body + disclaimer_text
        
        return email_body
    
    def generate_initial_email(
        self,
        route: str,
        lead_name: str,
        company_name: str,
        location: str,
        specialty: str,
        competitive_analysis: Dict,
        disclaimer_mode: Dict,
        playbook_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate ELM-compliant initial cold email using route + playbook.
        
        Args:
            route: "central" or "peripheral"
            lead_name: Lead's name
            company_name: Company name
            location: Location/geography
            specialty: Medical specialty
            competitive_analysis: Competitive analysis dictionary
            disclaimer_mode: Dictionary with disclaimer flags
            playbook_path: Optional path to playbook JSON
            
        Returns:
            Dictionary with 'subject', 'body', and 'route' keys
        """
        import asyncio
        
        # Load playbook
        playbook = self._load_playbook(playbook_path)
        route_config = playbook["routes"].get(route, playbook["routes"]["peripheral"])
        
        # Build context from competitive analysis
        competitor_context = f"""
        Lead Information:
        - Name: {lead_name}
        - Company: {company_name}
        - Location: {location}
        - Specialty: {specialty}
        
        Competitive Analysis:
        - Their AI Visibility Score: {competitive_analysis.get('lead_score', 0)}/100
        - {competitive_analysis.get('competitor_name', 'Competitor')} Visibility Score: {competitive_analysis.get('competitor_score', 0)}/100
        - Visibility Gap: {competitive_analysis.get('gap_percentage', 0)}%
        - {competitive_analysis.get('competitor_name', 'Competitor')} is getting approximately {competitive_analysis.get('referral_multiplier', 1.0)}x more referrals from ChatGPT
        - Competitor has Wikidata Knowledge Graph: {competitive_analysis.get('competitor_has_kg', False)}
        """
        
        # Add Wikidata-specific context if present
        if competitive_analysis.get("wikidata_qid"):
            qid = competitive_analysis["wikidata_qid"]
            missing_props = competitive_analysis.get("missing_properties", [])
            missing_text = ", ".join(missing_props[:3])
            if len(missing_props) > 3:
                missing_text += f", and {len(missing_props) - 3} more"
            
            wikidata_context = f"""
        
        Wikidata Entity Context:
        - {company_name} has Wikidata entity {qid} (https://www.wikidata.org/wiki/{qid})
        - Profile completeness: {competitive_analysis.get('lead_score', 0)}%
        - Missing properties: {missing_text if missing_props else 'None'}
        - These gaps reduce AI discoverability in ChatGPT, Claude, and Perplexity
        - GemFlush can help complete the Wikidata profile to improve AI visibility
        """
            competitor_context += wikidata_context
        
        # Build persuasion principles instructions
        principles = route_config.get("persuasion_principles", {})
        principle_instructions = []
        
        if principles.get("authority", {}).get("enabled"):
            cues = principles["authority"].get("cues", [])
            principle_instructions.append(f"Authority cues: {', '.join(cues)}")
        
        if principles.get("social_proof", {}).get("enabled"):
            cues = principles["social_proof"].get("cues", [])
            principle_instructions.append(f"Social proof cues: {', '.join(cues)}")
        
        if principles.get("loss_aversion", {}).get("enabled"):
            cues = principles["loss_aversion"].get("cues", [])
            principle_instructions.append(f"Loss aversion: {', '.join(cues)}")
        
        if principles.get("reciprocity", {}).get("enabled"):
            cues = principles["reciprocity"].get("cues", [])
            principle_instructions.append(f"Reciprocity: {', '.join(cues)}")
        
        if principles.get("commitment", {}).get("enabled"):
            cues = principles["commitment"].get("cues", [])
            principle_instructions.append(f"Commitment: {', '.join(cues)}")
        
        cognitive_fluency = principles.get("cognitive_fluency", {})
        if cognitive_fluency.get("enabled"):
            rules = cognitive_fluency.get("rules", [])
            principle_instructions.append(f"Cognitive fluency: {', '.join(rules)}")
        
        # Build structure rules
        structure_rules = "\n".join([f"- {rule}" for rule in route_config.get("structure_rules", [])])
        
        # Build disclaimer requirements
        allowed_claims = route_config.get("allowed_claims", {})
        disclaimer_requirements = []
        if allowed_claims.get("must_say_estimate"):
            disclaimer_requirements.append("MUST use words like 'estimate' or 'estimated' when referring to data")
        if allowed_claims.get("must_say_simulated"):
            disclaimer_requirements.append("MUST use words like 'simulated' or 'preview' when referring to audit data")
        if allowed_claims.get("must_say_preview"):
            disclaimer_requirements.append("MUST indicate this is a 'preview' or 'preliminary' analysis")
        
        prohibited = allowed_claims.get("prohibited_claims", [])
        if prohibited:
            disclaimer_requirements.append(f"DO NOT use these words: {', '.join(prohibited)}")
        
        # Build prompt
        prompt = f"""
        {competitor_context}
        
        Generate a personalized cold email following the {route.upper()} ROUTE of the Elaboration Likelihood Model.
        
        ROUTE-SPECIFIC STRUCTURE RULES:
        {structure_rules}
        
        PERSUASION PRINCIPLES TO APPLY:
        {chr(10).join(principle_instructions)}
        
        DISCLAIMER REQUIREMENTS (CRITICAL - MUST FOLLOW):
        {chr(10).join(disclaimer_requirements)}
        
        SPECIFIC REQUIREMENTS:
        1. Mention {competitive_analysis.get('competitor_name', 'the competitor')} specifically as a local competitor
        2. Note they have {'Wikidata knowledge graph presence' if competitive_analysis.get('competitor_has_kg') else 'significantly better AI visibility'}
        3. State they're getting approximately {competitive_analysis.get('referral_multiplier', 1.0)}x more patient referrals from ChatGPT
        4. Reference the specific location ({location})
        5. Make it personal and specific to their situation
        6. Professional but direct tone
        {f"7. Acknowledge their existing Wikidata entity ({competitive_analysis.get('wikidata_qid')}) - shows they understand knowledge graphs" if competitive_analysis.get('wikidata_qid') else ""}
        {f"8. Highlight missing properties ({', '.join(competitive_analysis.get('missing_properties', [])[:3])}) that impact AI discoverability" if competitive_analysis.get('missing_properties') else ""}
        
        Generate the email body only (no subject line needed).
        Keep it concise and follow the {route} route structure rules exactly.
        """
        
        # Seed conversation at Introduction stage
        self.sales_api.sales_agent.seed_agent()
        
        # Add prompt to conversation history
        self.sales_api.sales_agent.conversation_history.append(prompt)
        
        # Generate email
        response = self._run_async_safely(self.sales_api.do())
        email_body = response.get("response", "")
        
        # Clean up response
        email_body = email_body.replace("<END_OF_TURN>", "").replace("<END_OF_CALL>", "").strip()
        
        # Inject disclaimers
        email_body = self._inject_disclaimer(email_body, route_config, disclaimer_mode)
        
        # Generate subject line from patterns
        subject_patterns = route_config.get("subject_patterns", [])
        if subject_patterns:
            # Use first pattern as default, replace placeholders
            subject = subject_patterns[0].format(
                lead_name=lead_name.split()[0] if lead_name else "Hi",
                competitor_name=competitive_analysis.get('competitor_name', 'competitor'),
                multiplier=competitive_analysis.get('referral_multiplier', 1.0),
                location=location,
                company_name=company_name,
                gap=competitive_analysis.get('gap_percentage', 0)
            )
        else:
            # Fallback subject
            subject = f"{lead_name.split()[0] if lead_name else 'Hi'}, {competitive_analysis.get('competitor_name', 'competitor')} is getting {competitive_analysis.get('referral_multiplier', 1.0)}x more ChatGPT referrals"
        
        return {
            "subject": subject,
            "body": email_body,
            "route": route,
            "competitor_referenced": competitive_analysis.get('competitor_name', '')
        }