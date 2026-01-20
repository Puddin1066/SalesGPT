"""
Smartlead Account Setup Script

Sets up Smartlead account via API:
1. Check account status and mailboxes
2. Create campaign
3. Add email sequences
4. Configure webhook (if needed)
"""
import os
import sys
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.outbound.smartlead_agent import SmartleadAgent
except ImportError:
    print("❌ Error: Could not import SmartleadAgent")
    sys.exit(1)


class SmartleadSetup:
    """Smartlead account setup manager."""
    
    def __init__(self):
        """Initialize Smartlead setup."""
        api_key = os.getenv("SMARTLEAD_API_KEY")
        if not api_key:
            print("❌ Error: SMARTLEAD_API_KEY not found in .env file")
            print("   Please add: SMARTLEAD_API_KEY=your_api_key")
            sys.exit(1)
        
        self.agent = SmartleadAgent(api_key=api_key)
        self.base_url = self.agent.base_url
        
        # Get configuration from environment
        self.from_email = os.getenv("SMARTLEAD_FROM_EMAIL")
        self.from_name = os.getenv("SMARTLEAD_FROM_NAME", "SalesGPT")
        self.reply_to = os.getenv("SMARTLEAD_REPLY_TO") or self.from_email
        self.campaign_name = os.getenv("SMARTLEAD_CAMPAIGN_NAME", "SalesGPT Outreach")
        
        # Email templates from .env
        self.initial_subject = os.getenv("SMARTLEAD_INITIAL_SUBJECT", "Quick question about your clinic")
        self.initial_body = os.getenv("SMARTLEAD_INITIAL_BODY", "")
        
        print("✅ Smartlead agent initialized")
    
    def check_account_status(self) -> Dict:
        """Check Smartlead account status and mailboxes."""
        print("\n" + "="*60)
        print("📊 Checking Smartlead Account Status")
        print("="*60)
        
        status = {
            "api_connected": False,
            "mailboxes_count": 0,
            "mailboxes": [],
            "warnings": [],
            "errors": []
        }
        
        # Test API connection by getting mailboxes
        try:
            mailboxes = self.agent.get_mailboxes()
            
            # Check if we got an error response
            if isinstance(mailboxes, dict) and "error" in mailboxes:
                status["api_connected"] = False
                status["errors"].append(mailboxes.get("error", "Unknown error"))
                print(f"❌ API Error: {mailboxes.get('error')}")
                return status
            
            status["api_connected"] = True
            status["mailboxes"] = mailboxes
            status["mailboxes_count"] = len(mailboxes)
            
            print(f"✅ API Connection: Success")
            print(f"📬 Mailboxes Found: {len(mailboxes)}")
            
            if len(mailboxes) == 0:
                status["warnings"].append(
                    "No mailboxes found. You need to add mailboxes in Smartlead dashboard."
                )
                print("\n⚠️  WARNING: No mailboxes found!")
                print("   Mailboxes are required for sending emails.")
                print("   To add mailboxes:")
                print("   1. Go to https://app.smartlead.ai")
                print("   2. Navigate to Settings → Mailboxes")
                print("   3. Add your sending domains/email accounts")
                print("   4. Wait for warm-up to complete")
                print("   5. Run this script again")
                return status
            
            # Display mailbox details
            print("\n📬 Available Mailboxes:")
            for i, mb in enumerate(mailboxes[:5], 1):  # Show first 5
                mb_id = mb.get("id", "N/A")
                mb_email = mb.get("email", "N/A")
                mb_status = mb.get("status", "unknown")
                print(f"   {i}. ID: {mb_id}, Email: {mb_email}, Status: {mb_status}")
            
            if len(mailboxes) > 5:
                print(f"   ... and {len(mailboxes) - 5} more")
            
        except Exception as e:
            status["api_connected"] = False
            error_str = str(e)
            status["errors"].append(error_str)
            print(f"❌ API Connection Failed: {e}")
            
            if "401" in error_str or "Unauthorized" in error_str:
                print("\n🔒 Authentication Error Detected")
                print("   Possible issues:")
                print("   1. Invalid API key - Check SMARTLEAD_API_KEY in .env")
                print("   2. API key format - Should be your Smartlead API key")
                print("   3. Account access - Verify your Smartlead account is active")
                print("\n   To get your API key:")
                print("   1. Go to https://app.smartlead.ai")
                print("   2. Navigate to Settings → API")
                print("   3. Copy your API key")
                print("   4. Add to .env: SMARTLEAD_API_KEY=your_key_here")
            elif "403" in error_str or "Forbidden" in error_str:
                print("\n🚫 Permission Error")
                print("   Your API key may not have permission to access mailboxes")
                print("   Check your Smartlead plan and API permissions")
            else:
                print(f"\n   Error details: {error_str}")
        
        return status
    
    def create_campaign(self, mailbox_ids: Optional[List[int]] = None) -> Optional[int]:
        """Create a Smartlead campaign."""
        print("\n" + "="*60)
        print("📧 Creating Smartlead Campaign")
        print("="*60)
        
        # First, check if campaign already exists
        print("🔍 Checking for existing campaigns...")
        try:
            import requests
            response = requests.get(
                f"{self.agent.base_url}/campaigns",
                params=self.agent.api_key_param
            )
            if response.status_code == 200:
                existing_campaigns = response.json()
                if existing_campaigns:
                    print(f"✅ Found {len(existing_campaigns)} existing campaign(s)")
                    for camp in existing_campaigns[:3]:
                        camp_id = camp.get('id') or camp.get('campaign_id')
                        camp_name = camp.get('name') or camp.get('campaign_name')
                        print(f"   - ID: {camp_id}, Name: {camp_name}")
                    
                    # Check if any existing campaign matches our name
                    matching_campaign = None
                    for camp in existing_campaigns:
                        camp_name = camp.get('name') or camp.get('campaign_name', '')
                        if camp_name == self.campaign_name:
                            matching_campaign = camp
                            break
                    
                    if matching_campaign:
                        camp_id = matching_campaign.get('id') or matching_campaign.get('campaign_id')
                        print(f"\n✅ Found existing campaign with matching name!")
                        print(f"   Campaign ID: {camp_id}")
                        print(f"   Name: {self.campaign_name}")
                        use_existing = input("\n   Use this campaign? (y/n): ").lower().strip()
                        if use_existing == 'y':
                            return int(camp_id)
                    
                    print("\n💡 Creating new campaign...")
                    # Continue to create new campaign
        except Exception as e:
            print(f"   ⚠️  Could not check existing campaigns: {e}")
        
        # Try to create via API
        print("\n🔄 Attempting to create campaign via API...")
        
        # Per official API docs, campaigns can be created with just a name
        # Mailboxes and other settings can be configured later via campaign settings
        
        print(f"📝 Campaign Name: {self.campaign_name}")
        if self.from_email:
            print(f"📧 From Email: {self.from_email} (will be set via campaign settings)")
        if self.from_name:
            print(f"👤 From Name: {self.from_name} (will be set via campaign settings)")
        
        try:
            # Create campaign with just name (per official API docs)
            campaign_id = self.agent.create_campaign(
                name=self.campaign_name,
                client_id=None  # Can be set if you have clients
            )
            
            if campaign_id:
                print(f"\n✅ Campaign Created Successfully via API!")
                print(f"   Campaign ID: {campaign_id}")
                print("\n💡 Next Steps:")
                print("   1. Configure campaign settings (from_email, schedule, etc.) via dashboard")
                print("   2. Add mailboxes in dashboard (Settings → Mailboxes)")
                print("   3. Add email sequences (see below)")
                print("   4. Add leads to the campaign")
                return campaign_id
            else:
                print("\n⚠️  Campaign creation via API failed.")
                print("\n📋 Manual Creation Required:")
                print("   1. Go to https://app.smartlead.ai")
                print("   2. Navigate to Campaigns → Create Campaign")
                print(f"   3. Campaign Name: {self.campaign_name}")
                print("   4. Note the Campaign ID from the dashboard")
                return None
                
        except Exception as e:
            print(f"\n❌ Error creating campaign: {e}")
            print("\n💡 Campaign creation may require dashboard setup first.")
            return None
    
    def add_sequences(self, campaign_id: int) -> Dict:
        """Add email sequences to campaign."""
        print("\n" + "="*60)
        print("📨 Adding Email Sequences")
        print("="*60)
        
        results = {
            "sequences_added": [],
            "errors": []
        }
        
        # Sequence 1: Initial email
        if self.initial_body:
            print("\n📧 Adding Initial Email Sequence...")
            print(f"   Subject: {self.initial_subject}")
            print(f"   Body Preview: {self.initial_body[:100]}...")
            
            try:
                seq_id = self.agent.add_sequence(
                    campaign_id=campaign_id,
                    subject=self.initial_subject,
                    body=self.initial_body,
                    delay_days=0
                )
                
                if seq_id:
                    results["sequences_added"].append({
                        "id": seq_id,
                        "name": "Initial Email",
                        "delay_days": 0
                    })
                    print(f"   ✅ Sequence added (ID: {seq_id})")
                else:
                    results["errors"].append("Failed to add initial email sequence")
                    print("   ❌ Failed to add sequence")
            except Exception as e:
                results["errors"].append(f"Error adding initial sequence: {str(e)}")
                print(f"   ❌ Error: {e}")
        else:
            print("\n⚠️  No initial email body configured (SMARTLEAD_INITIAL_BODY)")
            print("   Skipping initial email sequence")
        
        # Sequence 2: Follow-up 1 (3 days)
        print("\n📧 Adding Follow-up Email 1 (3 days)...")
        followup1_subject = "Following up on my previous email"
        followup1_body = """Hi {{first_name}},

I wanted to follow up on my previous email about {{company_name}}.

Are you open to a brief conversation this week?

Best,
{{from_name}}"""
        
        try:
            seq_id = self.agent.add_sequence(
                campaign_id=campaign_id,
                subject=followup1_subject,
                body=followup1_body,
                delay_days=3
            )
            
            if seq_id:
                results["sequences_added"].append({
                    "id": seq_id,
                    "name": "Follow-up 1",
                    "delay_days": 3
                })
                print(f"   ✅ Sequence added (ID: {seq_id})")
            else:
                results["errors"].append("Failed to add follow-up 1 sequence")
                print("   ❌ Failed to add sequence")
        except Exception as e:
            results["errors"].append(f"Error adding follow-up 1: {str(e)}")
            print(f"   ❌ Error: {e}")
        
        # Sequence 3: Follow-up 2 (7 days)
        print("\n📧 Adding Follow-up Email 2 (7 days)...")
        followup2_subject = "One last follow-up"
        followup2_body = """Hi {{first_name}},

I know you're busy, but I wanted to reach out one more time about {{company_name}}.

If you're interested, I'd love to share how we can help.

Best,
{{from_name}}"""
        
        try:
            seq_id = self.agent.add_sequence(
                campaign_id=campaign_id,
                subject=followup2_subject,
                body=followup2_body,
                delay_days=7
            )
            
            if seq_id:
                results["sequences_added"].append({
                    "id": seq_id,
                    "name": "Follow-up 2",
                    "delay_days": 7
                })
                print(f"   ✅ Sequence added (ID: {seq_id})")
            else:
                results["errors"].append("Failed to add follow-up 2 sequence")
                print("   ❌ Failed to add sequence")
        except Exception as e:
            results["errors"].append(f"Error adding follow-up 2: {str(e)}")
            print(f"   ❌ Error: {e}")
        
        return results
    
    def setup_webhook_info(self) -> None:
        """Display webhook configuration information."""
        print("\n" + "="*60)
        print("🔗 Webhook Configuration")
        print("="*60)
        
        webhook_url = os.getenv("WEBHOOK_URL", "http://your-domain.com/webhook/smartlead")
        
        print("To receive email replies, configure webhook in Smartlead:")
        print(f"   URL: {webhook_url}")
        print("\nSteps:")
        print("   1. Go to https://app.smartlead.ai")
        print("   2. Navigate to Settings → Webhooks")
        print(f"   3. Add webhook URL: {webhook_url}")
        print("   4. Select events: 'Email Reply'")
        print("   5. Save webhook")
        print("\nNote: Make sure your webhook server is running and accessible")
    
    def run_full_setup(self) -> Dict:
        """Run complete Smartlead setup."""
        print("\n" + "="*80)
        print("🚀 Smartlead Account Setup")
        print("="*80)
        
        setup_results = {
            "account_status": {},
            "campaign_id": None,
            "sequences": {},
            "success": False
        }
        
        # Step 1: Check account status
        account_status = self.check_account_status()
        setup_results["account_status"] = account_status
        
        if not account_status["api_connected"]:
            print("\n❌ Cannot proceed - API connection failed")
            return setup_results
        
        # Note: Campaigns can be created without mailboxes (per official API docs)
        # Mailboxes can be configured later via dashboard
        if account_status["mailboxes_count"] == 0:
            print("\n⚠️  No mailboxes found via API")
            print("   Campaign can still be created - mailboxes can be added later")
            print("   To add mailboxes: https://app.smartlead.ai → Settings → Mailboxes")
        
        # Step 2: Create campaign
        campaign_id = self.create_campaign()
        if not campaign_id:
            print("\n❌ Setup incomplete - failed to create campaign")
            return setup_results
        
        setup_results["campaign_id"] = campaign_id
        
        # Step 3: Add sequences
        sequences = self.add_sequences(campaign_id)
        setup_results["sequences"] = sequences
        
        # Step 4: Webhook info
        self.setup_webhook_info()
        
        # Summary
        print("\n" + "="*80)
        print("✅ Setup Complete!")
        print("="*80)
        print(f"Campaign ID: {campaign_id}")
        print(f"Sequences Added: {len(sequences.get('sequences_added', []))}")
        
        if sequences.get("errors"):
            print(f"\n⚠️  Warnings: {len(sequences['errors'])} errors occurred")
            for error in sequences["errors"]:
                print(f"   - {error}")
        
        setup_results["success"] = True
        
        # Save campaign ID to .env (optional)
        print("\n💡 Tip: You can save the campaign ID to .env:")
        print(f"   SMARTLEAD_CAMPAIGN_ID={campaign_id}")
        
        return setup_results


def main():
    """Main entry point."""
    setup = SmartleadSetup()
    results = setup.run_full_setup()
    
    if results["success"]:
        print("\n✅ Smartlead account setup completed successfully!")
        print("\nNext steps:")
        print("   1. Verify campaign in Smartlead dashboard")
        print("   2. Configure webhook (see instructions above)")
        print("   3. Start adding leads to the campaign")
    else:
        print("\n⚠️  Setup incomplete. Please fix errors above and try again.")


if __name__ == "__main__":
    main()

