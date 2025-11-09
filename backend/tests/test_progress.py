"""
Test Progress model.
"""

from sqlmodel import Session, create_engine, SQLModel, select
from app.models import User, Progress
from sqlalchemy.exc import IntegrityError
import pytest
from datetime import datetime


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints in SQLite
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


# ============================================================================
# BASIC MODEL TESTS
# ============================================================================


def test_create_progress_record(session: Session):
    """Test creating a progress record with all fields."""
    # Create user first
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create progress
    progress = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,
        points_earned=100,
        hints_used=2,
    )
    session.add(progress)
    session.commit()
    session.refresh(progress)

    # Assertions
    assert progress.id is not None  # Auto-generated
    assert progress.user_id == user.id
    assert progress.unit_id == 1
    assert progress.challenge_id == 1
    assert progress.points_earned == 100
    assert progress.hints_used == 2
    assert progress.completed_at is not None


def test_progress_default_values(session: Session):
    """Test that hints_used defaults to 0 and completed_at is auto-set."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create progress WITHOUT specifying hints_used or completed_at
    progress = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,
        points_earned=50,
    )
    session.add(progress)
    session.commit()
    session.refresh(progress)

    # Assertions
    assert progress.hints_used == 0  # Default value
    assert progress.completed_at is not None  # Auto-set


def test_progress_completed_at_timestamp(session: Session):
    """Test that completed_at is properly set to current time."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Record time before creating progress
    before_time = datetime.now()

    # Create progress
    progress = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,
        points_earned=75,
    )
    session.add(progress)
    session.commit()
    session.refresh(progress)

    # Record time after
    after_time = datetime.now()

    # Assert completed_at is between before_time and after_time
    assert before_time <= progress.completed_at <= after_time


def test_progress_points_earned(session: Session):
    """Test storing different point values."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create progress with different point values
    progress1 = Progress(user_id=user.id, unit_id=1, challenge_id=1, points_earned=100)
    progress2 = Progress(user_id=user.id, unit_id=1, challenge_id=2, points_earned=0)
    progress3 = Progress(user_id=user.id, unit_id=1, challenge_id=3, points_earned=250)

    session.add(progress1)
    session.add(progress2)
    session.add(progress3)
    session.commit()

    assert progress1.points_earned == 100
    assert progress2.points_earned == 0
    assert progress3.points_earned == 250


# ============================================================================
# CONSTRAINT TESTS
# ============================================================================


def test_unique_constraint_user_unit_challenge(session: Session):
    """Test that (user_id, unit_id, challenge_id) must be unique."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create first progress record
    progress1 = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,
        points_earned=100,
    )
    session.add(progress1)
    session.commit()

    # Try to create second progress with SAME user_id, unit_id, challenge_id
    progress2 = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,  # Same combination!
        points_earned=200,
    )
    session.add(progress2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        session.commit()


def test_different_challenges_allowed(session: Session):
    """Test that same user can have multiple progress records for different challenges."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create progress for challenge 1
    progress1 = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=1,
        points_earned=100,
    )
    session.add(progress1)
    session.commit()

    # Create progress for challenge 2 (different challenge, same user and unit)
    progress2 = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=2,  # Different challenge
        points_earned=150,
    )
    session.add(progress2)
    session.commit()

    # Both should exist
    statement = select(Progress).where(Progress.user_id == user.id)
    results = session.exec(statement).all()
    assert len(results) == 2


def test_different_users_same_challenge_allowed(session: Session):
    """Test that different users can complete the same challenge."""
    # Create two users
    user1 = User(
        email="student1@test.com",
        name="Student One",
        role="student",
        password_hash="hash",
    )
    user2 = User(
        email="student2@test.com",
        name="Student Two",
        role="student",
        password_hash="hash",
    )
    session.add(user1)
    session.add(user2)
    session.commit()
    session.refresh(user1)
    session.refresh(user2)

    # Both users complete the same challenge
    progress1 = Progress(
        user_id=user1.id,
        unit_id=1,
        challenge_id=1,
        points_earned=100,
    )
    progress2 = Progress(
        user_id=user2.id,  # Different user
        unit_id=1,
        challenge_id=1,  # Same challenge
        points_earned=150,
    )
    session.add(progress1)
    session.add(progress2)
    session.commit()

    # Both should exist
    statement = select(Progress)
    results = session.exec(statement).all()
    assert len(results) == 2


# ============================================================================
# FOREIGN KEY TESTS
# ============================================================================


def test_progress_requires_valid_user(session: Session):
    """Test that progress cannot be created with non-existent user_id."""
    # Try to create progress with user_id that doesn't exist
    progress = Progress(
        user_id=99999,  # Non-existent user
        unit_id=1,
        challenge_id=1,
        points_earned=100,
    )
    session.add(progress)

    # Should raise IntegrityError due to foreign key constraint
    # Note: SQLite may not enforce this by default
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_can_have_multiple_progress_records(session: Session):
    """Test that a user can have multiple progress records."""
    # Create user
    user = User(
        email="student@test.com",
        name="Test Student",
        role="student",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create 3 different progress records for same user
    progress1 = Progress(user_id=user.id, unit_id=1, challenge_id=1, points_earned=100)
    progress2 = Progress(user_id=user.id, unit_id=1, challenge_id=2, points_earned=150)
    progress3 = Progress(user_id=user.id, unit_id=2, challenge_id=1, points_earned=200)

    session.add(progress1)
    session.add(progress2)
    session.add(progress3)
    session.commit()

    # Query all progress for that user
    statement = select(Progress).where(Progress.user_id == user.id)
    results = session.exec(statement).all()

    # Assert count == 3
    assert len(results) == 3
