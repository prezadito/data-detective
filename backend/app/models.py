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
