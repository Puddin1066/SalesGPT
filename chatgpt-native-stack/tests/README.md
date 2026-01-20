# Test Suite for GemFlush ChatGPT-Native Marketing System

This directory contains comprehensive tests for all components.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_openai_api.py
│   ├── test_hubspot_api.py
│   ├── test_apollo_api.py
│   └── test_content_generation.py
├── integration/       # Integration tests for workflows
│   ├── test_content_workflow.py
│   ├── test_crm_workflow.py
│   └── test_campaign_workflow.py
├── e2e/              # End-to-end tests
│   └── test_complete_campaign.py
├── fixtures/         # Test fixtures and mock data
│   ├── mock_responses.py
│   └── sample_data.py
└── conftest.py       # Pytest configuration
```

## Running Tests

### All Tests
```bash
cd /Users/JJR/SalesGPT
pytest chatgpt-native-stack/tests/ -v
```

### Unit Tests Only
```bash
pytest chatgpt-native-stack/tests/unit/ -v
```

### Integration Tests Only
```bash
pytest chatgpt-native-stack/tests/integration/ -v
```

### E2E Tests Only
```bash
pytest chatgpt-native-stack/tests/e2e/ -v
```

### With Coverage Report
```bash
pytest chatgpt-native-stack/tests/ --cov=chatgpt-native-stack --cov-report=html
```

### Specific Test
```bash
pytest chatgpt-native-stack/tests/unit/test_openai_api.py::test_content_generation -v
```

## Test Categories

### 1. Unit Tests (Fast, No API Calls)
- Mock all external APIs
- Test individual functions
- Fast execution (~1 second)

### 2. Integration Tests (Moderate, Some API Calls)
- Test component interactions
- Use test credentials
- Moderate execution (~30 seconds)

### 3. E2E Tests (Slow, Full API Calls)
- Test complete workflows
- Use real APIs (with caution)
- Slow execution (~2-3 minutes)

## Environment Variables

Set test credentials in `.env.test`:

```bash
# Test API keys (use test accounts)
OPENAI_API_KEY=sk-test-...
HUBSPOT_API_KEY=pat-test-...
APOLLO_API_KEY=test-...

# Test mode flag
TEST_MODE=true
```

## Test Markers

Use pytest markers to run specific test types:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

## Mock Data

Tests use mock data from `fixtures/` to avoid:
- API rate limits
- Consuming API credits
- Network dependencies
- Slow execution

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest chatgpt-native-stack/tests/unit/ -v
    pytest chatgpt-native-stack/tests/integration/ -v
```

## Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: Critical paths
- E2E tests: Complete workflows

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_my_function():
    # Arrange
    mock_data = {"key": "value"}
    
    # Act
    result = my_function(mock_data)
    
    # Assert
    assert result == expected
```

### Integration Test Template
```python
import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('HUBSPOT_API_KEY'), reason="API key required")
def test_hubspot_integration():
    # Test with real API (carefully)
    pass
```

### E2E Test Template
```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_campaign_flow():
    # Test entire workflow
    pass
```

## Troubleshooting

### Issue: Tests fail with missing API keys
**Solution:** Set test API keys in `.env.test` or skip with `pytest -m unit`

### Issue: Tests are slow
**Solution:** Run unit tests only: `pytest -m unit`

### Issue: API rate limits
**Solution:** Use mock mode: `pytest --mock-apis`

## Best Practices

1. **Mock external APIs in unit tests**
2. **Use test credentials for integration tests**
3. **Run E2E tests sparingly (expensive)**
4. **Keep tests fast (<1 sec per unit test)**
5. **Use fixtures for common setup**
6. **Test error cases, not just happy paths**
7. **Clean up test data after tests**

## Dependencies

Install test dependencies:
```bash
pip3 install -r tests/requirements-test.txt
```

Required packages:
- pytest
- pytest-mock
- pytest-cov
- responses
- requests-mock


