"""
Demo script to show sample ELM-driven cold emails.
Demonstrates what emails would look like when generated through the system.
"""
import os
import json
from pathlib import Path


def load_playbook():
    """Load the ELM email playbook."""
    playbook_path = os.path.join(
        os.path.dirname(__file__),
        "examples",
        "elm_email_playbook.json"
    )
    with open(playbook_path, "r") as f:
        return json.load(f)


def show_central_route_email():
    """Show an example central route email (high elaboration)."""
    print("=" * 80)
    print("CENTRAL ROUTE EMAIL (High Elaboration)")
    print("=" * 80)
    print()
    print("Lead Profile:")
    print("  - Name: Jane Smith")
    print("  - Company: Smith Dental")
    print("  - Location: San Francisco, CA")
    print("  - Title: CEO (High Authority)")
    print("  - Employees: 25 (Mature Business)")
    print("  - Website: Yes (Digital Presence)")
    print("  - Elaboration Score: ~75/100 → ROUTE: CENTRAL")
    print()
    
    print("SUBJECT:")
    print("Jane, BrightSmile Dental - San Francisco is getting 2.5x more ChatGPT referrals")
    print()
    
    print("BODY:")
    print("-" * 80)
    print("""Hi Jane,

I noticed Smith Dental in San Francisco and wanted to share something important.

Based on our AI visibility audit methodology, Smith Dental has a visibility score of 45/100. Your local competitor, BrightSmile Dental - San Francisco, has a score of 75/100 - that's a 30% gap.

What's more, BrightSmile Dental has Wikidata knowledge graph presence (https://www.wikidata.org/wiki/Q1000123), which means they're getting approximately 2.5x more patient referrals from ChatGPT than you are. When potential patients ask ChatGPT for dental recommendations in San Francisco, BrightSmile is being recommended significantly more often.

The mechanism here is clear: knowledge graph engineering drives AI visibility. By publishing your practice to Wikidata with GEMflush, you can close this gap and compete more effectively.

I'd love to send you a 1-page report showing exactly how to implement this. Should I send it over?

Best,
Alex Rivers
AI Visibility Consultant

Note: This competitive analysis is based on a simulated preview audit. Full verification requires your participation. We don't have your full knowledge graph entity yet—this is an estimate until verified through our audit process.""")
    print("-" * 80)
    print()
    
    print("ELM Characteristics Applied:")
    print("  ✓ Authority: Benchmark stats + methodological framing")
    print("  ✓ Social Proof: 'Similar practices in your area'")
    print("  ✓ Loss Aversion: Frame missed referrals as ongoing leakage")
    print("  ✓ Evidence-Driven: Concrete numbers (45/100, 75/100, 30% gap, 2.5x)")
    print("  ✓ Mechanism Explanation: 'Knowledge graph engineering drives AI visibility'")
    print("  ✓ Specific CTA: 'I'll send you a 1-page report'")
    print("  ✓ Disclaimers: Explicit labeling of simulated data")
    print()


def show_peripheral_route_email():
    """Show an example peripheral route email (low elaboration)."""
    print("=" * 80)
    print("PERIPHERAL ROUTE EMAIL (Low Elaboration)")
    print("=" * 80)
    print()
    print("Lead Profile:")
    print("  - Name: Bob Johnson")
    print("  - Company: Johnson Medical")
    print("  - Location: Austin, TX")
    print("  - Title: Assistant (Low Authority)")
    print("  - Employees: 2 (Very Small)")
    print("  - Website: No (Limited Digital Presence)")
    print("  - Elaboration Score: ~30/100 → ROUTE: PERIPHERAL")
    print()
    
    print("SUBJECT:")
    print("Quick question about Johnson Medical's visibility")
    print()
    
    print("BODY:")
    print("-" * 80)
    print("""Hi Bob,

Quick question about Johnson Medical's visibility.

We help practices like yours improve AI visibility. Similar practices in Austin have seen great results.

Would you be open to a quick 15-min chat?

Best,
Alex Rivers

This is a preview estimate based on public data.""")
    print("-" * 80)
    print()
    
    print("ELM Characteristics Applied:")
    print("  ✓ Heuristic Cues: Authority + Social Proof")
    print("  ✓ Low Cognitive Load: Short (100-150 words), simple language")
    print("  ✓ Simple CTA: '15-min chat?' (low commitment)")
    print("  ✓ Reciprocity: 'We help practices like yours' (free offer)")
    print("  ✓ Minimal Technical Detail: No numbers or jargon")
    print("  ✓ Brief Disclaimer: 'Preview estimate based on public data'")
    print()


