"""
State Manager - Conversation and lead state persistence.

Manages conversation history and lead states using SQLite database.
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from salesgpt.models.database import Lead, Conversation, ConversationMessage
from salesgpt.db.connection import DatabaseManager


class StateManager:
    """
    Manages conversation and lead state persistence using SQLite database.
    
    Replaces JSON file-based storage with proper database persistence.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize State Manager.
        
        Args:
            db_manager: DatabaseManager instance for database access
        """
        self.db_manager = db_manager
    
    def get_conversation_history(self, thread_id: str) -> List[str]:
        """
        Get conversation history for a thread.
        
        Args:
            thread_id: Email thread ID
            
        Returns:
            List of conversation messages in format "SENDER: message"
        """
        try:
            with self.db_manager.session() as session:
                conversation = session.query(Conversation).filter_by(thread_id=thread_id).first()
                
                if not conversation:
                    return []
                
                messages = session.query(ConversationMessage).filter_by(
                    conversation_id=conversation.id
                ).order_by(ConversationMessage.created_at).all()
                
                return [f"{msg.sender.upper()}: {msg.content}" for msg in messages]
        except SQLAlchemyError as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def add_conversation_message(
        self,
        thread_id: str,
        message: str,
        sender: str = "user",
        lead_email: Optional[str] = None
    ):
        """
        Add a message to conversation history.
        
        Args:
            thread_id: Email thread ID
            message: Message content
            sender: "user" or "agent"
            lead_email: Optional lead email to associate conversation with lead
        """
        try:
            with self.db_manager.session() as session:
                # Get or create conversation
                conversation = session.query(Conversation).filter_by(thread_id=thread_id).first()
                
                if not conversation:
                    # Find lead by email if provided
                    lead_id = None
                    if lead_email:
                        lead = session.query(Lead).filter_by(email=lead_email).first()
                        if lead:
                            lead_id = lead.id
                    
                    conversation = Conversation(
                        thread_id=thread_id,
                        lead_id=lead_id,
                        status="active"
                    )
                    session.add(conversation)
                    session.flush()  # Get conversation.id
                
                # Add message
                msg = ConversationMessage(
                    conversation_id=conversation.id,
                    sender=sender.lower(),
                    content=message
                )
                session.add(msg)
                session.commit()
        except SQLAlchemyError as e:
            print(f"Error adding conversation message: {e}")
            raise
    
    def get_lead_state(self, email: str) -> Optional[Dict]:
        """
        Get lead state by email.
        
        Args:
            email: Lead email address
            
        Returns:
            Lead state dictionary or None
        """
        try:
            with self.db_manager.session() as session:
                lead = session.query(Lead).filter_by(email=email).first()
                
                if not lead:
                    return None
                
                # Convert Lead model to dictionary
                result = {
                    "email": lead.email,
                    "name": lead.name,
                    "company_name": lead.company_name,
                    "website": lead.website,
                    "location": lead.location,
                    "specialty": lead.specialty,
                    "status": lead.status,
                    "apollo_person_id": lead.apollo_person_id,
                    "apollo_organization_id": lead.apollo_organization_id,
                    "hubspot_contact_id": lead.hubspot_contact_id,
                    "campaign_id": lead.campaign_id,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None,
                    "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                }
                
                # Merge metadata
                if lead.lead_metadata:
                    result.update(lead.lead_metadata)
                
                return result
        except SQLAlchemyError as e:
            print(f"Error getting lead state: {e}")
            return None
    
    def update_lead_state(self, email: str, state: Dict):
        """
        Update lead state.
        
        Args:
            email: Lead email address
            state: State dictionary to update
        """
        try:
            with self.db_manager.session() as session:
                lead = session.query(Lead).filter_by(email=email).first()
                
                if not lead:
                    # Create new lead if it doesn't exist
                    lead = Lead(
                        email=email,
                        status="idle",
                        lead_metadata={}
                    )
                    session.add(lead)
                
                # Initialize metadata if None (preserve existing metadata)
                if lead.lead_metadata is None:
                    lead.lead_metadata = {}
                else:
                    # Make a copy to ensure we're working with a mutable dict
                    lead.lead_metadata = dict(lead.lead_metadata) if lead.lead_metadata else {}
                
                # Map direct fields
                field_map = {
                    "status": "status",
                    "name": "name",
                    "company_name": "company_name",
                    "website": "website",
                    "location": "location",
                    "specialty": "specialty",
                    "apollo_person_id": "apollo_person_id",
                    "apollo_organization_id": "apollo_organization_id",
                    "hubspot_contact_id": "hubspot_contact_id",
                    "campaign_id": "campaign_id",
                }
                
                # Update fields from state dict
                for key, value in state.items():
                    if key in field_map:
                        setattr(lead, field_map[key], value)
                    else:
                        # Store in metadata if not a direct field
                        lead.lead_metadata[key] = value
                
                lead.updated_at = datetime.utcnow()
                session.commit()
        except SQLAlchemyError as e:
            print(f"Error updating lead state: {e}")
            raise
    
    def set_lead_status(
        self,
        email: str,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """
        Set lead status and optional metadata.
        
        Args:
            email: Lead email address
            status: Status string (e.g., "idle", "engaged", "booked")
            metadata: Optional metadata dictionary
        """
        try:
            with self.db_manager.session() as session:
                lead = session.query(Lead).filter_by(email=email).first()
                
                if not lead:
                    # Create new lead if it doesn't exist
                    lead = Lead(
                        email=email,
                        status=status,
                        lead_metadata=metadata or {}
                    )
                    session.add(lead)
                else:
                    # Update existing lead
                    lead.status = status
                    if metadata:
                        if lead.lead_metadata is None:
                            lead.lead_metadata = {}
                        lead.lead_metadata.update(metadata)
                    lead.updated_at = datetime.utcnow()
                
                session.commit()
        except SQLAlchemyError as e:
            print(f"Error setting lead status: {e}")
            raise
    
    def get_all_leads_by_status(self, status: str) -> List[Dict]:
        """
        Get all leads with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of lead dictionaries
        """
        try:
            with self.db_manager.session() as session:
                leads = session.query(Lead).filter_by(status=status).all()
                
                result = []
                for lead in leads:
                    lead_dict = {
                        "email": lead.email,
                        "name": lead.name,
                        "company_name": lead.company_name,
                        "website": lead.website,
                        "location": lead.location,
                        "specialty": lead.specialty,
                        "status": lead.status,
                        "apollo_person_id": lead.apollo_person_id,
                        "apollo_organization_id": lead.apollo_organization_id,
                        "hubspot_contact_id": lead.hubspot_contact_id,
                        "campaign_id": lead.campaign_id,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                    }
                    
                    # Merge metadata
                    if lead.lead_metadata:
                        lead_dict.update(lead.lead_metadata)
                    
                    result.append(lead_dict)
                
                return result
        except SQLAlchemyError as e:
            print(f"Error getting leads by status: {e}")
            return []
    
    def get_all_leads_by_config(self, apollo_config_code: str) -> List[Dict]:
        """
        Get all leads by Apollo config code.
        
        Args:
            apollo_config_code: Apollo configuration code
            
        Returns:
            List of lead dictionaries
        """
        try:
            with self.db_manager.session() as session:
                leads = session.query(Lead).filter(
                    Lead.apollo_config_code == apollo_config_code
                ).all()
                
                result = []
                for lead in leads:
                    lead_dict = {
                        "email": lead.email,
                        "name": lead.name,
                        "company_name": lead.company_name,
                        "website": lead.website,
                        "location": lead.location,
                        "specialty": lead.specialty,
                        "status": lead.status,
                        "apollo_person_id": lead.apollo_person_id,
                        "apollo_organization_id": lead.apollo_organization_id,
                        "hubspot_contact_id": lead.hubspot_contact_id,
                        "campaign_id": lead.campaign_id,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                    }
                    
                    # Merge metadata and A/B testing fields
                    if lead.lead_metadata:
                        lead_dict.update(lead.lead_metadata)
                    
                    # Add A/B testing columns
                    if lead.variant_code:
                        lead_dict["variant_code"] = lead.variant_code
                    if lead.apollo_config_code:
                        lead_dict["apollo_config_code"] = lead.apollo_config_code
                    if lead.persuasion_route:
                        lead_dict["persuasion_route"] = lead.persuasion_route
                    if lead.elaboration_score is not None:
                        lead_dict["elaboration_score"] = lead.elaboration_score
                    if lead.email_sent_at:
                        lead_dict["email_sent_at"] = lead.email_sent_at.isoformat()
                    if lead.reply_received_at:
                        lead_dict["reply_received_at"] = lead.reply_received_at.isoformat()
                    if lead.reply_intent:
                        lead_dict["reply_intent"] = lead.reply_intent
                    if lead.booked_at:
                        lead_dict["booked_at"] = lead.booked_at.isoformat()
                    if lead.closed_at:
                        lead_dict["closed_at"] = lead.closed_at.isoformat()
                    if lead.deal_value:
                        lead_dict["deal_value"] = lead.deal_value
                    
                    result.append(lead_dict)
                
                return result
        except SQLAlchemyError as e:
            print(f"Error getting leads by config: {e}")
            return []
    
    def count_leads_by_status(self, status: str) -> int:
        """
        Count leads with specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            Count of leads
        """
        try:
            with self.db_manager.session() as session:
                count = session.query(Lead).filter_by(status=status).count()
                return count
        except SQLAlchemyError as e:
            print(f"Error counting leads by status: {e}")
            return 0
    
    def get_all_leads(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        Get all leads with optional pagination.
        
        Args:
            limit: Maximum number of leads to return
            offset: Number of leads to skip
            
        Returns:
            List of lead dictionaries
        """
        try:
            with self.db_manager.session() as session:
                query = session.query(Lead)
                
                if limit:
                    query = query.limit(limit).offset(offset)
                
                leads = query.all()
                
                result = []
                for lead in leads:
                    lead_dict = {
                        "email": lead.email,
                        "name": lead.name,
                        "company_name": lead.company_name,
                        "website": lead.website,
                        "location": lead.location,
                        "specialty": lead.specialty,
                        "status": lead.status,
                        "apollo_person_id": lead.apollo_person_id,
                        "apollo_organization_id": lead.apollo_organization_id,
                        "hubspot_contact_id": lead.hubspot_contact_id,
                        "campaign_id": lead.campaign_id,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                    }
                    
                    # Merge metadata
                    if lead.lead_metadata:
                        lead_dict.update(lead.lead_metadata)
                    
                    # Add A/B testing columns
                    if lead.variant_code:
                        lead_dict["variant_code"] = lead.variant_code
                    if lead.apollo_config_code:
                        lead_dict["apollo_config_code"] = lead.apollo_config_code
                    if lead.persuasion_route:
                        lead_dict["persuasion_route"] = lead.persuasion_route
                    if lead.elaboration_score is not None:
                        lead_dict["elaboration_score"] = lead.elaboration_score
                    if lead.email_subject:
                        lead_dict["email_subject"] = lead.email_subject
                    if lead.email_body:
                        lead_dict["email_body"] = lead.email_body
                    if lead.email_generated_at:
                        lead_dict["email_generated_at"] = lead.email_generated_at.isoformat()
                    if lead.email_sent_at:
                        lead_dict["email_sent_at"] = lead.email_sent_at.isoformat()
                    if lead.reply_received_at:
                        lead_dict["reply_received_at"] = lead.reply_received_at.isoformat()
                    if lead.reply_intent:
                        lead_dict["reply_intent"] = lead.reply_intent
                    if lead.booked_at:
                        lead_dict["booked_at"] = lead.booked_at.isoformat()
                    if lead.closed_at:
                        lead_dict["closed_at"] = lead.closed_at.isoformat()
                    if lead.deal_value:
                        lead_dict["deal_value"] = lead.deal_value
                    
                    result.append(lead_dict)
                
                return result
        except SQLAlchemyError as e:
            print(f"Error getting all leads: {e}")
            return []
    
    def get_leads_by_variant(self, variant_code: str, days_back: int = 30) -> List[Dict]:
        """
        Get leads by email variant code within time range.
        
        Args:
            variant_code: Email variant code
            days_back: Number of days to look back
            
        Returns:
            List of lead dictionaries
        """
        try:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            
            with self.db_manager.session() as session:
                leads = session.query(Lead).filter(
                    Lead.variant_code == variant_code,
                    Lead.email_sent_at >= cutoff
                ).all()
                
                result = []
                for lead in leads:
                    lead_dict = {
                        "email": lead.email,
                        "name": lead.name,
                        "company_name": lead.company_name,
                        "website": lead.website,
                        "location": lead.location,
                        "specialty": lead.specialty,
                        "status": lead.status,
                        "variant_code": lead.variant_code,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
                    }
                    
                    # Add A/B testing fields
                    if lead.email_sent_at:
                        lead_dict["email_sent_at"] = lead.email_sent_at.isoformat()
                    if lead.reply_received_at:
                        lead_dict["reply_received_at"] = lead.reply_received_at.isoformat()
                    if lead.reply_intent:
                        lead_dict["reply_intent"] = lead.reply_intent
                    if lead.booked_at:
                        lead_dict["booked_at"] = lead.booked_at.isoformat()
                    if lead.closed_at:
                        lead_dict["closed_at"] = lead.closed_at.isoformat()
                    
                    # Merge metadata
                    if lead.lead_metadata:
                        lead_dict.update(lead.lead_metadata)
                    
                    result.append(lead_dict)
                
                return result
        except SQLAlchemyError as e:
            print(f"Error getting leads by variant: {e}")
            return []