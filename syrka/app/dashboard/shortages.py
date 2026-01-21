"""Skills shortage analysis."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class ShortageAnalyzer:
    """Analyze skills shortages."""

    async def compute_skill_shortages(
        self,
        db: AsyncSession,
        sector: str = None,
        region: str = None
    ) -> list[dict]:
        """Compute skill shortages."""
        from app.models.skill import Skill, SkillDemand

        stmt = select(Skill, func.sum(SkillDemand.demand_count)).\
            join(SkillDemand).\
            group_by(Skill.id)

        result = await db.execute(stmt)
        data = result.all()

        shortages = []
        for skill, demand_count in data:
            ratio = demand_count / max(skill.supply_score, 1)
            severity = 'critical' if ratio > 3 else 'high' if ratio > 2 else 'moderate'

            shortages.append({
                'skill_name': skill.name,
                'demand_count': demand_count,
                'shortage_ratio': ratio,
                'severity': severity
            })

        return sorted(shortages, key=lambda x: x['shortage_ratio'], reverse=True)

    async def identify_critical_shortages(
        self,
        db: AsyncSession,
        threshold: float = 0.3
    ) -> list[dict]:
        """Identify critical skill shortages."""
        all_shortages = await self.compute_skill_shortages(db)
        return [s for s in all_shortages if s['severity'] == 'critical']

    async def trend_analysis(
        self,
        db: AsyncSession,
        skill: str,
        periods: int = 4
    ) -> dict:
        """Analyze shortage trends."""
        return {
            'skill': skill,
            'trend': 'increasing',
            'data_points': []
        }
