"""
Hints routes - track when students access hints for challenges.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models import User, Hint
from app.schemas import HintAccessRequest, HintAccessResponse
from app.auth import get_current_user, require_student
from app.challenges import get_challenge


router = APIRouter(prefix="/hints", tags=["Hints"])


@router.post(
    "/access", response_model=HintAccessResponse, status_code=status.HTTP_201_CREATED
)
async def access_hint(
    submission: HintAccessRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_student),
    session: Session = Depends(get_session),
):
    """
    Track a hint access by a student (student-only).

    Students can access hints multiple times for the same challenge.
    Each access is tracked separately (no unique constraint).

    Args:
        submission: Hint access data (unit_id, challenge_id, hint_level)
        current_user: Current authenticated user (injected from JWT)
        _: Student role check (403 if not student)
        session: Database session (injected)

    Returns:
        HintAccessResponse with hint_id and accessed_at timestamp

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

    # 2. Create hint access record (no uniqueness check - track all accesses)
    hint = Hint(
        user_id=current_user.id,  # From JWT token - no spoofing!
        unit_id=submission.unit_id,
        challenge_id=submission.challenge_id,
        hint_level=submission.hint_level,
    )

    # 3. Save to database
    session.add(hint)
    session.commit()
    session.refresh(hint)

    return HintAccessResponse(hint_id=hint.id, accessed_at=hint.accessed_at)
