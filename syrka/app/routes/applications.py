"""Application routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.utils.dependencies import get_current_user
from app.automation.applicator import ApplicationAutomator

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's applications."""
    stmt = select(Application).where(Application.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ApplicationResponse)
async def create_application(
    app_data: ApplicationCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create application."""
    stmt = select(Job).where(Job.id == app_data.job_id)
    result = await db.execute(stmt)
    job = result.scalar_one()

    automator = ApplicationAutomator()
    application = await automator.prepare_application(current_user, job, db)

    return application


@router.post("/{app_id}/send", response_model=ApplicationResponse)
async def send_application(
    app_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send application."""
    stmt = select(Application).where(
        Application.id == app_id,
        Application.user_id == current_user.id
    )
    result = await db.execute(stmt)
    application = result.scalar_one()

    automator = ApplicationAutomator()
    application = await automator.send_application(application, db)

    return application
