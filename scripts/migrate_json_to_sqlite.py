"""
One-time migration utility to import existing JSON state files into SQLite.

This script migrates data from:
- state/conversation_states.json
- state/lead_states.json

Into the new SQLite database.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesgpt.config import get_settings
from salesgpt.db.connection import DatabaseManager
from salesgpt.models.database import Lead, Conversation, ConversationMessage


def load_json_file(filepath: Path) -> Dict:
    """Load JSON file, return empty dict if not found."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def migrate_leads(db_manager: DatabaseManager, lead_file: Path):
    """Migrate leads from JSON to database."""
    print("Migrating leads...")
    
    leads_data = load_json_file(lead_file)
    
    if not leads_data:
        print("No leads to migrate.")
        return
    
    migrated_count = 0
    skipped_count = 0
    
    with db_manager.session() as session:
        for email, lead_data in leads_data.items():
            # Check if lead already exists
            existing = session.query(Lead).filter_by(email=email).first()
            if existing:
                print(f"  Skipping existing lead: {email}")
                skipped_count += 1
                continue
            
            # Extract direct fields
            lead = Lead(
                email=email,
                name=lead_data.get("name", ""),
                company_name=lead_data.get("company_name", ""),
                website=lead_data.get("website", ""),
                location=lead_data.get("location", ""),
                specialty=lead_data.get("specialty", ""),
                status=lead_data.get("status", "idle"),
                apollo_person_id=lead_data.get("apollo_person_id", ""),
                apollo_organization_id=lead_data.get("apollo_organization_id", ""),
                hubspot_contact_id=lead_data.get("hubspot_contact_id"),
                campaign_id=lead_data.get("campaign_id"),
            )
            
            # Store remaining fields in metadata
            metadata_fields = {
                "title", "linkedin_url", "person_phone", "person_city",
                "person_state", "person_country", "person_postal_code",
                "organization_name", "organization_website", "organization_phone",
                "employee_count", "organization_industry", "organization_city",
                "organization_state", "organization_country", "organization_postal_code",
                "score", "first_seen", "last_updated", "apollo_updated_at",
                "organization_updated_at", "audit_data", "competitor",
                "personalized_email", "sequence_id", "persuasion_route",
                "elaboration_score", "copy_disclaimer_mode", "email_variant",
                "email_sent_timestamp", "reply_intent", "outcome", "outcome_timestamp"
            }
            
            metadata = {}
            for key, value in lead_data.items():
                if key not in {
                    "email", "name", "company_name", "website", "location",
                    "specialty", "status", "apollo_person_id", "apollo_organization_id",
                    "hubspot_contact_id", "campaign_id"
                }:
                    metadata[key] = value
            
            lead.lead_metadata = metadata
            
            # Parse timestamps if present
            if "first_seen" in lead_data:
                try:
                    lead.created_at = datetime.fromisoformat(lead_data["first_seen"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
            if "last_updated" in lead_data:
                try:
                    lead.updated_at = datetime.fromisoformat(lead_data["last_updated"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
            session.add(lead)
            migrated_count += 1
        
        session.commit()
    
    print(f"  Migrated {migrated_count} leads, skipped {skipped_count} existing leads.")


def migrate_conversations(db_manager: DatabaseManager, conversation_file: Path):
    """Migrate conversations from JSON to database."""
    print("Migrating conversations...")
    
    conversations_data = load_json_file(conversation_file)
    
    if not conversations_data:
        print("No conversations to migrate.")
        return
    
    migrated_count = 0
    skipped_count = 0
    
    with db_manager.session() as session:
        for thread_id, messages in conversations_data.items():
            # Check if conversation already exists
            existing = session.query(Conversation).filter_by(thread_id=thread_id).first()
            if existing:
                print(f"  Skipping existing conversation: {thread_id}")
                skipped_count += 1
                continue
            
            # Try to find associated lead by extracting email from thread_id or messages
            lead_id = None
            # This is a heuristic - you may need to adjust based on your thread_id format
            # For now, we'll create conversations without lead association if we can't find it
            
            conversation = Conversation(
                thread_id=thread_id,
                lead_id=lead_id,
                status="active"
            )
            session.add(conversation)
            session.flush()  # Get conversation.id
            
            # Parse messages
            for msg_str in messages:
                if not isinstance(msg_str, str):
                    continue
                
                # Parse "SENDER: message" format
                if ":" in msg_str:
                    parts = msg_str.split(":", 1)
                    sender = parts[0].strip().lower()
                    content = parts[1].strip() if len(parts) > 1 else ""
                    
                    if sender in ["user", "agent"]:
                        msg = ConversationMessage(
                            conversation_id=conversation.id,
                            sender=sender,
                            content=content
                        )
                        session.add(msg)
            
            migrated_count += 1
        
        session.commit()
    
    print(f"  Migrated {migrated_count} conversations, skipped {skipped_count} existing conversations.")


def main():
    """Main migration function."""
    print("=" * 60)
    print("SalesGPT JSON to SQLite Migration")
    print("=" * 60)
    
    # Load settings
    settings = get_settings()
    
    # Initialize database
    db_manager = DatabaseManager(settings.database_url)
    
    # Create tables if they don't exist
    print("\nCreating database tables...")
    db_manager.create_tables()
    print("  Tables created.")
    
    # Find JSON files
    state_dir = Path("state")
    conversation_file = state_dir / "conversation_states.json"
    lead_file = state_dir / "lead_states.json"
    
    if not conversation_file.exists() and not lead_file.exists():
        print("\nNo JSON state files found. Nothing to migrate.")
        return
    
    # Migrate data
    print("\nStarting migration...")
    
    if lead_file.exists():
        migrate_leads(db_manager, lead_file)
    else:
        print("No lead_states.json found.")
    
    if conversation_file.exists():
        migrate_conversations(db_manager, conversation_file)
    else:
        print("No conversation_states.json found.")
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print(f"\nDatabase location: {settings.database_url}")
    print("\nYou can now safely remove the JSON files if migration was successful.")


if __name__ == "__main__":
    main()

