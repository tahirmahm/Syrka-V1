# Syrka Testing Guide

## Overview

Syrka uses pytest for comprehensive testing with async support. Tests are organized into unit tests, integration tests, and API tests.

## Test Structure

```
tests/
├── conftest.py          # Fixtures and configuration
├── test_auth.py         # Authentication tests
├── test_matching.py     # Matching engine tests
├── test_curriculum.py   # Curriculum generation tests
└── ...
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# API tests only
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
pytest tests/test_auth.py
pytest tests/test_matching.py -v
```

### Run Specific Test Functions

```bash
pytest tests/test_auth.py::TestAuth::test_login_success
```

## Test Database Setup

Tests use a separate test database to avoid affecting production data.

### Create Test Database

```bash
createdb syrka_test
psql syrka_test -f migrations/initial_schema.sql
```

### Configure Test Database

Set in `tests/conftest.py`:

```python
TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/syrka_test"
```

## Writing Tests

### Test Structure

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.api
class TestMyFeature:
    """Test my feature."""

    async def test_something(self, client: AsyncClient):
        """Test description."""
        response = await client.get("/endpoint")
        assert response.status_code == 200
```

### Available Fixtures

#### Database Fixtures

- `db_session` - Fresh database session for each test
- `test_user` - Regular user account
- `test_educator` - Educator account
- `test_government` - Government account

#### HTTP Client Fixtures

- `client` - Async HTTP client
- `auth_headers` - Auth headers for test_user
- `educator_headers` - Auth headers for educator
- `government_headers` - Auth headers for government user

#### Data Fixtures

- `sample_job_data` - Job data dictionary
- `sample_curriculum_data` - Curriculum data dictionary

### Example: Testing API Endpoint

```python
@pytest.mark.asyncio
@pytest.mark.api
async def test_get_jobs(client: AsyncClient, auth_headers: dict):
    """Test retrieving job listings."""
    response = await client.get("/jobs", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)
```

### Example: Testing Authentication

```python
@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user):
    """Test user login."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test123!"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Example: Testing Unit Functions

```python
@pytest.mark.unit
def test_skill_extraction():
    """Test skill extraction function."""
    from app.matching.skill_extractor import SkillExtractor

    extractor = SkillExtractor()
    skills = extractor.extract_from_text("Python and FastAPI required")

    assert "python" in skills
    assert "fastapi" in skills
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit        # Unit test
@pytest.mark.integration # Integration test
@pytest.mark.api         # API endpoint test
@pytest.mark.slow        # Slow test (skip in CI)
```

## Mocking External Services

### Mock OpenAI/DeepSeek API

```python
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_cv_generation():
    """Test CV generation with mocked LLM."""
    with patch('app.automation.cv_generator.ChatOpenAI') as mock_llm:
        mock_llm.return_value.invoke.return_value = "Generated CV"

        from app.automation.cv_generator import CVGenerator
        generator = CVGenerator()
        cv = generator.tailor_cv(user, job)

        assert "Generated CV" in cv
```

### Mock Gmail API

```python
@pytest.mark.asyncio
async def test_send_email():
    """Test email sending with mocked Gmail."""
    with patch('app.automation.gmail_client.build') as mock_gmail:
        # Configure mock
        mock_gmail.return_value.users().messages().send().execute.return_value = {
            'id': 'message123'
        }

        from app.automation.gmail_client import GmailClient
        client = GmailClient()
        message_id = client.send_email("to@example.com", "Subject", "Body")

        assert message_id == 'message123'
```

## Integration Testing

### Test Complete Workflows

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_job_application_workflow(
    client: AsyncClient,
    auth_headers: dict,
    db_session
):
    """Test complete application workflow."""
    # 1. Create job
    job_response = await client.post(
        "/jobs",
        headers=auth_headers,
        json=sample_job_data
    )
    job_id = job_response.json()["id"]

    # 2. Find matches
    matches_response = await client.get(
        "/matching/matches",
        headers=auth_headers
    )
    assert matches_response.status_code == 200

    # 3. Prepare application
    app_response = await client.post(
        f"/applications/prepare/{job_id}",
        headers=auth_headers
    )
    assert app_response.status_code == 201
    app_id = app_response.json()["id"]

    # 4. Send application
    send_response = await client.post(
        f"/applications/{app_id}/send",
        headers=auth_headers
    )
    assert send_response.status_code == 200
```

## Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task


class SyrkaUser(HttpUser):
    """Load test user."""

    def on_start(self):
        """Login once."""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def get_jobs(self):
        """Get job listings."""
        self.client.get("/jobs", headers=self.headers)

    @task
    def get_matches(self):
        """Get job matches."""
        self.client.get("/matching/matches", headers=self.headers)
```

Run:
```bash
locust -f tests/load/test_load.py --host=http://localhost:8000
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Coverage Goals

- **Overall:** > 80%
- **Critical paths:** > 95%
  - Authentication
  - Job matching
  - Application automation
- **UI/CLI:** > 60%

### Check Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

## Debugging Tests

### Run with Debugging

```bash
pytest --pdb  # Drop into debugger on failure
pytest -x     # Stop on first failure
pytest -v     # Verbose output
pytest -s     # Show print statements
```

### Use Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_something():
    """Test with logging."""
    logger.debug("Test starting...")
    # Test code
    logger.debug("Test complete")
```

## Best Practices

1. **Test Isolation:** Each test should be independent
2. **Clear Names:** Use descriptive test function names
3. **One Assertion Per Test:** Focus on one behavior
4. **Arrange-Act-Assert:** Structure tests clearly
5. **Use Fixtures:** Reuse setup code
6. **Mock External APIs:** Don't rely on external services
7. **Fast Tests:** Keep unit tests under 1 second
8. **Comprehensive Coverage:** Test happy paths and edge cases

## Common Patterns

### Testing Exceptions

```python
import pytest


async def test_invalid_input():
    """Test exception handling."""
    with pytest.raises(ValueError) as exc_info:
        # Code that should raise ValueError
        pass

    assert "expected error message" in str(exc_info.value)
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await my_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("python", True),
    ("java", True),
    ("unknown", False),
])
def test_skill_recognition(input, expected):
    """Test skill recognition with multiple inputs."""
    result = is_valid_skill(input)
    assert result == expected
```

## Troubleshooting

### Tests Fail with Database Errors

1. Ensure test database exists: `createdb syrka_test`
2. Run migrations: `psql syrka_test -f migrations/initial_schema.sql`
3. Check DATABASE_URL in conftest.py

### Tests Hang

- Check for missing `await` in async tests
- Ensure async context managers are properly closed
- Use `pytest-timeout` to catch hanging tests

### Import Errors

- Ensure virtual environment is activated
- Run `pip install -e .` to install package in development mode
- Check PYTHONPATH includes project root

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
