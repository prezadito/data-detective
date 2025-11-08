"""
User routes - protected endpoints requiring authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models import User
from app.schemas import UserResponse
from app.auth import get_current_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user.

    This endpoint requires a valid JWT token in the Authorization header.

    Args:
        current_user: Current authenticated user (injected by dependency)

    Returns:
        Current user data (without password)
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get user by ID (requires authentication).

    Any authenticated user can view any other user's profile.
    This endpoint requires a valid JWT token in the Authorization header.

    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated user (injected by dependency)
        session: Database session (injected)

    Returns:
        User data for requested user_id (without password)

    Raises:
        HTTPException: 404 if user not found
    """
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user
