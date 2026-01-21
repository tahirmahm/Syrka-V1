"""Job posting model for workforce mobility engine."""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, LargeBinary, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Job(Base):
    """
    Job posting model representing available positions.

    Attributes:
        id: Unique identifier (UUID)
        external_id: ID from external source (for deduplication)
        title: Job title
        company: Company/organization name
        description: Full job description
        requirements: Job requirements text
        location: Job location
        sector: Industry sector
        seniority_level: Junior/Mid/Senior/Lead/Executive
        salary_min: Minimum salary (if available)
        salary_max: Maximum salary (if available)
        source: Data source (scraped/api)
        embedding: Vector embedding for similarity matching (stored as bytes)
        skills_extracted: JSON array of extracted required skills
        posted_at: When the job was posted by employer
        ingested_at: When we ingested this job
        is_active: Whether this job is currently active
    """

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    external_id = Column(String(255), unique=True, index=True)

    # Basic job information
    title = Column(String(500), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    location = Column(String(255), index=True)
    sector = Column(String(100), index=True)
    seniority_level = Column(String(50), index=True)

    # Salary information
    salary_min = Column(Integer)
    salary_max = Column(Integer)

    # Source and metadata
    source = Column(String(100), index=True)  # linkedin, indeed, adzuna, etc.
    embedding = Column(LargeBinary)  # Vector embedding stored as bytes
    skills_extracted = Column(JSON, default=list, nullable=False)

    # Timestamps and status
    posted_at = Column(DateTime(timezone=True), index=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"
