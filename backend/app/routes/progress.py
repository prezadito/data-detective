"""
Progress routes - challenge submission and progress tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models import User, Progress
from app.schemas import (
    ChallengeSubmitRequest,
    ProgressResponse,
    ProgressDetailResponse,
    ProgressSummaryStats,
    ProgressSummaryResponse,
)
from app.auth import get_current_user, require_student, require_teacher
from app.challenges import get_challenge


router = APIRouter(prefix="/progress", tags=["Progress"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _build_progress_detail(progress: Progress) -> ProgressDetailResponse:
    """
    Convert Progress model to ProgressDetailResponse with challenge title.

    Looks up the challenge title from the CHALLENGES dict and enriches
    the progress record for API response.

    Args:
        progress: Progress database model instance

    Returns:
        ProgressDetailResponse with all fields including challenge_title
    """
    challenge = get_challenge(progress.unit_id, progress.challenge_id) or {}
    return ProgressDetailResponse(
        id=progress.id,
        user_id=progress.user_id,
        unit_id=progress.unit_id,
        challenge_id=progress.challenge_id,
        points_earned=progress.points_earned,
        hints_used=progress.hints_used,
        completed_at=progress.completed_at,
        query=progress.query,
        challenge_title=challenge.get("title", "Unknown Challenge"),
    )


def _calculate_summary_stats(progress_items: list[Progress]) -> ProgressSummaryStats:
    """
    Calculate aggregate statistics from progress list.

    Computes total points earned, count of completed challenges, and
    completion percentage based on 7 total challenges in the system.

    Args:
        progress_items: List of Progress model instances

    Returns:
        ProgressSummaryStats with calculated values
    """
    total_points = sum(p.points_earned for p in progress_items)
    total_completed = len(progress_items)
    # Calculate percentage based on 7 total challenges in system
    completion_percentage = (total_completed / 7) * 100
    return ProgressSummaryStats(
        total_points=total_points,
        total_completed=total_completed,
        completion_percentage=completion_percentage,
    )


def _get_progress_summary(user_id: int, session: Session) -> ProgressSummaryResponse:
    """
    Get complete progress summary for a user.

    Queries all progress records for the user, ordered by unit_id and
    challenge_id, enriches them with challenge titles, and calculates
    summary statistics.

    Args:
        user_id: ID of user to get progress for
        session: Database session

    Returns:
        ProgressSummaryResponse with ordered progress items and summary stats
    """
    statement = (
        select(Progress)
        .where(Progress.user_id == user_id)
        .order_by(Progress.unit_id, Progress.challenge_id)
    )
    progress_records = session.exec(statement).all()
    progress_items = [_build_progress_detail(p) for p in progress_records]
    summary = _calculate_summary_stats(progress_records)
    return ProgressSummaryResponse(progress_items=progress_items, summary=summary)


@router.post("/submit", response_model=ProgressResponse, status_code=status.HTTP_200_OK)
async def submit_challenge(
    submission: ChallengeSubmitRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_student),
    session: Session = Depends(get_session),
):
    """
    Submit a challenge solution (student-only).

    Students submit their SQL query for a specific challenge.
    The endpoint:
    1. Validates the challenge exists
    2. Records the submission (without validating the query - MVP)
    3. Awards points based on challenge definition
    4. Returns idempotent responses (duplicate submissions return existing record)

    Args:
        submission: Challenge submission data (unit_id, challenge_id, query, hints_used)
        current_user: Current authenticated user (injected from JWT)
        _: Student role check (403 if not student)
        session: Database session (injected)

    Returns:
        Progress record with points earned

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a student
        HTTPException: 404 if challenge doesn't exist
    """
    # 1. Validate challenge exists
    challenge = get_challenge(submission.unit_id, submission.challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge not found: unit={submission.unit_id}, challenge={submission.challenge_id}",
        )

    # 2. Check if already completed (idempotency)
    statement = select(Progress).where(
        Progress.user_id == current_user.id,
        Progress.unit_id == submission.unit_id,
        Progress.challenge_id == submission.challenge_id,
    )
    existing_progress = session.exec(statement).first()

    if existing_progress:
        # Already completed - return existing record (idempotent)
        return existing_progress

    # 3. Create new progress record
    progress = Progress(
        user_id=current_user.id,  # From JWT token - no spoofing!
        unit_id=submission.unit_id,
        challenge_id=submission.challenge_id,
        points_earned=challenge["points"],  # From challenge definition
        hints_used=submission.hints_used,
        query=submission.query,
    )

    try:
        session.add(progress)
        session.commit()
        session.refresh(progress)
        return progress

    except IntegrityError:
        # Race condition: another request created it
        # Rollback and return existing
        session.rollback()
        existing_progress = session.exec(statement).first()
        return existing_progress


@router.get("/me", response_model=ProgressSummaryResponse)
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get current user's progress (any authenticated user).

    Returns all completed challenges with detailed information and
    summary statistics including total points, completion count,
    and completion percentage.

    Any authenticated user (student or teacher) can view their own
    progress using this endpoint.

    Args:
        current_user: Current authenticated user (injected from JWT)
        session: Database session (injected)

    Returns:
        ProgressSummaryResponse with progress items and summary stats

    Raises:
        HTTPException: 401 if not authenticated
    """
    return _get_progress_summary(current_user.id, session)


@router.get("/user/{user_id}", response_model=ProgressSummaryResponse)
async def get_user_progress(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get student's progress (teachers only).

    Teachers can view progress of any student to monitor their learning.
    Students cannot use this endpoint (403 Forbidden).

    Args:
        user_id: ID of student to view progress for
        current_user: Current authenticated user (must be teacher)
        _: Teacher role check (403 if not teacher)
        session: Database session (injected)

    Returns:
        ProgressSummaryResponse with student's progress and summary stats

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a teacher
        HTTPException: 404 if user doesn't exist
    """
    # Verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: user_id={user_id}",
        )

    return _get_progress_summary(user_id, session)
