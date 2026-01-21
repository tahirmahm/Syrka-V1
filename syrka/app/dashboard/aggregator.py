"""Dashboard data aggregation."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.job import Job
from app.models.user import User
from app.models.application import Application

logger = logging.getLogger(__name__)


class DashboardAggregator:
    """Aggregate dashboard statistics."""

    async def get_overview_stats(self, db: AsyncSession) -> dict:
        """Get overview statistics."""
        # Count total jobs
        stmt = select(func.count(Job.id))
        result = await db.execute(stmt)
        total_jobs = result.scalar() or 0

        # Count active jobs
        stmt = select(func.count(Job.id)).where(Job.is_active == True)
        result = await db.execute(stmt)
        active_jobs = result.scalar() or 0

        # Count applications
        stmt = select(func.count(Application.id))
        result = await db.execute(stmt)
        total_applications = result.scalar() or 0

        # Count users
        stmt = select(func.count(User.id))
        result = await db.execute(stmt)
        total_users = result.scalar() or 0

        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'total_users': total_users,
            'total_skills_tracked': 0,
            'critical_shortages': 0,
            'top_sectors': [],
            'top_regions': [],
            'recent_activity': {}
        }

    async def get_sector_breakdown(self, db: AsyncSession) -> list[dict]:
        """Get job distribution by sector."""
        stmt = select(
            Job.sector,
            func.count(Job.id)
        ).group_by(Job.sector)

        result = await db.execute(stmt)
        return [{'sector': sector, 'count': count} for sector, count in result.all()]

    async def get_regional_breakdown(self, db: AsyncSession) -> list[dict]:
        """Get job distribution by region."""
        stmt = select(
            Job.location,
            func.count(Job.id)
        ).group_by(Job.location)

        result = await db.execute(stmt)
        return [{'region': location, 'count': count} for location, count in result.all()]

    async def get_policy_alignment_metrics(self, db: AsyncSession) -> dict:
        """Get policy alignment metrics."""
        return {
            'overall_score': 0.75,
            'sector_scores': {},
            'aligned_curricula_count': 0,
            'total_curricula_count': 0,
            'top_aligned_skills': [],
            'gaps': []
        }
