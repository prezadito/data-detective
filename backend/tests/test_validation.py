"""
Test challenge validation - query validation and attempt tracking.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch

# Import models at module level so SQLModel knows about them
from app.models import User, Progress, Attempt  # noqa: F401


@pytest.fixture(name="engine")
def engine_fixture():
    """
    Create a test database engine that persists for the test.
    Uses StaticPool to ensure all connections share the same in-memory database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    """
    Create a database session for direct database access in tests.
    """
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    """
    Create a test client with a fresh test database for each test.
    """
    # Patch create_db_and_tables FIRST before importing app
    with patch("app.database.create_db_and_tables"):
        from app.main import app
        from app.database import get_session

        # Override dependency to use test database
        def get_test_session():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session

        # Create test client
        client = TestClient(app, raise_server_exceptions=True)
        yield client

        app.dependency_overrides.clear()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_student_and_get_token(
    client: TestClient, email: str, password: str, name: str
) -> str:
    """
    Helper to create a student and get their JWT token.

    Args:
        client: TestClient instance
        email: Student email
        password: Student password
        name: Student name

    Returns:
        JWT access token string
    """
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "student"},
    )
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


# ============================================================================
# QUERY VALIDATION TESTS (5 tests)
# ============================================================================


def test_correct_query_passes_validation(client: TestClient):
    """Test that correct query (matches sample_solution) passes validation."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit correct query for challenge (1, 1)
    # sample_solution is "SELECT * FROM users"
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 100


def test_incorrect_query_fails_validation(client: TestClient):
    """Test that incorrect query (doesn't match sample_solution) fails validation."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit incorrect query for challenge (1, 1)
    # sample_solution is "SELECT * FROM users"
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT name FROM users",  # Wrong!
            "hints_used": 0,
        },
    )

    assert response.status_code == 400


def test_query_validation_case_insensitive(client: TestClient):
    """Test that query validation is case insensitive."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit with different casing - should still pass
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "select * from users",  # lowercase
            "hints_used": 0,
        },
    )

    assert response.status_code == 200


def test_query_validation_ignores_whitespace(client: TestClient):
    """Test that query validation ignores extra whitespace."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit with extra whitespace - should still pass
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT  *  FROM  users",  # Extra spaces
            "hints_used": 0,
        },
    )

    assert response.status_code == 200


def test_query_validation_with_empty_query(client: TestClient):
    """Test that empty query fails validation."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit empty query - should fail
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "",
            "hints_used": 0,
        },
    )

    assert response.status_code == 400 or response.status_code == 422


# ============================================================================
# ATTEMPT MODEL TESTS (4 tests)
# ============================================================================


def test_attempt_created_on_submission(client: TestClient, session: Session):
    """Test that Attempt record is created for every submission."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenge
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200

    # Verify Attempt record created in database
    statement = select(Attempt).where(Attempt.unit_id == 1, Attempt.challenge_id == 1)
    attempt = session.exec(statement).first()
    assert attempt is not None


def test_attempt_marked_correct_for_valid_query(client: TestClient, session: Session):
    """Test that Attempt.is_correct is True for valid query."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit correct query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200

    # Verify is_correct=True in database
    statement = select(Attempt).where(Attempt.unit_id == 1, Attempt.challenge_id == 1)
    attempt = session.exec(statement).first()
    assert attempt is not None
    assert attempt.is_correct is True


def test_attempt_marked_incorrect_for_invalid_query(
    client: TestClient, session: Session
):
    """Test that Attempt.is_correct is False for invalid query."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit incorrect query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT name FROM users",  # Wrong
            "hints_used": 0,
        },
    )

    assert response.status_code == 400

    # Verify is_correct=False in database
    statement = select(Attempt).where(Attempt.unit_id == 1, Attempt.challenge_id == 1)
    attempt = session.exec(statement).first()
    assert attempt is not None
    assert attempt.is_correct is False


