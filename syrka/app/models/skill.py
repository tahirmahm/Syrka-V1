"""Skill taxonomy and demand tracking models."""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, LargeBinary, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Skill(Base):
    """
    Skill taxonomy model for standardized skill naming.

    Attributes:
        id: Unique identifier
        name: Skill name (unique)
        category: Skill category (technical, soft, domain, etc.)
        embedding: Vector embedding for skill similarity
        demand_score: Current overall demand score (0-100)
        supply_score: Current overall supply score (0-100)
    """

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), index=True)
    embedding = Column(LargeBinary)  # Vector embedding for skill matching
    demand_score = Column(Float, default=0.0)
    supply_score = Column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class SkillDemand(Base):
    """
    Time-series model tracking skill demand by sector and region.

    Attributes:
        id: Unique identifier (UUID)
        skill_id: Foreign key to Skill
        sector: Industry sector
        region: Geographic region
        demand_count: Number of job postings requiring this skill
        period_start: Start of measurement period
        period_end: End of measurement period
        created_at: Record creation timestamp
    """

    __tablename__ = "skill_demands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    sector = Column(String(100), index=True)
    region = Column(String(255), index=True)
    demand_count = Column(Integer, default=0, nullable=False)

    # Time period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    skill = relationship("Skill", backref="demands")

    def __repr__(self) -> str:
        return f"<SkillDemand(skill_id={self.skill_id}, sector='{self.sector}', region='{self.region}', count={self.demand_count})>"
