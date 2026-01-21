"""Curriculum generation models for education alignment layer."""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Curriculum(Base):
    """
    Curriculum model representing a complete training program.

    Attributes:
        id: Unique identifier (UUID)
        title: Curriculum title
        description: Curriculum description
        target_sector: Target industry sector
        target_skills: JSON array of skills this curriculum develops
        policy_alignment_score: Score indicating alignment with national policies
        created_by: User ID who created this curriculum
        created_at: Creation timestamp
    """

    __tablename__ = "curricula"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    target_sector = Column(String(100), index=True)
    target_skills = Column(JSON, default=list, nullable=False)
    policy_alignment_score = Column(Float, default=0.0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Curriculum(id={self.id}, title='{self.title}')>"


class CurriculumModule(Base):
    """
    Module within a curriculum (e.g., "Database Design", "API Development").

    Attributes:
        id: Unique identifier (UUID)
        curriculum_id: Foreign key to Curriculum
        order_index: Sequential order within curriculum
        title: Module title
        description: Module description
        duration_hours: Estimated duration in hours
    """

    __tablename__ = "curriculum_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    curriculum_id = Column(UUID(as_uuid=True), ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    duration_hours = Column(Integer, default=0)

    # Relationship
    curriculum = relationship("Curriculum", backref="modules")

    def __repr__(self) -> str:
        return f"<CurriculumModule(id={self.id}, title='{self.title}', order={self.order_index})>"


class CurriculumUnit(Base):
    """
    Unit within a module containing specific competencies and assessments.

    Attributes:
        id: Unique identifier (UUID)
        module_id: Foreign key to CurriculumModule
        order_index: Sequential order within module
        title: Unit title
        competencies: JSON array of competency objects
        learning_outcomes: JSON array of learning outcome objects
        assessment_criteria: JSON object defining assessment
        microcredential_id: Optional reference to microcredential
    """

    __tablename__ = "curriculum_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)

    # Structured content stored as JSON
    competencies = Column(JSON, default=list, nullable=False)
    learning_outcomes = Column(JSON, default=list, nullable=False)
    assessment_criteria = Column(JSON, default=dict, nullable=False)
    microcredential_id = Column(String(255))

    # Relationship
    module = relationship("CurriculumModule", backref="units")

    def __repr__(self) -> str:
        return f"<CurriculumUnit(id={self.id}, title='{self.title}', order={self.order_index})>"
