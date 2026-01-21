"""Job matching routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.matching import MatchListResponse
from app.utils.dependencies import get_current_user
from app.matching.engine import MatchingEngine
from app.rag.embeddings import EmbeddingService

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/match", response_model=MatchListResponse)
async def match_jobs(
    limit: int = 20,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get matched jobs for current user."""
    embedding_service = EmbeddingService()
    engine = MatchingEngine(embedding_service)

    matches = await engine.match(current_user, db, limit=limit)

    return MatchListResponse(
        matches=matches,
        total_candidates=len(matches),
        user_id=current_user.id
    )
