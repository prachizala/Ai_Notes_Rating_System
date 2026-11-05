"""
FastAPI Request Dependencies: Authentication, Authorization, CSRF validation.
"""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extracts access token from httpOnly cookie or Authorization header.
    Validates token and returns active User instance.
    """
    token: Optional[str] = None

    # 1. Prefer httpOnly cookie
    if "access_token" in request.cookies:
        token = request.cookies["access_token"]
    # 2. Fallback to Bearer token header
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session identifier.",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token was not found.",
        )

    return user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns the authenticated User or None if anonymous."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


def require_moderator(current_user: User = Depends(get_current_user)) -> User:
    """Enforces that current user has is_moderator=True."""
    if not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required for this action.",
        )
    return current_user


def check_resource_owner(
    resource_owner_id: uuid.UUID,
    current_user: User,
    resource_name: str = "resource",
) -> None:
    """Raises 403 Forbidden if user is neither owner nor moderator."""
    if current_user.id != resource_owner_id and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to modify this {resource_name}.",
        )


async def verify_csrf(request: Request) -> None:
    """
    Validates Double-Submit CSRF Token on mutating HTTP requests when using cookies.
    """
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        # Only require CSRF validation if session cookie is present
        if "access_token" in request.cookies:
            cookie_csrf = request.cookies.get("csrf_token")
            header_csrf = request.headers.get("X-CSRF-Token")
            if not cookie_csrf or not header_csrf or cookie_csrf != header_csrf:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed. Request blocked.",
                )
