"""
User routes - protected endpoints requiring authentication.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Progress, Attempt, Hint
from app.schemas import (
    UserResponse,
    UserUpdate,
    StudentWithStats,
    StudentListResponse,
    AttemptRecord,
    HintAccessRecord,
    ChallengeMetrics,
    ChallengeProgressDetail,
    UnitDetail,
    StudentMetrics,
    ActivityLogEntry,
    StudentDetailResponse,
)
from app.auth import get_current_user, require_teacher
from app.challenges import get_challenge


router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# HELPER FUNCTIONS FOR DETAILED STUDENT VIEW
# ============================================================================


def _get_student_attempts(user_id: int, session: Session) -> list[Attempt]:
    """Get all attempts for a student."""
    statement = select(Attempt).where(Attempt.user_id == user_id)
    return session.exec(statement).all()


def _get_student_hints(user_id: int, session: Session) -> list[Hint]:
    """Get all hint accesses for a student."""
    statement = select(Hint).where(Hint.user_id == user_id)
    return session.exec(statement).all()


def _get_student_progress(user_id: int, session: Session) -> list[Progress]:
    """Get all completed challenges for a student."""
    statement = select(Progress).where(Progress.user_id == user_id)
    return session.exec(statement).all()


def _calculate_challenge_metrics(
    unit_id: int, challenge_id: int, attempts: list[Attempt]
) -> ChallengeMetrics:
    """Calculate metrics for a specific challenge."""
    # Filter attempts for this challenge
    challenge_attempts = [
        a for a in attempts if a.unit_id == unit_id and a.challenge_id == challenge_id
    ]

    total = len(challenge_attempts)
    correct = sum(1 for a in challenge_attempts if a.is_correct)
    success_rate = (correct / total * 100) if total > 0 else 0.0

    # Get last attempted time
    last_attempted = (
        max(a.attempted_at for a in challenge_attempts) if challenge_attempts else None
    )

    return ChallengeMetrics(
        total_attempts=total,
        correct_attempts=correct,
        success_rate=success_rate,
        total_hints_used=0,  # Will update below
        last_attempted=last_attempted or datetime.now(),
    )


def _build_activity_log(
    attempts: list[Attempt], hints: list[Hint], limit: int = 10
) -> list[ActivityLogEntry]:
    """Build activity log from attempts and hints (newest first, limited to N items)."""
    activities = []

    # Add attempts
    for attempt in attempts:
        challenge = get_challenge(attempt.unit_id, attempt.challenge_id)
        action = "Submitted" if attempt.is_correct else "Attempted"
        details = (
            f"{action} challenge (correct)"
            if attempt.is_correct
            else f"{action} challenge"
        )

        activities.append(
            ActivityLogEntry(
                action_type="attempt",
                unit_id=attempt.unit_id,
                challenge_id=attempt.challenge_id,
                challenge_title=challenge.get("title", "Unknown")
                if challenge
                else "Unknown",
                timestamp=attempt.attempted_at,
                details=details,
            )
        )

    # Add hints
    for hint in hints:
        challenge = get_challenge(hint.unit_id, hint.challenge_id)
        activities.append(
            ActivityLogEntry(
                action_type="hint",
                unit_id=hint.unit_id,
                challenge_id=hint.challenge_id,
                challenge_title=challenge.get("title", "Unknown")
                if challenge
                else "Unknown",
                timestamp=hint.accessed_at,
                details=f"Accessed level {hint.hint_level} hint",
            )
        )

    # Sort by timestamp descending (newest first) and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


def _build_detailed_response(
    user: User,
    progress: list[Progress],
    attempts: list[Attempt],
    hints: list[Hint],
    session: Session,
) -> StudentDetailResponse:
    """Build the complete detailed student response."""
    # Build challenge details by unit
    units_dict = {}  # unit_id -> list of ChallengeDetail

    # Add all completed challenges
    for p in progress:
        if p.unit_id not in units_dict:
            units_dict[p.unit_id] = []

        challenge = get_challenge(p.unit_id, p.challenge_id)
        if not challenge:
            continue

        # Get attempts for this challenge
        challenge_attempts = [
            a
            for a in attempts
            if a.unit_id == p.unit_id and a.challenge_id == p.challenge_id
        ]

        # Convert to AttemptRecords
        attempt_records = [
            AttemptRecord(
                unit_id=a.unit_id,
                challenge_id=a.challenge_id,
                query=a.query,
                is_correct=a.is_correct,
                attempted_at=a.attempted_at,
            )
            for a in sorted(challenge_attempts, key=lambda x: x.attempted_at)
        ]

        # Get hints for this challenge
        challenge_hints = [
            h
            for h in hints
            if h.unit_id == p.unit_id and h.challenge_id == p.challenge_id
        ]

        hint_records = [
            HintAccessRecord(
                unit_id=h.unit_id,
                challenge_id=h.challenge_id,
                hint_level=h.hint_level,
                accessed_at=h.accessed_at,
            )
            for h in sorted(challenge_hints, key=lambda x: x.accessed_at)
        ]

        # Calculate metrics
        metrics = _calculate_challenge_metrics(p.unit_id, p.challenge_id, attempts)
        metrics.total_hints_used = len(hint_records)

        # Build challenge detail
        challenge_detail = ChallengeProgressDetail(
            unit_id=p.unit_id,
            challenge_id=p.challenge_id,
            title=challenge.get("title", "Unknown"),
            description=challenge.get("description", ""),
            points=challenge.get("points", 0),
            metrics=metrics,
            attempts=attempt_records,
            hints=hint_records,
        )

        units_dict[p.unit_id].append(challenge_detail)

    # Build units (include all 3 units, even empty ones)
    units = []
    unit_titles = {
        1: "Unit 1: SELECT Basics",
        2: "Unit 2: JOINs",
        3: "Unit 3: Aggregations",
    }

    for unit_id in [1, 2, 3]:
        challenges = units_dict.get(unit_id, [])
        # Sort challenges by challenge_id
        challenges.sort(key=lambda c: c.challenge_id)

        unit_detail = UnitDetail(
            unit_id=unit_id,
            unit_title=unit_titles.get(unit_id, f"Unit {unit_id}"),
            challenges=challenges,
        )
        units.append(unit_detail)

    # Calculate overall metrics
    total_points = sum(p.points_earned for p in progress)
    total_completed = len(progress)
    total_attempts = len(attempts)
    avg_attempts = (total_attempts / total_completed) if total_completed > 0 else 0.0
    correct_attempts = sum(1 for a in attempts if a.is_correct)
    overall_success_rate = (
        (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0.0
    )
    total_hints = len(hints)

    metrics = StudentMetrics(
        total_points=total_points,
        total_challenges_completed=total_completed,
        total_attempts=total_attempts,
        average_attempts_per_challenge=avg_attempts,
        overall_success_rate=overall_success_rate,
        total_hints_used=total_hints,
    )

    # Build activity log
    activity_log = _build_activity_log(attempts, hints, limit=10)

    # Build user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
    )

    return StudentDetailResponse(
        user=user_response,
        metrics=metrics,
        units=units,
        activity_log=activity_log,
    )


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


@router.get("/{user_id}")
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    detailed: bool = Query(default=False),
):
    """
    Get user by ID with optional detailed view (role-based permissions).

    - Teachers can view any user's profile
    - Students can only view their own profile
    - Returns basic UserResponse or detailed StudentDetailResponse based on ?detailed param

    This endpoint requires a valid JWT token in the Authorization header.

    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated user (injected by dependency)
        session: Database session (injected)
        detailed: If True, return detailed view with progress breakdown

    Returns:
        UserResponse (basic) or StudentDetailResponse (detailed)

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

    # Return detailed view if requested
    if detailed:
        progress = _get_student_progress(user_id, session)
        attempts = _get_student_attempts(user_id, session)
        hints = _get_student_hints(user_id, session)
        return _build_detailed_response(user, progress, attempts, hints, session)

    # Return basic user response
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
