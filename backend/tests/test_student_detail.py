"""
Test detailed student view for teachers.
Tests GET /users/{user_id}?detailed=true endpoint.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch

# Import models at module level so SQLModel knows about them
from app.models import User, Progress, Attempt, Hint  # noqa: F401


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


def create_user_and_get_token(
    client: TestClient, email: str, password: str, name: str, role: str
) -> str:
    """
    Helper function to register a user and get their JWT token.

    Args:
        client: TestClient instance
        email: User email
        password: User password
        name: User name
        role: User role (student or teacher)

    Returns:
        JWT access token string
    """
    # Register user
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": role},
    )

    # Login and get token
    response = client.post("/auth/login", json={"email": email, "password": password})

    return response.json()["access_token"]


def create_student_with_progress(client: TestClient) -> tuple[str, int]:
    """
    Create a student and add progress with attempts and hints.
    Returns (student_token, student_id).
    """
    # Create teacher and student
    create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Get student ID (should be 2 since teacher is 1)
    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {student_token}"}
    )
    student_id = response.json()["id"]

    # Submit challenges with correct answers
    # Challenge (1,1): 100 points
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    # Challenge (1,2): 150 points (first wrong, then correct)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name FROM users",  # Wrong
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",  # Correct
            "hints_used": 1,
        },
    )

    # Challenge (2,1): 250 points
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
            "hints_used": 0,
        },
    )

    return student_token, student_id


# ============================================================================
# PERMISSION TESTS
# ============================================================================


def test_teacher_can_view_student_detail(client: TestClient):
    """Test that teacher can view detailed student view."""
    student_token, student_id = create_student_with_progress(client)

    # Create second teacher
    teacher_token = create_user_and_get_token(
        client, "teacher2@test.com", "password123", "Teacher 2", "teacher"
    )

    # Teacher views student detail
    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert "metrics" in data
    assert "units" in data
    assert "activity_log" in data


def test_student_cannot_view_other_student_detail(client: TestClient):
    """Test that student gets 403 when viewing another student's detail."""
    # Create two students
    student1_token = create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    student2_token = create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )

    # Get student2 ID
    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {student2_token}"}
    )
    student2_id = response.json()["id"]

    # Student1 tries to view Student2's detail
    response = client.get(
        f"/users/{student2_id}?detailed=true",
        headers={"Authorization": f"Bearer {student1_token}"},
    )

    assert response.status_code == 403


# ============================================================================
# RESPONSE STRUCTURE TESTS
# ============================================================================


def test_detail_response_has_required_fields(client: TestClient):
    """Test that detail response has all required top-level fields."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "user" in data
    assert "metrics" in data
    assert "units" in data
    assert "activity_log" in data

    # Check nested structures exist
    assert isinstance(data["user"], dict)
    assert isinstance(data["metrics"], dict)
    assert isinstance(data["units"], list)
    assert isinstance(data["activity_log"], list)


def test_units_properly_nested(client: TestClient):
    """Test that units contain challenges with proper nesting."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check unit structure
    units = data["units"]
    assert len(units) > 0

    for unit in units:
        assert "unit_id" in unit
        assert "unit_title" in unit
        assert "challenges" in unit
        assert isinstance(unit["challenges"], list)

        # Check challenge structure
        for challenge in unit["challenges"]:
            assert "unit_id" in challenge
            assert "challenge_id" in challenge
            assert "title" in challenge
            assert "points" in challenge
            assert "metrics" in challenge
            assert "attempts" in challenge
            assert "hints" in challenge


def test_activity_log_has_max_10_items(client: TestClient):
    """Test that activity log is limited to 10 most recent actions."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    activity_log = data["activity_log"]
    assert len(activity_log) <= 10


# ============================================================================
# USER INFO TESTS
# ============================================================================


def test_detail_includes_user_basic_info(client: TestClient):
    """Test that detail includes basic user information."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    user = data["user"]

    # Check basic user fields
    assert user["id"] == student_id
    assert user["email"] == "student@test.com"
    assert user["name"] == "Student"
    assert user["role"] == "student"
    assert "created_at" in user


def test_detail_includes_enrollment_metrics(client: TestClient):
    """Test that detail includes enrollment metrics (total points, challenges)."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    # Check metrics fields
    assert "total_points" in metrics
    assert "total_challenges_completed" in metrics
    assert "total_attempts" in metrics
    assert "average_attempts_per_challenge" in metrics
    assert "overall_success_rate" in metrics
    assert "total_hints_used" in metrics

    # Verify actual values based on test data
    assert metrics["total_challenges_completed"] == 3  # (1,1), (1,2), (2,1)
    assert metrics["total_attempts"] == 4  # 1 + 2 + 1


# ============================================================================
# UNIT/CHALLENGE STRUCTURE TESTS
# ============================================================================


def test_units_ordered_by_id(client: TestClient):
    """Test that units are ordered by unit_id."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    units = data["units"]

    # Extract unit IDs
    unit_ids = [u["unit_id"] for u in units]

    # Should be ordered
    assert unit_ids == sorted(unit_ids)


