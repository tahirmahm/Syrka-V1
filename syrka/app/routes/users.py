"""User management routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserProfile, UserUpdate
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user = Depends(get_current_user)):
    """Get user profile."""
    return current_user


@router.patch("/profile", response_model=UserProfile)
async def update_profile(
    updates: UserUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    await db.flush()
    await db.refresh(current_user)

    return current_user
