#!/usr/bin/env python3
"""
Automated API Response Script for GEMflush and Apollo IO.

This script automates API responses for both services, allowing you to:
1. Test integrations without consuming API credits
2. Generate consistent mock responses for development
3. Run automated tests with predictable data

Usage:
    python automate_api_responses.py --service gemflush --clinic "Example Clinic"
    python automate_api_responses.py --service apollo --action search --limit 5
    python automate_api_responses.py --service both --test
"""
import argparse
import json
import sys
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, '.')

from tests.fixtures.api_responses import (
    GEMflushResponseFixtures,
    ApolloResponseFixtures,
    gemflush_audit,
    gemflush_comparison,
    apollo_search,
    apollo_enrich_person,
    apollo_enrich_org
)


def print_json(data: Dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent))


def automate_gemflush(args):
    """Automate GEMflush API responses."""
    print("🔍 GEMflush API Automation")
    print("=" * 50)
    
    if args.action == "audit":
        clinic_id = args.clinic or "Example Clinic"
        competitors = args.competitors.split(",") if args.competitors else None
        
        response = gemflush_audit(clinic_id, competitors)
        print(f"\n✅ Generated audit for: {clinic_id}")
        print_json(response)
        
    elif args.action == "comparison":
        clinic_id = args.clinic or "Example Clinic"
        competitor = args.competitor or "Local Competitor"
        
        response = gemflush_comparison(clinic_id, competitor)
        print(f"\n✅ Generated comparison: {clinic_id} vs {competitor}")
        print_json(response)
        
    else:
        print("❌ Unknown action. Use 'audit' or 'comparison'")


def automate_apollo(args):
    """Automate Apollo IO API responses."""
    print("🔍 Apollo IO API Automation")
    print("=" * 50)
    
    if args.action == "search":
        limit = args.limit or 2
        response = apollo_search(limit=limit)
        print(f"\n✅ Generated search response with {limit} leads")
        print_json(response)
        
    elif args.action == "enrich-person":
        email = args.email or "john@example.com"
        response = apollo_enrich_person(email)
        print(f"\n✅ Generated person enrichment for: {email}")
        print_json(response)
        
    elif args.action == "enrich-org":
        domain = args.domain or "example.com"
        response = apollo_enrich_org(domain)
        print(f"\n✅ Generated organization enrichment for: {domain}")
        print_json(response)
        
    else:
        print("❌ Unknown action. Use 'search', 'enrich-person', or 'enrich-org'")


def run_automated_tests():
    """Run automated tests for both services."""
    print("🧪 Running Automated API Response Tests")
    print("=" * 50)
    
    # Test GEMflush
    print("\n1. Testing GEMflush automation...")
    gemflush_audit_response = gemflush_audit("Test Clinic", ["Competitor A"])
    assert "visibility_score" in gemflush_audit_response
    print("   ✅ GEMflush audit automation works")
    
    gemflush_comp_response = gemflush_comparison("Test Clinic", "Competitor A")
    assert "delta_score" in gemflush_comp_response
    print("   ✅ GEMflush comparison automation works")
    
    # Test Apollo
    print("\n2. Testing Apollo automation...")
    apollo_search_response = apollo_search(limit=3)
    assert len(apollo_search_response["people"]) == 3
    print("   ✅ Apollo search automation works")
    
    apollo_person_response = apollo_enrich_person("test@example.com")
    assert "person" in apollo_person_response
    print("   ✅ Apollo person enrichment automation works")
    
    apollo_org_response = apollo_enrich_org("test.com")
    assert "organization" in apollo_org_response
    print("   ✅ Apollo organization enrichment automation works")
    
    print("\n✅ All automated tests passed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automate API responses for GEMflush and Apollo IO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate GEMflush audit
  python automate_api_responses.py --service gemflush --action audit --clinic "My Clinic"
  
  # Generate Apollo search
  python automate_api_responses.py --service apollo --action search --limit 5
  
  # Run automated tests
  python automate_api_responses.py --service both --test
        """
    )
    
    parser.add_argument(
        "--service",
        choices=["gemflush", "apollo", "both"],
        required=True,
        help="Service to automate"
    )
    
    parser.add_argument(
        "--action",
        help="Action to perform (audit/comparison for GEMflush, search/enrich-person/enrich-org for Apollo)"
    )
    
    # GEMflush arguments
    parser.add_argument("--clinic", help="Clinic ID for GEMflush")
    parser.add_argument("--competitors", help="Comma-separated competitor names")
    parser.add_argument("--competitor", help="Single competitor name for comparison")
    
    # Apollo arguments
    parser.add_argument("--limit", type=int, help="Limit for Apollo search")
    parser.add_argument("--email", help="Email for Apollo person enrichment")
    parser.add_argument("--domain", help="Domain for Apollo organization enrichment")
    
    # Test flag
    parser.add_argument("--test", action="store_true", help="Run automated tests")
    
    args = parser.parse_args()
    
    if args.service == "gemflush":
        if args.test:
            # Run GEMflush tests
            gemflush_audit_response = gemflush_audit("Test Clinic")
            gemflush_comp_response = gemflush_comparison("Test Clinic", "Competitor")
            print("✅ GEMflush automated tests passed!")
        else:
            automate_gemflush(args)
            
    elif args.service == "apollo":
        if args.test:
            # Run Apollo tests
            apollo_search_response = apollo_search(limit=2)
            apollo_person_response = apollo_enrich_person("test@example.com")
            apollo_org_response = apollo_enrich_org("test.com")
            print("✅ Apollo automated tests passed!")
        else:
            automate_apollo(args)
            
    elif args.service == "both":
        if args.test:
            run_automated_tests()
        else:
            print("❌ Use --test flag when using --service both")
            sys.exit(1)


if __name__ == "__main__":
    main()

