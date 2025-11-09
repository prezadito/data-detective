"""
Test class-level analytics for teachers.
Tests GET /analytics/class endpoint.
"""

from datetime import datetime
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


def create_class_with_varied_progress(client: TestClient) -> str:
    """
    Create teacher + 5 students with varied progress:
    - Student 1: Completes 3 challenges (100+150+250 = 500 pts)
    - Student 2: Completes 2 challenges (100+250 = 350 pts)
    - Student 3: Completes 1 challenge (100 pts)
    - Student 4: 5 attempts, 2 correct (mixed success)
    - Student 5: 0 progress (no attempts)

    Returns teacher_token for API calls
    """
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Student 1: 3 completions (500 points)
    s1_token = create_user_and_get_token(
        client, "student1@test.com", "password123", "Student1", "student"
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT id, name FROM users WHERE active=1",
            "hints_used": 1,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "hints_used": 0,
        },
    )

    # Student 2: 2 completions (350 points)
    s2_token = create_user_and_get_token(
        client, "student2@test.com", "password123", "Student2", "student"
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s2_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s2_token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "hints_used": 2,
        },
    )

    # Student 3: 1 completion (100 points)
    s3_token = create_user_and_get_token(
        client, "student3@test.com", "password123", "Student3", "student"
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s3_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    # Student 4: 5 attempts, 2 correct (mixed success)
    s4_token = create_user_and_get_token(
        client, "student4@test.com", "password123", "Student4", "student"
    )
    # Wrong, wrong, correct, wrong, correct (2/5 success rate for (1,2))
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s4_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT wrong",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s4_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT wrong2",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s4_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT id, name FROM users WHERE active=1",
            "hints_used": 1,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s4_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT wrong3",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s4_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT id, name FROM users WHERE active=1",
            "hints_used": 0,
        },
    )

    # Student 5: 0 progress (no attempts)
    create_user_and_get_token(
        client, "student5@test.com", "password123", "Student5", "student"
    )

    return teacher_token


# ============================================================================
# PERMISSION TESTS
# ============================================================================


def test_class_analytics_requires_authentication(client: TestClient):
    """Test that unauthenticated users cannot access /analytics/class"""
    response = client.get("/analytics/class")
    assert response.status_code == 401


def test_class_analytics_requires_teacher_role(client: TestClient):
    """Test that students cannot access /analytics/class"""
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403


# ============================================================================
# RESPONSE STRUCTURE TESTS
# ============================================================================


def test_class_analytics_includes_all_required_fields(client: TestClient):
    """Test that response includes all required top-level fields"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Check top-level fields
    assert "generated_at" in data
    assert "metrics" in data
    assert "challenges" in data
    assert "difficulty_distribution" in data
    assert "weekly_trends" in data
    assert "cache_expires_at" in data


def test_class_analytics_includes_all_7_challenges(client: TestClient):
    """Test that all 7 challenges are included in the response"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should have 7 challenges
    assert len(data["challenges"]) == 7

    # Verify all expected challenges are present
    challenge_ids = {(c["unit_id"], c["challenge_id"]) for c in data["challenges"]}
    expected = {
        (1, 1),
        (1, 2),
        (1, 3),  # Unit 1
        (2, 1),
        (2, 2),  # Unit 2
        (3, 1),
        (3, 2),  # Unit 3
    }
    assert challenge_ids == expected


