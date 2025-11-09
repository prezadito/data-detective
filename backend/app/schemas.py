"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str
    created_at: datetime


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
