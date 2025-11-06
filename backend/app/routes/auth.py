"""
Authentication routes - register, login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.auth import hash_password


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
