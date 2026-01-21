"""Dashboard-related Pydantic schemas for government analytics."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class HeatmapRequest(BaseModel):
    """Schema for heatmap generation request."""
    regions: Optional[list[str]] = None
    sectors: Optional[list[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HeatmapCell(BaseModel):
    """Schema for a single heatmap cell."""
    region: str
    sector: str
    value: float
    label: Optional[str] = None


class HeatmapResponse(BaseModel):
    """Schema for heatmap data response."""
    title: str
    description: str
    cells: list[HeatmapCell]
    regions: list[str]
    sectors: list[str]
    min_value: float
    max_value: float


class SkillShortage(BaseModel):
    """Schema for skill shortage information."""
    skill_name: str
    sector: Optional[str]
    region: Optional[str]
    demand_count: int
    supply_count: int
    shortage_ratio: float = Field(..., description="demand/supply ratio, higher = worse shortage")
    severity: str = Field(..., description="critical/high/moderate/low")


class ShortageResponse(BaseModel):
    """Schema for skills shortage response."""
    shortages: list[SkillShortage]
    total_critical: int
    total_high: int
    period_start: date
    period_end: date


class ForecastRequest(BaseModel):
    """Schema for demand forecasting request."""
    skill: Optional[str] = None
    sector: Optional[str] = None
    years: int = Field(default=3, ge=1, le=10)


class ForecastDataPoint(BaseModel):
    """Schema for a single forecast data point."""
    year: int
    predicted_demand: float
    confidence_interval_low: float
    confidence_interval_high: float


class ForecastResponse(BaseModel):
    """Schema for forecast response."""
    skill: Optional[str]
    sector: Optional[str]
    forecast: list[ForecastDataPoint]
    trend: str = Field(..., description="increasing/decreasing/stable")
    growth_rate: float


class DashboardOverview(BaseModel):
    """Schema for dashboard overview statistics."""
    total_jobs: int
    active_jobs: int
    total_applications: int
    total_users: int
    total_skills_tracked: int
    critical_shortages: int
    top_sectors: list[dict]
    top_regions: list[dict]
    recent_activity: dict


class PolicyAlignmentMetrics(BaseModel):
    """Schema for policy alignment metrics."""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    sector_scores: dict[str, float]
    aligned_curricula_count: int
    total_curricula_count: int
    top_aligned_skills: list[str]
    gaps: list[dict] = Field(default_factory=list, description="Areas where policy priorities lack workforce alignment")
