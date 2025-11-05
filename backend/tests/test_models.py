"""
Test database models.
"""

from sqlmodel import Session, create_engine, SQLModel
from app.models import User
from sqlalchemy.exc import IntegrityError
import pytest


@pytest.fixture(name="session")
def session_fixture():
    """
    Create a fresh in-memory database for each test.
    This ensures tests don't interfere with each other.
    """
    # In-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_create_user(session: Session):
    """Test creating a user in the database."""

    # Create a user
    user = User(
        email="student@school.edu",
        name="Test Student",
        role="student",
        password_hash="hashed_password_here",
    )

    # Add to database
    session.add(user)
    session.commit()
    session.refresh(user)  # Refresh to get the ID from database

    # Assertions
    assert user.id is not None  # Database assigned an ID
    assert user.email == "student@school.edu"
    assert user.name == "Test Student"
    assert user.role == "student"
    assert user.created_at is not None  # Should auto-set timestamp


def test_user_email_must_be_unique(session: Session):
    """Test that two users cannot have the same email."""
    # from app.models import User

    # Create first user
    user1 = User(
        email="same@email.com", name="User One", role="student", password_hash="hash1"
    )
    session.add(user1)
    session.commit()

    # Try to create second user with same email
    user2 = User(
        email="same@email.com",  # Same email!
        name="User Two",
        role="student",
        password_hash="hash2",
    )
    session.add(user2)

    # Should raise IntegrityError
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_roles(session: Session):
    """Test creating users with different roles."""
    # from app.models import User

    # Create student
    student = User(
        email="student@school.edu",
        name="Student Name",
        role="student",
        password_hash="hash",
    )

    # Create teacher
    teacher = User(
        email="teacher@school.edu",
        name="Teacher Name",
        role="teacher",
        password_hash="hash",
    )

    session.add(student)
    session.add(teacher)
    session.commit()

    assert student.role == "student"
    assert teacher.role == "teacher"
