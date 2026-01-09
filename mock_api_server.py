"""
Mock API Server for External APIs.

Provides mock endpoints for Apollo, Smartlead, HubSpot, and other external services.
Used for development and testing without requiring real API credentials.
"""
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import random
import uuid
from datetime import datetime

app = FastAPI(title="Mock API Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for mock data
mock_leads = []
mock_campaigns = {}
mock_contacts = {}
mock_deals = {}
mock_conversations = {}


# ==================== APOLLO.IO MOCK ====================

class ApolloSearchRequest(BaseModel):
    api_key: Optional[str] = None  # Can be in body or header
    q_keywords: Optional[str] = None
    person_titles: Optional[List[str]] = None
    person_locations: Optional[List[str]] = None
    organization_locations: Optional[List[str]] = None
    organization_num_employees_ranges: Optional[List[str]] = None
    organization_keywords: Optional[str] = None
    page: int = 1
    per_page: int = 25


@app.post("/v1/mixed_people/search")
async def apollo_search_people(
    request: ApolloSearchRequest,
    api_key: Optional[str] = Header(None, alias="X-Api-Key")
):
    """Mock Apollo people search."""
    # Generate mock leads
    leads = []
    for i in range(min(request.per_page, 25)):
        lead_id = str(uuid.uuid4())
        leads.append({
            "id": lead_id,
            "first_name": random.choice(["John", "Jane", "Mike", "Sarah", "David"]),
            "last_name": random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"]),
            "email": f"{random.choice(['john', 'jane', 'mike'])}{i}@example.com",
            "title": random.choice(["CEO", "Owner", "Director", "Manager", "Founder"]),
            "linkedin_url": f"https://linkedin.com/in/person{i}",
            "organization": {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(['Dental', 'Medical', 'Health'])} Clinic {i}",
                "website_url": f"https://clinic{i}.com",
                "estimated_num_employees": random.choice([5, 10, 15, 25, 50]),
                "primary_phone": {"number": f"555-{1000+i}"},
                "addresses": [{
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston"]),
                    "state": random.choice(["NY", "CA", "IL", "TX"]),
                    "country": "United States"
                }]
            }
        })
    
    return {
        "people": leads,
        "pagination": {
            "page": request.page,
            "per_page": request.per_page,
            "total_entries": 100,
            "total_pages": 4
        }
    }


@app.get("/v1/people/{person_id}")
async def apollo_get_person(person_id: str, api_key: str = Header(...)):
    """Mock Apollo get person."""
    return {
        "person": {
            "id": person_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "organization": {
                "id": str(uuid.uuid4()),
                "name": "Example Clinic",
                "website_url": "https://example.com"
            }
        }
    }


@app.get("/v1/organizations/{org_id}")
async def apollo_get_organization(org_id: str, api_key: str = Header(...)):
    """Mock Apollo get organization."""
    return {
        "organization": {
            "id": org_id,
            "name": "Example Clinic",
            "website_url": "https://example.com",
            "estimated_num_employees": 25,
            "primary_phone": {"number": "555-1234"},
            "addresses": [{
                "city": "New York",
                "state": "NY",
                "country": "United States"
            }]
        }
    }


# ==================== SMARTLEAD MOCK ====================

class SmartleadCampaignRequest(BaseModel):
    name: str
    from_email: str
    from_name: str
    reply_to: Optional[str] = None


class SmartleadLeadRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    custom_fields: Optional[Dict[str, Any]] = None


@app.post("/api/v1/campaigns")
async def smartlead_create_campaign(request: SmartleadCampaignRequest, api_key: str = Header(...)):
    """Mock Smartlead create campaign."""
    campaign_id = str(uuid.uuid4())
    mock_campaigns[campaign_id] = {
        "id": campaign_id,
        "name": request.name,
        "from_email": request.from_email,
        "from_name": request.from_name,
        "status": "active"
    }
    return {"campaign_id": campaign_id, "status": "success"}


