"""Pydantic models for curriculum structure (duplicates from schemas for internal use)."""

from pydantic import BaseModel, Field
from typing import Optional


class Competency(BaseModel):
    """Competency model."""
    name: str
    description: str
    proficiency_level: str


class LearningOutcome(BaseModel):
    """Learning outcome model."""
    statement: str
    bloom_level: str
    measurable_criteria: str


class Assessment(BaseModel):
    """Assessment model."""
    type: str
    criteria: list[str]
    weight: float
    rubric: Optional[dict] = None


class Microcredential(BaseModel):
    """Microcredential model."""
    name: str
    skills: list[str]
    duration: int
    badge_criteria: str


class Unit(BaseModel):
    """Curriculum unit model."""
    title: str
    competencies: list[Competency]
    outcomes: list[LearningOutcome]
    assessments: list[Assessment]
    microcredential: Optional[Microcredential] = None
    duration_hours: int = 0


class Module(BaseModel):
    """Curriculum module model."""
    title: str
    description: str
    units: list[Unit]
    total_duration: int


class FullCurriculum(BaseModel):
    """Complete curriculum model."""
    title: str
    modules: list[Module]
    target_sector: str
    target_skills: list[str]
    policy_alignment: float = 0.0
