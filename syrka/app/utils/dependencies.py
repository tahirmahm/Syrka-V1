"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import verify_token
from app.utils.exceptions import UnauthorizedException, ForbiddenException

# Security scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        UnauthorizedException: If token is invalid or user not found
    """
    token = credentials.credentials
    email = verify_token(token)

    if email is None:
        raise UnauthorizedException("Invalid authentication credentials")

    # Fetch user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("User not found")

    return user


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of roles allowed to access the endpoint

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin", dependencies=[Depends(require_role([UserRole.GOVERNMENT]))])
        async def admin_endpoint():
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user

    return role_checker


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.

    Useful for endpoints that behave differently for authenticated vs anonymous users.

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        email = verify_token(token)

        if email is None:
            return None

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        return user
    except Exception:
        return None
