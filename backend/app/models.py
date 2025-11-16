"""
Database models for SQL Query Master.
"""

from sqlmodel import SQLModel, Field, UniqueConstraint, Column, Text
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    """
    User model - represents both students and teachers.

    This is a SQLModel, which means:
    - It's a database table (table=True)
    - It validates data (Pydantic)
    - It has type hints (Python types)
    """

    __tablename__ = "users"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # User details
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=100)
    role: str = Field(max_length=20)  # 'student' or 'teacher'
    password_hash: str = Field(max_length=255)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None


class RefreshToken(SQLModel, table=True):
    """
    RefreshToken model - stores refresh tokens for user sessions.

    Allows:
    - Long-lived authentication (days instead of minutes)
    - Token revocation (logout)
    - Multiple sessions per user (different devices)
    """

    __tablename__ = "refresh_tokens"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Token data
    token: str = Field(unique=True, index=True, max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Token lifecycle
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)


class PasswordResetToken(SQLModel, table=True):
    """
    PasswordResetToken model - stores temporary tokens for password reset.

    Allows:
    - Secure password reset flow
    - Single-use tokens (via used flag)
    - Short expiration (1 hour)
    - Multiple pending reset requests per user
    """

    __tablename__ = "password_reset_tokens"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Token data
    token: str = Field(unique=True, index=True, max_length=500)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Token lifecycle
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)


class Progress(SQLModel, table=True):
    """
    Progress model - tracks student progress on challenges.

    Records when a student completes a challenge, tracking:
    - Which challenge was completed (hardcoded or custom)
    - When it was completed
    - Points earned
    - How many hints were used

    One record per student per challenge (unique constraint).
    For custom challenges, unit_id and challenge_id are nullable.
    """

    __tablename__ = "progress"

    # Unique constraint: one progress record per user per challenge
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "unit_id",
            "challenge_id",
            "custom_challenge_id",
            name="unique_user_challenge",
        ),
    )

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Challenge identifiers (for hardcoded challenges)
    unit_id: Optional[int] = Field(default=None, index=True)
    challenge_id: Optional[int] = Field(default=None, index=True)

    # Custom challenge identifier (for teacher-created challenges)
    custom_challenge_id: Optional[int] = Field(
        default=None, foreign_key="custom_challenges.id", index=True
    )

    # Progress data
    points_earned: int
    hints_used: int = Field(default=0)
    query: str = Field(max_length=5000)  # SQL query submitted by student

    # Timestamp
    completed_at: datetime = Field(default_factory=datetime.now)


class Hint(SQLModel, table=True):
    """
    Hint model - tracks when students access hints for challenges.

    Records every hint access (no unique constraint - students can access
    same hint multiple times, and each access is tracked separately).

    Allows tracking:
    - Which student accessed a hint
    - Which challenge (hardcoded or custom) and hint level
    - When the hint was accessed
    """

    __tablename__ = "hints"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key
    user_id: int = Field(foreign_key="users.id", index=True)

    # Challenge identifiers (for hardcoded challenges)
    unit_id: Optional[int] = Field(default=None, index=True)
    challenge_id: Optional[int] = Field(default=None, index=True)

    # Custom challenge identifier (for teacher-created challenges)
    custom_challenge_id: Optional[int] = Field(
        default=None, foreign_key="custom_challenges.id", index=True
    )

    # Hint level (1-3 for MVP, flexible for future validation)
    hint_level: int

    # Timestamp (when hint was accessed)
    accessed_at: datetime = Field(default_factory=datetime.now)


class Attempt(SQLModel, table=True):
    """
    Attempt model - tracks every challenge submission attempt.

    Records each attempt to solve a challenge (correct or incorrect).
    Multiple attempts per student per challenge allowed (no unique constraint).

    Enables:
    - Tracking learning progress (how many tries before success)
    - Analytics on common mistakes
    - Future: difficulty scoring, hint effectiveness
    """

    __tablename__ = "attempts"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key
    user_id: int = Field(foreign_key="users.id", index=True)

    # Challenge identifiers (for hardcoded challenges)
    unit_id: Optional[int] = Field(default=None, index=True)
    challenge_id: Optional[int] = Field(default=None, index=True)

    # Custom challenge identifier (for teacher-created challenges)
    custom_challenge_id: Optional[int] = Field(
        default=None, foreign_key="custom_challenges.id", index=True
    )

    # Attempt data
    query: str = Field(max_length=5000)  # Student's SQL query
    is_correct: bool  # True if query matches expected, False otherwise

    # Timestamp
    attempted_at: datetime = Field(default_factory=datetime.now)


class Dataset(SQLModel, table=True):
    """
    Dataset model - stores metadata about teacher-uploaded CSV files.

    Each dataset has a corresponding dynamically created table in the database
    where the CSV data is stored. Teachers can create custom challenges that
    query these datasets.
    """

    __tablename__ = "datasets"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Ownership
    teacher_id: int = Field(foreign_key="users.id", index=True)

    # Dataset metadata
    name: str = Field(max_length=200)  # User-friendly name
    description: Optional[str] = Field(default=None, max_length=1000)
    original_filename: str = Field(max_length=255)  # e.g., "sales_data.csv"

    # Database info
    table_name: str = Field(
        max_length=100, unique=True, index=True
    )  # e.g., "dataset_123"
    row_count: int = Field(default=0)

    # Schema storage (JSON string)
    schema_json: str = Field(
        sa_column=Column(Text)
    )  # {"columns": [{"name": "id", "type": "INTEGER"}, ...]}

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CustomChallenge(SQLModel, table=True):
    """
    CustomChallenge model - stores teacher-created challenges.

    Each custom challenge is linked to a dataset and contains the expected
    query, hints, and metadata. Teachers can create challenges for students
    to practice SQL on custom datasets.
    """

    __tablename__ = "custom_challenges"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Ownership
    teacher_id: int = Field(foreign_key="users.id", index=True)
    dataset_id: int = Field(foreign_key="datasets.id", index=True)

    # Challenge content
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    points: int = Field(default=100, ge=50, le=500)  # 50-500 points
    difficulty: str = Field(
        default="medium", max_length=20
    )  # "easy", "medium", "hard"

    # SQL query
    expected_query: str = Field(max_length=5000)

    # Hints (JSON array stored as string)
    hints_json: str = Field(
        sa_column=Column(Text)
    )  # ["Hint 1", "Hint 2", "Hint 3"]

    # Visibility
    is_active: bool = Field(default=True)  # Can be deactivated without deletion
    is_public: bool = Field(default=False)  # Future: share with other teachers

    # Expected output (cached for result-based validation)
    expected_output_json: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # Cached query result

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