def test_challenges_within_unit_ordered(client: TestClient):
    """Test that challenges within a unit are ordered by challenge_id."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    units = data["units"]

    # Check ordering within each unit
    for unit in units:
        challenge_ids = [c["challenge_id"] for c in unit["challenges"]]
        assert challenge_ids == sorted(challenge_ids)


def test_includes_all_units_even_incomplete(client: TestClient):
    """Test that response includes all 3 units even if some are incomplete."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    units = data["units"]

    # Should have all 3 units
    unit_ids = [u["unit_id"] for u in units]
    assert len(unit_ids) == 3
    assert 1 in unit_ids
    assert 2 in unit_ids
    assert 3 in unit_ids


# ============================================================================
# ATTEMPT TRACKING TESTS
# ============================================================================


def test_challenge_shows_all_attempts(client: TestClient):
    """Test that challenge shows all attempts (correct and incorrect)."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Find unit 1, challenge 2 (should have 2 attempts: 1 wrong, 1 correct)
    unit1 = next(u for u in data["units"] if u["unit_id"] == 1)
    challenge2 = next(c for c in unit1["challenges"] if c["challenge_id"] == 2)

    # Should have 2 attempts
    assert len(challenge2["attempts"]) == 2


def test_attempts_include_query_and_result(client: TestClient):
    """Test that each attempt includes query and result."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Find a challenge with attempts
    unit1 = next(u for u in data["units"] if u["unit_id"] == 1)
    challenge1 = next(c for c in unit1["challenges"] if c["challenge_id"] == 1)

    # Check attempt fields
    for attempt in challenge1["attempts"]:
        assert "query" in attempt
        assert "is_correct" in attempt
        assert "attempted_at" in attempt
        assert isinstance(attempt["query"], str)
        assert isinstance(attempt["is_correct"], bool)


def test_attempts_ordered_chronologically(client: TestClient):
    """Test that attempts are ordered chronologically (oldest first)."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Find a challenge with multiple attempts
    unit1 = next(u for u in data["units"] if u["unit_id"] == 1)
    challenge2 = next(c for c in unit1["challenges"] if c["challenge_id"] == 2)

    # Check ordering
    timestamps = [a["attempted_at"] for a in challenge2["attempts"]]
    assert timestamps == sorted(timestamps)


# ============================================================================
# METRICS CALCULATION TESTS
# ============================================================================


def test_success_rate_calculated_correctly(client: TestClient):
    """Test that success rate is calculated correctly."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Find challenge (1,2) which has 2 attempts (1 wrong, 1 correct)
    unit1 = next(u for u in data["units"] if u["unit_id"] == 1)
    challenge2 = next(c for c in unit1["challenges"] if c["challenge_id"] == 2)

    metrics = challenge2["metrics"]

    # Should have 50% success rate (1 correct out of 2)
    assert metrics["success_rate"] == 50.0
    assert metrics["total_attempts"] == 2
    assert metrics["correct_attempts"] == 1


def test_avg_attempts_per_challenge(client: TestClient):
    """Test that average attempts per challenge is calculated correctly."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]

    # Total: 4 attempts across 3 challenges = 1.33...
    assert metrics["total_attempts"] == 4
    assert metrics["total_challenges_completed"] == 3
    expected_avg = 4 / 3
    assert abs(metrics["average_attempts_per_challenge"] - expected_avg) < 0.01


def test_challenge_metrics_include_success_rate(client: TestClient):
    """Test that per-challenge metrics include success rate."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check all challenges have metrics with success_rate
    for unit in data["units"]:
        for challenge in unit["challenges"]:
            metrics = challenge["metrics"]
            assert "success_rate" in metrics
            assert 0 <= metrics["success_rate"] <= 100


# ============================================================================
# HINT STATISTICS TESTS
# ============================================================================


def test_hint_usage_statistics(client: TestClient):
    """Test that hint usage statistics are included."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check overall hint usage
    metrics = data["metrics"]
    assert "total_hints_used" in metrics
    assert isinstance(metrics["total_hints_used"], int)


def test_hints_accessed_before_completion(client: TestClient):
    """Test that hint access records are shown for challenges."""
    student_token, student_id = create_student_with_progress(client)

    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    response = client.get(
        f"/users/{student_id}?detailed=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check that challenges have hints list (even if empty)
    for unit in data["units"]:
        for challenge in unit["challenges"]:
            assert "hints" in challenge
            assert isinstance(challenge["hints"], list)
            # Each hint should have required fields
            for hint in challenge["hints"]:
                assert "hint_level" in hint
                assert "accessed_at" in hint
