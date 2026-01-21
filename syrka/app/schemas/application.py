"""Application-related Pydantic schemas for request/response validation."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    """Schema for creating a job application."""
    job_id: uuid.UUID


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    tailored_cv: Optional[str]
    cover_letter: Optional[str]
    sent_at: Optional[datetime]
    gmail_message_id: Optional[str]
    last_status_check: Optional[datetime]
    created_at: datetime


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""
    status: ApplicationStatus


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list."""
    applications: list[ApplicationResponse]
    total: int
    page: int
    page_size: int
