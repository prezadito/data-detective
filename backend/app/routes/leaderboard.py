"""
Leaderboard routes - public gamification endpoint with caching.
"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Progress
from app.schemas import LeaderboardEntry, LeaderboardResponse


router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

# In-memory cache with TTL
_cache = {"data": None, "timestamp": None}
CACHE_TTL = 5 * 60  # 5 minutes in seconds


# ============================================================================
# CACHE MANAGEMENT FUNCTIONS
# ============================================================================


def _is_cache_valid() -> bool:
    """
    Check if cache exists and hasn't expired.

    Returns:
        True if cache is valid and fresh, False otherwise
    """
    if _cache["data"] is None or _cache["timestamp"] is None:
        return False
    elapsed = time.time() - _cache["timestamp"]
    return elapsed < CACHE_TTL


def invalidate_cache() -> None:
    """
    Invalidate the leaderboard cache.

    Called after new progress submissions to ensure fresh data.
    This function can be imported and called from other modules.
    """
    _cache["data"] = None
    _cache["timestamp"] = None


# ============================================================================
# DATABASE QUERY FUNCTION
# ============================================================================


def _get_leaderboard_data(session: Session) -> LeaderboardResponse:
    """
    Query database and build leaderboard response.

    Aggregates student progress data to create a ranked leaderboard.
    Excludes teachers and limits to top 100 students.

    Args:
        session: Database session

    Returns:
        LeaderboardResponse with ranked entries
    """
    # Query: GROUP BY user to aggregate points and challenge count
    # Only include students, exclude teachers
    statement = (
        select(
            User.id,
            User.name,
            func.sum(Progress.points_earned).label("total_points"),
            func.count(Progress.id).label("challenges_completed"),
        )
        .join(Progress, User.id == Progress.user_id)
        .where(User.role == "student")
        .group_by(User.id, User.name)
        .order_by(func.sum(Progress.points_earned).desc(), User.id)
        .limit(100)
    )

    results = session.exec(statement).all()

    # Build leaderboard entries with rank
    entries = []
    for rank, (user_id, name, total_points, challenges_completed) in enumerate(
        results, start=1
    ):
        entries.append(
            LeaderboardEntry(
                rank=rank,
                student_name=name,
                total_points=total_points or 0,  # Handle NULL from empty join
                challenges_completed=challenges_completed or 0,  # Handle NULL
            )
        )

    return LeaderboardResponse(entries=entries)


# ============================================================================
# PUBLIC ENDPOINT
# ============================================================================


@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(session: Session = Depends(get_session)):
    """
    Get the public leaderboard (top 100 students).

    This is a public endpoint - no authentication required.
    Returns students ranked by total points earned across all challenges.

    The leaderboard is cached for 5 minutes to improve performance.
    Cache is invalidated when new progress submissions are made.

    Args:
        session: Database session (injected)

    Returns:
        LeaderboardResponse with top 100 students ranked by points
    """
    # Check if cache is valid
    if _is_cache_valid():
        return _cache["data"]

    # Query database
    data = _get_leaderboard_data(session)

    # Store in cache with timestamp
    _cache["data"] = data
    _cache["timestamp"] = time.time()

    return data
