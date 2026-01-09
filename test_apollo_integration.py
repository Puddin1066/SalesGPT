import os
import logging
import json
from dotenv import load_dotenv
from services.apollo import ApolloAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('apollo_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_apollo():
    # Load environment variables
    # Priority: .env.local then .env
    if os.path.exists(".env.local"):
        logger.info("Loading environment from .env.local")
        load_dotenv(".env.local")
    else:
        logger.info("Loading environment from .env")
        load_dotenv()

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        logger.error("APOLLO_API_KEY not found in environment variables.")
        return

    logger.info(f"Testing Apollo API Integration with key: {api_key[:5]}***{api_key[-3:] if len(api_key) > 8 else ''}")

    try:
        # Initialize the agent
        apollo = ApolloAgent()
        
        # Test Search Criteria
        search_geography = "New York, NY"
        search_specialty = "Dermatology"
        search_limit = 2
        
        logger.info(f"Initiating search: Specialty='{search_specialty}', Geography='{search_geography}', Limit={search_limit}")
        
        # Live search
        leads = apollo.search_leads(
            geography=search_geography,
            specialty=search_specialty,
            limit=search_limit
        )
        
        if leads:
            logger.info(f"✅ Success! Received {len(leads)} leads from Apollo.")
            for i, lead in enumerate(leads, 1):
                logger.info(f"Lead {i}: {lead.name} | Company: {lead.company_name} | Email: {lead.email} | Title: {lead.metadata.get('title')}")
                # Log extra metadata for verification
                logger.debug(f"Lead {i} full metadata: {json.dumps(lead.metadata, indent=2)}")
        else:
            logger.warning("⚠️ No leads returned. This could mean your API key is valid but the search query yielded no results, or your key has 0 credits.")
            
    except Exception as e:
        logger.error(f"❌ Apollo Integration Test Failed with error: {str(e)}")
        if "401" in str(e):
            logger.error("Suggestion: Authentication error. Check if your APOLLO_API_KEY is correct and active.")
        elif "429" in str(e):
            logger.error("Suggestion: Rate limit exceeded. Wait a few minutes or check your Apollo plan.")

if __name__ == "__main__":
    test_apollo()

