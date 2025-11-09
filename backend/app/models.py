"""
Database models for SQL Query Master.
"""

from sqlmodel import SQLModel, Field
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