def show_comparison():
    """Show side-by-side comparison."""
    print("=" * 80)
    print("KEY DIFFERENCES: Central vs Peripheral Routes")
    print("=" * 80)
    print()
    print(f"{'Aspect':<25} {'Central Route':<30} {'Peripheral Route':<30}")
    print("-" * 85)
    print(f"{'Length':<25} {'200-250 words':<30} {'100-150 words':<30}")
    print(f"{'Evidence':<25} {'Concrete numbers':<30} {'Heuristic cues':<30}")
    print(f"{'Technical Detail':<25} {'High (explains mechanism)':<30} {'Low (simple language)':<30}")
    print(f"{'CTA Type':<25} {'Specific next step':<30} {'Simple question':<30}")
    print(f"{'Persuasion':<25} {'Evidence-driven':<30} {'Cues-driven':<30}")
    print(f"{'Target Lead':<25} {'High authority/maturity':<30} {'Low authority/small':<30}")
    print()


def show_sequence_progression():
    """Show the ELM email sequence progression."""
    playbook = load_playbook()
    progression = playbook.get("sequence_progression", {})
    
    print("=" * 80)
    print("ELM EMAIL SEQUENCE PROGRESSION")
    print("=" * 80)
    print()
    print("Email 1: Route-Specific Opener (Personalized per lead)")
    print("  - Central: Evidence-driven with competitor comparison")
    print("  - Peripheral: Quick question with heuristic cues")
    print()
    
    email_2 = progression.get("email_2", {})
    print(f"Email 2: {email_2.get('purpose', 'Reciprocity')} (Day {email_2.get('delay_days', 3)})")
    print(f"  Subject: {email_2.get('subject_template', '').replace('{company_name}', '{{company_name}}')}")
    print()
    
    email_3 = progression.get("email_3", {})
    print(f"Email 3: {email_3.get('purpose', 'Commitment')} (Day {email_3.get('delay_days', 5)})")
    print(f"  Subject: {email_3.get('subject_template', '').replace('{company_name}', '{{company_name}}')}")
    print()
    
    email_4 = progression.get("email_4", {})
    print(f"Email 4: {email_4.get('purpose', 'Authority + Social Proof')} (Day {email_4.get('delay_days', 7)})")
    print(f"  Subject: {email_4.get('subject_template', '').replace('{company_name}', '{{company_name}}')}")
    print()


def main():
    """Generate and display sample emails."""
    print()
    print("🚀 ELM-Driven Cold Email Generation Demo")
    print("=" * 80)
    print()
    print("This demo shows how SalesGPT generates personalized cold emails")
    print("based on the Elaboration Likelihood Model (ELM).")
    print()
    
    # Show central route email
    show_central_route_email()
    
    # Show peripheral route email
    show_peripheral_route_email()
    
    # Show comparison
    show_comparison()
    
    # Show sequence progression
    show_sequence_progression()
    
    print("=" * 80)
    print("✅ Demo Complete")
    print()
    print("The system automatically selects the route based on:")
    print("  - Lead's title/authority (Motivation)")
    print("  - Business size/maturity (Ability)")
    print("  - Website/digital presence (Opportunity)")
    print()
    print("This ensures each lead receives the most effective persuasion")
    print("approach based on their likelihood to elaborate on the message.")
    print()


if __name__ == "__main__":
    main()
