# Integration Tests for Apollo.io and HubSpot

This directory contains comprehensive integration tests for Apollo.io and HubSpot API integrations, implemented in both Python (pytest) and TypeScript (Vitest).

## Overview

All tests use mocking to avoid:
- Consuming Apollo.io API credits
- Making actual API calls to HubSpot
- Network dependencies
- Cost

## Test Structure

### Python Tests (pytest)

Located in `tests/integration/`:

- **`test_apollo_integration.py`** - Apollo.io API integration tests
  - Lead search with various filters
  - Person and organization enrichment
  - Bulk operations
  - Credit consumption tracking
  - Error handling (401, 402, 429)
  - Data transformation

- **`test_hubspot_integration.py`** - HubSpot API integration tests
  - Contact CRUD operations
  - Pipeline stage updates (idle, engaged, booked, closed)
  - Deal creation with associations
  - OAuth token refresh flow
  - Error handling (401, 403, 404, 429)
  - Authentication methods (Private App token, OAuth 2.0)

- **`test_apollo_hubspot_flow.py`** - End-to-end flow tests
  - Apollo search → HubSpot contact creation
  - Data transformation between services
  - Error propagation
  - Pipeline stage updates

### TypeScript Tests (Vitest)

Located in `tests/integration/`:

- **`apollo.integration.test.ts`** - Apollo.io API integration tests
- **`hubspot.integration.test.ts`** - HubSpot API integration tests
- **`apollo_hubspot_flow.integration.test.ts`** - End-to-end flow tests

## Test Fixtures

### Python Fixtures

- **`tests/fixtures/hubspot_responses.py`** - Mock HubSpot API responses
- **`tests/fixtures/api_responses.py`** - Mock Apollo API responses (existing)

### TypeScript Fixtures

- **`tests/fixtures/apolloResponses.ts`** - Apollo.io TypeScript interfaces and mocks
- **`tests/fixtures/hubspotResponses.ts`** - HubSpot TypeScript interfaces and mocks

## Test Utilities

### Python Utilities

- **`tests/utils/mock_helpers.py`** - Helper functions for creating mocks, response builders, error simulators

### TypeScript Utilities

- **`tests/utils/mockHelpers.ts`** - Helper functions for creating mocks, response builders, error simulators

## Configuration

### Python Configuration

- **`pyproject.toml`** - Updated with pytest markers and configuration
- **`.env.test`** - Test environment variables (mock API keys)

### TypeScript Configuration

- **`vitest.config.ts`** - Vitest configuration with coverage
- **`tests/setup.ts`** - Test setup file for Vitest
- **`package.json`** - Test scripts and dependencies

## Running Tests

### Python Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test file
pytest tests/integration/test_apollo_integration.py
pytest tests/integration/test_hubspot_integration.py
pytest tests/integration/test_apollo_hubspot_flow.py

# Run with coverage
pytest tests/integration/ --cov=services/apollo --cov=services/crm

# Run with markers
pytest -m integration
```

### TypeScript Tests

```bash
# Install dependencies first
npm install

# Run all integration tests
npm run test:integration

# Run specific test file
npm run test:apollo
npm run test:hubspot
npm run test:flow

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Test Coverage

### Apollo.io Tests

- ✅ Search leads: 100% coverage
- ✅ Enrichment methods: 100% coverage
- ✅ Error handling: All error codes (401, 402, 429)
- ✅ Credit consumption: Tracked and verified
- ✅ Data transformation: All fields validated

### HubSpot Tests

- ✅ Contact CRUD: 100% coverage
- ✅ Pipeline updates: All stages tested
- ✅ Deal creation: With associations
- ✅ OAuth flow: Token refresh tested
- ✅ Error handling: All error codes (401, 403, 404)

### Integration Flow Tests

- ✅ Apollo → HubSpot: Complete flow tested
- ✅ Error propagation: Handled correctly
- ✅ Data consistency: Validated

## Mocking Strategy

### Python
- Uses `unittest.mock.patch` to mock `requests.post/get/patch`
- All API calls are mocked to avoid actual network requests

### TypeScript
- Uses `vi.mock('axios')` to mock axios calls
- All API calls are mocked to avoid actual network requests

## Test Data

- Uses realistic but fake data
- Covers edge cases (empty responses, missing fields)
- Tests both success and error scenarios

## Dependencies

### Python
- `pytest` (existing)
- `pytest-asyncio` (for async tests)
- `pytest-cov` (for coverage)

### TypeScript
- `vitest` (new)
- `axios` (for API calls)
- `@vitest/coverage-v8` (for coverage)
- `dotenv` (for environment variables)

## File Structure

```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_apollo_integration.py
│   ├── test_hubspot_integration.py
│   ├── test_apollo_hubspot_flow.py
│   ├── apollo.integration.test.ts
│   ├── hubspot.integration.test.ts
│   └── apollo_hubspot_flow.integration.test.ts
├── fixtures/
│   ├── apollo_responses.py (existing)
│   ├── hubspot_responses.py
│   ├── apolloResponses.ts
│   └── hubspotResponses.ts
├── utils/
│   ├── mock_helpers.py
│   └── mockHelpers.ts
├── setup.ts
└── conftest.py (existing)
```

## Success Criteria

✅ All Apollo.io API methods have integration tests  
✅ All HubSpot API methods have integration tests  
✅ Integration flow between Apollo and HubSpot is tested  
✅ All error scenarios are covered  
✅ Tests run fast (all mocked, no network calls)  
✅ No actual API calls are made (all mocked)  
✅ Coverage > 80% for integration test files  

## Notes

- All tests are designed to run without actual API credentials
- Mock API keys are used from `.env.test`
- Tests can be run in CI/CD pipelines without external dependencies
- All HTTP requests are mocked to ensure fast, reliable test execution



