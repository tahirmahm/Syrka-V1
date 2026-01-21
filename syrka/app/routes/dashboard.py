"""Dashboard routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dashboard import DashboardOverview
from app.utils.dependencies import require_role
from app.models.user import UserRole
from app.dashboard.aggregator import DashboardAggregator

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(
    current_user = Depends(require_role([UserRole.GOVERNMENT])),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard overview."""
    aggregator = DashboardAggregator()
    stats = await aggregator.get_overview_stats(db)

    return DashboardOverview(**stats)
