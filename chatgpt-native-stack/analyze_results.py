"""
Pull metrics from HubSpot, format for ChatGPT analysis.

Automates metrics export for weekly ChatGPT optimization sessions.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import gemflush_campaign
import importlib.util
gemflush_path = os.path.join(os.path.dirname(__file__), 'gemflush_campaign.py')
spec = importlib.util.spec_from_file_location("gemflush_campaign", gemflush_path)
gemflush_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gemflush_module)
GemFlushCampaign = gemflush_module.GemFlushCampaign

load_dotenv('.env.local')


def format_for_chatgpt(results: dict, week: int) -> str:
    """
    Format metrics results for ChatGPT analysis prompt.
    
    Args:
        results: Dictionary of metrics by vertical
        week: Week number (1-4)
        
    Returns:
        Formatted prompt string for ChatGPT
    """
    
    prompt = f"""Analyze GemFlush Week {week} cold email results:

CONTEXT:
- Product: GemFlush - AI Visibility Audit tool
- Goal: >5% reply rate, >1.5% positive reply rate, >40% reply→demo conversion
- Testing: 4 verticals (Medical, Legal, Real Estate, Agencies)
- Budget: 2,000 emails/month via HubSpot Free

METRICS:
{json.dumps(results, indent=2)}

ANALYZE:
1. Which vertical performed best? Why might that be?
2. Which subject line variant (A or B) drove better open + reply rates?
3. Are we hitting >5% reply rate target? Which verticals are closest?
4. What patterns do you see in reply quality?
5. Any verticals showing <2% reply rate that should be paused?

RECOMMEND:
1. KILL: Which vertical/variant should be paused? (Underperforming)
2. SCALE: Which vertical/variant should we 2x next week? (Best performer)
3. TEST: What new A/B test should we run next week? (Based on learnings)
4. IMPROVE: Any messaging/positioning tweaks based on what's working?
5. NEXT WEEK: Specific action plan (where to focus, what to test)

Be specific and data-driven. Reference exact metrics."""
    
    return prompt


def main():
    """Main analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export GemFlush campaign metrics for ChatGPT analysis')
    parser.add_argument('--week', type=int, required=True, help='Week number (1-4)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    campaign = GemFlushCampaign()
    
    # Get metrics for all verticals
    results = {}
    verticals = ['medical', 'legal', 'realestate', 'agencies']
    
    print(f"📊 Pulling metrics for Week {args.week}...\n")
    
    for vertical in verticals:
        print(f"   Fetching {vertical}...")
        metrics = campaign.track_metrics(vertical)
        results[vertical] = metrics
    
    # Format for ChatGPT
    analysis_prompt = format_for_chatgpt(results, args.week)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(analysis_prompt)
        print(f"\n✅ Analysis prompt saved to: {args.output}")
        print(f"\n📋 Copy the contents and paste into ChatGPT for analysis")
    else:
        print("\n" + "="*80)
        print(analysis_prompt)
        print("="*80)
        print("\n📋 Copy the above prompt and paste into ChatGPT for analysis")
    
    # Also print summary
    print("\n📈 Summary:")
    for vertical, metrics in results.items():
        print(f"   {vertical}: {metrics.get('sent_count', 0)} emails sent")
        if 'open_rate' in metrics:
            print(f"      Open rate: {metrics['open_rate']:.1%}")
        if 'reply_rate' in metrics:
            print(f"      Reply rate: {metrics['reply_rate']:.1%}")


if __name__ == "__main__":
    main()

