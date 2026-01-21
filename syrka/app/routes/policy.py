"""Policy routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.policy import PolicyQuery, PolicyRetrievalResult
from app.utils.dependencies import get_current_user, require_role
from app.models.user import UserRole

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/query", response_model=PolicyRetrievalResult)
async def query_policies(
    query: PolicyQuery,
    current_user = Depends(require_role([UserRole.GOVERNMENT, UserRole.EDUCATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Query policy documents."""
    return PolicyRetrievalResult(
        query=query.query,
        results=[],
        answer="Policy RAG not fully initialized"
    )
