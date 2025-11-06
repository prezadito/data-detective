"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


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

    id: int
    email: str
    name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel
