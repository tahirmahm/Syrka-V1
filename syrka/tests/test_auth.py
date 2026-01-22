"""Authentication and authorization tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.api
class TestAuth:
    """Test authentication and authorization."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewUser123!",
                "full_name": "New User",
                "role": "user",
                "skills": ["Python", "FastAPI"],
                "experience_years": 3,
                "location": "San Francisco, USA",
                "sector_preference": "Technology"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword!"
            }
        )
        assert response.status_code == 401

    async def test_access_protected_route_without_token(self, client: AsyncClient):
        """Test accessing protected route without token."""
        response = await client.get("/users/me")
        assert response.status_code == 401

    async def test_access_protected_route_with_valid_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test accessing protected route with valid token."""
        response = await client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
