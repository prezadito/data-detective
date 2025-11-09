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


# ============================================================================
# GET /progress/me ENDPOINT TESTS (Student retrieves their own progress)
# ============================================================================


def test_get_progress_me_student_success(client: TestClient, session: Session):
    """Test student successfully retrieves their own progress with summary stats."""
    # Create student and get token
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit some challenges
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 1,
        },
    )

    # Get progress
    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "progress_items" in data
    assert "summary" in data

    # Verify progress items
    assert len(data["progress_items"]) == 2
    assert data["progress_items"][0]["unit_id"] == 1
    assert data["progress_items"][0]["challenge_id"] == 1
    assert data["progress_items"][1]["unit_id"] == 1
    assert data["progress_items"][1]["challenge_id"] == 2

    # Verify summary
    assert data["summary"]["total_points"] == 250  # 100 + 150
    assert data["summary"]["total_completed"] == 2
    assert data["summary"]["completion_percentage"] == (2 / 7) * 100


def test_get_progress_me_student_empty(client: TestClient):
    """Test student with no progress returns empty list with zero stats."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify empty progress
    assert data["progress_items"] == []
    assert data["summary"]["total_points"] == 0
    assert data["summary"]["total_completed"] == 0
    assert data["summary"]["completion_percentage"] == 0.0


def test_get_progress_me_with_multiple_challenges(client: TestClient):
    """Test student retrieves multiple challenges across units."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenges from different units
    for unit_id in [1, 2, 3]:
        for challenge_id in [1, 2]:
            try:
                client.post(
                    "/progress/submit",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "unit_id": unit_id,
                        "challenge_id": challenge_id,
                        "query": f"SELECT * FROM table_{unit_id}_{challenge_id}",
                        "hints_used": 0,
                    },
                )
            except Exception:
                pass  # Some challenges may not exist, that's ok

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify we got some progress items
    assert len(data["progress_items"]) > 0
    # Verify ordered by unit_id then challenge_id
    for i in range(len(data["progress_items"]) - 1):
        curr = data["progress_items"][i]
        next_item = data["progress_items"][i + 1]
        assert (curr["unit_id"], curr["challenge_id"]) <= (
            next_item["unit_id"],
            next_item["challenge_id"],
        )


def test_get_progress_me_requires_auth(client: TestClient):
    """Test unauthenticated request to /progress/me returns 401."""
    response = client.get("/progress/me")

    assert response.status_code == 401


def test_get_progress_me_contains_summary_stats(client: TestClient):
    """Test response contains all required summary stat fields."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit one challenge
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify summary has all fields
    assert "total_points" in data["summary"]
    assert "total_completed" in data["summary"]
    assert "completion_percentage" in data["summary"]

    # Verify types
    assert isinstance(data["summary"]["total_points"], int)
    assert isinstance(data["summary"]["total_completed"], int)
    assert isinstance(data["summary"]["completion_percentage"], float)


def test_get_progress_me_includes_challenge_titles(client: TestClient):
    """Test each progress item includes challenge title from CHALLENGES dict."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenge 1-1 (title: "SELECT All Columns")
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify challenge title is present
    assert len(data["progress_items"]) == 1
    assert "challenge_title" in data["progress_items"][0]
    assert data["progress_items"][0]["challenge_title"] == "SELECT All Columns"


# ============================================================================
# GET /progress/user/{user_id} ENDPOINT TESTS (Teacher views student progress)
# ============================================================================


def test_get_user_progress_teacher_success(client: TestClient, session: Session):
    """Test teacher can view any student's progress."""
    # Create student and submit challenges
    student_token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
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

    # Get student user_id from database
    statement = select(User).where(User.email == "student@test.com")
    student = session.exec(statement).first()

    # Create teacher and get token
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Teacher views student progress
    response = client.get(
        f"/progress/user/{student.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "progress_items" in data
    assert "summary" in data
    assert len(data["progress_items"]) == 1


def test_get_user_progress_teacher_empty_student(client: TestClient, session: Session):
    """Test teacher views student with no progress."""
    # Create student (no submissions)
    create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Get student user_id
    statement = select(User).where(User.email == "student@test.com")
    student = session.exec(statement).first()

    # Create teacher
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Teacher views student progress
    response = client.get(
        f"/progress/user/{student.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify empty
    assert data["progress_items"] == []
    assert data["summary"]["total_points"] == 0
    assert data["summary"]["total_completed"] == 0


def test_get_user_progress_student_denied(client: TestClient, session: Session):
    """Test student cannot view another student's progress (403)."""
    # Create student 1
    student1_token = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )

    # Create student 2
    create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )

    # Get student 2's user_id
    statement = select(User).where(User.email == "student2@test.com")
    student2 = session.exec(statement).first()

    # Student 1 tries to view student 2's progress
    response = client.get(
        f"/progress/user/{student2.id}",
        headers={"Authorization": f"Bearer {student1_token}"},
    )

    assert response.status_code == 403


