"""Job matching-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.schemas.job import JobResponse


class MatchScores(BaseModel):
    """Breakdown of match scoring components."""
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    skill_overlap: float = Field(..., ge=0.0, le=1.0)
    location_score: float = Field(..., ge=0.0, le=1.0)
    seniority_score: float = Field(..., ge=0.0, le=1.0)
    sector_score: float = Field(..., ge=0.0, le=1.0)


class MatchResult(BaseModel):
    """Schema for a single job match result."""
    job: JobResponse
    match_probability: float = Field(..., ge=0.0, le=1.0, description="Overall match probability")
    scores: MatchScores
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    """Schema for job matching request."""
    user_id: Optional[uuid.UUID] = None  # If None, use current user
    limit: int = Field(default=20, ge=1, le=100)
    min_probability: float = Field(default=0.3, ge=0.0, le=1.0)
    filters: Optional[dict] = None


class MatchListResponse(BaseModel):
    """Schema for match results response."""
    matches: list[MatchResult]
    total_candidates: int
    user_id: uuid.UUID


class MatchExplanation(BaseModel):
    """Detailed explanation of a specific match."""
    job_id: uuid.UUID
    user_id: uuid.UUID
    match_probability: float
    scores: MatchScores
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str] = Field(default_factory=list, description="Recommendations to improve match")
