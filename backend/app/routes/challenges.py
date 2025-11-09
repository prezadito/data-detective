"""
Challenge management endpoints - read challenge definitions and view statistics.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Progress, Attempt
from app.auth import get_current_user
from app.challenges import CHALLENGES
from app.schemas import (
    ChallengeDetail,
    UnitChallenges,
    AllChallengesResponse,
)

router = APIRouter(prefix="/challenges", tags=["Challenges"])

# Unit titles mapping
UNIT_TITLES = {
    1: "Unit 1: SELECT Basics",
    2: "Unit 2: JOINs",
    3: "Unit 3: Aggregations",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_challenge_from_dict(unit_id: int, challenge_id: int) -> dict | None:
    """
    Get a challenge from the CHALLENGES dictionary.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID

    Returns:
        Challenge dict or None if not found
    """
    return CHALLENGES.get((unit_id, challenge_id))


def _calculate_completion_rate(
    unit_id: int, challenge_id: int, session: Session
) -> float:
    """
    Calculate completion rate for a challenge.

    Formula: (count of distinct users with Progress record) / (total students) * 100

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID
        session: Database session

    Returns:
        Percentage (0-100)
    """
    # Count total students
    total_students = (
        session.exec(
            select(func.count(func.distinct(User.id))).where(User.role == "student")
        ).one()
        or 0
    )

    if total_students == 0:
        return 0.0

    # Count students who completed this challenge
    completed = (
        session.exec(
            select(func.count(func.distinct(Progress.user_id)))
            .where(Progress.unit_id == unit_id)
            .where(Progress.challenge_id == challenge_id)
        ).one()
        or 0
    )

    return (completed / total_students) * 100 if total_students > 0 else 0.0


def _calculate_avg_attempts(unit_id: int, challenge_id: int, session: Session) -> float:
    """
    Calculate average attempts for a challenge.

    Formula: count(Attempt) / count(distinct users who attempted)

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID
        session: Database session

    Returns:
        Average attempts as float
    """
    # Count total attempts
    total_attempts = (
        session.exec(
            select(func.count(Attempt.id))
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        ).one()
        or 0
    )

    if total_attempts == 0:
        return 0.0

    # Count unique students who attempted
    unique_students = (
        session.exec(
            select(func.count(func.distinct(Attempt.user_id)))
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        ).one()
        or 0
    )

    return total_attempts / unique_students if unique_students > 0 else 0.0


def _get_challenge_stats(unit_id: int, challenge_id: int, session: Session) -> dict:
    """
    Get statistics for a challenge.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID
        session: Database session

    Returns:
        Dict with total_attempts and success_count
    """
    # Get all attempts
    total_attempts = (
        session.exec(
            select(func.count(Attempt.id))
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        ).one()
        or 0
    )

    # Get successful attempts
    success_count = (
        session.exec(
            select(func.count(Attempt.id))
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
            .where(Attempt.is_correct)
        ).one()
        or 0
    )

    return {
        "total_attempts": total_attempts,
        "success_count": success_count,
    }


def _build_challenge_response(
    unit_id: int,
    challenge_id: int,
    challenge_dict: dict,
    session: Session,
    include_solution: bool = False,
) -> ChallengeDetail:
    """
    Build a complete challenge detail response.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID
        challenge_dict: Challenge data from CHALLENGES dict
        session: Database session
        include_solution: Whether to include sample_solution (for teachers)

    Returns:
        ChallengeDetail response
    """
    completion_rate = _calculate_completion_rate(unit_id, challenge_id, session)
    avg_attempts = _calculate_avg_attempts(unit_id, challenge_id, session)
    stats = _get_challenge_stats(unit_id, challenge_id, session)

    return ChallengeDetail(
        unit_id=unit_id,
        challenge_id=challenge_id,
        title=challenge_dict["title"],
        points=challenge_dict["points"],
        description=challenge_dict["description"],
        sample_solution=challenge_dict["sample_solution"] if include_solution else None,
        completion_rate=round(completion_rate, 2),
        avg_attempts=round(avg_attempts, 2),
        total_attempts=stats["total_attempts"],
        success_count=stats["success_count"],
    )


def _build_unit_challenges_response(
    unit_id: int, session: Session, include_solution: bool = False
) -> UnitChallenges:
    """
    Build a response for all challenges in a unit.

    Args:
        unit_id: Unit ID
        session: Database session
        include_solution: Whether to include sample solutions (for teachers)

    Returns:
        UnitChallenges response
    """
    challenges = []

    # Find all challenges in this unit from CHALLENGES dict
    for (u_id, c_id), challenge_dict in CHALLENGES.items():
        if u_id == unit_id:
            challenge_response = _build_challenge_response(
                u_id, c_id, challenge_dict, session, include_solution
            )
            challenges.append(challenge_response)

    # Sort by challenge_id
    challenges.sort(key=lambda c: c.challenge_id)

    unit_title = UNIT_TITLES.get(unit_id, f"Unit {unit_id}")

    return UnitChallenges(
        unit_id=unit_id,
        unit_title=unit_title,
        challenges=challenges,
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get("", response_model=AllChallengesResponse, status_code=200)
async def get_all_challenges(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get all challenges across all units with statistics.

    Returns a response with all units and their challenges, including:
    - Challenge metadata (title, points, description)
    - Statistics (completion_rate, avg_attempts)
    - Sample solutions (for teachers only)

    Args:
        current_user: Authenticated user (to check role for solutions)
        session: Database session

    Returns:
        AllChallengesResponse with all units and challenges
    """
    # Check if user is teacher to show solutions
    include_solution = current_user.role == "teacher"

    # Get all unique unit IDs from CHALLENGES dict
    unit_ids = set(unit_id for unit_id, _ in CHALLENGES.keys())
    unit_ids = sorted(unit_ids)

    # Build response for each unit
    units = []
    for unit_id in unit_ids:
        unit_response = _build_unit_challenges_response(
            unit_id, session, include_solution
        )
        units.append(unit_response)

    return AllChallengesResponse(units=units, generated_at=datetime.now())


@router.get("/{unit_id}", response_model=UnitChallenges, status_code=200)
async def get_unit_challenges(
    unit_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get all challenges in a specific unit with statistics.

    Args:
        unit_id: Unit ID (1-3)
        current_user: Authenticated user (to check role for solutions)
        session: Database session

    Returns:
        UnitChallenges with all challenges in the unit

    Raises:
        HTTPException: 404 if unit not found
    """
    # Validate unit exists
    if not any(u_id == unit_id for u_id, _ in CHALLENGES.keys()):
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")

    # Check if user is teacher to show solutions
    include_solution = current_user.role == "teacher"

    return _build_unit_challenges_response(unit_id, session, include_solution)


@router.get(
    "/{unit_id}/{challenge_id}", response_model=ChallengeDetail, status_code=200
)
async def get_challenge_detail(
    unit_id: int,
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get detailed information about a specific challenge.

    Includes statistics and optional sample solution.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID
        current_user: Authenticated user (to check role for solutions)
        session: Database session

    Returns:
        ChallengeDetail with complete challenge information

    Raises:
        HTTPException: 404 if challenge not found
    """
    # Validate challenge exists
    challenge_dict = _get_challenge_from_dict(unit_id, challenge_id)
    if challenge_dict is None:
        raise HTTPException(
            status_code=404,
            detail=f"Challenge {unit_id}/{challenge_id} not found",
        )

    # Check if user is teacher to show solutions
    include_solution = current_user.role == "teacher"

    return _build_challenge_response(
        unit_id, challenge_id, challenge_dict, session, include_solution
    )
