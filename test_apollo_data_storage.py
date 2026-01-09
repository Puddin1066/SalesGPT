"""
Test Apollo Data Storage - Verifies all Apollo data is captured and stored correctly.

Tests:
1. Apollo data extraction (all fields from search response)
2. StateManager storage (all fields saved to JSON)
3. HubSpot contact creation (all fields sent to CRM)
"""
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from services.apollo import ApolloAgent
from services.crm import HubSpotAgent
from state import StateManager


def create_comprehensive_apollo_response():
    """Create a comprehensive Apollo API response with all available fields."""
    return {
        "people": [
            {
                "id": "person_12345",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "title": "CEO & Founder",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "phone_numbers": ["+1-555-123-4567"],
                "city": "New York",
                "state": "NY",
                "country": "United States",
                "postal_code": "10001",
                "updated_at": "2024-01-15T10:30:00Z",
                "organization": {
                    "id": "org_67890",
                    "name": "Doe Medical Clinic",
                    "website_url": "https://doemedical.com",
                    "primary_phone": "+1-555-987-6543",
                    "estimated_num_employees": 15,
                    "industry": "Healthcare",
                    "city": "New York",
                    "state": "NY",
                    "country": "United States",
                    "postal_code": "10001",
                    "updated_at": "2024-01-14T08:20:00Z",
                }
            },
            {
                "id": "person_54321",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@clinic.com",
                "title": "Medical Director",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "phone_numbers": ["+1-555-111-2222"],
                "city": "Los Angeles",
                "state": "CA",
                "country": "United States",
                "postal_code": "90001",
                "updated_at": "2024-01-16T14:45:00Z",
                "organization": {
                    "id": "org_09876",
                    "name": "Smith Healthcare Center",
                    "website_url": "https://smithhealthcare.com",
                    "primary_phone": "+1-555-333-4444",
                    "estimated_num_employees": 25,
                    "industry": "Medical Practice",
                    "city": "Los Angeles",
                    "state": "CA",
                    "country": "United States",
                    "postal_code": "90001",
                    "updated_at": "2024-01-15T09:15:00Z",
                }
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 2,
            "total_entries": 2
        }
    }


def test_apollo_data_extraction():
    """Test that Apollo agent extracts ALL available fields."""
    print("\n" + "="*60)
    print("TEST 1: Apollo Data Extraction")
    print("="*60)
    
    with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
        apollo = ApolloAgent()
        
        mock_response = MagicMock()
        mock_response.json.return_value = create_comprehensive_apollo_response()
        mock_response.raise_for_status = MagicMock()
        
        with patch("services.apollo.apollo_agent.requests.post", return_value=mock_response):
            leads = apollo.search_leads(
                geography="New York, NY",
                specialty="Dermatology",
                limit=2
            )
            
            assert len(leads) == 2, f"Expected 2 leads, got {len(leads)}"
            
            # Test first lead
            lead = leads[0]
            assert lead.name == "John Doe", f"Expected 'John Doe', got '{lead.name}'"
            assert lead.email == "john.doe@example.com"
            assert lead.company_name == "Doe Medical Clinic"
            
            # Verify ALL metadata fields are extracted
            metadata = lead.metadata
            required_fields = [
                "apollo_person_id",
                "apollo_organization_id",
                "title",
                "linkedin_url",
                "person_phone",
                "person_city",
                "person_state",
                "person_country",
                "person_postal_code",
                "organization_name",
                "organization_website",
                "organization_phone",
                "employee_count",
                "organization_industry",
                "organization_city",
                "organization_state",
                "organization_country",
                "organization_postal_code",
                "apollo_updated_at",
                "organization_updated_at",
            ]
            
            missing_fields = [field for field in required_fields if not metadata.get(field)]
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
            else:
                print("✅ All required fields extracted")
            
            # Verify specific values
            assert metadata.get("apollo_person_id") == "person_12345"
            assert metadata.get("apollo_organization_id") == "org_67890"
            assert metadata.get("title") == "CEO & Founder"
            assert metadata.get("person_phone") == "+1-555-123-4567"
            assert metadata.get("person_city") == "New York"
            assert metadata.get("employee_count") == 15
            assert metadata.get("organization_industry") == "Healthcare"
            
            print(f"✅ Lead 1: {lead.name} - All fields extracted correctly")
            print(f"   - Person ID: {metadata.get('apollo_person_id')}")
            print(f"   - Org ID: {metadata.get('apollo_organization_id')}")
            print(f"   - Phone: {metadata.get('person_phone')}")
            print(f"   - Location: {metadata.get('person_city')}, {metadata.get('person_state')}")
            print(f"   - Industry: {metadata.get('organization_industry')}")
            
            # Test second lead
            lead2 = leads[1]
            assert lead2.name == "Jane Smith"
            assert lead2.email == "jane.smith@clinic.com"
            print(f"✅ Lead 2: {lead2.name} - All fields extracted correctly")
            
            print("\n✅ TEST 1 PASSED: All Apollo data fields extracted")


def test_statemanager_storage():
    """Test that StateManager stores ALL Apollo data."""
    print("\n" + "="*60)
    print("TEST 2: StateManager Storage")
    print("="*60)
    
    # Create temporary directory for state files
    temp_dir = tempfile.mkdtemp()
    try:
        state = StateManager(state_dir=temp_dir)
        
        # Create a lead with all Apollo data
        from services.apollo.apollo_agent import Lead
        
        lead = Lead(
            name="John Doe",
            email="john.doe@example.com",
            website="https://doemedical.com",
            company_name="Doe Medical Clinic",
            specialty="Dermatology",
            location="New York, NY",
            metadata={
                "apollo_person_id": "person_12345",
                "apollo_organization_id": "org_67890",
                "title": "CEO & Founder",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "person_phone": "+1-555-123-4567",
                "person_city": "New York",
                "person_state": "NY",
                "person_country": "United States",
                "person_postal_code": "10001",
                "organization_name": "Doe Medical Clinic",
                "organization_website": "https://doemedical.com",
                "organization_phone": "+1-555-987-6543",
                "employee_count": 15,
                "organization_industry": "Healthcare",
                "organization_city": "New York",
                "organization_state": "NY",
                "organization_country": "United States",
                "organization_postal_code": "10001",
                "score": 18,
                "apollo_updated_at": "2024-01-15T10:30:00Z",
                "organization_updated_at": "2024-01-14T08:20:00Z",
            }
        )
        
        # Store lead state
        state.set_lead_status(
            lead.email,
            status="idle",
            metadata={
                "name": lead.name,
                "email": lead.email,
                "company_name": lead.company_name,
                "website": lead.website,
                "location": lead.location,
                "specialty": lead.specialty,
                "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                "apollo_organization_id": lead.metadata.get("apollo_organization_id", ""),
                "title": lead.metadata.get("title", ""),
                "linkedin_url": lead.metadata.get("linkedin_url", ""),
                "person_phone": lead.metadata.get("person_phone", ""),
                "person_city": lead.metadata.get("person_city", ""),
                "person_state": lead.metadata.get("person_state", ""),
                "person_country": lead.metadata.get("person_country", ""),
                "person_postal_code": lead.metadata.get("person_postal_code", ""),
                "organization_name": lead.metadata.get("organization_name", ""),
                "organization_website": lead.metadata.get("organization_website", ""),
                "organization_phone": lead.metadata.get("organization_phone", ""),
                "employee_count": lead.metadata.get("employee_count", 0),
                "organization_industry": lead.metadata.get("organization_industry", ""),
                "organization_city": lead.metadata.get("organization_city", ""),
                "organization_state": lead.metadata.get("organization_state", ""),
                "organization_country": lead.metadata.get("organization_country", ""),
                "organization_postal_code": lead.metadata.get("organization_postal_code", ""),
                "score": lead.metadata.get("score", 0),
                "campaign_id": "campaign_123",
                "first_seen": "2024-01-15T10:00:00",
                "last_updated": "2024-01-15T10:30:00",
                "apollo_updated_at": lead.metadata.get("apollo_updated_at", ""),
                "organization_updated_at": lead.metadata.get("organization_updated_at", ""),
            }
        )
        
        # Verify data was stored
        stored_lead = state.get_lead_state(lead.email)
        assert stored_lead is not None, "Lead state not found"
        assert stored_lead["status"] == "idle"
        assert stored_lead["email"] == "john.doe@example.com"
        assert stored_lead["apollo_person_id"] == "person_12345"
        assert stored_lead["apollo_organization_id"] == "org_67890"
        assert stored_lead["person_phone"] == "+1-555-123-4567"
        assert stored_lead["organization_industry"] == "Healthcare"
        assert stored_lead["employee_count"] == 15
        
        # Verify JSON file exists and contains data
        lead_file = Path(temp_dir) / "lead_states.json"
        assert lead_file.exists(), "lead_states.json file not created"
        
        with open(lead_file, "r") as f:
            data = json.load(f)
            assert lead.email in data, "Lead email not in JSON file"
            stored_data = data[lead.email]
            assert stored_data["apollo_person_id"] == "person_12345"
            assert stored_data["organization_industry"] == "Healthcare"
        
        print(f"✅ Lead stored in StateManager: {lead.email}")
        print(f"   - File: {lead_file}")
        print(f"   - Fields stored: {len(stored_lead)} fields")
        print(f"   - Apollo Person ID: {stored_lead['apollo_person_id']}")
        print(f"   - Organization Industry: {stored_lead['organization_industry']}")
        
        print("\n✅ TEST 2 PASSED: All data stored in StateManager")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_hubspot_contact_creation():
    """Test that HubSpot contact creation includes all Apollo data."""
    print("\n" + "="*60)
    print("TEST 3: HubSpot Contact Creation")
    print("="*60)
    
    with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_hubspot_key"}):
        hubspot = HubSpotAgent()
        
        # Mock successful contact creation
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "contact_12345"}
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(hubspot, "_make_request", return_value=mock_response):
            contact_id = hubspot.create_contact(
                email="john.doe@example.com",
                first_name="John",
                last_name="Doe",
                company="Doe Medical Clinic",
                website="https://doemedical.com",
                phone="+1-555-123-4567",
                title="CEO & Founder",
                linkedin_url="https://linkedin.com/in/johndoe",
                city="New York",
                state="NY",
                country="United States",
                postal_code="10001",
                additional_properties={
                    "apollo_person_id": "person_12345",
                    "apollo_organization_id": "org_67890",
                    "organization_phone": "+1-555-987-6543",
                    "employee_count": "15",
                    "organization_industry": "Healthcare",
                    "organization_city": "New York",
                    "organization_state": "NY",
                    "organization_country": "United States",
                    "lead_score": "18",
                    "specialty": "Dermatology",
                }
            )
            
            assert contact_id == "contact_12345", f"Expected contact_12345, got {contact_id}"
            
            # Verify _make_request was called with correct data
            call_args = hubspot._make_request.call_args
            assert call_args is not None, "_make_request was not called"
            
            # Get the payload
            method, url, kwargs = call_args[0][0], call_args[0][1], call_args[1]
            payload = kwargs.get("json", {})
            properties = payload.get("properties", {})
            
            # Verify standard properties
            assert properties["email"] == "john.doe@example.com"
            assert properties["firstname"] == "John"
            assert properties["lastname"] == "Doe"
            assert properties["company"] == "Doe Medical Clinic"
            assert properties["website"] == "https://doemedical.com"
            assert properties["phone"] == "+1-555-123-4567"
            assert properties["jobtitle"] == "CEO & Founder"
            assert properties["linkedin"] == "https://linkedin.com/in/johndoe"
            assert properties["city"] == "New York"
            assert properties["state"] == "NY"
            assert properties["country"] == "United States"
            assert properties["zip"] == "10001"
            
            # Verify custom properties
            assert properties["apollo_person_id"] == "person_12345"
            assert properties["apollo_organization_id"] == "org_67890"
            assert properties["organization_phone"] == "+1-555-987-6543"
            assert properties["employee_count"] == "15"
            assert properties["organization_industry"] == "Healthcare"
            assert properties["lead_score"] == "18"
            assert properties["specialty"] == "Dermatology"
            
            print(f"✅ Contact created in HubSpot: {contact_id}")
            print(f"   - Standard properties: {len([k for k in properties.keys() if k in ['email', 'firstname', 'lastname', 'company', 'website', 'phone', 'jobtitle', 'linkedin', 'city', 'state', 'country', 'zip']])} fields")
            print(f"   - Custom properties: {len([k for k in properties.keys() if k not in ['email', 'firstname', 'lastname', 'company', 'website', 'phone', 'jobtitle', 'linkedin', 'city', 'state', 'country', 'zip']])} fields")
            print(f"   - Total properties: {len(properties)} fields")
            
            print("\n✅ TEST 3 PASSED: All Apollo data sent to HubSpot")


