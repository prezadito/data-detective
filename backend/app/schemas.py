"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """
    Schema for creating a new user.
    Used for registration requests.
    """

    email: EmailStr  # Validates email format!
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    role: str = Field(pattern="^(student|teacher)$")  # Only these two roles


class UserResponse(BaseModel):
    """
    Schema for user in responses.
    NEVER includes password or password_hash!
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str
    created_at: datetime


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    Used for PUT /users/me endpoint.
    Only allows updating name (email/role cannot be changed for security).
    """

    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """
    Schema for user login.
    Used for login requests.
    """

    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Schema for JWT token response.
    Now includes both access and refresh tokens.
    """

    access_token: str
    token_type: str
    refresh_token: str


class TokenData(BaseModel):
    """
    Schema for decoded JWT token payload.
    """

    email: str
    user_id: int
    role: str


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.
    Used for /auth/refresh and /auth/logout endpoints.
    """

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """
    Schema for refresh token response.
    Returns new access token.
    """

    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    """
    Schema for password reset request.
    Used for /auth/password-reset-request endpoint.
    """

    email: EmailStr


class PasswordResetResponse(BaseModel):
    """
    Schema for password reset response.
    Returns message and reset token (temporarily - will be sent via email later).
    """

    message: str
    reset_token: str


class PasswordResetConfirm(BaseModel):
    """
    Schema for password reset confirmation.
    Used for /auth/password-reset-confirm endpoint.
    """

    reset_token: str
    new_password: str = Field(min_length=8, max_length=100)


class PasswordResetConfirmResponse(BaseModel):
    """
    Schema for password reset confirmation response.
    Returns success message.
    """

    message: str


class ProgressCreate(BaseModel):
    """
    Schema for creating a new progress record.
    Used when student completes a challenge.
    """

    user_id: int
    unit_id: int
    challenge_id: int
    points_earned: int
    hints_used: int = Field(default=0)


class ProgressResponse(BaseModel):
    """
    Schema for progress in responses.
    Returns all progress data including timestamps.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    unit_id: int
    challenge_id: int
    points_earned: int
    hints_used: int
    completed_at: datetime


class ProgressUpdate(BaseModel):
    """
    Schema for updating progress record.
    Allows updating points_earned and hints_used only.
    """

    points_earned: Optional[int] = None
    hints_used: Optional[int] = None


class ChallengeSubmitRequest(BaseModel):
    """
    Schema for challenge submission request.
    Student submits their SQL query for a specific challenge.

    Note: user_id is NOT in request body - it's extracted from JWT token.
    This prevents students from submitting on behalf of others.
    """

    unit_id: int = Field(ge=1, description="Unit ID (must be >= 1)")
    challenge_id: int = Field(
        ge=1, description="Challenge ID within unit (must be >= 1)"
    )
    query: str = Field(
        min_length=1, max_length=5000, description="SQL query submitted by student"
    )
    hints_used: int = Field(default=0, ge=0, description="Number of hints used (>= 0)")


class ProgressDetailResponse(BaseModel):
    """
    Progress detail with challenge title and query.
    Extends ProgressResponse with enriched challenge info from CHALLENGES dict.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    unit_id: int
    challenge_id: int
    points_earned: int
    hints_used: int
    completed_at: datetime
    query: str
    challenge_title: str  # Looked up from CHALLENGES dict


class ProgressSummaryStats(BaseModel):
    """
    Aggregate statistics for student progress.
    Calculated from all completed challenges.
    """

    total_points: int
    total_completed: int
    completion_percentage: float


class ProgressSummaryResponse(BaseModel):
    """
    Complete progress response with details and summary statistics.
    Returned by GET /progress/me and GET /progress/user/{user_id}.
    """

    progress_items: list[ProgressDetailResponse]
    summary: ProgressSummaryStats


class LeaderboardEntry(BaseModel):
    """
    Single entry in the leaderboard.
    Represents a student's ranking and statistics.
    """

    rank: int
    student_name: str
    total_points: int
    challenges_completed: int


class LeaderboardResponse(BaseModel):
    """
    Complete leaderboard response.
    Contains top 100 students ranked by total points.
    """

    entries: list[LeaderboardEntry]


class HintAccessRequest(BaseModel):
    """
    Request to access a hint for a challenge.
    Student submits unit, challenge, and hint level.
    """

    unit_id: int = Field(ge=1, description="Unit ID (must be >= 1)")
    challenge_id: int = Field(ge=1, description="Challenge ID (must be >= 1)")
    hint_level: int = Field(ge=1, description="Hint level (must be >= 1)")


class HintAccessResponse(BaseModel):
    """
    Response when a hint is successfully accessed.
    Returns the hint record ID and timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    hint_id: int
    accessed_at: datetime


class StudentProgressSummary(BaseModel):
    """
    Summary of a single student's progress in the past week.
    Used in weekly reports to show individual student statistics.
    """

    student_name: str
    completions_this_week: int
    points_this_week: int


class WeeklyReportResponse(BaseModel):
    """
    Complete weekly progress report for all students.
    Provides aggregated metrics and top/struggling student lists.
    """

    students_active: int  # Count of students with activity in past 7 days
    total_completions: int  # Total challenges completed by all students in week
    avg_points_per_student: float  # Average points earned per active student

    top_performers: list[StudentProgressSummary]  # Top 5 by points
    struggling_students: list[StudentProgressSummary]  # <3 completions

    generated_at: datetime  # When this report was generated


