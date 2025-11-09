"""
Authentication utilities - password hashing and JWT tokens.
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import uuid
import secrets
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from app.database import get_session

# Load environment variables from .env file
load_dotenv()

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = int(
    os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", "1")
)

# OAuth2 scheme for token extraction
# tokenUrl points to our login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to check
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration time (use timezone-aware datetime)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims for uniqueness and tracking
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),  # Issued at
            "jti": str(uuid.uuid4()),  # Unique JWT ID
        }
    )

    # Create and return the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
):
    """
    Dependency to get current authenticated user from JWT token.

    This dependency extracts and validates the JWT token from the
    Authorization header, decodes it, and retrieves the user from database.

    Args:
        token: JWT token from Authorization header (extracted by oauth2_scheme)
        db: Database session (injected by FastAPI)

    Returns:
        User object if authentication succeeds

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    from app.models import User

    # Exception to raise for any authentication failure
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract claims from token
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        # Validate required claims are present
        if email is None or user_id is None:
            raise credentials_exception

    except JWTError:
        # Invalid token, expired token, or decoding error
        raise credentials_exception

    # Get user from database
    user = db.get(User, user_id)

    if user is None:
        # Token is valid but user doesn't exist (deleted?)
        raise credentials_exception

    return user


def create_refresh_token(user_id: int, db: Session) -> str:
    """
    Create a refresh token and store it in the database.

    Refresh tokens are long-lived (days instead of minutes) and allow
    users to get new access tokens without re-entering credentials.

    Args:
        user_id: ID of the user
        db: Database session

    Returns:
        JWT refresh token string
    """
    from app.models import RefreshToken

    # Create JWT with longer expiration
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data = {
        "sub": str(user_id),  # User ID as subject
        "type": "refresh",  # Mark as refresh token
    }

    # Create the JWT token
    token_string = create_access_token(token_data, expires_delta)

    # Calculate expiration datetime
    expires_at = datetime.now(timezone.utc) + expires_delta

    # Store in database
    refresh_token = RefreshToken(
        token=token_string, user_id=user_id, expires_at=expires_at, revoked=False
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return token_string


def verify_refresh_token(token: str, db: Session):
    """
    Verify a refresh token and return the associated user.

    Checks that the token:
    - Is a valid JWT
    - Is marked as a refresh token
    - Exists in the database
    - Is not revoked
    - Is not expired
    - Belongs to an existing user

    Args:
        token: Refresh token string
        db: Database session

    Returns:
        User object if token is valid

    Raises:
        HTTPException: 401 if token is invalid for any reason
    """
    from app.models import RefreshToken, User
    from sqlmodel import select

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        token_type: str = payload.get("type")

        # Verify it's a refresh token
        if token_type != "refresh":
            raise credentials_exception

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    # Check token exists in database
    statement = select(RefreshToken).where(
        RefreshToken.token == token, RefreshToken.user_id == user_id
    )
    db_token = db.exec(statement).first()

    if not db_token:
        raise credentials_exception

    # Check not revoked
    if db_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )

    # Check not expired
    # Make database datetime timezone-aware (SQLite stores naive datetimes)
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at_aware:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )

    # Get and return user
    user = db.get(User, user_id)
    if not user:
        raise credentials_exception

    return user


def revoke_refresh_token(token: str, db: Session) -> bool:
    """
    Revoke a refresh token (logout).

    Marks the token as revoked in the database, preventing it from
    being used for future token refreshes.

    Args:
        token: Refresh token to revoke
        db: Database session

    Returns:
        True if successful

    Raises:
        HTTPException: 401 if token doesn't exist or is already revoked
    """
    from app.models import RefreshToken
    from sqlmodel import select

    statement = select(RefreshToken).where(RefreshToken.token == token)
    db_token = db.exec(statement).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Check if already revoked
    if db_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Mark as revoked
    db_token.revoked = True
    db.add(db_token)
    db.commit()

    return True


def create_password_reset_token(email: str, db: Session) -> Optional[str]:
    """
    Create a password reset token for a user.

    This function generates a secure random token and stores it in the database
    with a 1-hour expiration. For security, it returns None if the user doesn't
    exist, allowing the calling code to always return a success response to
    prevent user enumeration attacks.

    Args:
        email: User's email address
        db: Database session

    Returns:
        Reset token string if user exists, None otherwise
    """
    from app.models import User, PasswordResetToken
    from sqlmodel import select

    # Find user by email
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()

    # If user doesn't exist, return None (don't reveal this to client!)
    if not user:
        return None

    # Generate cryptographically secure random token
    # token_urlsafe(32) generates 32 bytes = 256 bits of randomness
    # Encoded as URL-safe base64 string (~43 characters)
    token_string = secrets.token_urlsafe(32)

    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )

    # Store token in database
    reset_token = PasswordResetToken(
        token=token_string,
        user_id=user.id,
        expires_at=expires_at,
        used=False,
    )

    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)

    return token_string


def verify_and_use_reset_token(token: str, new_password: str, db: Session) -> bool:
    """
    Verify reset token and update user password.

    This function validates a password reset token and, if valid, updates the
    user's password and marks the token as used. All validations use a generic
    error message to prevent information leakage.

    Validation order (fail fast):
    1. Token exists in database
    2. Token not already used (used tokens stay invalid forever)
    3. Token not expired
    4. User still exists

    Args:
        token: Password reset token string
        new_password: New password (plain text, will be hashed)
        db: Database session

    Returns:
        True if successful

    Raises:
        HTTPException: 401 if token is invalid for any reason
                      (generic message: "Invalid or expired reset token")
    """
    from app.models import PasswordResetToken, User
    from sqlmodel import select

    # Generic exception for all failures (don't reveal specifics!)
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired reset token",
    )

    # 1. Find token in database
    statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
    db_token = db.exec(statement).first()

    if not db_token:
        raise invalid_token_exception

    # 2. Check if already used (fail fast - used tokens stay invalid forever)
    if db_token.used:
        raise invalid_token_exception

    # 3. Check expiration (with timezone-aware comparison like refresh tokens)
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at_aware:
        raise invalid_token_exception

    # 4. Get user (ensure they still exist)
    user = db.get(User, db_token.user_id)
    if not user:
        raise invalid_token_exception

    # 5. Update user password (hash the new password)
    user.password_hash = hash_password(new_password)
    db.add(user)

    # 6. Mark token as used
    db_token.used = True
    db.add(db_token)

    # 7. Commit both changes atomically
    db.commit()

    return True
