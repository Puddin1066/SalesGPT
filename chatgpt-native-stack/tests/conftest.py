"""
Pytest configuration and shared fixtures.
"""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load test environment
load_dotenv('.env.test')
load_dotenv('.env.local')


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, mocked)")
    config.addinivalue_line("markers", "integration: Integration tests (moderate, some API)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow, full API)")
    config.addinivalue_line("markers", "slow: Slow tests (skip in CI)")


# Shared fixtures
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4-turbo-preview",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "SUBJECT_A: Test Subject A\nSUBJECT_B: Test Subject B\n\nBODY:\nTest email body with {{firstname}} and {{company}}."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_hubspot_contact():
    """Mock HubSpot contact data."""
    return {
        "id": "12345",
        "properties": {
            "email": "test@example.com",
            "firstname": "John",
            "lastname": "Smith",
            "company": "Test Company",
            "city": "New York",
            "jobtitle": "Practice Manager",
            "vertical": "medical"
        },
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z"
    }


@pytest.fixture
def mock_apollo_person():
    """Mock Apollo.io person data."""
    return {
        "id": "abc123",
        "first_name": "Jane",
        "last_name": "Doe",
        "title": "Managing Partner",
        "email": "jane@lawfirm.com",
        "organization_name": "Law Firm LLC",
        "city": "Los Angeles",
        "state": "California",
        "country": "United States"
    }


@pytest.fixture
def sample_email_content():
    """Sample email content file."""
    return """Quick question about {{company}}'s AI visibility
Is {{company}} Invisible in ChatGPT?

Dear {{firstname}},

With 64% of patients using ChatGPT to research providers, AI visibility is crucial.

Is {{company}} showing up when potential patients search in {{city}}?

Best regards,
Alex"""


@pytest.fixture
def sample_landing_page_content():
    """Sample landing page content."""
    return """# Unlock Your Clinic's AI Visibility

## See How You Rank in ChatGPT vs Competitors

### The Problem

64% of patients use ChatGPT to research medical providers...

### How GemFlush Works

1. **AI Audit** - Scan your visibility
2. **Competitor Analysis** - See how you compare
3. **Action Plan** - Improve your rankings

### Get Your Free Audit

[CTA Button]"""


@pytest.fixture
def test_verticals():
    """Test vertical definitions."""
    return {
        'medical': {
            'name': 'medical clinics',
            'targets': 'Practice Managers',
            'stat': '64% of patients use ChatGPT'
        },
        'legal': {
            'name': 'legal firms',
            'targets': 'Managing Partners',
            'stat': '57% of clients use AI tools'
        }
    }


@pytest.fixture
def test_leads_csv(tmp_path):
    """Create a test CSV file."""
    csv_content = """Email,First Name,Last Name,Company,City,Job Title,vertical
test1@clinic.com,John,Smith,Medical Clinic,New York,Practice Manager,medical
test2@lawfirm.com,Jane,Doe,Law Firm,Los Angeles,Managing Partner,legal
test3@realty.com,Bob,Johnson,Real Estate,Chicago,Broker Owner,realestate"""
    
    csv_file = tmp_path / "test_leads.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def mock_hubspot_agent():
    """Mock HubSpot agent."""
    agent = MagicMock()
    agent.create_contact.return_value = "12345"
    agent.update_contact_properties.return_value = True
    agent.get_contact_by_email.return_value = {
        "id": "12345",
        "properties": {"email": "test@example.com"}
    }
    return agent


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = MagicMock()
    
    # Mock chat completion
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = "Test generated content"
    
    client.chat.completions.create.return_value = completion
    
    return client


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment before each test."""
    # Save original env
    original_env = os.environ.copy()
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


# Skip markers
skip_without_openai = pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="OPENAI_API_KEY not set"
)

skip_without_hubspot = pytest.mark.skipif(
    not os.getenv('HUBSPOT_API_KEY') and not os.getenv('HUBSPOT_PAT'),
    reason="HubSpot API key not set"
)

skip_without_apollo = pytest.mark.skipif(
    not os.getenv('APOLLO_API_KEY'),
    reason="APOLLO_API_KEY not set"
)


