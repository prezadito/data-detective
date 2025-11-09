"""
User routes - protected endpoints requiring authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Progress
from app.schemas import (
    UserResponse,
    UserUpdate,
    StudentWithStats,
    StudentListResponse,
)
from app.auth import get_current_user, require_teacher


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=StudentListResponse)
async def list_all_users(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
    role: str | None = None,
    sort: str = Query(
        default="name", pattern="^(name|points|date)$"
    ),  # Validate sort parameter
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """
    List all users with filtering, sorting, and pagination (teachers only).

    Teachers can view all students in the system with their progress statistics.
    Results can be filtered by role, sorted by name/points/date, and paginated.

    Query Parameters:
        role: Filter by user role (student|teacher). Optional.
        sort: Sort by field (name|points|date). Default: name
        offset: Pagination offset. Default: 0
        limit: Pagination limit (1-100). Default: 10

    Returns:
        StudentListResponse with paginated students and their aggregated stats

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not a teacher
        HTTPException: 422 if validation fails (invalid sort or limit)
    """
    # Build aggregation subquery to get stats per user
    stats_subquery = (
        select(
            Progress.user_id,
            func.sum(Progress.points_earned).label("total_points"),
            func.count(Progress.id).label("challenges_completed"),
        )
        .group_by(Progress.user_id)
        .subquery()
    )

    # Build main query with LEFT JOIN to stats subquery
    statement = select(
        User.id,
        User.email,
        User.name,
        User.role,
        User.created_at,
        stats_subquery.c.total_points,
        stats_subquery.c.challenges_completed,
    ).outerjoin(stats_subquery, User.id == stats_subquery.c.user_id)

    # Filter by role if provided
    if role:
        statement = statement.where(User.role == role)

    # Sort based on parameter
    if sort == "name":
        statement = statement.order_by(User.name)
    elif sort == "points":
        # Sort by total_points descending, then by name for tie-breaking
        statement = statement.order_by(
            stats_subquery.c.total_points.desc().nullslast(), User.name
        )
    elif sort == "date":
        # Sort by created_at ascending
        statement = statement.order_by(User.created_at)

    # Get total count BEFORE pagination
    count_query = select(func.count(User.id)).select_from(User)
    if role:
        count_query = count_query.where(User.role == role)

    total_count = session.exec(count_query).one()

    # Apply pagination
    statement = statement.offset(offset).limit(limit)

    # Execute main query
    results = session.exec(statement).all()

    # Build StudentWithStats objects from results
    students = []
    for row in results:
        students.append(
            StudentWithStats(
                id=row.id,
                email=row.email,
                name=row.name,
                role=row.role,
                created_at=row.created_at,
                total_points=row.total_points or 0,
                challenges_completed=row.challenges_completed or 0,
            )
        )

    return StudentListResponse(
        students=students,
        total_count=total_count,
        offset=offset,
        limit=limit,
    )


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
