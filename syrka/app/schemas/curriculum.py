"""Curriculum-related Pydantic schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class CompetencySchema(BaseModel):
    """Schema for a competency within a unit."""
    name: str
    description: str
    proficiency_level: str = Field(..., description="Beginner/Intermediate/Advanced/Expert")


class LearningOutcomeSchema(BaseModel):
    """Schema for a learning outcome."""
    statement: str = Field(..., description="What learner will be able to do")
    bloom_level: str = Field(..., description="Remember/Understand/Apply/Analyze/Evaluate/Create")
    measurable_criteria: str


class AssessmentSchema(BaseModel):
    """Schema for assessment criteria."""
    type: str = Field(..., description="Quiz/Project/Exam/Portfolio")
    criteria: list[str]
    weight: float = Field(..., ge=0.0, le=1.0)
    rubric: Optional[dict] = None


class MicrocredentialSchema(BaseModel):
    """Schema for microcredential."""
    name: str
    skills: list[str]
    duration: int = Field(..., description="Duration in hours")
    badge_criteria: str


class UnitResponse(BaseModel):
    """Schema for curriculum unit response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    order_index: int
    title: str
    competencies: list[dict]
    learning_outcomes: list[dict]
    assessment_criteria: dict
    microcredential_id: Optional[str]


class ModuleResponse(BaseModel):
    """Schema for curriculum module response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    curriculum_id: uuid.UUID
    order_index: int
    title: str
    description: Optional[str]
    duration_hours: int
    units: list[UnitResponse] = Field(default_factory=list)


class CurriculumResponse(BaseModel):
    """Schema for curriculum response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    target_sector: Optional[str]
    target_skills: list[str]
    policy_alignment_score: float
    created_by: Optional[uuid.UUID]
    created_at: datetime
    modules: list[ModuleResponse] = Field(default_factory=list)


class CurriculumRequest(BaseModel):
    """Schema for curriculum generation request."""
    sector: str = Field(..., min_length=1)
    skills: list[str] = Field(..., min_items=1)
    include_policy_alignment: bool = True
    max_modules: int = Field(default=6, ge=1, le=10)
    target_duration_hours: Optional[int] = Field(None, ge=10, le=500)


class CurriculumExport(BaseModel):
    """Schema for curriculum export."""
    curriculum_id: uuid.UUID
    format: str = Field(..., description="json/scorm/markdown")


class CurriculumExportResponse(BaseModel):
    """Schema for curriculum export response."""
    format: str
    content: str
    filename: str
