"""
Authentication routes - register, login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from app.database import get_session
from app.models import User
from app.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    create_password_reset_token,
    verify_and_use_reset_token,
)
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user (student or teacher).

    Args:
        user_data: User registration data (email, name, password, role)
        session: Database session (injected)

    Returns:
        Created user (without password!)

    Raises:
        HTTPException: If email already registered
    """
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        logger.warning(
            f"Registration attempt with existing email: {user_data.email}",
            extra={"email": user_data.email, "role": user_data.role},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create user with hashed password
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=hashed_password,
    )

    # Save to database
    session.add(new_user)
    session.commit()
    session.refresh(new_user)  # Get the ID assigned by database

    logger.info(
        f"New user registered: {new_user.email} (role: {new_user.role})",
        extra={"user_id": new_user.id, "email": new_user.email, "role": new_user.role},
    )

    return new_user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, session: Session = Depends(get_session)):
    """
    Login a user and return JWT access token and refresh token.

    Args:
        login_data: User login credentials (email, password)
        session: Database session (injected)

    Returns:
        JWT access token, refresh token, and token type

    Raises:
        HTTPException: 401 if credentials are incorrect
    """
    # Find user by email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()

    # Verify user exists and password is correct
    # IMPORTANT: Use same error message for both cases to prevent user enumeration
    if not user or not verify_password(login_data.password, user.password_hash):
        logger.warning(
            f"Failed login attempt for email: {login_data.email}",
            extra={"email": login_data.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    user.last_login = datetime.now()
    session.add(user)
    session.commit()

    logger.info(
        f"User logged in: {user.email}",
        extra={"user_id": user.id, "email": user.email, "role": user.role},
    )

    # Create JWT access token with user information
    access_token = create_access_token(
        data={
            "sub": user.email,  # Standard JWT claim for subject (user identifier)
            "user_id": user.id,
            "role": user.role,
        }
    )

    # Create refresh token and store in database
    refresh_token = create_refresh_token(user.id, session)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    request: RefreshTokenRequest, session: Session = Depends(get_session)
):
    """
    Exchange refresh token for new access token.

    This endpoint allows users to get a new access token without
    re-entering their credentials, as long as they have a valid refresh token.

    Args:
        request: Refresh token request with refresh_token field
        session: Database session (injected)

    Returns:
        New access token and token type

    Raises:
        HTTPException: 401 if refresh token is invalid, expired, or revoked
    """
    # Verify refresh token and get user
    user = verify_refresh_token(request.refresh_token, session)

    # Create new access token with user information
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: RefreshTokenRequest, session: Session = Depends(get_session)):
    """
    Logout user by revoking their refresh token.

    This endpoint marks the refresh token as revoked in the database,
    preventing it from being used for future token refreshes.
    The access token will continue to work until it expires.

    Args:
        request: Refresh token request with refresh_token field
        session: Database session (injected)

    Returns:
        Success message

    Raises:
        HTTPException: 401 if refresh token is invalid
    """
    # Revoke the refresh token
    user = revoke_refresh_token(request.refresh_token, session)

    if user:
        logger.info(
            f"User logged out: {user.email}",
            extra={"user_id": user.id, "email": user.email},
        )

    return {"message": "Successfully logged out"}


@router.post("/password-reset-request", response_model=PasswordResetResponse)
def request_password_reset(
    request: PasswordResetRequest, session: Session = Depends(get_session)
):
    """
    Request a password reset token.

    This endpoint accepts an email address and generates a password reset token
    if the user exists. For security (preventing user enumeration), it always
    returns a 200 response with a generic message, regardless of whether the
    email exists in the system.

    In production, the token would be sent via email. For now, it's returned
    in the response for testing purposes.

    Args:
        request: Password reset request with email field
        session: Database session (injected)

    Returns:
        Message and reset token (empty string if user doesn't exist)

    Security Note:
        Always returns 200 OK to prevent attackers from discovering which
        email addresses are registered in the system.
    """
    # Generate reset token (returns None if user doesn't exist)
    reset_token = create_password_reset_token(request.email, session)

    # Generic message that doesn't reveal if user exists
    message = "If this email exists, a reset token has been sent"

    # Return token if created, empty string otherwise
    # In production, we would send email instead and not return token
    return {
        "message": message,
        "reset_token": reset_token if reset_token else "",
    }


@router.post("/password-reset-confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(
    request: PasswordResetConfirm, session: Session = Depends(get_session)
):
    """
    Confirm password reset with token and new password.

    This endpoint validates the reset token and updates the user's password
    if the token is valid. The token is marked as used after successful reset
    to prevent reuse.

    Token validation checks:
    - Token exists in database
    - Token not already used
    - Token not expired (1 hour limit)
    - User still exists

    Args:
        request: Password reset confirmation with reset_token and new_password
        session: Database session (injected)

    Returns:
        Success message

    Raises:
        HTTPException: 401 if token is invalid, expired, or already used
        HTTPException: 422 if new_password doesn't meet requirements (8-100 chars)
    """
    # Verify token and update password
    verify_and_use_reset_token(request.reset_token, request.new_password, session)

    return {"message": "Password has been reset successfully"}