@app.post("/api/v1/campaigns/{campaign_id}/leads")
async def smartlead_add_leads(campaign_id: str, leads: List[SmartleadLeadRequest], api_key: str = Header(...)):
    """Mock Smartlead add leads to campaign."""
    if campaign_id not in mock_campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    added = []
    for lead in leads:
        lead_id = str(uuid.uuid4())
        mock_leads.append({
            "id": lead_id,
            "campaign_id": campaign_id,
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "status": "pending"
        })
        added.append(lead_id)
    
    return {"added": len(added), "lead_ids": added}


@app.post("/api/v1/campaigns/{campaign_id}/sequences")
async def smartlead_add_sequence(campaign_id: str, sequence: Dict[str, Any], api_key: str = Header(...)):
    """Mock Smartlead add sequence."""
    if campaign_id not in mock_campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    sequence_id = str(uuid.uuid4())
    return {"sequence_id": sequence_id, "status": "success"}


@app.post("/api/v1/replies/send")
async def smartlead_send_reply(request: Dict[str, Any], api_key: str = Header(...)):
    """Mock Smartlead send reply."""
    thread_id = request.get("thread_id", str(uuid.uuid4()))
    return {"thread_id": thread_id, "status": "sent"}


# ==================== HUBSPOT MOCK ====================

class HubSpotContactRequest(BaseModel):
    properties: Dict[str, Any]


@app.post("/crm/v3/objects/contacts")
async def hubspot_create_contact(request: HubSpotContactRequest, authorization: str = Header(...)):
    """Mock HubSpot create contact."""
    contact_id = str(uuid.uuid4())
    mock_contacts[contact_id] = {
        "id": contact_id,
        "properties": request.properties,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    return {
        "id": contact_id,
        "properties": request.properties,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }


@app.patch("/crm/v3/objects/contacts/{contact_id}")
async def hubspot_update_contact(contact_id: str, request: HubSpotContactRequest, authorization: str = Header(...)):
    """Mock HubSpot update contact."""
    if contact_id not in mock_contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    mock_contacts[contact_id]["properties"].update(request.properties)
    mock_contacts[contact_id]["updatedAt"] = datetime.now().isoformat()
    
    return mock_contacts[contact_id]


@app.post("/crm/v3/objects/deals")
async def hubspot_create_deal(request: Dict[str, Any], authorization: str = Header(...)):
    """Mock HubSpot create deal."""
    deal_id = str(uuid.uuid4())
    mock_deals[deal_id] = {
        "id": deal_id,
        "properties": request.get("properties", {}),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    return mock_deals[deal_id]


@app.patch("/crm/v3/objects/deals/{deal_id}")
async def hubspot_update_deal(deal_id: str, request: Dict[str, Any], authorization: str = Header(...)):
    """Mock HubSpot update deal."""
    if deal_id not in mock_deals:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    mock_deals[deal_id]["properties"].update(request.get("properties", {}))
    mock_deals[deal_id]["updatedAt"] = datetime.now().isoformat()
    
    return mock_deals[deal_id]


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mock-api-server",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "apollo": "/v1/mixed_people/search",
            "smartlead": "/api/v1/campaigns",
            "hubspot": "/crm/v3/objects/contacts"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Mock API Server",
        "version": "1.0.0",
        "description": "Mock endpoints for Apollo, Smartlead, and HubSpot APIs",
        "endpoints": {
            "apollo": {
                "search": "POST /v1/mixed_people/search",
                "get_person": "GET /v1/people/{person_id}",
                "get_organization": "GET /v1/organizations/{org_id}"
            },
            "smartlead": {
                "create_campaign": "POST /api/v1/campaigns",
                "add_leads": "POST /api/v1/campaigns/{campaign_id}/leads",
                "add_sequence": "POST /api/v1/campaigns/{campaign_id}/sequences",
                "send_reply": "POST /api/v1/replies/send"
            },
            "hubspot": {
                "create_contact": "POST /crm/v3/objects/contacts",
                "update_contact": "PATCH /crm/v3/objects/contacts/{contact_id}",
                "create_deal": "POST /crm/v3/objects/deals",
                "update_deal": "PATCH /crm/v3/objects/deals/{deal_id}"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