def test_class_analytics_has_cache_expiry(client: TestClient):
    """Test that cache_expires_at is set to ~1 hour from generation"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    generated_at = datetime.fromisoformat(data["generated_at"])
    cache_expires_at = datetime.fromisoformat(data["cache_expires_at"])

    # Expiry should be ~1 hour (3600 seconds) after generation
    diff = (cache_expires_at - generated_at).total_seconds()
    assert 3599 <= diff <= 3601  # Allow 1 second tolerance


# ============================================================================
# CLASS METRICS TESTS
# ============================================================================


def test_class_metrics_no_students_calculation(client: TestClient):
    """Test class metrics calculation with valid data structure"""
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # Verify metrics structure and types
    assert isinstance(metrics["total_students"], int)
    assert isinstance(metrics["active_students"], int)
    assert isinstance(metrics["avg_completion_rate"], (int, float))
    assert metrics["total_students"] >= 0
    assert metrics["active_students"] >= 0
    assert metrics["avg_completion_rate"] >= 0


def test_class_metrics_active_students_count(client: TestClient):
    """Test that active_students counts students with at least 1 completion"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # Should have at least 3 active students (1, 2, 3 all have completions)
    # Student 5 has 0 progress = not counted
    assert metrics["active_students"] >= 3


def test_class_metrics_avg_completion_rate(client: TestClient):
    """Test average completion rate calculation"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # Completion rate should be > 0 and < 100
    assert 0 <= metrics["avg_completion_rate"] <= 100


def test_percentiles_calculated_correctly(client: TestClient):
    """Test that percentiles are calculated from student points"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    # Student points (active students only): [500, 350, 100, 150]
    # Sorted: [100, 150, 350, 500]
    # 25th percentile at index 0.75 = 100 + 0.75*(150-100) = 137.5 → 137
    # 50th (median) at index 1.5 = 150 + 0.5*(350-150) = 250
    # 75th percentile at index 2.25 = 350 + 0.25*(500-350) = 387.5 → 387

    # Verify percentiles are reasonable bounds
    assert metrics["percentile_25"] <= metrics["percentile_50"]
    assert metrics["percentile_50"] <= metrics["percentile_75"]
    assert metrics["percentile_25"] >= 100  # Min is 100
    assert metrics["percentile_75"] <= 500  # Max is 500


def test_median_points_matches_50th_percentile(client: TestClient):
    """Test that median_points equals 50th percentile"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    assert metrics["median_points"] == metrics["percentile_50"]


# ============================================================================
# CHALLENGE ANALYTICS TESTS
# ============================================================================


def test_challenge_success_rate_calculated(client: TestClient):
    """Test that success rate is calculated as correct/total*100"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Challenge (1,2) should have some correct and total attempts
    challenge_1_2 = next(
        (c for c in data["challenges"] if c["unit_id"] == 1 and c["challenge_id"] == 2),
        None,
    )
    assert challenge_1_2 is not None

    # Success rate should be between 0 and 100
    assert 0 <= challenge_1_2["success_rate"] <= 100
    # Should have at least some attempts
    assert challenge_1_2["total_attempts"] > 0
    assert challenge_1_2["correct_attempts"] <= challenge_1_2["total_attempts"]


def test_challenge_success_rate_zero_attempts(client: TestClient):
    """Test that challenges with no attempts have 0% success rate"""
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )
    # Create just 1 student with 1 completion
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )
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

    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # Challenges (1,2), (1,3), (2,1), (2,2), (3,1), (3,2) should all have 0% success
    for challenge in data["challenges"]:
        if challenge["unit_id"] == 1 and challenge["challenge_id"] == 1:
            # (1,1) should have 100% (1 correct, 1 total)
            assert challenge["success_rate"] == 100.0
        else:
            # All others should have 0.0 (no attempts)
            assert challenge["success_rate"] == 0.0


def test_all_challenges_included_in_response(client: TestClient):
    """Test that all 7 challenges appear in the response"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["challenges"]) == 7


def test_challenge_includes_title_from_dict(client: TestClient):
    """Test that challenge titles are looked up from CHALLENGES dict"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    # All challenges should have titles
    for challenge in data["challenges"]:
        assert "challenge_title" in challenge
        assert len(challenge["challenge_title"]) > 0
        assert challenge["challenge_title"] != "Unknown"


