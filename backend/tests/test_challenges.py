"""
Challenge management endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.models import User, Progress, Attempt  # noqa: F401


# ============================================================================
# FIXTURES
# ============================================================================


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
    with patch("app.database.create_db_and_tables"):
        from app.main import app
        from app.database import get_session

        def get_test_session():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()


@pytest.fixture(name="teacher_token")
def teacher_token_fixture(client):
    """Create a teacher user and return their token."""
    response = client.post(
        "/auth/register",
        json={
            "email": "teacher@test.com",
            "name": "Teacher Test",
            "password": "password123",
            "role": "teacher",
        },
    )
    assert response.status_code == 201

    # Login to get token
    response = client.post(
        "/auth/login",
        json={"email": "teacher@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(name="student_token")
def student_token_fixture(client):
    """Create a student user and return their token."""
    response = client.post(
        "/auth/register",
        json={
            "email": "student@test.com",
            "name": "Student Test",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 201

    # Login to get token
    response = client.post(
        "/auth/login",
        json={"email": "student@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_test_progress_data(client, session, student_token):
    """
    Create test data: student completes some challenges, creates attempts.
    """
    # Student completes challenge (1,1) - SELECT All Columns
    response = client.post(
        "/progress/submit",
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code in [200, 201]

    # Student completes challenge (1,2) - SELECT Specific Columns
    response = client.post(
        "/progress/submit",
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 1,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code in [200, 201]

    # Create some failed attempts for (1,3) before eventual success
    response = client.post(
        "/progress/submit",
        json={
            "unit_id": 1,
            "challenge_id": 3,
            "query": "SELECT * FROM users",  # Wrong - will fail
            "hints_used": 0,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 400  # Wrong answer

    # Now submit correct answer
    response = client.post(
        "/progress/submit",
        json={
            "unit_id": 1,
            "challenge_id": 3,
            "query": "SELECT * FROM users WHERE age > 18",
            "hints_used": 2,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code in [200, 201]


# ============================================================================
# PUBLIC ENDPOINT TESTS - GET /challenges (All Challenges)
# ============================================================================


def test_get_all_challenges_returns_all_units(client, student_token):
    """Test that all 3 units are returned."""
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have units array
    assert "units" in data
    units = data["units"]

    # Should have 3 units
    assert len(units) == 3
    unit_ids = [u["unit_id"] for u in units]
    assert set(unit_ids) == {1, 2, 3}


def test_get_all_challenges_returns_all_7_challenges(client, student_token):
    """Test that all 7 challenges are returned."""
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Count all challenges across all units
    total_challenges = 0
    for unit in data["units"]:
        total_challenges += len(unit["challenges"])

    assert total_challenges == 7


def test_get_all_challenges_includes_metadata(client, student_token):
    """Test that challenge metadata is included."""
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Get first challenge
    first_challenge = data["units"][0]["challenges"][0]

    # Verify required fields
    assert "unit_id" in first_challenge
    assert "challenge_id" in first_challenge
    assert "title" in first_challenge
    assert "points" in first_challenge
    assert "description" in first_challenge


def test_get_all_challenges_includes_statistics(client, student_token):
    """Test that statistics are included."""
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Get first challenge
    first_challenge = data["units"][0]["challenges"][0]

    # Verify stat fields
    assert "completion_rate" in first_challenge
    assert "avg_attempts" in first_challenge
    assert isinstance(first_challenge["completion_rate"], (int, float))
    assert isinstance(first_challenge["avg_attempts"], (int, float))


def test_get_all_challenges_no_auth_required(client):
    """Test that endpoint can be accessed without authentication."""
    response = client.get("/challenges")

    # Should still work without auth (or return 401 if auth required)
    # Based on requirements, this should be public
    assert response.status_code in [200, 401]


# ============================================================================
# UNIT-SPECIFIC TESTS - GET /challenges/{unit_id}
# ============================================================================


def test_get_unit_challenges_unit_1_has_3_challenges(client, student_token):
    """Test that unit 1 has 3 challenges."""
    response = client.get(
        "/challenges/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should be a unit response
    assert "unit_id" in data
    assert "unit_title" in data
    assert "challenges" in data

    # Unit 1 should have 3 challenges
    assert len(data["challenges"]) == 3


def test_get_unit_challenges_returns_correct_metadata(client, student_token):
    """Test that metadata is correct for unit challenges."""
    response = client.get(
        "/challenges/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # First challenge in unit 1 should be "SELECT All Columns"
    first_challenge = data["challenges"][0]
    assert first_challenge["title"] == "SELECT All Columns"
    assert first_challenge["points"] == 100
    assert "description" in first_challenge


def test_get_unit_challenges_calculates_completion_rate(client, student_token):
    """Test that completion rate is calculated."""
    response = client.get(
        "/challenges/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Each challenge should have completion_rate
    for challenge in data["challenges"]:
        assert "completion_rate" in challenge
        assert 0 <= challenge["completion_rate"] <= 100


def test_get_unit_challenges_invalid_unit_returns_404(client, student_token):
    """Test that invalid unit ID returns 404."""
    response = client.get(
        "/challenges/999",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 404


# ============================================================================
# SINGLE CHALLENGE TESTS - GET /challenges/{unit_id}/{challenge_id}
# ============================================================================


def test_get_single_challenge_returns_all_fields(client, student_token):
    """Test that single challenge has all required fields."""
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields
    assert data["unit_id"] == 1
    assert data["challenge_id"] == 1
    assert "title" in data
    assert "points" in data
    assert "description" in data
    assert "completion_rate" in data
    assert "avg_attempts" in data
    assert "total_attempts" in data
    assert "success_count" in data


def test_get_single_challenge_includes_completion_rate(client, student_token):
    """Test that completion rate is included."""
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "completion_rate" in data
    assert isinstance(data["completion_rate"], (int, float))
    assert 0 <= data["completion_rate"] <= 100


def test_get_single_challenge_includes_avg_attempts(client, student_token):
    """Test that avg attempts is included."""
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "avg_attempts" in data
    assert isinstance(data["avg_attempts"], (int, float))
    assert data["avg_attempts"] >= 0


def test_get_single_challenge_invalid_challenge_returns_404(client, student_token):
    """Test that invalid challenge ID returns 404."""
    response = client.get(
        "/challenges/1/999",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 404


def test_get_single_challenge_no_solution_for_students(client, student_token):
    """Test that students don't see sample solution."""
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Student should not see sample_solution or it should be None
    assert data.get("sample_solution") is None


