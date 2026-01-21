"""Job-related Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class JobCreate(BaseModel):
    """Schema for creating a new job posting."""
    external_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    company: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = None
    sector: Optional[str] = None
    seniority_level: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    source: str
    skills_extracted: list[str] = Field(default_factory=list)
    posted_at: Optional[datetime] = None


class JobResponse(BaseModel):
    """Schema for job response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: Optional[str]
    title: str
    company: str
    description: str
    requirements: Optional[str]
    location: Optional[str]
    sector: Optional[str]
    seniority_level: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    source: str
    skills_extracted: list[str]
    posted_at: Optional[datetime]
    ingested_at: datetime
    is_active: bool


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int


class JobFilters(BaseModel):
    """Schema for job filtering parameters."""
    sector: Optional[str] = None
    location: Optional[str] = None
    seniority_level: Optional[str] = None
    skills: Optional[list[str]] = None
    salary_min: Optional[int] = Field(None, ge=0)
    is_active: bool = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
