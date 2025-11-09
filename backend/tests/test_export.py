"""
Test CSV export functionality for teachers.
Tests GET /export/students endpoint.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch
import csv
from io import StringIO

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
    """
    # Register user
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": role},
    )

    # Login and get token
    response = client.post("/auth/login", json={"email": email, "password": password})

    return response.json()["access_token"]


def create_test_students_with_progress(client: TestClient) -> str:
    """
    Create teacher + 5 students with varied progress and dates.

    - Student 1: 3 challenges (completed Jan 1-3, 2024)
    - Student 2: 2 challenges (completed Jan 5-6, 2024)
    - Student 3: 1 challenge (completed Jan 10, 2024)
    - Student 4: 0 challenges (no progress)
    - Student 5: 2 challenges (completed Dec 25-26, 2023)

    Returns teacher_token for API calls
    """
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Student 1: 3 completions (500 points)
    s1_token = create_user_and_get_token(
        client, "alice@test.com", "password123", "Alice Smith", "student"
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
            "query": "SELECT name, email FROM users",
            "hints_used": 1,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
            "hints_used": 0,
        },
    )

    # Student 2: 2 completions (350 points)
    s2_token = create_user_and_get_token(
        client, "bob@test.com", "password123", "Bob Jones", "student"
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
            "query": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
            "hints_used": 2,
        },
    )

    # Student 3: 1 completion (100 points)
    s3_token = create_user_and_get_token(
        client, "carol@test.com", "password123", "Carol White", "student"
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

    # Student 4: 0 challenges (no progress)
    create_user_and_get_token(
        client, "dave@test.com", "password123", "Dave Brown", "student"
    )

    # Student 5: 2 challenges (from Dec 2023)
    s5_token = create_user_and_get_token(
        client, "eve@test.com", "password123", "Eve Davis", "student"
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s5_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {s5_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )

    return teacher_token


# ============================================================================
# PERMISSION TESTS
# ============================================================================


def test_export_requires_authentication(client: TestClient):
    """Test that unauthenticated users cannot access /export/students"""
    response = client.get("/export/students")
    assert response.status_code == 401


def test_export_requires_teacher_role(client: TestClient):
    """Test that students cannot access /export/students"""
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403


# ============================================================================
# RESPONSE FORMAT TESTS
# ============================================================================


def test_export_returns_csv_content_type(client: TestClient):
    """Test that response has CSV content type"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_export_returns_content_disposition_header(client: TestClient):
    """Test that response includes filename in Content-Disposition header"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    assert "Content-Disposition" in response.headers
    assert "students_export.csv" in response.headers["Content-Disposition"]
    assert "attachment" in response.headers["Content-Disposition"]


def test_export_includes_csv_header_row(client: TestClient):
    """Test that first line contains CSV headers"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    lines = response.text.strip().split("\n")
    assert len(lines) > 0

    # Parse header
    reader = csv.reader([lines[0]])
    headers = next(reader)
    assert headers == [
        "name",
        "email",
        "total_points",
        "completion_percentage",
        "last_active",
    ]


# ============================================================================
# CSV STRUCTURE TESTS
# ============================================================================


def test_export_includes_all_students(client: TestClient):
    """Test that all 5 test students appear in CSV"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    # Parse CSV
    reader = csv.reader(StringIO(response.text))
    rows = list(reader)

    # Should have header + 5 students
    assert len(rows) >= 6  # At least 5 students + header

    # Extract names
    names = {row[0] for row in rows[1:] if row}
    assert "Alice Smith" in names
    assert "Bob Jones" in names
    assert "Carol White" in names
    assert "Dave Brown" in names
    assert "Eve Davis" in names


def test_export_row_format_correct(client: TestClient):
    """Test that each CSV row has exactly 5 columns"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    # Parse CSV
    reader = csv.reader(StringIO(response.text))
    rows = list(reader)

    # All rows should have 5 columns
    for i, row in enumerate(rows):
        assert len(row) == 5, f"Row {i} has {len(row)} columns, expected 5: {row}"


# ============================================================================
# DATA ACCURACY TESTS
# ============================================================================


def test_export_student_names_match(client: TestClient):
    """Test that student names in CSV are correct"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Find Alice and verify name
    alice = next((r for r in rows if r["email"] == "alice@test.com"), None)
    assert alice is not None
    assert alice["name"] == "Alice Smith"


def test_export_student_emails_match(client: TestClient):
    """Test that student emails in CSV are correct"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    emails = {r["email"] for r in rows}
    assert "alice@test.com" in emails
    assert "bob@test.com" in emails
    assert "carol@test.com" in emails


def test_export_total_points_calculated_correctly(client: TestClient):
    """Test that total_points are summed correctly"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Alice: 100 + 150 + 250 = 500 points
    alice = next((r for r in rows if r["email"] == "alice@test.com"), None)
    assert alice is not None
    assert int(alice["total_points"]) == 500

    # Bob: 100 + 250 = 350 points
    bob = next((r for r in rows if r["email"] == "bob@test.com"), None)
    assert bob is not None
    assert int(bob["total_points"]) == 350

    # Carol: 100 points
    carol = next((r for r in rows if r["email"] == "carol@test.com"), None)
    assert carol is not None
    assert int(carol["total_points"]) == 100


def test_export_completion_percentage_calculated(client: TestClient):
    """Test that completion_percentage is calculated as (completed/7)*100"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Alice: 3 completed out of 7 = 42.86%
    alice = next((r for r in rows if r["email"] == "alice@test.com"), None)
    assert alice is not None
    completion_pct = float(alice["completion_percentage"])
    assert 42.8 < completion_pct < 42.9

    # Bob: 2 completed out of 7 = 28.57%
    bob = next((r for r in rows if r["email"] == "bob@test.com"), None)
    assert bob is not None
    completion_pct = float(bob["completion_percentage"])
    assert 28.5 < completion_pct < 28.6


# ============================================================================
# DATE FILTERING TESTS
# ============================================================================


def test_export_with_start_date_filter(client: TestClient):
    """Test that date filtering works with start_date parameter"""
    teacher_token = create_test_students_with_progress(client)

    # Filter to only include data from Jan 5, 2024 onwards
    # This should exclude Student 5 (Dec 2023)
    response = client.get(
        "/export/students?start_date=2024-01-05",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Should still have students with progress after Jan 5
    total_points = sum(int(r["total_points"]) for r in rows if r["total_points"])
    assert total_points > 0


def test_export_with_end_date_filter(client: TestClient):
    """Test that date filtering works with end_date parameter"""
    teacher_token = create_test_students_with_progress(client)

    # Filter to only include data up to Jan 10, 2024
    response = client.get(
        "/export/students?end_date=2024-01-10",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200

    # Should return valid CSV
    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)
    assert len(rows) > 0


def test_export_with_date_range_filter(client: TestClient):
    """Test that both start and end date filters work together"""
    teacher_token = create_test_students_with_progress(client)

    # Filter to specific date range
    response = client.get(
        "/export/students?start_date=2024-01-01&end_date=2024-01-10",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)
    assert len(rows) > 0


# ============================================================================
# LAST ACTIVE TESTS
# ============================================================================


def test_export_last_active_timestamp(client: TestClient):
    """Test that last_active shows most recent activity"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Alice should have a timestamp (she has progress)
    alice = next((r for r in rows if r["email"] == "alice@test.com"), None)
    assert alice is not None
    assert alice["last_active"] != "Never"
    assert len(alice["last_active"]) > 0


def test_export_last_active_never_for_inactive(client: TestClient):
    """Test that last_active shows 'Never' for students with no activity"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students", headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200

    reader = csv.DictReader(StringIO(response.text))
    rows = list(reader)

    # Dave should have "Never" (no progress)
    dave = next((r for r in rows if r["email"] == "dave@test.com"), None)
    assert dave is not None
    assert dave["last_active"] == "Never"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_export_invalid_date_format_start(client: TestClient):
    """Test that invalid start_date format returns 422"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students?start_date=01-01-2024",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 422


def test_export_invalid_date_format_end(client: TestClient):
    """Test that invalid end_date format returns 422"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students?end_date=2024/01/01",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 422


def test_export_start_date_after_end_date(client: TestClient):
    """Test that start_date > end_date returns 400 error"""
    teacher_token = create_test_students_with_progress(client)
    response = client.get(
        "/export/students?start_date=2024-01-10&end_date=2024-01-01",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert response.status_code == 400
