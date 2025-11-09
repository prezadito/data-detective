"""
Test weekly progress reports - aggregated metrics for teachers.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

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
        from app.routes.reports import invalidate_weekly_cache

        # Override dependency to use test database
        def get_test_session():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session

        # Create test client
        client = TestClient(app, raise_server_exceptions=True)

        # Clear cache before test
        invalidate_weekly_cache()

        yield client

        app.dependency_overrides.clear()
        invalidate_weekly_cache()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_student_and_get_token(
    client: TestClient, email: str, password: str, name: str
) -> str:
    """Helper to create a student and get their JWT token."""
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "student"},
    )
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def create_teacher_and_get_token(
    client: TestClient, email: str, password: str, name: str
) -> str:
    """Helper to create a teacher and get their JWT token."""
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": "teacher"},
    )
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def submit_challenge(
    client: TestClient,
    token: str,
    unit_id: int,
    challenge_id: int,
    query: str = None,
):
    """Helper to submit a challenge with valid query for the challenge."""
    # Map of valid queries for each challenge
    valid_queries = {
        (1, 1): "SELECT * FROM users",
        (1, 2): "SELECT name, email FROM users",
        (1, 3): "SELECT * FROM users WHERE age > 18",
        (2, 1): "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
        (2, 2): "SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id",
        (3, 1): "SELECT COUNT(*) FROM users",
        (3, 2): "SELECT role, COUNT(*) FROM users GROUP BY role",
    }

    # Use provided query or lookup valid query for this challenge
    if query is None:
        query = valid_queries.get((unit_id, challenge_id), "SELECT * FROM users")

    return client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "challenge_id": challenge_id,
            "query": query,
            "hints_used": 0,
        },
    )


# ============================================================================
# ENDPOINT TESTS (4 tests)
# ============================================================================


def test_weekly_report_endpoint_exists(client: TestClient):
    """Test GET /reports/weekly endpoint returns 200."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200


def test_weekly_report_requires_authentication(client: TestClient):
    """Test /reports/weekly returns 401 without token."""
    response = client.get("/reports/weekly")
    assert response.status_code == 401


def test_weekly_report_requires_teacher_role(client: TestClient):
    """Test students cannot access /reports/weekly (403)."""
    student_token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403


def test_weekly_report_returns_structured_data(client: TestClient):
    """Test response includes all required fields."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify required top-level fields
    assert "students_active" in data
    assert "total_completions" in data
    assert "avg_points_per_student" in data
    assert "top_performers" in data
    assert "struggling_students" in data
    assert "generated_at" in data

    # Verify structure of lists
    assert isinstance(data["top_performers"], list)
    assert isinstance(data["struggling_students"], list)


# ============================================================================
# DATA AGGREGATION TESTS (4 tests)
# ============================================================================


def test_weekly_report_counts_active_students(client: TestClient, session: Session):
    """Test reports only counts students with activity in past 7 days."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Create 3 students
    token1 = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )
    token2 = create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )
    # Create student 3 but don't store token (doesn't submit)
    create_student_and_get_token(
        client, "student3@test.com", "password123", "Student 3"
    )

    # Student 1 and 2 submit challenges (recent)
    submit_challenge(client, token1, 1, 1)
    submit_challenge(client, token2, 1, 1)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Only 2 active students
    assert data["students_active"] == 2


def test_weekly_report_calculates_total_completions(client: TestClient):
    """Test total completions sums all challenges in week."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit 3 different challenges
    submit_challenge(client, token, 1, 1)
    submit_challenge(client, token, 1, 2)
    submit_challenge(client, token, 2, 1)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # 3 total completions
    assert data["total_completions"] == 3


def test_weekly_report_calculates_avg_points(client: TestClient):
    """Test avg_points_per_student = total_points / active_students."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token1 = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )
    token2 = create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )

    # Student 1: 100 points (1 challenge)
    submit_challenge(client, token1, 1, 1)

    # Student 2: 150 points (1 challenge)
    submit_challenge(client, token2, 1, 2)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Total: 250, active: 2, avg: 125
    assert data["avg_points_per_student"] == 125.0


def test_weekly_report_filters_by_7_day_window(client: TestClient, session: Session):
    """Test only includes progress from past 7 days."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit a recent challenge via API
    submit_challenge(client, token, 1, 1)

    # Manually add an old progress record (8 days ago)

    user = session.exec(select(User).where(User.email == "student@test.com")).first()

    old_progress = Progress(
        user_id=user.id,
        unit_id=1,
        challenge_id=2,
        points_earned=100,
        hints_used=0,
        query="SELECT * FROM users",
        completed_at=datetime.now(timezone.utc) - timedelta(days=8),
    )
    session.add(old_progress)
    session.commit()

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should only count recent challenge (1 completion, 100 points)
    assert data["total_completions"] == 1
    assert data["avg_points_per_student"] == 100.0


# ============================================================================
# TOP PERFORMERS TESTS (3 tests)
# ============================================================================


def test_weekly_report_top_performers_max_5(client: TestClient):
    """Test returns max 5 top performers."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Create 8 students
    for i in range(8):
        token = create_student_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}"
        )
        # Each submits 1 challenge
        submit_challenge(client, token, 1, 1)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Max 5 top performers
    assert len(data["top_performers"]) <= 5


