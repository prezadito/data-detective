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
