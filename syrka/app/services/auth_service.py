"""Authentication service."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password
from app.utils.exceptions import ConflictException, UnauthorizedException


async def register_user(user_data: UserCreate, db: AsyncSession) -> User:
    """Register new user."""
    # Check if email exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException("Email already registered")

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        skills=user_data.skills,
        experience_years=user_data.experience_years,
        location=user_data.location,
        sector_preference=user_data.sector_preference
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    """Authenticate user."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Invalid credentials")

    return user