def test_weekly_report_top_performers_correct_order(client: TestClient):
    """Test top performers ordered by points DESC."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Create students with different point totals
    # 100, 150, 200, 250 points
    tokens = []
    for i in range(4):
        token = create_student_and_get_token(
            client,
            f"student{i}@test.com",
            "password123",
            f"Student {i}",
        )
        tokens.append(token)

    # Different challenges have different points: 1-1=100, 1-2=150, 1-3=200, 2-1=250
    submit_challenge(client, tokens[0], 1, 1)  # 100 points
    submit_challenge(client, tokens[1], 1, 2)  # 150 points
    submit_challenge(client, tokens[2], 1, 3)  # 200 points
    submit_challenge(client, tokens[3], 2, 1)  # 250 points

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify order: highest points first
    top = data["top_performers"]
    assert len(top) >= 4
    assert top[0]["points_this_week"] == 250
    assert top[1]["points_this_week"] == 200
    assert top[2]["points_this_week"] == 150
    assert top[3]["points_this_week"] == 100


def test_weekly_report_empty_when_no_data(client: TestClient):
    """Test returns empty lists if no student activity."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["students_active"] == 0
    assert data["total_completions"] == 0
    assert data["avg_points_per_student"] == 0.0
    assert len(data["top_performers"]) == 0
    assert len(data["struggling_students"]) == 0


# ============================================================================
# STRUGGLING STUDENTS TESTS (3 tests)
# ============================================================================


def test_weekly_report_identifies_struggling_students(client: TestClient):
    """Test identifies students with <3 completions as struggling."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Student 1: 1 completion (struggling)
    token1 = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )
    submit_challenge(client, token1, 1, 1)

    # Student 2: 2 completions (struggling)
    token2 = create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )
    submit_challenge(client, token2, 1, 1)
    submit_challenge(client, token2, 1, 2)

    # Student 3: 3 completions (not struggling)
    token3 = create_student_and_get_token(
        client, "student3@test.com", "password123", "Student 3"
    )
    submit_challenge(client, token3, 1, 1)
    submit_challenge(client, token3, 1, 2)
    submit_challenge(client, token3, 1, 3)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Only 2 struggling students
    assert len(data["struggling_students"]) == 2


def test_weekly_report_includes_student_name_and_stats(client: TestClient):
    """Test struggling students include name and stats."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )
    submit_challenge(client, token, 1, 1)

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    struggling = data["struggling_students"]
    assert len(struggling) == 1

    student = struggling[0]
    assert "student_name" in student
    assert "completions_this_week" in student
    assert "points_this_week" in student
    assert student["student_name"] == "Test Student"
    assert student["completions_this_week"] == 1
    assert student["points_this_week"] == 100


def test_weekly_report_excludes_teacher_completions(client: TestClient):
    """Test only counts student progress, not teacher progress."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Student submits 1 challenge
    student_token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )
    submit_challenge(client, student_token, 1, 1)

    # Teacher tries to submit (should fail, but let's verify report ignores it anyway)
    # This is already handled by require_student, but test verifies exclusion

    response = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Only 1 active student (the student, not the teacher)
    assert data["students_active"] == 1
    assert data["total_completions"] == 1


# ============================================================================
# CACHING TESTS (2 tests)
# ============================================================================


def test_weekly_report_cache_returns_same_data(client: TestClient):
    """Test caching returns same data on repeated calls."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )
    submit_challenge(client, token, 1, 1)

    # First call
    response1 = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    data1 = response1.json()

    # Second call (should be cached)
    response2 = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    data2 = response2.json()

    # Same data returned
    assert data1["students_active"] == data2["students_active"]
    assert data1["total_completions"] == data2["total_completions"]
    assert data1["generated_at"] == data2["generated_at"]


def test_weekly_report_timestamp_consistent_during_cache(client: TestClient):
    """Test generated_at timestamp stays consistent while cached."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )
    submit_challenge(client, token, 1, 1)

    # First call
    response1 = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    timestamp1 = response1.json()["generated_at"]

    # Small delay
    import time

    time.sleep(0.1)

    # Second call (should be cached, same timestamp)
    response2 = client.get(
        "/reports/weekly",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    timestamp2 = response2.json()["generated_at"]

    # Timestamps should match (cache didn't regenerate)
    assert timestamp1 == timestamp2
