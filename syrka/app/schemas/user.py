"""User-related Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.USER
    skills: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    location: Optional[str] = None
    sector_preference: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Schema for user data response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    skills: list[str]
    experience_years: int
    location: Optional[str]
    sector_preference: Optional[str]
    created_at: datetime


class UserProfile(BaseModel):
    """Extended user profile with resume."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    skills: list[str]
    experience_years: int
    location: Optional[str]
    sector_preference: Optional[str]
    resume_text: Optional[str]
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    skills: Optional[list[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    sector_preference: Optional[str] = None
    resume_text: Optional[str] = None
