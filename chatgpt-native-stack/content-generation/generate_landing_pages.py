"""
Generate landing page content using OpenAI API.

Automatically generates 8 landing page content files (2 variants × 4 verticals).
"""

import os
import sys
import json
from typing import Dict, List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv('.env.local')

try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: OpenAI library not found")
    print("   Install with: pip3 install openai")
    sys.exit(1)


VERTICALS = {
    'medical': {
        'name': 'medical clinics',
        'targets': 'Practice Managers, Office Managers, Medical Directors',
        'stat': '64% of patients now use ChatGPT to research medical providers',
        'use_case': 'Patient search behavior and local competition'
    },
    'legal': {
        'name': 'legal firms',
        'targets': 'Managing Partners, Marketing Directors, Solo Practitioners',
        'stat': '57% of clients use AI tools for legal research',
        'use_case': 'Client acquisition and practice area differentiation'
    },
    'realestate': {
        'name': 'real estate agencies',
        'targets': 'Broker Owners, Marketing Managers, Team Leads',
        'stat': '71% of home buyers use ChatGPT for property research',
        'use_case': 'Listing visibility and agent recruitment'
    },
    'agencies': {
        'name': 'marketing agencies and venture capital firms',
        'targets': 'Partners, CMOs, Heads of Growth',
        'stat': 'Portfolio companies need AI visibility strategy',
        'use_case': 'Competitive intelligence and AI strategy'
    }
}


def generate_landing_page(client: OpenAI, vertical: str, variant: str) -> str:
    """Generate landing page content for a specific vertical and variant."""
    
    v = VERTICALS[vertical]
    
    if variant == 'A':
        # Audit-focused variant
        prompt = f"""Create a landing page for {v['name']} interested in AI visibility.

Product: GemFlush - AI Visibility Audit tool
Shows how businesses appear in ChatGPT/Claude/Gemini vs competitors

VARIANT A: Audit-Focused Approach
- Headline: Focus on audit tool value
- Hook: "See how you rank in ChatGPT vs competitors"
- 3 problem points about AI search affecting their industry
- How GemFlush works (3 steps)
- Social proof placeholder
- CTA: "Get Your Free AI Audit" (form capture)

Target: {v['targets']}
Key Stat: {v['stat']}
Use Case: {v['use_case']}

Generate complete copy for landing page with sections:
1. Hero headline (H1)
2. Hero subheadline (H2)
3. Problem section (3 pain points as H3 + paragraph)
4. How it works (3 steps with icons)
5. Social proof (testimonial placeholder)
6. CTA section

Tone: Professional, data-driven, no hype
Format: Markdown with clear section headers
"""
    else:
        # Demo-focused variant
        prompt = f"""Create a landing page for {v['name']} interested in AI visibility.

Product: GemFlush - AI Visibility Audit tool
Shows how businesses appear in ChatGPT/Claude/Gemini vs competitors

VARIANT B: Demo-Focused Approach
- Headline: Focus on competitor advantage/invisibility risk
- Hook: "Your competitors are visible in ChatGPT. Are you?"
- 3 data points about AI search adoption in their industry
- The cost of invisibility
- How GemFlush reveals the gap
- CTA: "Book 15-Min Demo" (Calendly)

Target: {v['targets']}
Key Stat: {v['stat']}
Use Case: {v['use_case']}

Generate complete copy for landing page with sections:
1. Hero headline (H1) - urgent but professional
2. Hero subheadline (H2) - backed by data
3. AI Adoption section (3 data points as H3 + paragraph)
4. Cost of invisibility (quantified impact)
5. How GemFlush reveals the gap (3 steps)
6. CTA section with urgency

Tone: Urgent but professional, backed by data
Format: Markdown with clear section headers
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or "gpt-4o" if available
            messages=[
                {"role": "system", "content": "You are an expert marketing copywriter specializing in SaaS landing pages. You write compelling, data-driven copy that converts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None


def save_landing_page(vertical: str, variant: str, content: str) -> bool:
    """Save landing page content to file."""
    
    output_dir = os.path.join(os.path.dirname(__file__), 'output', 'landing-pages')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{vertical}_landing_page_{variant.lower()}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# GemFlush Landing Page - {vertical.capitalize()} - Variant {variant}\n\n")
            f.write(content)
        
        print(f"   ✅ {filename}")
        return True
        
    except Exception as e:
        print(f"   ❌ {filename} - Error: {e}")
        return False


def generate_all_landing_pages():
    """Generate all landing pages using OpenAI API."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env.local")
        return False
    
    client = OpenAI(api_key=api_key)
    
    print("🚀 Generating landing pages with OpenAI API...\n")
    
    total = len(VERTICALS) * 2  # 4 verticals × 2 variants
    generated = 0
    
    for vertical in VERTICALS.keys():
        print(f"\n📄 {vertical.capitalize()}:")
        
        for variant in ['A', 'B']:
            print(f"   Generating Variant {variant}...", end=" ", flush=True)
            
            content = generate_landing_page(client, vertical, variant)
            
            if content:
                if save_landing_page(vertical, variant, content):
                    generated += 1
            
    print(f"\n\n📊 Summary:")
    print(f"   Generated: {generated}/{total}")
    
    if generated == total:
        print(f"\n✅ All landing pages generated!")
        print(f"\n📁 Files saved to: content-generation/output/landing-pages/")
        print(f"\n💡 Next steps:")
        print(f"   1. Review generated content")
        print(f"   2. Build pages in HubSpot UI using this copy")
        return True
    else:
        print(f"\n⚠️  Some pages failed to generate")
        return False


if __name__ == "__main__":
    success = generate_all_landing_pages()
    sys.exit(0 if success else 1)