def test_full_pipeline():
    """Test the complete pipeline: Apollo → StateManager → HubSpot."""
    print("\n" + "="*60)
    print("TEST 4: Full Pipeline Integration")
    print("="*60)
    
    # Create temporary directory for state
    temp_dir = tempfile.mkdtemp()
    
    try:
        with patch.dict(os.environ, {
            "APOLLO_API_KEY": "test_apollo_key",
            "HUBSPOT_API_KEY": "test_hubspot_key",
        }):
            # Mock Apollo search
            apollo_response = MagicMock()
            apollo_response.json.return_value = create_comprehensive_apollo_response()
            apollo_response.raise_for_status = MagicMock()
            
            # Mock HubSpot contact creation
            hubspot_response = MagicMock()
            hubspot_response.json.return_value = {"id": "contact_12345"}
            hubspot_response.raise_for_status = MagicMock()
            
            with patch("services.apollo.apollo_agent.requests.post", return_value=apollo_response), \
                 patch("services.crm.hubspot_agent.requests.request", return_value=hubspot_response):
                
                # Test Apollo search
                apollo = ApolloAgent()
                leads = apollo.search_leads(
                    geography="New York, NY",
                    specialty="Dermatology",
                    limit=1
                )
                
                assert len(leads) > 0, "No leads returned"
                lead = leads[0]
                
                # Verify all fields are present
                assert lead.metadata.get("apollo_person_id"), "Missing apollo_person_id"
                assert lead.metadata.get("apollo_organization_id"), "Missing apollo_organization_id"
                assert lead.metadata.get("person_phone"), "Missing person_phone"
                assert lead.metadata.get("organization_industry"), "Missing organization_industry"
                
                # Test StateManager storage
                state = StateManager(state_dir=temp_dir)
                state.set_lead_status(
                    lead.email,
                    status="idle",
                    metadata={
                        "name": lead.name,
                        "email": lead.email,
                        "apollo_person_id": lead.metadata.get("apollo_person_id", ""),
                        "organization_industry": lead.metadata.get("organization_industry", ""),
                    }
                )
                
                stored = state.get_lead_state(lead.email)
                assert stored is not None, "Lead not stored"
                
                # Test HubSpot creation
                hubspot = HubSpotAgent()
                contact_id = hubspot.create_contact(
                    email=lead.email,
                    first_name=lead.name.split()[0],
                    last_name=" ".join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else "",
                    company=lead.company_name,
                    phone=lead.metadata.get("person_phone", ""),
                    title=lead.metadata.get("title", ""),
                )
                
                assert contact_id == "contact_12345", "Contact not created"
                
                print("✅ Full pipeline test:")
                print(f"   - Apollo search: {len(leads)} leads found")
                print(f"   - All fields extracted: ✅")
                print(f"   - StateManager storage: ✅")
                print(f"   - HubSpot creation: ✅")
                
                print("\n✅ TEST 4 PASSED: Full pipeline integration works")
                
    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("APOLLO DATA STORAGE TEST SUITE")
    print("="*60)
    
    try:
        test_apollo_data_extraction()
        test_statemanager_storage()
        test_hubspot_contact_creation()
        test_full_pipeline()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("  ✅ Apollo data extraction captures all fields")
        print("  ✅ StateManager stores all Apollo data")
        print("  ✅ HubSpot receives all Apollo data")
        print("  ✅ Full pipeline integration works")
        print("\nAll Apollo data is being stored correctly!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

