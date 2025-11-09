"""
Test hints endpoint - track when students access hints for challenges.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch

# Import models at module level so SQLModel knows about them
from app.models import User, Hint  # noqa: F401


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


def create_teacher_and_get_token(
    client: TestClient, email: str, password: str, name: str
) -> str:
    """
    Helper to create a teacher and get their JWT token.

    Args:
        client: TestClient instance
        email: Teacher email
        password: Teacher password
        name: Teacher name

    Returns:
        JWT access token string
    """
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "teacher"},
    )
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


# ============================================================================
# POST /hints/access ENDPOINT TESTS (6 tests)
# ============================================================================


def test_hint_access_endpoint_exists(client: TestClient):
    """Test POST /hints/access endpoint returns 201 Created."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )
    assert response.status_code == 201


def test_hint_access_requires_authentication(client: TestClient):
    """Test POST /hints/access returns 401 without token."""
    response = client.post(
        "/hints/access",
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )
    assert response.status_code == 401


def test_hint_access_requires_student_role(client: TestClient):
    """Test teachers cannot access hints (403 Forbidden)."""
    token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )
    assert response.status_code == 403


def test_hint_access_success(client: TestClient):
    """Test student can successfully access a hint (201)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 2},
    )

    assert response.status_code == 201
    data = response.json()
    assert "hint_id" in data
    assert "accessed_at" in data


def test_hint_access_creates_database_record(client: TestClient, session: Session):
    """Test hint access creates a database record."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Access a hint
    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 2},
    )

    assert response.status_code == 201

    # Verify in database
    statement = select(Hint).where(
        Hint.unit_id == 1, Hint.challenge_id == 1, Hint.hint_level == 2
    )
    hint = session.exec(statement).first()
    assert hint is not None
    assert hint.hint_level == 2


def test_hint_access_challenge_must_exist(client: TestClient):
    """Test accessing hint for non-existent challenge returns 404."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 999, "challenge_id": 999, "hint_level": 1},
    )

    assert response.status_code == 404


# ============================================================================
# REQUEST VALIDATION TESTS (4 tests)
# ============================================================================


def test_hint_access_missing_unit_id(client: TestClient):
    """Test missing unit_id returns validation error (422)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"challenge_id": 1, "hint_level": 1},
    )

    assert response.status_code == 422


def test_hint_access_missing_challenge_id(client: TestClient):
    """Test missing challenge_id returns validation error (422)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "hint_level": 1},
    )

    assert response.status_code == 422


def test_hint_access_missing_hint_level(client: TestClient):
    """Test missing hint_level returns validation error (422)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1},
    )

    assert response.status_code == 422


def test_hint_access_invalid_hint_level_zero(client: TestClient):
    """Test hint_level=0 returns validation error (422)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 0},
    )

    assert response.status_code == 422


# ============================================================================
# MULTIPLE ACCESS TESTS (3 tests)
# ============================================================================


def test_hint_access_same_hint_multiple_times(client: TestClient, session: Session):
    """Test student can access same hint multiple times (each tracked)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Access same hint 3 times
    for i in range(3):
        response = client.post(
            "/hints/access",
            headers={"Authorization": f"Bearer {token}"},
            json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
        )
        assert response.status_code == 201

    # Verify all 3 records in database
    statement = select(Hint).where(
        Hint.unit_id == 1, Hint.challenge_id == 1, Hint.hint_level == 1
    )
    hints = session.exec(statement).all()
    assert len(hints) == 3


def test_hint_access_no_unique_constraint(client: TestClient, session: Session):
    """Test multiple identical hint accesses are all stored (no unique constraint)."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Access same hint twice identically
    response1 = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 2},
    )
    response2 = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 2},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    # Both should have different hint_ids
    data1 = response1.json()
    data2 = response2.json()
    assert data1["hint_id"] != data2["hint_id"]

    # Both records in database
    statement = select(Hint)
    all_hints = session.exec(statement).all()
    assert len(all_hints) >= 2


def test_hint_access_different_students_same_hint(client: TestClient, session: Session):
    """Test different students can access same hint."""
    # Student 1
    token1 = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )

    # Student 2
    token2 = create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )

    # Both access same hint
    response1 = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token1}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 3},
    )
    response2 = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token2}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 3},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    # Both in database
    statement = select(Hint).where(
        Hint.unit_id == 1, Hint.challenge_id == 1, Hint.hint_level == 3
    )
    hints = session.exec(statement).all()
    assert len(hints) == 2


# ============================================================================
# RESPONSE FORMAT TESTS (3 tests)
# ============================================================================


def test_hint_access_response_has_required_fields(client: TestClient):
    """Test response includes hint_id and accessed_at."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )

    assert response.status_code == 201
    data = response.json()

    assert "hint_id" in data
    assert "accessed_at" in data


def test_hint_access_response_field_types(client: TestClient):
    """Test response field types are correct."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )

    assert response.status_code == 201
    data = response.json()

    assert isinstance(data["hint_id"], int)
    assert isinstance(data["accessed_at"], str)  # ISO format datetime string


def test_hint_access_timestamp_is_recent(client: TestClient):
    """Test accessed_at timestamp is set to recent time."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
    )

    assert response.status_code == 201
    data = response.json()

    # Verify timestamp is not empty and is ISO format
    assert data["accessed_at"]
    assert "T" in data["accessed_at"]  # ISO format includes T


# ============================================================================
# DIFFERENT HINT LEVELS TESTS (2 tests)
# ============================================================================


def test_hint_access_multiple_levels_same_challenge(
    client: TestClient, session: Session
):
    """Test student can access different hint levels for same challenge."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Access levels 1, 2, 3
    for level in [1, 2, 3]:
        response = client.post(
            "/hints/access",
            headers={"Authorization": f"Bearer {token}"},
            json={"unit_id": 1, "challenge_id": 1, "hint_level": level},
        )
        assert response.status_code == 201

    # Verify all 3 levels in database
    statement = select(Hint).where(Hint.unit_id == 1, Hint.challenge_id == 1)
    hints = session.exec(statement).all()
    assert len(hints) == 3
    levels = {h.hint_level for h in hints}
    assert levels == {1, 2, 3}


def test_hint_access_different_levels_tracked_separately(
    client: TestClient, session: Session
):
    """Test different hint levels are tracked as separate records."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Access level 1 twice, level 2 once
    for _ in range(2):
        client.post(
            "/hints/access",
            headers={"Authorization": f"Bearer {token}"},
            json={"unit_id": 1, "challenge_id": 1, "hint_level": 1},
        )
    client.post(
        "/hints/access",
        headers={"Authorization": f"Bearer {token}"},
        json={"unit_id": 1, "challenge_id": 1, "hint_level": 2},
    )

    # Level 1: 2 records, Level 2: 1 record
    level1_hints = session.exec(
        select(Hint).where(
            Hint.unit_id == 1,
            Hint.challenge_id == 1,
            Hint.hint_level == 1,
        )
    ).all()
    level2_hints = session.exec(
        select(Hint).where(
            Hint.unit_id == 1,
            Hint.challenge_id == 1,
            Hint.hint_level == 2,
        )
    ).all()

    assert len(level1_hints) == 2
    assert len(level2_hints) == 1
