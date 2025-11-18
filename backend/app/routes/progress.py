"""
Progress routes - challenge submission and progress tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models import User, Progress, Attempt, CustomChallenge
from app.schemas import (
    ChallengeSubmitRequest,
    ProgressResponse,
    ProgressDetailResponse,
    ProgressSummaryStats,
    ProgressSummaryResponse,
)
from app.auth import get_current_user, require_student, require_teacher
from app.challenges import get_challenge, validate_query
from app.routes.leaderboard import invalidate_cache
from app.routes.reports import invalidate_weekly_cache
from app.routes.analytics import invalidate_analytics_cache
from app.logging_config import get_logger

logger = get_logger(__name__)

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

    Students submit their SQL query for either a hardcoded challenge or
    a custom challenge. The endpoint:
    1. Validates the challenge exists (hardcoded or custom)
    2. Validates the query matches the expected solution
    3. Creates an Attempt record for every submission (tracks all attempts)
    4. If correct: creates Progress record and awards points
    5. If incorrect: returns 400 error with helpful message
    6. Returns idempotent responses for correct submissions

    Args:
        submission: Challenge submission data (unit_id/challenge_id OR custom_challenge_id, query, hints_used)
        current_user: Current authenticated user (injected from JWT)
        _: Student role check (403 if not student)
        session: Database session (injected)

    Returns:
        Progress record with points earned (only if query is correct)

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a student
        HTTPException: 404 if challenge doesn't exist
        HTTPException: 400 if query is incorrect or submission format invalid
    """
    # Determine challenge type
    is_custom = submission.custom_challenge_id is not None
    is_hardcoded = (
        submission.unit_id is not None and submission.challenge_id is not None
    )

    # Validate submission has exactly one challenge type
    if is_custom and is_hardcoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit both hardcoded and custom challenge in same request",
        )

    if not is_custom and not is_hardcoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either (unit_id + challenge_id) or custom_challenge_id",
        )

    # Handle custom challenge submission
    if is_custom:
        custom_challenge = session.get(CustomChallenge, submission.custom_challenge_id)
        if not custom_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Custom challenge not found: id={submission.custom_challenge_id}",
            )

        if not custom_challenge.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This challenge is no longer active",
            )

        # Validate query
        is_correct = validate_query(
            submission.query, custom_challenge.expected_query
        )

        # Create Attempt record
        attempt = Attempt(
            user_id=current_user.id,
            custom_challenge_id=submission.custom_challenge_id,
            query=submission.query,
            is_correct=is_correct,
        )
        session.add(attempt)
        session.commit()

        # If incorrect, return error
        if not is_correct:
            logger.warning(
                f"Incorrect challenge submission: custom_challenge_id={submission.custom_challenge_id}",
                extra={
                    "user_id": current_user.id,
                    "custom_challenge_id": submission.custom_challenge_id,
                    "is_correct": False,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query is incorrect. Expected: {custom_challenge.expected_query}",
            )

        # Check if already completed
        statement = select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.custom_challenge_id == submission.custom_challenge_id,
        )
        existing_progress = session.exec(statement).first()

        if existing_progress:
            return existing_progress

        # Create new progress record
        progress = Progress(
            user_id=current_user.id,
            custom_challenge_id=submission.custom_challenge_id,
            points_earned=custom_challenge.points,
            hints_used=submission.hints_used,
            query=submission.query,
        )

        try:
            session.add(progress)
            session.commit()
            session.refresh(progress)
            invalidate_cache()
            invalidate_weekly_cache()
            invalidate_analytics_cache()

            logger.info(
                f"Challenge completed: custom_challenge_id={submission.custom_challenge_id}, points={custom_challenge.points}",
                extra={
                    "user_id": current_user.id,
                    "custom_challenge_id": submission.custom_challenge_id,
                    "points_earned": custom_challenge.points,
                    "hints_used": submission.hints_used,
                },
            )

            return progress

        except IntegrityError:
            session.rollback()
            existing_progress = session.exec(statement).first()
            invalidate_cache()
            invalidate_weekly_cache()
            invalidate_analytics_cache()
            return existing_progress

    # Handle hardcoded challenge submission (original logic)
    else:
        # 1. Validate challenge exists
        challenge = get_challenge(submission.unit_id, submission.challenge_id)
        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Challenge not found: unit={submission.unit_id}, challenge={submission.challenge_id}",
            )

        # 2. Validate query (MVP: simple string comparison after normalization)
        is_correct = validate_query(submission.query, challenge["sample_solution"])

        # 3. Create Attempt record (for EVERY submission - correct or incorrect)
        attempt = Attempt(
            user_id=current_user.id,
            unit_id=submission.unit_id,
            challenge_id=submission.challenge_id,
            query=submission.query,
            is_correct=is_correct,
        )
        session.add(attempt)
        session.commit()

        # 4. If incorrect, return error
        if not is_correct:
            logger.warning(
                f"Incorrect challenge submission: unit={submission.unit_id}, challenge={submission.challenge_id}",
                extra={
                    "user_id": current_user.id,
                    "unit_id": submission.unit_id,
                    "challenge_id": submission.challenge_id,
                    "is_correct": False,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query is incorrect. Expected: {challenge['sample_solution']}",
            )

        # 5. Check if already completed (idempotency - only for correct submissions)
        statement = select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.unit_id == submission.unit_id,
            Progress.challenge_id == submission.challenge_id,
        )
        existing_progress = session.exec(statement).first()

        if existing_progress:
            # Already completed - return existing record (idempotent)
            return existing_progress

        # 6. Create new progress record (only for first correct submission)
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
            # Invalidate leaderboard and weekly report caches after new submission
            invalidate_cache()
            invalidate_weekly_cache()
            invalidate_analytics_cache()

            logger.info(
                f"Challenge completed: unit={submission.unit_id}, challenge={submission.challenge_id}, points={challenge['points']}",
                extra={
                    "user_id": current_user.id,
                    "unit_id": submission.unit_id,
                    "challenge_id": submission.challenge_id,
                    "points_earned": challenge["points"],
                    "hints_used": submission.hints_used,
                },
            )

            return progress

        except IntegrityError:
            # Race condition: another request created it
            # Rollback and return existing
            session.rollback()
            existing_progress = session.exec(statement).first()
            # Invalidate caches in case this completes a first-time submission
            invalidate_cache()
            invalidate_weekly_cache()
            invalidate_analytics_cache()
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
