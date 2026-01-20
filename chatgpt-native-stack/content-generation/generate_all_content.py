"""
Generate ALL content (landing pages + emails) in one command.

Fully automated content generation using OpenAI API.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv('.env.local')

# Import generation scripts
from generate_landing_pages import generate_all_landing_pages
from generate_emails import generate_all_emails


def generate_all_content():
    """Generate all content (landing pages + emails)."""
    
    print("=" * 70)
    print("🚀 GemFlush Content Generation - Fully Automated")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env.local")
        print()
        print("💡 Add your OpenAI API key:")
        print("   echo 'OPENAI_API_KEY=sk-...' >> .env.local")
        return False
    
    print(f"✅ OpenAI API key found")
    print(f"   Model: gpt-4-turbo-preview")
    print()
    print("=" * 70)
    
    # Generate emails first (faster, used by campaign script)
    print("\n📧 PHASE 1: Generating Email Sequences")
    print("=" * 70)
    emails_success = generate_all_emails()
    
    print("\n" + "=" * 70)
    print("📄 PHASE 2: Generating Landing Pages")
    print("=" * 70)
    pages_success = generate_all_landing_pages()
    
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print()
    
    if emails_success and pages_success:
        print("✅ ALL CONTENT GENERATED SUCCESSFULLY!")
        print()
        print("📁 Generated Files:")
        print("   - 12 email sequences → email-content/")
        print("   - 8 landing pages → content-generation/output/landing-pages/")
        print()
        print("⏱️  Total time: ~2-3 minutes (vs 4-6 hours manual)")
        print()
        print("💡 Next Steps:")
        print("   1. Review generated content")
        print("   2. Build landing pages in HubSpot UI")
        print("   3. Run campaigns: gemflush_campaign.py")
        print()
        return True
    else:
        print("⚠️  Some content failed to generate")
        print()
        if not emails_success:
            print("   ❌ Email sequences incomplete")
        if not pages_success:
            print("   ❌ Landing pages incomplete")
        print()
        print("💡 Check errors above and retry")
        return False


if __name__ == "__main__":
    success = generate_all_content()
    sys.exit(0 if success else 1)