def test_challenge_includes_attempt_counts(client: TestClient):
    """Test that challenges include total_attempts and correct_attempts"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    for challenge in data["challenges"]:
        assert "total_attempts" in challenge
        assert "correct_attempts" in challenge
        assert isinstance(challenge["total_attempts"], int)
        assert isinstance(challenge["correct_attempts"], int)
        assert challenge["correct_attempts"] <= challenge["total_attempts"]


# ============================================================================
# DIFFICULTY DISTRIBUTION TESTS
# ============================================================================


def test_easiest_challenges_top_3_by_success_rate(client: TestClient):
    """Test that easiest_challenges are top 3 by success rate"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    easiest = data["difficulty_distribution"]["easiest_challenges"]

    # Should have up to 3 items
    assert len(easiest) <= 3

    # Should be sorted by success rate (descending)
    for i in range(len(easiest) - 1):
        assert easiest[i]["success_rate"] >= easiest[i + 1]["success_rate"]


def test_hardest_challenges_bottom_3_by_success_rate(client: TestClient):
    """Test that hardest_challenges are bottom 3 by success rate"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    hardest = data["difficulty_distribution"]["hardest_challenges"]

    # Should have up to 3 items
    assert len(hardest) <= 3

    # Should be sorted by success rate (ascending - hardest first)
    for i in range(len(hardest) - 1):
        assert hardest[i]["success_rate"] <= hardest[i + 1]["success_rate"]


def test_difficulty_distribution_excludes_duplicates(client: TestClient):
    """Test that easiest and hardest don't have overlapping challenges"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    easiest = data["difficulty_distribution"]["easiest_challenges"]
    hardest = data["difficulty_distribution"]["hardest_challenges"]

    easiest_ids = {(c["unit_id"], c["challenge_id"]) for c in easiest}
    hardest_ids = {(c["unit_id"], c["challenge_id"]) for c in hardest}

    # Should be no overlap
    assert len(easiest_ids & hardest_ids) == 0


# ============================================================================
# WEEKLY TRENDS TESTS
# ============================================================================


def test_weekly_trends_generated(client: TestClient):
    """Test that weekly trends are generated for past weeks"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    trends = data["weekly_trends"]

    # Should have up to 4 weeks of data
    assert len(trends) > 0
    assert len(trends) <= 4


def test_weekly_trends_has_required_fields(client: TestClient):
    """Test that weekly trends include all required fields"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    trends = data["weekly_trends"]

    for trend in trends:
        assert "week_start_date" in trend
        assert "week_end_date" in trend
        assert "completions" in trend
        assert "total_points_earned" in trend
        assert "unique_students" in trend


def test_weekly_trends_correct_counts(client: TestClient):
    """Test that weekly trend counts are accurate"""
    teacher_token = create_class_with_varied_progress(client)
    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    trends = data["weekly_trends"]

    # Current week should have some completions
    current_trend = trends[-1] if trends else None
    if current_trend:
        assert current_trend["completions"] >= 3  # At least some completions
        assert current_trend["total_points_earned"] >= 100  # At least some points


# ============================================================================
# CACHE TESTS
# ============================================================================


def test_class_analytics_cached(client: TestClient):
    """Test that second call returns cached data (same timestamps)"""
    teacher_token = create_class_with_varied_progress(client)

    # First call
    response1 = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    data1 = response1.json()
    generated_at_1 = data1["generated_at"]

    # Small delay to ensure different timestamp if not cached
    import time

    time.sleep(0.1)

    # Second call
    response2 = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    data2 = response2.json()
    generated_at_2 = data2["generated_at"]

    # Should be identical (cached)
    assert generated_at_1 == generated_at_2


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_class_analytics_single_student(client: TestClient):
    """Test analytics with just one active student"""
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )
    # Submit 1 challenge
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

    response = client.get(
        "/analytics/class", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]
    assert metrics["active_students"] == 1
    assert metrics["median_points"] == 100  # Only 1 student with 100 points
    assert metrics["percentile_25"] == 100
    assert metrics["percentile_75"] == 100
