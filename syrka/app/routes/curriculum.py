"""Curriculum routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.curriculum import CurriculumRequest, CurriculumResponse
from app.utils.dependencies import get_current_user
from app.curriculum.generator import CurriculumGenerator

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.post("/generate", response_model=dict)
async def generate_curriculum(
    request: CurriculumRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate curriculum."""
    generator = CurriculumGenerator()
    curriculum = generator.generate_curriculum(
        sector=request.sector,
        skills=request.skills,
        policy_context=request.include_policy_alignment
    )

    return curriculum.model_dump()
