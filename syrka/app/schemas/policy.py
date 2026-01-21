"""Policy document-related Pydantic schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class PolicyUpload(BaseModel):
    """Schema for policy document upload metadata."""
    title: str = Field(..., min_length=1, max_length=500)
    source_url: Optional[str] = None
    country: str
    document_type: str = Field(..., description="national_plan/sector_strategy/education_policy/etc")


class PolicyResponse(BaseModel):
    """Schema for policy document response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_url: Optional[str]
    file_path: str
    processed_at: datetime
    country: str
    document_type: str
    chunk_count: Optional[int] = None


class PolicyQuery(BaseModel):
    """Schema for RAG query over policy documents."""
    query: str = Field(..., min_length=1)
    sector: Optional[str] = None
    country: Optional[str] = None
    document_type: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class PolicyChunkResult(BaseModel):
    """Schema for a retrieved policy chunk."""
    document_id: uuid.UUID
    document_title: str
    content: str
    similarity_score: float
    metadata: dict


class PolicyRetrievalResult(BaseModel):
    """Schema for policy retrieval response."""
    query: str
    results: list[PolicyChunkResult]
    answer: Optional[str] = None  # Generated answer using RAG


class PolicyPriority(BaseModel):
    """Schema for extracted policy priority."""
    sector: str
    priority: str
    description: str
    skills_mentioned: list[str]
    source_document: str
