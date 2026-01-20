"""
Comprehensive API Connection Testing Script

Tests all API connections in the SalesGPT repository and identifies:
- Connection status
- Rate limits
- Budget/credit constraints
- Error handling
"""
import os
import sys
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import service agents
try:
    from services.apollo.apollo_agent import ApolloAgent
except ImportError:
    ApolloAgent = None

try:
    from services.outbound.smartlead_agent import SmartleadAgent
except ImportError:
    SmartleadAgent = None

try:
    from services.crm.hubspot_agent import HubSpotAgent
except ImportError:
    HubSpotAgent = None

try:
    from services.visibility.gemflush_agent import GEMflushAgent
except ImportError:
    GEMflushAgent = None

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "apis": {}
        }
        self.use_mock = os.getenv("USE_MOCK_APIS", "false").lower() == "true"
    
    def test_apollo_api(self) -> Dict:
        """Test Apollo API connection and identify constraints."""
        print("\n" + "="*60)
        print("🔍 Testing Apollo API")
        print("="*60)
        
        result = {
            "name": "Apollo.io",
            "status": "unknown",
            "rate_limits": {},
            "budget_constraints": {},
            "errors": [],
            "warnings": []
        }
        
        if not ApolloAgent:
            result["status"] = "not_available"
            result["errors"].append("ApolloAgent not imported")
            return result
        
        api_key = os.getenv("APOLLO_API_KEY")
        if not api_key:
            result["status"] = "no_credentials"
            result["warnings"].append("APOLLO_API_KEY not found in environment")
            return result
        
        try:
            # Initialize agent
            agent = ApolloAgent(api_key=api_key)
            result["credentials_present"] = True
            
            # Test 1: Simple search (minimal credits)
            print("  Testing search_leads()...")
            try:
                start_time = time.time()
                leads = agent.search_leads(
                    geography="New York, NY",
                    specialty="Dermatology",
                    limit=1  # Minimal request
                )
                elapsed = time.time() - start_time
                
                result["search_test"] = {
                    "success": True,
                    "leads_found": len(leads),
                    "response_time_ms": round(elapsed * 1000, 2)
                }
                result["status"] = "connected"
                print(f"  ✅ Search successful: {len(leads)} leads found in {elapsed:.2f}s")
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                result["search_test"] = {"success": False, "status_code": status_code}
                
                if status_code == 401:
                    result["status"] = "authentication_failed"
                    result["errors"].append("Invalid API key")
                elif status_code == 402:
                    result["status"] = "payment_required"
                    result["budget_constraints"]["credits_exhausted"] = True
                    result["errors"].append("Payment required - credits may be exhausted")
                elif status_code == 429:
                    result["status"] = "rate_limited"
                    result["rate_limits"]["rate_limit_hit"] = True
                    if e.response and "Retry-After" in e.response.headers:
                        retry_after = e.response.headers["Retry-After"]
                        result["rate_limits"]["retry_after_seconds"] = int(retry_after)
                    result["errors"].append("Rate limit exceeded")
                else:
                    result["status"] = "error"
                    result["errors"].append(f"HTTP {status_code}: {str(e)}")
                
                print(f"  ❌ Search failed: {e}")
                
            except Exception as e:
                result["status"] = "error"
                result["errors"].append(f"Unexpected error: {str(e)}")
                print(f"  ❌ Error: {e}")
            
            # Test 2: Check rate limits (make multiple rapid requests)
            if result["status"] == "connected":
                print("  Testing rate limits...")
                try:
                    request_times = []
                    for i in range(3):  # Make 3 rapid requests
                        start = time.time()
                        agent.search_leads("New York, NY", "Dermatology", limit=1)
                        elapsed = time.time() - start
                        request_times.append(elapsed)
                        time.sleep(0.5)  # Small delay between requests
                    
                    avg_time = sum(request_times) / len(request_times)
                    result["rate_limits"]["avg_response_time_ms"] = round(avg_time * 1000, 2)
                    print(f"  ✅ Average response time: {avg_time*1000:.2f}ms")
                    
                except requests.exceptions.HTTPError as e:
                    if e.response and e.response.status_code == 429:
                        result["rate_limits"]["rate_limit_detected"] = True
                        if "Retry-After" in e.response.headers:
                            result["rate_limits"]["retry_after_seconds"] = int(
                                e.response.headers["Retry-After"]
                            )
                        print(f"  ⚠️  Rate limit detected: {e.response.headers.get('Retry-After', 'unknown')}s")
            
            # Document known constraints from code/docs
            result["budget_constraints"]["credit_consumption"] = {
                "search_leads": "Plan-dependent (may be free on some plans)",
                "enrich_person": "1 credit per person",
                "enrich_organization": "1 credit per organization",
                "bulk_enrich_people": "1 credit per person matched",
                "bulk_enrich_organizations": "1 credit per organization enriched"
            }
            
            result["rate_limits"]["known_limits"] = {
                "source": "Apollo API documentation",
                "note": "Rate limits vary by plan. Check your Apollo dashboard for specific limits."
            }
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Initialization error: {str(e)}")
            print(f"  ❌ Initialization failed: {e}")
        
        return result
    
    def test_openai_api(self) -> Dict:
        """Test OpenAI API connection and identify constraints."""
        print("\n" + "="*60)
        print("🤖 Testing OpenAI API")
        print("="*60)
        
        result = {
            "name": "OpenAI",
            "status": "unknown",
            "rate_limits": {},
            "budget_constraints": {},
            "errors": [],
            "warnings": []
        }
        
        if not HAS_OPENAI:
            result["status"] = "not_available"
            result["errors"].append("OpenAI library not installed")
            return result
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            result["status"] = "no_credentials"
            result["warnings"].append("OPENAI_API_KEY not found in environment")
            return result
        
        try:
            client = OpenAI(api_key=api_key)
            result["credentials_present"] = True
            
            # Test 1: Simple completion
            print("  Testing chat completion...")
            try:
                start_time = time.time()
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    max_tokens=5
                )
                elapsed = time.time() - start_time
                
                result["completion_test"] = {
                    "success": True,
                    "response_time_ms": round(elapsed * 1000, 2),
                    "tokens_used": response.usage.total_tokens if response.usage else None
                }
                result["status"] = "connected"
                print(f"  ✅ Completion successful in {elapsed:.2f}s")
                
                if response.usage:
                    result["budget_constraints"]["tokens_used"] = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                    print(f"  📊 Tokens used: {response.usage.total_tokens}")
                
            except Exception as e:
                error_str = str(e)
                result["completion_test"] = {"success": False, "error": error_str}
                
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    result["status"] = "rate_limited"
                    result["rate_limits"]["rate_limit_hit"] = True
                    result["errors"].append("Rate limit exceeded")
                elif "insufficient_quota" in error_str.lower() or "quota" in error_str.lower():
                    result["status"] = "quota_exceeded"
                    result["budget_constraints"]["quota_exceeded"] = True
                    result["errors"].append("Quota exceeded - check billing")
                elif "invalid_api_key" in error_str.lower() or "401" in error_str:
                    result["status"] = "authentication_failed"
                    result["errors"].append("Invalid API key")
                else:
                    result["status"] = "error"
                    result["errors"].append(f"Error: {error_str}")
                
                print(f"  ❌ Completion failed: {e}")
            
            # Document known constraints
            result["budget_constraints"]["pricing"] = {
                "gpt-3.5-turbo": "~$0.0015 per 1K tokens (input + output)",
                "gpt-4": "Higher cost - check OpenAI pricing page",
                "note": "Pay-per-use model - costs accumulate with usage"
            }
            
            result["rate_limits"]["known_limits"] = {
                "source": "OpenAI API documentation",
                "tier_1": "500 RPM, 200K TPM (requests/min, tokens/min)",
                "tier_2": "5,000 RPM, 2M TPM",
                "tier_3": "10,000 RPM, 5M TPM",
                "note": "Limits vary by account tier and model"
            }
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Initialization error: {str(e)}")
            print(f"  ❌ Initialization failed: {e}")
        
        return result
    
    def test_smartlead_api(self) -> Dict:
        """Test Smartlead API connection and identify constraints."""
        print("\n" + "="*60)
        print("📧 Testing Smartlead API")
        print("="*60)
        
        result = {
            "name": "Smartlead.ai",
            "status": "unknown",
            "rate_limits": {},
            "budget_constraints": {},
            "errors": [],
            "warnings": []
        }
        
        if not SmartleadAgent:
            result["status"] = "not_available"
            result["errors"].append("SmartleadAgent not imported")
            return result
        
        api_key = os.getenv("SMARTLEAD_API_KEY")
        if not api_key:
            result["status"] = "no_credentials"
            result["warnings"].append("SMARTLEAD_API_KEY not found in environment")
            return result
        
        try:
            agent = SmartleadAgent(api_key=api_key)
            result["credentials_present"] = True
            
            # Test 1: Get mailboxes (read-only, safe test)
            print("  Testing get_mailboxes()...")
            try:
                start_time = time.time()
                mailboxes = agent.get_mailboxes()
                elapsed = time.time() - start_time
                
                result["mailboxes_test"] = {
                    "success": True,
                    "mailboxes_count": len(mailboxes),
                    "response_time_ms": round(elapsed * 1000, 2)
                }
                result["status"] = "connected"
                print(f"  ✅ Mailboxes retrieved: {len(mailboxes)} mailboxes in {elapsed:.2f}s")
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                result["mailboxes_test"] = {"success": False, "status_code": status_code}
                
                if status_code == 401:
                    result["status"] = "authentication_failed"
                    result["errors"].append("Invalid API key")
                elif status_code == 429:
                    result["status"] = "rate_limited"
                    result["rate_limits"]["rate_limit_hit"] = True
                    result["errors"].append("Rate limit exceeded")
                else:
                    result["status"] = "error"
                    result["errors"].append(f"HTTP {status_code}: {str(e)}")
                
                print(f"  ❌ Mailboxes test failed: {e}")
                
            except Exception as e:
                result["status"] = "error"
                result["errors"].append(f"Unexpected error: {str(e)}")
                print(f"  ❌ Error: {e}")
            
            # Document known constraints
            result["budget_constraints"]["pricing"] = {
                "model": "Subscription-based",
                "note": "Costs vary by plan - check Smartlead pricing"
            }
            
            result["rate_limits"]["known_limits"] = {
                "source": "Smartlead API documentation",
                "note": "Rate limits vary by subscription plan"
            }
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Initialization error: {str(e)}")
            print(f"  ❌ Initialization failed: {e}")
        
        return result
    
    def test_hubspot_api(self) -> Dict:
        """Test HubSpot API connection and identify constraints."""
        print("\n" + "="*60)
        print("🏢 Testing HubSpot API")
        print("="*60)
        
        result = {
            "name": "HubSpot",
            "status": "unknown",
            "rate_limits": {},
            "budget_constraints": {},
            "errors": [],
            "warnings": []
        }
        
        if not HubSpotAgent:
            result["status"] = "not_available"
            result["errors"].append("HubSpotAgent not imported")
            return result
        
        # Check for credentials (supports multiple auth methods)
        api_key = os.getenv("HUBSPOT_API_KEY") or os.getenv("HUBSPOT_ACCESS_TOKEN")
        client_id = os.getenv("HUBSPOT_CLIENT_ID")
        client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
        refresh_token = os.getenv("HUBSPOT_REFRESH_TOKEN")
        
        if not api_key and not (client_id and client_secret and refresh_token):
            result["status"] = "no_credentials"
            result["warnings"].append(
                "HubSpot credentials not found. Need either HUBSPOT_API_KEY or OAuth credentials."
            )
            return result
        
        try:
            agent = HubSpotAgent()
            result["credentials_present"] = True
            result["auth_method"] = "oauth" if agent.use_oauth else "private_app"
            
            # Test 1: Get contact by email (read-only, safe test)
            print("  Testing get_contact_by_email()...")
            try:
                # Use a test email that likely doesn't exist (safe read operation)
                start_time = time.time()
                contact = agent.get_contact_by_email("test-nonexistent-email-12345@example.com")
                elapsed = time.time() - start_time
                
                result["contact_test"] = {
                    "success": True,
                    "contact_found": contact is not None,
                    "response_time_ms": round(elapsed * 1000, 2)
                }
                result["status"] = "connected"
                print(f"  ✅ API connection successful in {elapsed:.2f}s")
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                result["contact_test"] = {"success": False, "status_code": status_code}
                
                if status_code == 401:
                    result["status"] = "authentication_failed"
                    result["errors"].append("Invalid token or expired credentials")
                elif status_code == 403:
                    result["status"] = "forbidden"
                    result["errors"].append("Insufficient permissions - check scopes")
                elif status_code == 429:
                    result["status"] = "rate_limited"
                    result["rate_limits"]["rate_limit_hit"] = True
                    if e.response and "Retry-After" in e.response.headers:
                        retry_after = e.response.headers["Retry-After"]
                        result["rate_limits"]["retry_after_seconds"] = int(retry_after)
                    result["errors"].append("Rate limit exceeded")
                else:
                    result["status"] = "error"
                    result["errors"].append(f"HTTP {status_code}: {str(e)}")
                
                print(f"  ❌ Contact test failed: {e}")
                
            except Exception as e:
                result["status"] = "error"
                result["errors"].append(f"Unexpected error: {str(e)}")
                print(f"  ❌ Error: {e}")
            
            # Document known constraints from docs
            result["rate_limits"]["known_limits"] = {
                "free_tier": "100 requests per 10 seconds, 250,000 requests per day",
                "professional_tier": "150 requests per 10 seconds, 500,000 requests per day",
                "source": "HubSpot API documentation"
            }
            
            result["budget_constraints"]["pricing"] = {
                "free_tier": "Available - API access works on free tier",
                "note": "Some advanced features require paid plans"
            }
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Initialization error: {str(e)}")
            print(f"  ❌ Initialization failed: {e}")
        
        return result
    
    def test_gemflush_api(self) -> Dict:
        """Test GEMflush API connection (if available)."""
        print("\n" + "="*60)
        print("🔬 Testing GEMflush API")
        print("="*60)
        
        result = {
            "name": "GEMflush",
            "status": "unknown",
            "rate_limits": {},
            "budget_constraints": {},
            "errors": [],
            "warnings": []
        }
        
        if not GEMflushAgent:
            result["status"] = "not_available"
            result["warnings"].append("GEMflushAgent not imported")
            return result
        
        api_key = os.getenv("GEMFLUSH_API_KEY")
        use_real_api = os.getenv("GEMFLUSH_USE_REAL_API", "false").lower() == "true"
        
        try:
            agent = GEMflushAgent(use_real_api=use_real_api)
            result["credentials_present"] = api_key is not None
            result["using_real_api"] = agent.use_real_api
            result["using_simulation"] = not agent.use_real_api
            
            # Test audit (works in both real and simulation mode)
            print("  Testing get_audit()...")
            try:
                start_time = time.time()
                audit = agent.get_audit("Test Clinic", competitors=["Competitor A"])
                elapsed = time.time() - start_time
                
                result["audit_test"] = {
                    "success": True,
                    "response_time_ms": round(elapsed * 1000, 2),
                    "has_visibility_score": "visibility_score" in audit,
                    "source": audit.get("source", "unknown")
                }
                result["status"] = "connected" if agent.use_real_api else "simulation_mode"
                print(f"  ✅ Audit retrieved in {elapsed:.2f}s (mode: {'real' if agent.use_real_api else 'simulation'})")
                
            except Exception as e:
                result["audit_test"] = {"success": False, "error": str(e)}
                result["status"] = "error"
                result["errors"].append(f"Audit test failed: {str(e)}")
                print(f"  ❌ Audit test failed: {e}")
            
            # Document constraints
            result["budget_constraints"]["pricing"] = {
                "note": "Contact alex@gemflush.com for API access and pricing"
            }
            
            if not agent.use_real_api:
                result["warnings"].append("Using simulation mode - real API not configured")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Initialization error: {str(e)}")
            print(f"  ❌ Initialization failed: {e}")
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all API tests."""
        print("\n" + "="*60)
        print("🚀 Starting Comprehensive API Connection Tests")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Mock Mode: {self.use_mock}")
        print()
        
        # Test each API
        self.results["apis"]["apollo"] = self.test_apollo_api()
        self.results["apis"]["openai"] = self.test_openai_api()
        self.results["apis"]["smartlead"] = self.test_smartlead_api()
        self.results["apis"]["hubspot"] = self.test_hubspot_api()
        self.results["apis"]["gemflush"] = self.test_gemflush_api()
        
        return self.results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive report."""
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("API CONNECTION TEST REPORT")
        report_lines.append("="*80)
        report_lines.append(f"Generated: {self.results['timestamp']}")
        report_lines.append("")
        
        # Summary
        report_lines.append("SUMMARY")
        report_lines.append("-"*80)
        total_apis = len(self.results["apis"])
        connected = sum(1 for api in self.results["apis"].values() if api["status"] == "connected")
        no_creds = sum(1 for api in self.results["apis"].values() if api["status"] == "no_credentials")
        errors = sum(1 for api in self.results["apis"].values() if api["status"] in ["error", "authentication_failed"])
        
        report_lines.append(f"Total APIs Tested: {total_apis}")
        report_lines.append(f"✅ Connected: {connected}")
        report_lines.append(f"⚠️  No Credentials: {no_creds}")
        report_lines.append(f"❌ Errors: {errors}")
        report_lines.append("")
        
        # Detailed results for each API
        for api_name, api_result in self.results["apis"].items():
            report_lines.append("="*80)
            report_lines.append(f"{api_result['name'].upper()} API")
            report_lines.append("="*80)
            
            # Status
            status_emoji = {
                "connected": "✅",
                "simulation_mode": "🔄",
                "no_credentials": "⚠️",
                "rate_limited": "⏱️",
                "quota_exceeded": "💰",
                "authentication_failed": "🔒",
                "error": "❌",
                "not_available": "🚫"
            }
            emoji = status_emoji.get(api_result["status"], "❓")
            report_lines.append(f"Status: {emoji} {api_result['status']}")
            report_lines.append("")
            
            # Rate Limits
            if api_result.get("rate_limits"):
                report_lines.append("Rate Limits:")
                for key, value in api_result["rate_limits"].items():
                    if key != "known_limits":
                        report_lines.append(f"  - {key}: {value}")
                if "known_limits" in api_result["rate_limits"]:
                    report_lines.append("  Known Limits:")
                    for key, value in api_result["rate_limits"]["known_limits"].items():
                        report_lines.append(f"    - {key}: {value}")
                report_lines.append("")
            
            # Budget Constraints
            if api_result.get("budget_constraints"):
                report_lines.append("Budget Constraints:")
                for key, value in api_result["budget_constraints"].items():
                    if isinstance(value, dict):
                        report_lines.append(f"  - {key}:")
                        for k, v in value.items():
                            report_lines.append(f"    - {k}: {v}")
                    else:
                        report_lines.append(f"  - {key}: {value}")
                report_lines.append("")
            
            # Errors
            if api_result.get("errors"):
                report_lines.append("Errors:")
                for error in api_result["errors"]:
                    report_lines.append(f"  ❌ {error}")
                report_lines.append("")
            
            # Warnings
            if api_result.get("warnings"):
                report_lines.append("Warnings:")
                for warning in api_result["warnings"]:
                    report_lines.append(f"  ⚠️  {warning}")
                report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write(report_text)
            print(f"\n📄 Report saved to: {output_file}")
        
        return report_text


def main():
    """Main entry point."""
    tester = APITester()
    results = tester.run_all_tests()
    
    # Generate report
    report = tester.generate_report(output_file="api_test_report.txt")
    print("\n" + "="*80)
    print("REPORT GENERATED")
    print("="*80)
    print(report)
    
    # Also save JSON results
    with open("api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📊 JSON results saved to: api_test_results.json")


if __name__ == "__main__":
    main()

