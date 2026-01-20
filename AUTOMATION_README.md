# API Automation Guide

Automated API response system for **GEMflush** (alex@gemflush.com) and **Apollo IO** integrations.

## Overview

This automation system allows you to:
- ✅ Test integrations without consuming API credits
- ✅ Generate consistent, predictable mock responses
- ✅ Run automated tests with reproducible data
- ✅ Develop and debug without real API dependencies

## Quick Start

### 1. Run Automated Tests

```bash
# Test both services
python3 automate_api_responses.py --service both --test

# Test GEMflush only
python3 automate_api_responses.py --service gemflush --test

# Test Apollo only
python3 automate_api_responses.py --service apollo --test
```

### 2. Generate Mock Responses

#### GEMflush Responses

```bash
# Generate audit response
python3 automate_api_responses.py --service gemflush --action audit \
  --clinic "My Clinic" \
  --competitors "Competitor A,Competitor B"

# Generate competitor comparison
python3 automate_api_responses.py --service gemflush --action comparison \
  --clinic "My Clinic" \
  --competitor "Competitor A"
```

#### Apollo IO Responses

```bash
# Generate search response
python3 automate_api_responses.py --service apollo --action search --limit 5

# Generate person enrichment
python3 automate_api_responses.py --service apollo --action enrich-person \
  --email "john@example.com"

# Generate organization enrichment
python3 automate_api_responses.py --service apollo --action enrich-org \
  --domain "example.com"
```

## Using in Code

### Python Fixtures

```python
from tests.fixtures.api_responses import (
    gemflush_audit,
    gemflush_comparison,
    apollo_search,
    apollo_enrich_person,
    apollo_enrich_org
)

# GEMflush
audit = gemflush_audit("Example Clinic", ["Competitor A"])
comparison = gemflush_comparison("Example Clinic", "Competitor A")

# Apollo
search_results = apollo_search(limit=5)
person_data = apollo_enrich_person("john@example.com")
org_data = apollo_enrich_org("example.com")
```

### In Tests

```python
from unittest.mock import patch
from tests.fixtures.api_responses import gemflush_audit, apollo_search

@patch('services.visibility.gemflush_agent.requests.post')
def test_with_automated_response(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = gemflush_audit("Test Clinic")
    mock_post.return_value = mock_response
    
    # Your test code here
```

## GEMflush Agent Configuration

The GEMflush agent now supports both real API calls and automated responses:

```python
from services.visibility import GEMflushAgent

# Use automated responses (default)
agent = GEMflushAgent()

# Force real API (requires GEMFLUSH_API_KEY)
agent = GEMflushAgent(
    use_real_api=True,
    api_key="your_key_here"
)

# Or set via environment
# GEMFLUSH_API_KEY=your_key
# GEMFLUSH_USE_REAL_API=true
```

## Apollo Agent Configuration

Apollo agent works with automated responses in tests:

```python
from services.apollo import ApolloAgent
from unittest.mock import patch
from tests.fixtures.api_responses import apollo_search

@patch('services.apollo.apollo_agent.requests.post')
def test_apollo(mock_post):
    mock_response.json.return_value = apollo_search(limit=2)
    # Your test code
```

## Running Pytest Tests

```bash
# Run all automation tests
python3 -m pytest tests/test_api_automation.py -v

# Run with coverage
python3 -m pytest tests/test_api_automation.py -v --cov=services

# Run specific test class
python3 -m pytest tests/test_api_automation.py::TestGEMflushAutomation -v
```

## Response Format

### GEMflush Audit Response

```json
{
  "clinic_id": "Example Clinic",
  "visibility_score": 47,
  "competitor_scores": {
    "Competitor A": 48,
    "Competitor B": 55
  },
  "top_keywords": ["urgent care", "walk-in clinic", "primary care"],
  "recommendation": "Improve AI search visibility...",
  "source": "automated_fixture"
}
```

### Apollo Search Response

```json
{
  "people": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "title": "CEO",
      "organization": {
        "name": "Example Clinic",
        "website_url": "https://example.com"
      }
    }
  ],
  "pagination": {...},
  "source": "automated_fixture"
}
```

## Features

### Deterministic Responses
- Same inputs always produce same outputs
- Hash-based scoring ensures consistency
- Perfect for testing and development

### No Credit Consumption
- All automated responses are free
- No API calls made
- Safe for CI/CD pipelines

### Easy Integration
- Drop-in replacements for real API calls
- Works with existing test infrastructure
- Compatible with pytest, unittest, etc.

## Environment Variables

```bash
# GEMflush
GEMFLUSH_API_KEY=your_key_here          # For real API
GEMFLUSH_API_URL=https://api.gemflush.com/v1
GEMFLUSH_USE_REAL_API=false              # Set to true to use real API

# Apollo
APOLLO_API_KEY=your_key_here             # For real API

# LLM (for GEMflush simulation fallback)
GPT_MODEL=gpt-3.5-turbo
```

## Files Created

- `tests/fixtures/api_responses.py` - Automated response generators
- `tests/test_api_automation.py` - Automated test suite
- `automate_api_responses.py` - CLI tool for generating responses
- `services/visibility/gemflush_agent.py` - Updated with API support

## Next Steps

1. **Use in Development**: Replace real API calls with automated responses during development
2. **CI/CD Integration**: Add automated tests to your CI pipeline
3. **Real API Testing**: When ready, switch to real APIs by setting environment variables

## Support

For issues or questions:
- Check test files for usage examples
- Review `automate_api_responses.py --help`
- See `tests/test_api_automation.py` for test patterns



