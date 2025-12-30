"""
SalesGPT Wrapper - Reply agent model with context memory.

Integrates with existing SalesGPT to handle email replies.
Checks sentiment and intent, returns appropriate responses.
"""
import os
import json
from typing import Dict, List, Optional, Literal
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
        
        # Initialize SalesGPT API instance
        self.sales_api = SalesGPTAPI(
            config_path=self.config_path,
            verbose=verbose,
            model_name=self.model_name,
            use_tools=True,
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
        clinic_name: Optional[str] = None,
        evidence_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate a contextual reply using SalesGPT.
        
        Args:
            email_body: Incoming email body
            sender_name: Sender's name
            sender_email: Sender's email
            conversation_history: Previous conversation messages
            clinic_name: Clinic name for personalization
            evidence_data: GEMflush evidence data if available
            
        Returns:
            Dictionary with 'body', 'intent', and 'action' keys
        """
        # Add user message to conversation
        self.sales_api.sales_agent.human_step(email_body)
        
        # Determine conversation stage
        self.sales_api.sales_agent.determine_conversation_stage()
        
        # Classify intent
        intent = self.classify_intent(email_body, conversation_history)
        
        # Generate reply
        import asyncio
        response = asyncio.run(self.sales_api.do())
        
        reply_body = response.get("response", "")
        
        # Inject evidence if available and intent is curious/neutral
        if evidence_data and intent in ["curious", "neutral"]:
            evidence_text = self._format_evidence(evidence_data)
            reply_body = f"{reply_body}\n\n{evidence_text}"
        
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
