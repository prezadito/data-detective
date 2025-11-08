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
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
)


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    user.last_login = datetime.now()
    session.add(user)
    session.commit()

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
    revoke_refresh_token(request.refresh_token, session)

    return {"message": "Successfully logged out"}
