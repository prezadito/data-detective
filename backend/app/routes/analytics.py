"""
Analytics routes - class-wide metrics and trends (teachers only).
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, Integer
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Progress, Attempt, Hint
from app.schemas import (
    ChallengeAnalytics,
    ClassMetrics,
    ChallengeDistribution,
    WeeklyTrend,
    ClassAnalyticsResponse,
)
from app.auth import get_current_user, require_teacher
from app.challenges import get_challenge


router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

_analytics_cache: dict = {}  # {cache_key: (response, timestamp)}
CACHE_TTL_SECONDS = 3600  # 1 hour


def _get_cached_analytics() -> ClassAnalyticsResponse | None:
    """
    Get cached analytics if fresh (< 1 hour old).

    Returns:
        Cached ClassAnalyticsResponse if valid, else None
    """
    cache_key = "class_analytics"
    if cache_key not in _analytics_cache:
        return None

    response, timestamp = _analytics_cache[cache_key]
    age_seconds = (datetime.now() - timestamp).total_seconds()

    if age_seconds >= CACHE_TTL_SECONDS:
        # Cache expired
        del _analytics_cache[cache_key]
        return None

    return response


def _cache_analytics(response: ClassAnalyticsResponse):
    """Store analytics in cache with current timestamp."""
    cache_key = "class_analytics"
    _analytics_cache[cache_key] = (response, datetime.now())


def invalidate_analytics_cache():
    """Clear the analytics cache."""
    cache_key = "class_analytics"
    if cache_key in _analytics_cache:
        del _analytics_cache[cache_key]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_class_points_distribution(session: Session) -> list[int]:
    """
    Get total points earned per student.

    Returns list of point totals for each active student (only students with progress).
    Used for calculating percentiles.

    Args:
        session: Database session

    Returns:
        List of total points per student (sorted ascending)
    """
    # Query: SUM(points_earned) per user_id
    statement = (
        select(func.sum(Progress.points_earned).label("total"))
        .group_by(Progress.user_id)
        .order_by("total")
    )
    results = session.exec(statement).all()

    # Extract point totals, handle None values
    points = [int(total) if total is not None else 0 for total in results]
    return sorted(points)


def _calculate_percentiles(points_list: list[int]) -> tuple[int, int, int]:
    """
    Calculate 25th, 50th (median), and 75th percentiles.

    Uses linear interpolation when percentile falls between values.
    No numpy: implemented with pure Python.

    Args:
        points_list: Sorted list of point values

    Returns:
        (percentile_25, percentile_50, percentile_75) as integers
    """
    if not points_list:
        return 0, 0, 0

    n = len(points_list)

    def calc_percentile(p: float) -> int:
        """Calculate percentile p (0-100) using linear interpolation."""
        # Index for percentile p
        idx = (p / 100.0) * (n - 1)
        lower_idx = int(idx)
        upper_idx = min(lower_idx + 1, n - 1)

        # Linear interpolation
        lower = points_list[lower_idx]
        upper = points_list[upper_idx]
        fraction = idx - lower_idx

        result = lower + (upper - lower) * fraction
        return int(round(result))

    p25 = calc_percentile(25)
    p50 = calc_percentile(50)
    p75 = calc_percentile(75)

    return p25, p50, p75


def _calculate_challenge_success_rates(session: Session) -> dict[tuple, float]:
    """
    Calculate success rate for each challenge.

    Returns dict mapping (unit_id, challenge_id) to success_rate (0-100).

    Queries Attempt table:
    - For each challenge, count correct attempts / total attempts * 100

    Args:
        session: Database session

    Returns:
        Dict: {(unit_id, challenge_id): success_rate_float}
    """
    # Get all attempts grouped by challenge
    statement = select(
        Attempt.unit_id,
        Attempt.challenge_id,
        func.count(Attempt.id).label("total"),
        func.sum(func.coalesce(func.cast(Attempt.is_correct, Integer), 0)).label(
            "correct"
        ),
    ).group_by(Attempt.unit_id, Attempt.challenge_id)

    results = session.exec(statement).all()

    success_rates = {}
    for unit_id, challenge_id, total, correct in results:
        if total is None or total == 0:
            success_rates[(unit_id, challenge_id)] = 0.0
        else:
            correct_count = correct if correct is not None else 0
            rate = (correct_count / total) * 100.0
            success_rates[(unit_id, challenge_id)] = rate

    return success_rates


def _calculate_class_metrics(session: Session) -> ClassMetrics:
    """
    Calculate overall class metrics.

    Aggregates:
    - Total students in system
    - Active students (with ≥1 completion)
    - Average completion rate
    - Median points and percentiles
    - Total completions and attempts
    - Overall success rate

    Args:
        session: Database session

    Returns:
        ClassMetrics object with all aggregated statistics
    """
    # Count total students (excluding teachers)
    total_students_result = session.exec(
        select(func.count(User.id)).where(User.role == "student")
    ).one()
    total_students = total_students_result if total_students_result else 0

    # Get points distribution for percentile calculation
    points_distribution = _get_class_points_distribution(session)
    active_students = len(points_distribution)

    # Calculate percentiles
    p25, p50, p75 = _calculate_percentiles(points_distribution)

    # Calculate completion rate
    total_completions_result = session.exec(select(func.count(Progress.id))).one()
    total_completions = total_completions_result if total_completions_result else 0

    if active_students > 0:
        avg_completion_rate = (total_completions / active_students / 7) * 100
    else:
        avg_completion_rate = 0.0

    # Calculate total attempts and success rate
    total_attempts_result = session.exec(select(func.count(Attempt.id))).one()
    total_attempts = total_attempts_result if total_attempts_result else 0

    correct_attempts_result = session.exec(
        select(func.count(Attempt.id)).where(Attempt.is_correct)
    ).one()
    correct_attempts = correct_attempts_result if correct_attempts_result else 0

    if total_attempts > 0:
        avg_success_rate = (correct_attempts / total_attempts) * 100.0
    else:
        avg_success_rate = 0.0

    return ClassMetrics(
        total_students=total_students,
        active_students=active_students,
        avg_completion_rate=avg_completion_rate,
        median_points=p50,
        percentile_25=p25,
        percentile_50=p50,
        percentile_75=p75,
        total_challenges_completed=total_completions,
        total_attempts=total_attempts,
        avg_success_rate=avg_success_rate,
    )


def _build_challenge_analytics_list(
    session: Session,
) -> list[ChallengeAnalytics]:
    """
    Build analytics for all 7 challenges.

    For each challenge, queries:
    - Total attempts (all students)
    - Correct attempts
    - Success rate
    - Average hints per attempt
    - Challenge title from CHALLENGES dict

    Args:
        session: Database session

    Returns:
        List of ChallengeAnalytics for all 7 challenges (ordered by unit, challenge)
    """
    # Get success rates for all challenges
    success_rates = _calculate_challenge_success_rates(session)

    # Get hint counts per challenge
    hints_statement = select(
        Hint.unit_id,
        Hint.challenge_id,
        func.count(Hint.id).label("hint_count"),
    ).group_by(Hint.unit_id, Hint.challenge_id)
    hint_results = session.exec(hints_statement).all()
    hint_counts = {
        (unit_id, challenge_id): hint_count
        for unit_id, challenge_id, hint_count in hint_results
    }

    # Build analytics for all 7 challenges
    analytics = []

    # Unit 1: 3 challenges
    for unit_id, challenge_id in [(1, 1), (1, 2), (1, 3)]:
        # Get attempt counts for this challenge
        attempts_statement = (
            select(
                func.count(Attempt.id).label("total"),
                func.sum(
                    func.coalesce(func.cast(Attempt.is_correct, Integer), 0)
                ).label("correct"),
            )
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        )
        attempt_row = session.exec(attempts_statement).first()

        total_attempts = attempt_row[0] if attempt_row and attempt_row[0] else 0
        correct_attempts = attempt_row[1] if attempt_row and attempt_row[1] else 0

        success_rate = success_rates.get((unit_id, challenge_id), 0.0)

        # Calculate average hints per attempt
        hint_count = hint_counts.get((unit_id, challenge_id), 0)
        avg_hints = (hint_count / total_attempts) if total_attempts > 0 else 0.0

        # Get challenge title
        challenge = get_challenge(unit_id, challenge_id) or {}
        title = challenge.get("title", f"Unknown Challenge U{unit_id}C{challenge_id}")

        analytics.append(
            ChallengeAnalytics(
                unit_id=unit_id,
                challenge_id=challenge_id,
                challenge_title=title,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                success_rate=success_rate,
                avg_hints_per_attempt=avg_hints,
            )
        )

    # Unit 2: 2 challenges
    for unit_id, challenge_id in [(2, 1), (2, 2)]:
        attempts_statement = (
            select(
                func.count(Attempt.id).label("total"),
                func.sum(
                    func.coalesce(func.cast(Attempt.is_correct, Integer), 0)
                ).label("correct"),
            )
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        )
        attempt_row = session.exec(attempts_statement).first()

        total_attempts = attempt_row[0] if attempt_row and attempt_row[0] else 0
        correct_attempts = attempt_row[1] if attempt_row and attempt_row[1] else 0

        success_rate = success_rates.get((unit_id, challenge_id), 0.0)

        hint_count = hint_counts.get((unit_id, challenge_id), 0)
        avg_hints = (hint_count / total_attempts) if total_attempts > 0 else 0.0

        challenge = get_challenge(unit_id, challenge_id) or {}
        title = challenge.get("title", f"Unknown Challenge U{unit_id}C{challenge_id}")

        analytics.append(
            ChallengeAnalytics(
                unit_id=unit_id,
                challenge_id=challenge_id,
                challenge_title=title,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                success_rate=success_rate,
                avg_hints_per_attempt=avg_hints,
            )
        )

    # Unit 3: 2 challenges
    for unit_id, challenge_id in [(3, 1), (3, 2)]:
        attempts_statement = (
            select(
                func.count(Attempt.id).label("total"),
                func.sum(
                    func.coalesce(func.cast(Attempt.is_correct, Integer), 0)
                ).label("correct"),
            )
            .where(Attempt.unit_id == unit_id)
            .where(Attempt.challenge_id == challenge_id)
        )
        attempt_row = session.exec(attempts_statement).first()

        total_attempts = attempt_row[0] if attempt_row and attempt_row[0] else 0
        correct_attempts = attempt_row[1] if attempt_row and attempt_row[1] else 0

        success_rate = success_rates.get((unit_id, challenge_id), 0.0)

        hint_count = hint_counts.get((unit_id, challenge_id), 0)
        avg_hints = (hint_count / total_attempts) if total_attempts > 0 else 0.0

        challenge = get_challenge(unit_id, challenge_id) or {}
        title = challenge.get("title", f"Unknown Challenge U{unit_id}C{challenge_id}")

        analytics.append(
            ChallengeAnalytics(
                unit_id=unit_id,
                challenge_id=challenge_id,
                challenge_title=title,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                success_rate=success_rate,
                avg_hints_per_attempt=avg_hints,
            )
        )

    return analytics


def _identify_difficulty_distribution(
    challenges: list[ChallengeAnalytics],
) -> ChallengeDistribution:
    """
    Identify easiest and hardest challenges.

    Easiest: Top 3 by success rate (highest first)
    Hardest: Bottom 3 by success rate (lowest first)

    Args:
        challenges: List of all ChallengeAnalytics

    Returns:
        ChallengeDistribution with easiest and hardest challenges
    """
    # Sort by success rate descending
    sorted_by_difficulty = sorted(
        challenges, key=lambda c: c.success_rate, reverse=True
    )

    # Top 3 are easiest
    easiest = sorted_by_difficulty[:3]

    # Bottom 3 are hardest (reverse order so lowest success rate first)
    hardest = list(reversed(sorted_by_difficulty[-3:]))

    return ChallengeDistribution(
        easiest_challenges=easiest,
        hardest_challenges=hardest,
    )


def _calculate_weekly_trends(session: Session) -> list[WeeklyTrend]:
    """
    Calculate trends for past 4 weeks.

    For each week (including current):
    - week_start_date: Monday of that week
    - week_end_date: Sunday of that week
    - completions: count of Progress records in that week
    - total_points_earned: sum of points_earned in that week
    - unique_students: count of distinct user_ids in that week

    Args:
        session: Database session

    Returns:
        List of WeeklyTrend objects (4 weeks, oldest first)
    """
    trends = []

    # Generate past 4 weeks (including current week)
    today = datetime.now().date()
    # Monday of current week
    current_monday = today - timedelta(days=today.weekday())

    for week_offset in range(3, -1, -1):  # 3, 2, 1, 0 (current)
        week_monday = current_monday - timedelta(weeks=week_offset)
        week_sunday = week_monday + timedelta(days=6)

        # Query Progress records for this week
        statement = (
            select(
                func.count(Progress.id).label("completions"),
                func.sum(Progress.points_earned).label("total_points"),
                func.count(func.distinct(Progress.user_id)).label("unique_students"),
            )
            .where(Progress.completed_at >= week_monday)
            .where(Progress.completed_at <= week_sunday + timedelta(days=1))
        )

        row = session.exec(statement).first()
        completions = row[0] if row and row[0] else 0
        total_points = int(row[1]) if row and row[1] else 0
        unique_students = row[2] if row and row[2] else 0

        trends.append(
            WeeklyTrend(
                week_start_date=datetime.combine(week_monday, datetime.min.time()),
                week_end_date=datetime.combine(week_sunday, datetime.max.time()),
                completions=completions,
                total_points_earned=total_points,
                unique_students=unique_students,
            )
        )

    return trends


def _build_class_analytics_response(session: Session) -> ClassAnalyticsResponse:
    """
    Build complete class analytics response.

    Orchestrates all helper functions to create comprehensive analytics report.

    Args:
        session: Database session

    Returns:
        ClassAnalyticsResponse ready to return to client
    """
    generated_at = datetime.now()
    cache_expires_at = generated_at + timedelta(seconds=CACHE_TTL_SECONDS)

    # Calculate metrics
    metrics = _calculate_class_metrics(session)

    # Build challenge analytics for all 7 challenges
    challenges = _build_challenge_analytics_list(session)

    # Identify difficulty distribution
    difficulty_distribution = _identify_difficulty_distribution(challenges)

    # Calculate weekly trends
    weekly_trends = _calculate_weekly_trends(session)

    return ClassAnalyticsResponse(
        generated_at=generated_at,
        metrics=metrics,
        challenges=challenges,
        difficulty_distribution=difficulty_distribution,
        weekly_trends=weekly_trends,
        cache_expires_at=cache_expires_at,
    )


# ============================================================================
# API ENDPOINT
# ============================================================================


@router.get("/class", response_model=ClassAnalyticsResponse)
async def get_class_analytics(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get class-wide analytics for all students (teachers only).

    Returns comprehensive metrics including:
    - Class-wide completion rates, points distribution (median, percentiles)
    - Per-challenge success rates and difficulty ranking
    - 4-week historical trends

    Results are cached for 1 hour to reduce database load.

    Args:
        current_user: Current authenticated user (must be teacher)
        _: Teacher role check (403 if not teacher)
        session: Database session (injected)

    Returns:
        ClassAnalyticsResponse with complete analytics data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a teacher
    """
    # Try to return cached data
    cached = _get_cached_analytics()
    if cached:
        return cached

    # Build fresh analytics
    response = _build_class_analytics_response(session)

    # Cache it
    _cache_analytics(response)

    return response