def test_multiple_attempts_tracked_separately(client: TestClient, session: Session):
    """Test that multiple attempts are tracked as separate records."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # First attempt (wrong)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT id FROM users",  # Wrong
            "hints_used": 0,
        },
    )

    # Second attempt (wrong)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT email FROM users",  # Still wrong
            "hints_used": 1,
        },
    )

    # Third attempt (correct)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",  # Correct!
            "hints_used": 2,
        },
    )

    # Verify all 3 attempts in database
    statement = select(Attempt).where(Attempt.unit_id == 1, Attempt.challenge_id == 2)
    attempts = session.exec(statement).all()
    assert len(attempts) == 3


# ============================================================================
# PROGRESS CREATION TESTS (3 tests)
# ============================================================================


def test_correct_query_creates_progress(client: TestClient, session: Session):
    """Test that Progress is created only when query is correct."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit correct query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200

    # Verify Progress record created
    statement = select(Progress).where(
        Progress.unit_id == 1, Progress.challenge_id == 1
    )
    progress = session.exec(statement).first()
    assert progress is not None


def test_incorrect_query_no_progress(client: TestClient, session: Session):
    """Test that Progress is NOT created when query is incorrect."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit incorrect query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 3,
            "query": "SELECT age FROM users",  # Wrong
            "hints_used": 0,
        },
    )

    assert response.status_code == 400

    # Verify NO Progress record created
    statement = select(Progress).where(
        Progress.unit_id == 1, Progress.challenge_id == 3
    )
    progress = session.exec(statement).first()
    assert progress is None


def test_correct_query_returns_200_with_points(client: TestClient):
    """Test that correct submission returns 200 with points earned."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit correct query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 150  # Challenge (1,2) is worth 150 points


# ============================================================================
# FIRST-ATTEMPT-WINS TESTS (3 tests)
# ============================================================================


def test_first_correct_attempt_awards_points(client: TestClient):
    """Test that first correct attempt awards points immediately."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit correct query
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
            "hints_used": 0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 250  # Challenge (2,1) is worth 250 points


def test_second_correct_attempt_no_duplicate_progress(
    client: TestClient, session: Session
):
    """Test that second correct attempt doesn't create duplicate Progress."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # First correct submission
    response1 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 2,
            "query": "SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id",
            "hints_used": 0,
        },
    )

    assert response1.status_code == 200
    first_progress_id = response1.json()["id"]

    # Second correct submission (same query, different formatting - still matches)
    response2 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 2,
            "query": "SELECT   *   FROM   users   LEFT   JOIN   orders   ON   users.id = orders.user_id",
            "hints_used": 1,
        },
    )

    assert response2.status_code == 200
    second_progress_id = response2.json()["id"]

    # Should return same Progress record (idempotent)
    assert second_progress_id == first_progress_id

    # Verify only ONE Progress record in database
    statement = select(Progress).where(
        Progress.unit_id == 2, Progress.challenge_id == 2
    )
    progress_records = session.exec(statement).all()
    assert len(progress_records) == 1


def test_wrong_then_correct_both_tracked(client: TestClient, session: Session):
    """Test that both wrong and correct attempts are tracked in Attempt table."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # First attempt (wrong)
    response1 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 3,
            "challenge_id": 1,
            "query": "SELECT COUNT(*) FROM users WHERE role='admin'",  # Wrong
            "hints_used": 0,
        },
    )

    assert response1.status_code == 400

    # Second attempt (correct)
    response2 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 3,
            "challenge_id": 1,
            "query": "SELECT COUNT(*) FROM users",  # Correct!
            "hints_used": 1,
        },
    )

    assert response2.status_code == 200

    # Verify both attempts in Attempt table
    statement = select(Attempt).where(Attempt.unit_id == 3, Attempt.challenge_id == 1)
    attempts = session.exec(statement).all()
    assert len(attempts) == 2

    # First should be incorrect, second should be correct
    assert attempts[0].is_correct is False
    assert attempts[1].is_correct is True

    # Verify only one Progress record (from correct attempt)
    statement = select(Progress).where(
        Progress.unit_id == 3, Progress.challenge_id == 1
    )
    progress = session.exec(statement).first()
    assert progress is not None


# ============================================================================
# ERROR MESSAGE TESTS (2 tests)
# ============================================================================


def test_incorrect_query_returns_400(client: TestClient):
    """Test that incorrect query returns HTTP 400."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT name FROM users",  # Wrong
            "hints_used": 0,
        },
    )

    assert response.status_code == 400


def test_error_includes_hint_about_answer(client: TestClient):
    """Test that error response includes helpful message about answer."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT name FROM users",  # Wrong
            "hints_used": 0,
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0
