"""
Progress routes - challenge submission and progress tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models import User, Progress
from app.schemas import ChallengeSubmitRequest, ProgressResponse
from app.auth import get_current_user, require_student
from app.challenges import get_challenge


router = APIRouter(prefix="/progress", tags=["Progress"])


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