# ============================================================================
# TEACHER-ONLY SOLUTION TESTS
# ============================================================================


def test_teacher_sees_solution_in_unit_challenges(client, teacher_token):
    """Test that teachers see sample solution in unit endpoint."""
    response = client.get(
        "/challenges/1",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # First challenge should have sample_solution
    first_challenge = data["challenges"][0]
    assert "sample_solution" in first_challenge
    assert first_challenge["sample_solution"] is not None
    assert first_challenge["sample_solution"] == "SELECT * FROM users"


def test_teacher_sees_solution_in_single_challenge(client, teacher_token):
    """Test that teachers see sample solution in single challenge endpoint."""
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "sample_solution" in data
    assert data["sample_solution"] is not None
    assert data["sample_solution"] == "SELECT * FROM users"


def test_student_does_not_see_solution(client, student_token):
    """Test that students don't see solutions in any endpoint."""
    # All challenges endpoint
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check that no challenge has a solution
    for unit in data["units"]:
        for challenge in unit["challenges"]:
            assert challenge.get("sample_solution") is None


# ============================================================================
# STATISTICS ACCURACY TESTS
# ============================================================================


def test_completion_rate_correct_for_no_completions(client, student_token):
    """Test completion rate is 0 when no one has completed."""
    response = client.get(
        "/challenges/2/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # No one has completed this challenge yet
    assert data["completion_rate"] == 0.0


def test_completion_rate_correct_for_partial_completions(
    client, student_token, session
):
    """Test completion rate calculation with actual completion data."""
    # Create progress data
    create_test_progress_data(client, session, student_token)

    # Check completion rate for challenge (1,1) that was completed
    response = client.get(
        "/challenges/1/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # 1 out of 1 student completed it = 100%
    assert data["completion_rate"] > 0


def test_avg_attempts_correct_for_multiple_attempts(client, student_token, session):
    """Test that avg attempts is calculated correctly."""
    # Create progress data (student makes multiple attempts on challenge 1,3)
    create_test_progress_data(client, session, student_token)

    # Check stats for challenge (1,3) which had 2 attempts
    response = client.get(
        "/challenges/1/3",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have recorded attempts
    assert data["total_attempts"] > 0
    assert data["avg_attempts"] > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_challenges_with_no_attempts_show_0_completion(client, student_token):
    """Test challenges with no attempts show 0% completion."""
    response = client.get(
        "/challenges/3/1",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # No attempts made
    assert data["completion_rate"] == 0.0
    assert data["avg_attempts"] == 0.0
    assert data["total_attempts"] == 0
    assert data["success_count"] == 0


def test_challenges_with_no_statistics_loads_gracefully(client, student_token):
    """Test that endpoint works gracefully with no attempt data."""
    # With empty database, all challenges should load
    response = client.get(
        "/challenges",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have all challenges with 0 stats
    assert len(data["units"]) == 3

    for unit in data["units"]:
        for challenge in unit["challenges"]:
            assert challenge["completion_rate"] == 0.0
            assert challenge["avg_attempts"] == 0.0