class StudentWithStats(UserResponse):
    """
    User response extended with aggregated progress statistics.
    Used when listing students with their total points and challenges completed.
    """

    total_points: int  # Sum of all points earned
    challenges_completed: int  # Count of completed challenges


class StudentListResponse(BaseModel):
    """
    Paginated list of students with their statistics.
    Returned by GET /users endpoint with filtering and sorting.
    """

    students: list[StudentWithStats]
    total_count: int  # Total number of students matching the filter
    offset: int  # Pagination offset
    limit: int  # Pagination limit


class AttemptRecord(BaseModel):
    """
    Single attempt record for detailed student view.
    Represents one submission attempt (correct or incorrect).
    """

    unit_id: int
    challenge_id: int
    query: str  # The SQL query submitted
    is_correct: bool  # Whether query was correct
    attempted_at: datetime


class HintAccessRecord(BaseModel):
    """
    Single hint access record for detailed student view.
    Represents one hint accessed by the student.
    """

    unit_id: int
    challenge_id: int
    hint_level: int
    accessed_at: datetime


class ChallengeMetrics(BaseModel):
    """
    Metrics for a single challenge.
    Calculated from attempts and completions.
    """

    total_attempts: int  # Total submissions (correct + incorrect)
    correct_attempts: int  # Number of correct submissions
    success_rate: float  # Percentage (0-100)
    total_hints_used: int  # Total hint accesses for this challenge
    last_attempted: datetime  # Timestamp of last attempt


class ChallengeDetail(BaseModel):
    """
    Detailed view of a single challenge.
    Includes challenge metadata, metrics, and attempt history.
    """

    unit_id: int
    challenge_id: int
    title: str  # From CHALLENGES dict
    description: str  # From CHALLENGES dict
    points: int  # From CHALLENGES dict
    metrics: ChallengeMetrics
    attempts: list[AttemptRecord]
    hints: list[HintAccessRecord]


class UnitDetail(BaseModel):
    """
    Detailed view of a unit.
    Contains all challenges in the unit with their details.
    """

    unit_id: int
    unit_title: str  # e.g., "Unit 1: SELECT Basics"
    challenges: list[ChallengeDetail]


class StudentMetrics(BaseModel):
    """
    Overall metrics for a student.
    Aggregated statistics across all challenges.
    """

    total_points: int
    total_challenges_completed: int
    total_attempts: int
    average_attempts_per_challenge: float
    overall_success_rate: float
    total_hints_used: int


class ActivityLogEntry(BaseModel):
    """
    Single entry in activity log.
    Represents either an attempt or hint access.
    """

    action_type: str  # "attempt" or "hint"
    unit_id: int
    challenge_id: int
    challenge_title: str
    timestamp: datetime
    details: str  # Human-readable action description


class StudentDetailResponse(BaseModel):
    """
    Complete detailed student profile.
    Returned by GET /users/{user_id}?detailed=true
    """

    user: UserResponse
    metrics: StudentMetrics
    units: list[UnitDetail]
    activity_log: list[ActivityLogEntry]  # Last 10 actions, newest first


class ChallengeAnalytics(BaseModel):
    """
    Analytics for a single challenge across all students.
    Includes success rates and attempt statistics.
    """

    unit_id: int
    challenge_id: int
    challenge_title: str
    total_attempts: int  # Total submissions by all students
    correct_attempts: int  # Correct submissions by all students
    success_rate: float  # Percentage (0-100)
    avg_hints_per_attempt: float  # Average hints used per attempt


class ClassMetrics(BaseModel):
    """
    Overall metrics for the entire class.
    Aggregated statistics across all students.
    """

    total_students: int  # Total students in system
    active_students: int  # Students with at least 1 completion
    avg_completion_rate: float  # Average % of 7 challenges completed per active student
    median_points: int  # Median total points earned
    percentile_25: int  # 25th percentile of points
    percentile_50: int  # 50th percentile (same as median)
    percentile_75: int  # 75th percentile of points
    total_challenges_completed: int  # Sum of all completions
    total_attempts: int  # Sum of all attempts (correct + incorrect)
    avg_success_rate: float  # Overall success rate across all attempts


class ChallengeDistribution(BaseModel):
    """
    Challenges ranked by difficulty.
    Shows hardest and easiest challenges based on success rates.
    """

    easiest_challenges: list[ChallengeAnalytics]  # Top 3 by success rate
    hardest_challenges: list[ChallengeAnalytics]  # Bottom 3 by success rate


class WeeklyTrend(BaseModel):
    """
    Class progress for a single week.
    Used for tracking week-over-week trends.
    """

    week_start_date: datetime
    week_end_date: datetime
    completions: int  # Challenges completed this week
    total_points_earned: int  # Points earned this week
    unique_students: int  # Number of students active this week


class ClassAnalyticsResponse(BaseModel):
    """
    Complete class-wide analytics response.
    Returned by GET /analytics/class endpoint (teachers only).
    """

    generated_at: datetime  # When this report was generated
    metrics: ClassMetrics
    challenges: list[ChallengeAnalytics]  # All 7 challenges with stats
    difficulty_distribution: ChallengeDistribution  # Hardest/easiest ranking
    weekly_trends: list[WeeklyTrend]  # Past 4 weeks of data
    cache_expires_at: datetime  # When cache will be refreshed
