"""
Custom challenge routes - CRUD operations for teacher-created challenges.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import CustomChallenge, Dataset, User, Attempt, Progress
from app.auth import get_current_user, require_teacher
from app.schemas import (
    CustomChallengeCreate,
    CustomChallengeUpdate,
    CustomChallengeResponse,
    CustomChallengeListResponse,
    CustomChallengeListItem,
    CustomChallengeDetailResponse,
)
from app.routes.datasets import verify_dataset_ownership
from app.validation import execute_query_safely, validate_query_syntax

router = APIRouter(prefix="/challenges/custom", tags=["Custom Challenges"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def verify_challenge_ownership(
    challenge_id: int, teacher_id: int, session: Session
) -> CustomChallenge:
    """
    Verify that a custom challenge exists and belongs to the teacher.

    Args:
        challenge_id: Challenge ID
        teacher_id: Teacher user ID
        session: Database session

    Returns:
        CustomChallenge object

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    challenge = session.get(CustomChallenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Custom challenge not found")
    if challenge.teacher_id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: you do not own this challenge",
        )
    return challenge


def execute_and_cache_expected_output(
    query: str, table_name: str, session: Session
) -> list[dict]:
    """
    Execute query and return results for caching.

    Args:
        query: SQL query to execute
        table_name: Dataset table name
        session: Database session

    Returns:
        List of result rows as dictionaries

    Raises:
        HTTPException: If query execution fails
    """
    try:
        result = execute_query_safely(query, [table_name], session, timeout=10)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Expected query failed to execute: {str(e)}",
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("", response_model=CustomChallengeResponse, status_code=201)
def create_custom_challenge(
    challenge_data: CustomChallengeCreate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Create a new custom challenge (teachers only).

    The endpoint will:
    1. Verify dataset ownership
    2. Validate expected query syntax
    3. Execute query to verify it works
    4. Cache expected output
    5. Create challenge record

    Args:
        challenge_data: Challenge creation data
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Created custom challenge

    Raises:
        HTTPException: 404 if dataset not found, 403 if access denied,
                      400 if query validation fails
    """
    # Verify dataset ownership
    dataset = verify_dataset_ownership(
        challenge_data.dataset_id, current_user.id, session
    )

    # Validate query syntax (SELECT only, no forbidden keywords)
    validate_query_syntax(challenge_data.expected_query)

    # Execute query to verify it works and cache output
    expected_output = execute_and_cache_expected_output(
        challenge_data.expected_query, dataset.table_name, session
    )

    # Create challenge
    challenge = CustomChallenge(
        teacher_id=current_user.id,
        dataset_id=challenge_data.dataset_id,
        title=challenge_data.title,
        description=challenge_data.description,
        points=challenge_data.points,
        difficulty=challenge_data.difficulty,
        expected_query=challenge_data.expected_query,
        hints_json=json.dumps(challenge_data.hints),
        expected_output_json=json.dumps(expected_output),
        is_active=True,
    )

    session.add(challenge)
    session.commit()
    session.refresh(challenge)

    return CustomChallengeResponse(
        id=challenge.id,
        dataset_id=challenge.dataset_id,
        dataset_name=dataset.name,
        title=challenge.title,
        description=challenge.description,
        points=challenge.points,
        difficulty=challenge.difficulty,
        expected_query=challenge.expected_query,
        hints=json.loads(challenge.hints_json),
        is_active=challenge.is_active,
        created_at=challenge.created_at,
        updated_at=challenge.updated_at,
    )


@router.get("", response_model=CustomChallengeListResponse)
def get_custom_challenges(
    dataset_id: int | None = None,
    is_active: bool | None = None,
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get list of custom challenges created by current teacher.

    Args:
        dataset_id: Optional filter by dataset ID
        is_active: Optional filter by active status
        offset: Pagination offset
        limit: Pagination limit (max 100)
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Paginated list of custom challenges with statistics
    """
    # Build query
    query = select(CustomChallenge).where(
        CustomChallenge.teacher_id == current_user.id
    )

    if dataset_id is not None:
        query = query.where(CustomChallenge.dataset_id == dataset_id)

    if is_active is not None:
        query = query.where(CustomChallenge.is_active == is_active)

    # Apply pagination
    limit = min(limit, 100)
    query = query.offset(offset).limit(limit).order_by(CustomChallenge.created_at.desc())

    challenges = session.exec(query).all()

    # Get total count
    count_query = select(func.count()).select_from(CustomChallenge).where(
        CustomChallenge.teacher_id == current_user.id
    )

    if dataset_id is not None:
        count_query = count_query.where(CustomChallenge.dataset_id == dataset_id)

    if is_active is not None:
        count_query = count_query.where(CustomChallenge.is_active == is_active)

    total = session.exec(count_query).one()

    # Build response with statistics
    challenge_items = []
    for challenge in challenges:
        # Get dataset name
        dataset = session.get(Dataset, challenge.dataset_id)
        dataset_name = dataset.name if dataset else "Unknown"

        # Count submissions (attempts for this challenge)
        submission_count_query = select(func.count()).select_from(Attempt).where(
            Attempt.custom_challenge_id == challenge.id
        )
        submission_count = session.exec(submission_count_query).one()

        # Calculate completion rate
        if submission_count > 0:
            success_count_query = select(func.count()).select_from(Attempt).where(
                Attempt.custom_challenge_id == challenge.id,
                Attempt.is_correct == True,  # noqa: E712
            )
            success_count = session.exec(success_count_query).one()
            completion_rate = (success_count / submission_count) * 100
        else:
            completion_rate = 0.0

        challenge_items.append(
            CustomChallengeListItem(
                id=challenge.id,
                dataset_id=challenge.dataset_id,
                dataset_name=dataset_name,
                title=challenge.title,
                points=challenge.points,
                difficulty=challenge.difficulty,
                is_active=challenge.is_active,
                submission_count=submission_count,
                completion_rate=completion_rate,
                created_at=challenge.created_at,
            )
        )

    return CustomChallengeListResponse(total=total, challenges=challenge_items)


@router.get("/{challenge_id}", response_model=CustomChallengeDetailResponse)
def get_custom_challenge_detail(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get detailed custom challenge information.

    Args:
        challenge_id: Challenge ID
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Detailed challenge information including expected output

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    # Verify ownership
    challenge = verify_challenge_ownership(challenge_id, current_user.id, session)

    # Get dataset name
    dataset = session.get(Dataset, challenge.dataset_id)
    dataset_name = dataset.name if dataset else "Unknown"

    # Parse expected output
    expected_output = None
    if challenge.expected_output_json:
        try:
            expected_output = json.loads(challenge.expected_output_json)
        except json.JSONDecodeError:
            pass

    return CustomChallengeDetailResponse(
        id=challenge.id,
        dataset_id=challenge.dataset_id,
        dataset_name=dataset_name,
        title=challenge.title,
        description=challenge.description,
        points=challenge.points,
        difficulty=challenge.difficulty,
        expected_query=challenge.expected_query,
        hints=json.loads(challenge.hints_json),
        is_active=challenge.is_active,
        expected_output=expected_output,
        created_at=challenge.created_at,
        updated_at=challenge.updated_at,
    )


@router.put("/{challenge_id}", response_model=CustomChallengeResponse)
def update_custom_challenge(
    challenge_id: int,
    update_data: CustomChallengeUpdate,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Update a custom challenge.

    Args:
        challenge_id: Challenge ID
        update_data: Fields to update
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Updated challenge

    Raises:
        HTTPException: 404 if not found, 403 if access denied,
                      400 if query validation fails
    """
    # Verify ownership
    challenge = verify_challenge_ownership(challenge_id, current_user.id, session)

    # Get dataset for query execution
    dataset = session.get(Dataset, challenge.dataset_id)

    # Update fields if provided
    if update_data.title is not None:
        challenge.title = update_data.title

    if update_data.description is not None:
        challenge.description = update_data.description

    if update_data.points is not None:
        challenge.points = update_data.points

    if update_data.difficulty is not None:
        challenge.difficulty = update_data.difficulty

    if update_data.hints is not None:
        challenge.hints_json = json.dumps(update_data.hints)

    if update_data.is_active is not None:
        challenge.is_active = update_data.is_active

    # If expected query is updated, re-validate and re-cache output
    if update_data.expected_query is not None:
        validate_query_syntax(update_data.expected_query)
        expected_output = execute_and_cache_expected_output(
            update_data.expected_query, dataset.table_name, session
        )
        challenge.expected_query = update_data.expected_query
        challenge.expected_output_json = json.dumps(expected_output)

    # Update timestamp
    challenge.updated_at = datetime.now()

    session.add(challenge)
    session.commit()
    session.refresh(challenge)

    return CustomChallengeResponse(
        id=challenge.id,
        dataset_id=challenge.dataset_id,
        dataset_name=dataset.name,
        title=challenge.title,
        description=challenge.description,
        points=challenge.points,
        difficulty=challenge.difficulty,
        expected_query=challenge.expected_query,
        hints=json.loads(challenge.hints_json),
        is_active=challenge.is_active,
        created_at=challenge.created_at,
        updated_at=challenge.updated_at,
    )


@router.delete("/{challenge_id}", status_code=200)
def delete_custom_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Delete a custom challenge.

    Note: Also deletes associated progress and attempt records.

    Args:
        challenge_id: Challenge ID
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    # Verify ownership
    challenge = verify_challenge_ownership(challenge_id, current_user.id, session)

    # Count associated records
    attempt_count_query = select(func.count()).select_from(Attempt).where(
        Attempt.custom_challenge_id == challenge_id
    )
    attempt_count = session.exec(attempt_count_query).one()

    progress_count_query = select(func.count()).select_from(Progress).where(
        Progress.custom_challenge_id == challenge_id
    )
    progress_count = session.exec(progress_count_query).one()

    try:
        # Delete associated attempts
        if attempt_count > 0:
            delete_attempts = select(Attempt).where(
                Attempt.custom_challenge_id == challenge_id
            )
            attempts = session.exec(delete_attempts).all()
            for attempt in attempts:
                session.delete(attempt)

        # Delete associated progress
        if progress_count > 0:
            delete_progress = select(Progress).where(
                Progress.custom_challenge_id == challenge_id
            )
            progress_records = session.exec(delete_progress).all()
            for record in progress_records:
                session.delete(record)

        # Delete challenge
        session.delete(challenge)
        session.commit()

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting challenge: {str(e)}"
        )

    return {
        "message": f"Challenge deleted successfully (removed {attempt_count} attempt(s) and {progress_count} progress record(s))"
    }
