"""Pytest configuration and fixtures for Syrka tests."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User, UserRole
from app.utils.security import hash_password


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://syrka_test:test@localhost:5432/syrka_test"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Creates all tables before test, drops them after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with overridden database dependency.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("Test123!"),
        full_name="Test User",
        role=UserRole.USER,
        skills=["Python", "FastAPI", "PostgreSQL"],
        experience_years=5,
        location="New York, USA",
        sector_preference="Technology"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_educator(db_session: AsyncSession) -> User:
    """Create a test educator user."""
    user = User(
        email="educator@example.com",
        hashed_password=hash_password("Educator123!"),
        full_name="Test Educator",
        role=UserRole.EDUCATOR,
        skills=["Curriculum Design", "Teaching"],
        experience_years=10,
        location="Boston, USA",
        sector_preference="Education"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_government(db_session: AsyncSession) -> User:
    """Create a test government user."""
    user = User(
        email="gov@example.com",
        hashed_password=hash_password("Gov123!"),
        full_name="Test Government",
        role=UserRole.GOVERNMENT,
        skills=["Policy Analysis", "Data Analytics"],
        experience_years=15,
        location="Washington DC, USA",
        sector_preference="Government"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def educator_headers(client: AsyncClient, test_educator: User) -> dict:
    """Get authentication headers for educator."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "educator@example.com",
            "password": "Educator123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def government_headers(client: AsyncClient, test_government: User) -> dict:
    """Get authentication headers for government user."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "gov@example.com",
            "password": "Gov123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_job_data() -> dict:
    """Sample job data for testing."""
    return {
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "description": "We are looking for an experienced Python developer...",
        "requirements": "5+ years Python, FastAPI, Docker",
        "location": "New York, USA",
        "sector": "Technology",
        "seniority_level": "senior",
        "salary_min": 120000,
        "salary_max": 160000,
        "source": "test",
        "external_id": "test-001",
        "skills_extracted": ["Python", "FastAPI", "Docker"]
    }


@pytest.fixture
def sample_curriculum_data() -> dict:
    """Sample curriculum data for testing."""
    return {
        "target_sector": "Technology",
        "target_skills": ["Python", "Machine Learning", "Data Science"],
        "level": "intermediate",
        "duration_weeks": 12
    }


# Markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.api = pytest.mark.api
pytest.mark.slow = pytest.mark.slow
