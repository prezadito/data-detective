"""
Database models for SQL Query Master.
"""

from sqlmodel import SQLModel, Field, UniqueConstraint
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
    - Which challenge was completed
    - When it was completed
    - Points earned
    - How many hints were used

    One record per student per challenge (unique constraint).
    """

    __tablename__ = "progress"

    # Unique constraint: one progress record per user per challenge
    __table_args__ = (
        UniqueConstraint(
            "user_id", "unit_id", "challenge_id", name="unique_user_challenge"
        ),
    )

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", index=True)

    # Challenge identifiers (no foreign keys yet - tables don't exist)
    unit_id: int = Field(index=True)
    challenge_id: int = Field(index=True)

    # Progress data
    points_earned: int
    hints_used: int = Field(default=0)
    query: str = Field(max_length=5000)  # SQL query submitted by student

    # Timestamp
    completed_at: datetime = Field(default_factory=datetime.now)
