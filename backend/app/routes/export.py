"""
Export routes - CSV data export for teachers.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlmodel import Session, select
import csv
from io import StringIO

from app.database import get_session
from app.models import User, Progress, Attempt, Hint
from app.auth import get_current_user, require_teacher


router = APIRouter(prefix="/export", tags=["Export"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _parse_date_string(date_str: str | None) -> datetime | None:
    """
    Parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in YYYY-MM-DD format or None

    Returns:
        datetime object at midnight (00:00:00) or None if not provided
    """
    if date_str is None:
        return None

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")


def _get_last_active(user_id: int, session: Session) -> datetime | None:
    """
    Get most recent activity for a student across all activity types.

    Checks Progress, Attempt, and Hint records to find the latest activity timestamp.

    Args:
        user_id: ID of the student
        session: Database session

    Returns:
        Most recent datetime or None if no activity
    """
    # Get latest from Progress
    progress_stmt = select(func.max(Progress.completed_at)).where(
        Progress.user_id == user_id
    )
    progress_date = session.exec(progress_stmt).one()

    # Get latest from Attempt
    attempt_stmt = select(func.max(Attempt.attempted_at)).where(
        Attempt.user_id == user_id
    )
    attempt_date = session.exec(attempt_stmt).one()

    # Get latest from Hint
    hint_stmt = select(func.max(Hint.accessed_at)).where(Hint.user_id == user_id)
    hint_date = session.exec(hint_stmt).one()

    # Return the maximum of all three
    dates = [d for d in [progress_date, attempt_date, hint_date] if d is not None]
    return max(dates) if dates else None


def _get_student_data(
    session: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """
    Get all students with their aggregated progress data.

    Optionally filters by date range applied to Progress records.

    Args:
        session: Database session
        start_date: Filter to progress on or after this date
        end_date: Filter to progress on or before this date (inclusive)

    Returns:
        List of dicts with: name, email, total_points, challenge_count
    """
    # Build subquery for aggregated progress
    progress_query = select(
        Progress.user_id,
        func.sum(Progress.points_earned).label("total_points"),
        func.count(Progress.id).label("challenge_count"),
    )

    # Apply date filters if provided
    if start_date is not None:
        progress_query = progress_query.where(Progress.completed_at >= start_date)
    if end_date is not None:
        # Add 1 day to end_date to include entire end day (up to 23:59:59)
        end_of_day = end_date.replace(hour=23, minute=59, second=59)
        progress_query = progress_query.where(Progress.completed_at <= end_of_day)

    progress_query = progress_query.group_by(Progress.user_id)
    progress_subquery = progress_query.subquery()

    # Main query: get students with their progress stats
    statement = (
        select(
            User.id,
            User.name,
            User.email,
            progress_subquery.c.total_points,
            progress_subquery.c.challenge_count,
        )
        .outerjoin(progress_subquery, User.id == progress_subquery.c.user_id)
        .where(User.role == "student")
        .order_by(User.name)
    )

    results = session.exec(statement).all()

    # Convert to list of dicts
    students = []
    for row in results:
        students.append(
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "total_points": row.total_points or 0,
                "challenge_count": row.challenge_count or 0,
            }
        )

    return students


def _calculate_completion_percentage(completed: int) -> float:
    """
    Calculate completion percentage based on 7 total challenges.

    Args:
        completed: Number of challenges completed

    Returns:
        Percentage as float (0-100)
    """
    if completed == 0:
        return 0.0

    percentage = (completed / 7) * 100
    return round(percentage, 2)


def _format_datetime(dt: datetime | None) -> str:
    """
    Format datetime for CSV output.

    Args:
        dt: datetime object or None

    Returns:
        Formatted string or "Never" if None
    """
    if dt is None:
        return "Never"

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _build_students_export(
    session: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:
    """
    Build complete CSV export for all students.

    Orchestrates data retrieval and CSV generation.

    Args:
        session: Database session
        start_date: Optional filter start date
        end_date: Optional filter end date

    Returns:
        Complete CSV content as string
    """
    # Get student data
    students = _get_student_data(session, start_date, end_date)

    # Build CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        ["name", "email", "total_points", "completion_percentage", "last_active"]
    )

    # Write data rows
    for student in students:
        # Get last active datetime
        last_active = _get_last_active(student["id"], session)
        last_active_str = _format_datetime(last_active)

        # Calculate completion percentage
        completion_pct = _calculate_completion_percentage(student["challenge_count"])

        # Write row
        writer.writerow(
            [
                student["name"],
                student["email"],
                student["total_points"],
                completion_pct,
                last_active_str,
            ]
        )

    return output.getvalue()


# ============================================================================
# API ENDPOINT
# ============================================================================


@router.get("/students")
async def export_students(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
    start_date: str | None = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
    ),
    end_date: str | None = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
    ),
):
    """
    Export all students and their progress as CSV (teachers only).

    Returns a CSV file with columns:
    - name: Student name
    - email: Student email
    - total_points: Sum of points earned (optionally filtered by date range)
    - completion_percentage: % of 7 challenges completed (optionally filtered)
    - last_active: Most recent activity timestamp

    Optional query parameters:
    - start_date: Filter to progress on or after this date (YYYY-MM-DD)
    - end_date: Filter to progress on or before this date (YYYY-MM-DD)

    Examples:
    - GET /export/students → All students, all time
    - GET /export/students?start_date=2024-01-01 → Since Jan 1, 2024
    - GET /export/students?start_date=2024-01-01&end_date=2024-12-31 → Specific year

    Args:
        current_user: Current authenticated user (must be teacher)
        _: Teacher role check (403 if not teacher)
        session: Database session (injected)
        start_date: Optional filter start date in YYYY-MM-DD format
        end_date: Optional filter end date in YYYY-MM-DD format

    Returns:
        CSV file with students and progress data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a teacher
        HTTPException: 400 if start_date > end_date
        HTTPException: 422 if date format invalid
    """
    # Parse dates
    parsed_start = None
    parsed_end = None

    if start_date:
        parsed_start = _parse_date_string(start_date)

    if end_date:
        parsed_end = _parse_date_string(end_date)

    # Validate date range
    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    # Build CSV content
    csv_content = _build_students_export(session, parsed_start, parsed_end)

    # Return as streaming response
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="students_export.csv"'},
    )
