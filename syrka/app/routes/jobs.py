"""Job routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobListResponse, JobFilters
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    sector: str = None,
    location: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List jobs."""
    stmt = select(Job).where(Job.is_active == True)

    if sector:
        stmt = stmt.where(Job.sector == sector)
    if location:
        stmt = stmt.where(Job.location.contains(location))

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Count total
    count_stmt = select(Job).where(Job.is_active == True)
    total_result = await db.execute(count_stmt)
    total = len(total_result.scalars().all())

    return JobListResponse(jobs=jobs, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get job by ID."""
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one()

    return job
