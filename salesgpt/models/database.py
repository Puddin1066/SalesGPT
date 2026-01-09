"""
Database models for SalesGPT using SQLAlchemy.

Replaces JSON file-based state management with proper database persistence.
"""
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Lead(Base):
    """
    Lead model - stores lead information.
    
    Replaces lead_states.json file.
    """
    __tablename__ = "leads"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    company_name = Column(String(255))
    website = Column(String(500))
    location = Column(String(255))
    specialty = Column(String(255))
    status = Column(String(50), nullable=False, index=True, default="idle")
    
    # Apollo identifiers
    apollo_person_id = Column(String(255))
    apollo_organization_id = Column(String(255))
    
    # HubSpot identifier
    hubspot_contact_id = Column(String(255), nullable=True)
    
    # Campaign tracking
    campaign_id = Column(String(255), nullable=True)
    
    # A/B Testing columns
    variant_code = Column(String(255), nullable=True, index=True)
    apollo_config_code = Column(String(255), nullable=True, index=True)
    persuasion_route = Column(String(50), nullable=True)  # "central" or "peripheral"
    elaboration_score = Column(Float, nullable=True)
    email_subject = Column(Text, nullable=True)
    email_body = Column(Text, nullable=True)
    email_generated_at = Column(DateTime, nullable=True)
    email_sent_at = Column(DateTime, nullable=True)
    reply_received_at = Column(DateTime, nullable=True)
    reply_intent = Column(String(50), nullable=True)  # interested, objection, curious, etc.
    booked_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    deal_value = Column(Float, nullable=True)
    
    # Metadata stored as JSON (renamed from 'metadata' to avoid SQLAlchemy conflict)
    lead_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_lead_email", "email"),
        Index("idx_lead_status", "status"),
        Index("idx_lead_variant_code", "variant_code"),
        Index("idx_lead_apollo_config_code", "apollo_config_code"),
    )


class Conversation(Base):
    """
    Conversation model - stores conversation threads.
    
    Replaces conversation_states.json file.
    """
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True, index=True)  # Optional - can exist without lead
    status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_thread_id", "thread_id"),
        Index("idx_conversation_lead_id", "lead_id"),
    )


class ConversationMessage(Base):
    """
    Conversation message model - stores individual messages in threads.
    """
    __tablename__ = "conversation_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)  # "user" or "agent"
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_message_conversation_id", "conversation_id"),
        Index("idx_message_created_at", "created_at"),
    )


class Campaign(Base):
    """
    Campaign model - tracks email campaigns.
    """
    __tablename__ = "campaigns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id = Column(String(255), unique=True, nullable=False, index=True)  # External campaign ID (e.g., Smartlead)
    name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), default="daily")  # "daily" or "gemflush-competitors"
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    campaign_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_campaign_campaign_id", "campaign_id"),
    )

