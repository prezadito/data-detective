"""
Test progress routes - challenge submission endpoint.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch

# Import models at module level so SQLModel knows about them
from app.models import User, Progress  # noqa: F401


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
    Helper function to register a student and get their JWT token.

    Args:
        client: TestClient instance
        email: Student email
        password: Student password
        name: Student name

    Returns:
        JWT access token string
    """
    # Register student
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "student"},
    )

    # Login and get token
    response = client.post("/auth/login", json={"email": email, "password": password})

    return response.json()["access_token"]


def create_teacher_and_get_token(
    client: TestClient, email: str, password: str, name: str
) -> str:
    """
    Helper function to register a teacher and get their JWT token.

    Args:
        client: TestClient instance
        email: Teacher email
        password: Teacher password
        name: Teacher name

    Returns:
        JWT access token string
    """
    # Register teacher
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "teacher"},
    )

    # Login and get token
    response = client.post("/auth/login", json={"email": email, "password": password})

    return response.json()["access_token"]


# ============================================================================
# BASIC SUBMISSION TESTS
# ============================================================================


def test_submit_challenge_success(client: TestClient, session: Session):
    """Test successful challenge submission by student."""
    # Create student and get token
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
    data = response.json()

    # Verify response fields
    assert "id" in data
    assert "user_id" in data
    assert data["unit_id"] == 1
    assert data["challenge_id"] == 1
    assert data["points_earned"] == 100  # From CHALLENGES definition
    assert data["hints_used"] == 0
    assert "completed_at" in data

    # Verify progress record created in database
    statement = select(Progress).where(
        Progress.unit_id == 1, Progress.challenge_id == 1
    )
    progress = session.exec(statement).first()
    assert progress is not None
    assert progress.query == "SELECT * FROM users"


def test_submit_challenge_with_hints(client: TestClient):
    """Test submission with hints_used."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit with hints
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify hints_used
    assert data["hints_used"] == 2
    assert data["points_earned"] == 150  # Challenge 1-2


def test_submit_stores_query(client: TestClient, session: Session):
    """Test that SQL query is stored in database."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit with specific query
    test_query = "SELECT name FROM students WHERE age > 18"
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 3,
            "query": test_query,
            "hints_used": 0,
        },
    )

    assert response.status_code == 200

    # Verify query stored in database
    statement = select(Progress).where(
        Progress.unit_id == 1, Progress.challenge_id == 3
    )
    progress = session.exec(statement).first()
    assert progress.query == test_query


# ============================================================================
# IDEMPOTENCY TESTS
# ============================================================================


def test_duplicate_submission_returns_existing(client: TestClient, session: Session):
    """Test that submitting same challenge twice returns existing progress."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # First submission
    response1 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users INNER JOIN orders",
            "hints_used": 0,
        },
    )

    assert response1.status_code == 200
    data1 = response1.json()
    first_id = data1["id"]
    first_completed_at = data1["completed_at"]

    # Second submission (duplicate)
    response2 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users JOIN orders",  # Different query!
            "hints_used": 3,  # Different hints!
        },
    )

    assert response2.status_code == 200
    data2 = response2.json()

    # Should return same progress record
    assert data2["id"] == first_id
    assert data2["completed_at"] == first_completed_at
    assert data2["hints_used"] == 0  # Original value, not new one

    # Verify only ONE progress record in database
    statement = select(Progress).where(
        Progress.unit_id == 2, Progress.challenge_id == 1
    )
    results = session.exec(statement).all()
    assert len(results) == 1


def test_duplicate_with_different_query_ignored(client: TestClient, session: Session):
    """Test that duplicate submission ignores new query/hints."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # First submission
    original_query = "SELECT COUNT(*) FROM users"
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 3,
            "challenge_id": 1,
            "query": original_query,
            "hints_used": 0,
        },
    )

    # Second submission with different data
    new_query = "SELECT COUNT(*) AS total FROM users"
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 3,
            "challenge_id": 1,
            "query": new_query,
            "hints_used": 5,
        },
    )

    assert response.status_code == 200

    # Verify original data preserved
    statement = select(Progress).where(
        Progress.unit_id == 3, Progress.challenge_id == 1
    )
    progress = session.exec(statement).first()
    assert progress.query == original_query  # Original query, not new one
    assert progress.hints_used == 0  # Original hints


# ============================================================================
# CHALLENGE VALIDATION TESTS
# ============================================================================


def test_submit_invalid_challenge_404(client: TestClient):
    """Test submitting non-existent challenge returns 404."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit invalid challenge
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 999,
            "challenge_id": 999,
            "query": "SELECT * FROM nowhere",
            "hints_used": 0,
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "challenge not found" in data["detail"].lower()


def test_submit_invalid_unit_404(client: TestClient):
    """Test submitting invalid unit returns 404."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit invalid unit
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 99,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 404


def test_multiple_challenges_same_student(client: TestClient, session: Session):
    """Test student can submit multiple different challenges."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenge 1
    response1 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    assert response1.status_code == 200
    assert response1.json()["points_earned"] == 100

    # Submit challenge 2
    response2 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 1,
        },
    )
    assert response2.status_code == 200
    assert response2.json()["points_earned"] == 150

    # Submit challenge 3 (different unit)
    response3 = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users JOIN orders",
            "hints_used": 0,
        },
    )
    assert response3.status_code == 200
    assert response3.json()["points_earned"] == 250

    # Verify 3 progress records in database
    statement = select(Progress)
    results = session.exec(statement).all()
    assert len(results) == 3


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================


def test_submit_requires_authentication(client: TestClient):
    """Test that unauthenticated request returns 401."""
    # Submit without token
    response = client.post(
        "/progress/submit",
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    assert response.status_code == 401


def test_teacher_cannot_submit(client: TestClient):
    """Test that teachers cannot submit challenges (student-only)."""
    # Create teacher and get token
    token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Try to submit
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

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "permission" in data["detail"].lower()


def test_student_can_only_submit_for_self(client: TestClient, session: Session):
    """Test that user_id is extracted from token (no spoofing)."""
    # Create student and get token
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

    # Verify progress.user_id matches student from token
    statement = select(User).where(User.email == "student@test.com")
    user = session.exec(statement).first()

    statement = select(Progress).where(
        Progress.unit_id == 1, Progress.challenge_id == 1
    )
    progress = session.exec(statement).first()

    assert progress.user_id == user.id


# ============================================================================
# RESPONSE FORMAT TESTS
# ============================================================================


def test_submit_response_format(client: TestClient):
    """Test that response contains all required fields."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenge
    response = client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 2,
            "challenge_id": 2,
            "query": "SELECT * FROM users LEFT JOIN orders",
            "hints_used": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields present
    required_fields = [
        "id",
        "user_id",
        "unit_id",
        "challenge_id",
        "points_earned",
        "hints_used",
        "completed_at",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify no sensitive data leaked
    assert "password" not in data
    assert "password_hash" not in data
