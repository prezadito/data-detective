"""
Reports routes - weekly progress summaries for teachers.
"""

import time
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Progress
from app.schemas import (
    WeeklyReportResponse,
    StudentProgressSummary,
)
from app.auth import get_current_user, require_teacher


router = APIRouter(prefix="/reports", tags=["Reports"])

# In-memory cache with TTL
_weekly_cache = {"data": None, "timestamp": None}
CACHE_TTL = 60 * 60  # 1 hour in seconds


# ============================================================================
# CACHE MANAGEMENT FUNCTIONS
# ============================================================================


def _is_cache_valid() -> bool:
    """
    Check if weekly report cache exists and hasn't expired.

    Returns:
        True if cache is valid and fresh, False otherwise
    """
    if _weekly_cache["data"] is None or _weekly_cache["timestamp"] is None:
        return False
    elapsed = time.time() - _weekly_cache["timestamp"]
    return elapsed < CACHE_TTL


def invalidate_weekly_cache() -> None:
    """
    Invalidate the weekly report cache.

    Called after new progress submissions to ensure fresh data.
    This function can be imported and called from other modules.
    """
    _weekly_cache["data"] = None
    _weekly_cache["timestamp"] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_cutoff_time() -> datetime:
    """
    Get datetime for 7 days ago (timezone-aware, UTC).

    Returns:
        Datetime representing 7 days in the past
    """
    return datetime.now(timezone.utc) - timedelta(days=7)


def _build_weekly_report(session: Session) -> WeeklyReportResponse:
    """
    Query database and build weekly progress report.

    Aggregates student progress from past 7 days and provides:
    - Count of active students
    - Total completions
    - Average points per student
    - Top 5 performers by points
    - Struggling students (<3 completions)

    Args:
        session: Database session

    Returns:
        WeeklyReportResponse with aggregated metrics
    """
    cutoff_time = _get_cutoff_time()

    # Query: aggregate progress by student for past 7 days
    # Only include students, exclude teachers
    statement = (
        select(
            User.id,
            User.name,
            func.sum(Progress.points_earned).label("total_points"),
            func.count(Progress.id).label("challenge_count"),
        )
        .join(Progress, User.id == Progress.user_id)
        .where(User.role == "student", Progress.completed_at >= cutoff_time)
        .group_by(User.id, User.name)
        .order_by(func.sum(Progress.points_earned).desc(), User.id)
    )

    results = session.exec(statement).all()

    # If no data, return empty report
    if not results:
        return WeeklyReportResponse(
            students_active=0,
            total_completions=0,
            avg_points_per_student=0.0,
            top_performers=[],
            struggling_students=[],
            generated_at=datetime.now(timezone.utc),
        )

    # Build lists of summaries
    student_summaries = [
        StudentProgressSummary(
            student_name=name,
            completions_this_week=challenge_count or 0,
            points_this_week=total_points or 0,
        )
        for user_id, name, total_points, challenge_count in results
    ]

    # Calculate statistics
    students_active = len(student_summaries)
    total_completions = sum(s.completions_this_week for s in student_summaries)
    total_points_all = sum(s.points_this_week for s in student_summaries)
    avg_points = total_points_all / students_active if students_active > 0 else 0.0

    # Top performers: sorted by points DESC (already sorted from query)
    top_performers = student_summaries[:5]

    # Struggling students: <3 completions
    struggling_students = [s for s in student_summaries if s.completions_this_week < 3]

    return WeeklyReportResponse(
        students_active=students_active,
        total_completions=total_completions,
        avg_points_per_student=avg_points,
        top_performers=top_performers,
        struggling_students=struggling_students,
        generated_at=datetime.now(timezone.utc),
    )


# ============================================================================
# PUBLIC ENDPOINT
# ============================================================================


@router.get(
    "/weekly", response_model=WeeklyReportResponse, status_code=status.HTTP_200_OK
)
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get weekly progress report (teacher-only).

    Returns aggregated metrics for all students:
    - Students active in past 7 days
    - Total challenges completed
    - Average points per active student
    - Top 5 performers by points
    - Struggling students (<3 completions)

    The report is cached for 1 hour to improve performance.
    Cache is invalidated when new progress submissions are made.

    Args:
        current_user: Current authenticated user (must be teacher)
        _: Teacher role check (403 if not teacher)
        session: Database session (injected)

    Returns:
        WeeklyReportResponse with aggregated metrics

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a teacher
    """
    # Check if cache is valid
    if _is_cache_valid():
        return _weekly_cache["data"]

    # Query database and build report
    data = _build_weekly_report(session)

    # Store in cache with timestamp
    _weekly_cache["data"] = data
    _weekly_cache["timestamp"] = time.time()

    return data
