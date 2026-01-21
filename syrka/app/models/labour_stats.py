"""Labour market statistics model for dashboard analytics."""

from sqlalchemy import Column, String, Float, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class MetricType(str, enum.Enum):
    """Labour market metric types."""
    JOB_POSTINGS = "job_postings"
    UNEMPLOYMENT = "unemployment"
    WAGE_AVG = "wage_avg"
    GROWTH_RATE = "growth_rate"
    SKILLS_SHORTAGE = "skills_shortage"


class LabourStat(Base):
    """
    Labour market statistics for government dashboard.

    Attributes:
        id: Unique identifier (UUID)
        region: Geographic region
        sector: Industry sector
        metric_type: Type of metric being measured
        value: Metric value (float)
        period_start: Start of measurement period
        period_end: End of measurement period
        created_at: Record creation timestamp
    """

    __tablename__ = "labour_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    region = Column(String(255), index=True)
    sector = Column(String(100), index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)

    # Time period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<LabourStat(region='{self.region}', sector='{self.sector}', metric='{self.metric_type}', value={self.value})>"