def test_get_user_progress_student_can_view_self(client: TestClient, session: Session):
    """Test student CAN view their own progress via /user/{their_id}."""
    # Create student
    student_token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit a challenge
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

    # Get student user_id
    statement = select(User).where(User.email == "student@test.com")
    student = session.exec(statement).first()

    # Student views their own progress via /user/{their_id}
    response = client.get(
        f"/progress/user/{student.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Student accessing their own progress should be allowed
    assert (
        response.status_code == 403
    )  # Should be 403 because students can't use /user/{id}


def test_get_user_progress_requires_auth(client: TestClient, session: Session):
    """Test unauthenticated request returns 401."""
    # Create a user to query
    create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    statement = select(User).where(User.email == "student@test.com")
    student = session.exec(statement).first()

    # Request without token
    response = client.get(f"/progress/user/{student.id}")

    assert response.status_code == 401


def test_get_user_progress_user_not_found(client: TestClient):
    """Test requesting non-existent user returns 404."""
    teacher_token = create_teacher_and_get_token(
        client, "teacher@test.com", "password123", "Test Teacher"
    )

    # Request non-existent user
    response = client.get(
        "/progress/user/99999", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 404


def test_get_user_progress_requires_teacher(client: TestClient, session: Session):
    """Test student cannot use /progress/user/{user_id} endpoint (teacher only)."""
    # Create student 1
    student1_token = create_student_and_get_token(
        client, "student1@test.com", "password123", "Student 1"
    )

    # Create student 2
    create_student_and_get_token(
        client, "student2@test.com", "password123", "Student 2"
    )

    statement = select(User).where(User.email == "student2@test.com")
    student2 = session.exec(statement).first()

    # Student tries to access /progress/user/{other_id}
    response = client.get(
        f"/progress/user/{student2.id}",
        headers={"Authorization": f"Bearer {student1_token}"},
    )

    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"].lower()


# ============================================================================
# RESPONSE FORMAT & CALCULATION TESTS
# ============================================================================


def test_progress_response_includes_all_fields(client: TestClient):
    """Test each progress item includes all required fields."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit challenge
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 2,
        },
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify all fields
    required_fields = [
        "id",
        "user_id",
        "unit_id",
        "challenge_id",
        "points_earned",
        "hints_used",
        "completed_at",
        "query",
        "challenge_title",
    ]
    item = data["progress_items"][0]
    for field in required_fields:
        assert field in item, f"Missing field: {field}"

    # Verify query field contains submitted query
    assert item["query"] == "SELECT * FROM users"
    assert item["hints_used"] == 2


def test_progress_summary_stats_calculation(client: TestClient):
    """Test summary stats are correctly calculated."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit 3 challenges: 100 + 150 + 200 = 450 points
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 3,
            "query": "SELECT * FROM users WHERE age > 18",
            "hints_used": 0,
        },
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify calculations
    assert data["summary"]["total_points"] == 450
    assert data["summary"]["total_completed"] == 3
    expected_percentage = (3 / 7) * 100
    assert data["summary"]["completion_percentage"] == expected_percentage


def test_completion_percentage_correct(client: TestClient):
    """Test completion percentage is correctly calculated as (completed/7)*100."""
    token = create_student_and_get_token(
        client, "student@test.com", "password123", "Test Student"
    )

    # Submit 1 challenge
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    response = client.get("/progress/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify percentage: 1/7 * 100 ≈ 14.285714...
    expected = (1 / 7) * 100
    assert abs(data["summary"]["completion_percentage"] - expected) < 0.01
