"""
User routes - protected endpoints requiring authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import UserResponse, UserUpdate
from app.auth import get_current_user, require_teacher


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
async def list_all_users(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    List all users (teachers only).

    This endpoint returns a list of all registered users in the system.
    Only users with the 'teacher' role can access this endpoint.

    Args:
        current_user: Current authenticated user (injected by dependency)
        _: Permission check (teacher role required)
        session: Database session (injected)

    Returns:
        List of all users (without passwords)

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not a teacher
    """
    # Get all users from database
    statement = select(User)
    users = session.exec(statement).all()

    return users


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
    Get user by ID with role-based permissions.

    - Teachers can view any user's profile
    - Students can only view their own profile

    This endpoint requires a valid JWT token in the Authorization header.

    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated user (injected by dependency)
        session: Database session (injected)

    Returns:
        User data for requested user_id (without password)

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if student tries to view another user
        HTTPException: 404 if user not found
    """
    # Permission check: students can only view their own profile
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )

    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Update current authenticated user's profile.

    Only allows updating name. Email and role cannot be changed for security.
    Requires valid JWT token in Authorization header.

    Args:
        user_update: Updated user data (name only)
        current_user: Current authenticated user (injected by dependency)
        session: Database session (injected)

    Returns:
        Updated user data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 422 if validation fails (name too short/long)
    """
    # Update user name
    current_user.name = user_update.name
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user
