"""Heatmap generation for labour market visualization."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta

from app.models.job import Job
from app.models.labour_stats import LabourStat

logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """Generate heat maps for labour market data."""

    async def generate_job_heatmap(
        self,
        db: AsyncSession,
        regions: list[str] = None,
        sectors: list[str] = None
    ) -> dict:
        """Generate job posting heatmap by region/sector."""
        # Query job counts by region and sector
        stmt = select(
            Job.sector,
            Job.location,
            func.count(Job.id).label('count')
        ).where(Job.is_active == True).group_by(Job.sector, Job.location)

        if sectors:
            stmt = stmt.where(Job.sector.in_(sectors))

        result = await db.execute(stmt)
        data = result.all()

        cells = []
        for sector, location, count in data:
            cells.append({
                'region': location or 'Unknown',
                'sector': sector or 'General',
                'value': float(count)
            })

        return {
            'title': 'Job Postings by Region and Sector',
            'cells': cells
        }

    async def generate_skill_heatmap(
        self,
        db: AsyncSession,
        skills: list[str],
        regions: list[str] = None
    ) -> dict:
        """Generate skill demand heatmap."""
        from app.models.skill import SkillDemand

        stmt = select(
            SkillDemand.region,
            SkillDemand.demand_count
        )

        result = await db.execute(stmt)
        data = result.all()

        cells = [{
            'region': region,
            'sector': 'Skills',
            'value': float(demand_count)
        } for region, demand_count in data]

        return {'title': 'Skill Demand by Region', 'cells': cells}

    async def generate_salary_heatmap(
        self,
        db: AsyncSession,
        sectors: list[str],
        regions: list[str]
    ) -> dict:
        """Generate average salary heatmap."""
        stmt = select(
            Job.sector,
            Job.location,
            func.avg((Job.salary_min + Job.salary_max) / 2).label('avg_salary')
        ).where(
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None)
        ).group_by(Job.sector, Job.location)

        result = await db.execute(stmt)
        data = result.all()

        cells = [{
            'region': location or 'Unknown',
            'sector': sector or 'General',
            'value': float(avg_salary) if avg_salary else 0.0
        } for sector, location, avg_salary in data]

        return {'title': 'Average Salary by Region/Sector', 'cells': cells}
