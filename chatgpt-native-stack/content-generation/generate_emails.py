"""
Generate email sequences using OpenAI API.

Automatically generates 12 email sequences (3 emails × 4 verticals).
"""

import os
import sys
from typing import Dict
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
        'pain': 'Local practices not showing up when patients search in ChatGPT',
        'specialty_token': '{{specialty}}'
    },
    'legal': {
        'name': 'legal firms',
        'targets': 'Managing Partners, Marketing Directors, Solo Practitioners',
        'stat': '57% of clients use AI tools for legal research',
        'pain': 'Law firms invisible in AI-powered legal research',
        'specialty_token': '{{practice_area}}'
    },
    'realestate': {
        'name': 'real estate agencies',
        'targets': 'Broker Owners, Marketing Managers, Team Leads',
        'stat': '71% of home buyers use ChatGPT for property research',
        'pain': 'Listings and agents not appearing in AI search results',
        'specialty_token': '{{area}}'
    },
    'agencies': {
        'name': 'marketing agencies and venture capital firms',
        'targets': 'Partners, CMOs, Heads of Growth',
        'stat': 'Portfolio companies need AI visibility to compete',
        'pain': 'Missing AI visibility strategy for portfolio companies',
        'specialty_token': '{{focus}}'
    }
}


def generate_email(client: OpenAI, vertical: str, email_num: int) -> Dict[str, str]:
    """Generate email content for a specific vertical and sequence number."""
    
    v = VERTICALS[vertical]
    
    if email_num == 1:
        # Initial outreach
        prompt = f"""Create evidence-driven cold email for {v['name']}.

Product: GemFlush - AI Visibility Audit tool
Shows how businesses appear in ChatGPT/Claude/Gemini vs competitors

Target: {v['targets']}

Email 1 (Initial Outreach):
- Subject Line A (problem-focused, 8 words max)
- Subject Line B (curiosity-focused, 8 words max)
- Body: 150 words max, evidence-driven
- Include stat: {v['stat']}
- Pain point: {v['pain']}
- Personalization tokens: {{{{firstname}}}}, {{{{company}}}}, {{{{city}}}}
- CTA: Link to landing page

Tone: Professional, data-backed, not salesy
Format: Plain text, conversational

Output format:
SUBJECT_A: [subject line A]
SUBJECT_B: [subject line B]

BODY:
[email body]
"""
    
    elif email_num == 2:
        # Follow-up
        prompt = f"""Create follow-up email for {v['name']} cold email sequence.

Product: GemFlush - AI Visibility Audit tool

Email 2 (Follow-up):
- Subject Line A (social proof angle, 8 words max)
- Subject Line B (competitor angle, 8 words max)
- Body: Brief case study or example (175 words max)
- Reference similar businesses in their vertical
- Show specific example of AI visibility gap
- Personalization tokens: {{{{firstname}}}}, {{{{company}}}}
- CTA: "Want to see your audit?"

Tone: Professional, consultative
Format: Plain text, story-driven

Output format:
SUBJECT_A: [subject line A]
SUBJECT_B: [subject line B]

BODY:
[email body]
"""
    
    else:  # email_num == 3
        # Breakup
        prompt = f"""Create breakup email for {v['name']} cold email sequence.

Product: GemFlush - AI Visibility Audit tool

Email 3 (Breakup):
- Subject Line A (FOMO angle, 6 words max)
- Subject Line B (helpful resource angle, 8 words max)
- Body: Urgency or helpful framing (125 words max)
- Offer: Free audit or limited demo slots
- Final value proposition
- Personalization tokens: {{{{firstname}}}}
- CTA: "Reply 'yes' for free audit" or strong CTA

Tone: Professional, helpful exit
Format: Plain text, brief

Output format:
SUBJECT_A: [subject line A]
SUBJECT_B: [subject line B]

BODY:
[email body]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert cold email copywriter. You write evidence-driven emails that get replies. Keep emails short, personal, and valuable."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        # Parse the output
        lines = content.strip().split('\n')
        subject_a = ""
        subject_b = ""
        body_lines = []
        in_body = False
        
        for line in lines:
            if line.startswith("SUBJECT_A:"):
                subject_a = line.replace("SUBJECT_A:", "").strip()
            elif line.startswith("SUBJECT_B:"):
                subject_b = line.replace("SUBJECT_B:", "").strip()
            elif line.startswith("BODY:"):
                in_body = True
            elif in_body:
                body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        return {
            'subject_a': subject_a,
            'subject_b': subject_b,
            'body': body
        }
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None


def save_email(vertical: str, email_num: int, email_data: Dict[str, str]) -> bool:
    """Save email content to file."""
    
    # Save to email-content directory (used by campaign script)
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'email-content')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{vertical}_email_{email_num}.txt"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{email_data['subject_a']}\n")
            f.write(f"{email_data['subject_b']}\n")
            f.write(f"\n{email_data['body']}\n")
        
        print(f"   ✅ {filename}")
        return True
        
    except Exception as e:
        print(f"   ❌ {filename} - Error: {e}")
        return False


def generate_all_emails():
    """Generate all email sequences using OpenAI API."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env.local")
        return False
    
    client = OpenAI(api_key=api_key)
    
    print("🚀 Generating email sequences with OpenAI API...\n")
    
    total = len(VERTICALS) * 3  # 4 verticals × 3 emails
    generated = 0
    
    for vertical in VERTICALS.keys():
        print(f"\n📧 {vertical.capitalize()}:")
        
        for email_num in [1, 2, 3]:
            print(f"   Generating Email {email_num}...", end=" ", flush=True)
            
            email_data = generate_email(client, vertical, email_num)
            
            if email_data:
                if save_email(vertical, email_num, email_data):
                    generated += 1
    
    print(f"\n\n📊 Summary:")
    print(f"   Generated: {generated}/{total}")
    
    if generated == total:
        print(f"\n✅ All email sequences generated!")
        print(f"\n📁 Files saved to: email-content/")
        print(f"\n💡 Next steps:")
        print(f"   1. Review generated emails")
        print(f"   2. Use in campaigns with gemflush_campaign.py")
        return True
    else:
        print(f"\n⚠️  Some emails failed to generate")
        return False


if __name__ == "__main__":
    success = generate_all_emails()
    sys.exit(0 if success else 1)


