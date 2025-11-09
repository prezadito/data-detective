"""
Bulk student import tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from io import BytesIO
from unittest.mock import patch
from app.models import User  # noqa: F401


# ============================================================================
# FIXTURES & HELPERS
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


def create_csv_content(rows: list[dict]) -> bytes:
    """
    Create CSV content from list of dicts.

    Args:
        rows: List of dicts with 'email' and 'name' keys

    Returns:
        CSV content as bytes
    """
    if not rows:
        return b""

    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["email", "name"])
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8")


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


# ============================================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ============================================================================


def test_import_requires_authentication(client):
    """Test that import endpoint requires authentication."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
    )

    assert response.status_code == 401


def test_import_requires_teacher_role(client, student_token):
    """Test that import endpoint requires teacher role."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403


# ============================================================================
# FILE FORMAT & STRUCTURE TESTS
# ============================================================================


def test_import_rejects_empty_file(client, teacher_token):
    """Test that empty CSV file is rejected."""
    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(b""), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_import_rejects_missing_email_column(client, teacher_token):
    """Test that CSV without email column is rejected."""
    csv_content = b"name\nAlice\nBob"

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_import_rejects_missing_name_column(client, teacher_token):
    """Test that CSV without name column is rejected."""
    csv_content = b"email\nalice@test.com\nbob@test.com"

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()


def test_import_accepts_csv_with_headers(client, teacher_token):
    """Test that valid CSV with headers is accepted."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    assert "imported_students" in response.json()


# ============================================================================
# EMAIL VALIDATION TESTS
# ============================================================================


def test_import_skips_invalid_email(client, teacher_token):
    """Test that rows with invalid email are skipped."""
    csv_content = create_csv_content(
        [
            {"email": "invalid-email", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 1 successful, 1 failed
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert len(data["errors"]) == 1
    assert "invalid-email" in str(data["errors"][0])


def test_import_detects_duplicate_emails_in_file(client, teacher_token):
    """Test that duplicate emails within same CSV file are detected."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "alice@test.com", "name": "Alice Again"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 1 successful, 1 skipped
    assert data["successful"] == 1
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1


def test_import_detects_existing_emails(client, teacher_token):
    """Test that emails already in database are detected."""
    # Create an existing student
    response = client.post(
        "/auth/register",
        json={
            "email": "existing@test.com",
            "name": "Existing User",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 201

    # Try to import CSV with that email
    csv_content = create_csv_content(
        [
            {"email": "existing@test.com", "name": "New Alice"},
            {"email": "newuser@test.com", "name": "New User"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 1 successful, 1 skipped (duplicate)
    assert data["successful"] == 1
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1
    assert "already exists" in data["errors"][0]["error"].lower()


# ============================================================================
# USER CREATION TESTS
# ============================================================================


def test_import_creates_students_from_csv(client, teacher_token, session):
    """Test that valid CSV rows create new student accounts."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
            {"email": "carol@test.com", "name": "Carol"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should create 3 students
    assert data["successful"] == 3
    assert data["failed"] == 0
    assert data["skipped"] == 0

    # Verify they exist in database
    statement = select(User).where(
        User.email.in_(["alice@test.com", "bob@test.com", "carol@test.com"])
    )
    users = session.exec(statement).all()
    assert len(users) == 3


def test_import_generates_random_passwords(client, teacher_token):
    """Test that each imported student gets a unique password."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
            {"email": "carol@test.com", "name": "Carol"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 3 imported students with unique passwords
    assert len(data["imported_students"]) == 3

    passwords = [student["temporary_password"] for student in data["imported_students"]]
    assert len(set(passwords)) == 3  # All unique


def test_import_hashes_passwords_with_bcrypt(client, teacher_token, session):
    """Test that passwords are hashed with bcrypt before storage."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200

    # Verify password is hashed (starts with bcrypt prefix)
    user = session.exec(select(User).where(User.email == "alice@test.com")).first()
    assert user is not None
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_import_sets_correct_role(client, teacher_token, session):
    """Test that imported users are created with role='student'."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200

    # Verify role is set to 'student'
    user = session.exec(select(User).where(User.email == "alice@test.com")).first()
    assert user is not None
    assert user.role == "student"


# ============================================================================
# RESPONSE & REPORTING TESTS
# ============================================================================


def test_import_returns_summary_statistics(client, teacher_token):
    """Test that response includes summary statistics."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
            {"email": "invalid-email", "name": "Charlie"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should include all statistics
    assert "successful" in data
    assert "skipped" in data
    assert "failed" in data
    assert data["successful"] == 2
    assert data["failed"] == 1
    assert data["skipped"] == 0


def test_import_returns_detailed_error_list(client, teacher_token):
    """Test that response includes detailed error messages per row."""
    csv_content = create_csv_content(
        [
            {"email": "invalid-email", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have error details
    assert "errors" in data
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert "row_number" in error
    assert "error" in error
    assert error["row_number"] == 2  # Second row (after header)


def test_import_returns_generated_passwords(client, teacher_token):
    """Test that response includes generated passwords for each user."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should include imported students with passwords
    assert "imported_students" in data
    assert len(data["imported_students"]) == 2

    for student in data["imported_students"]:
        assert "email" in student
        assert "name" in student
        assert "temporary_password" in student
        assert len(student["temporary_password"]) > 0


def test_import_returns_correct_status_code(client, teacher_token):
    """Test that successful import returns 200 status code."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================


def test_import_emails_are_unique_after_import(client, teacher_token, session):
    """Test that no duplicate emails exist after import."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice"},
            {"email": "bob@test.com", "name": "Bob"},
            {"email": "carol@test.com", "name": "Carol"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200

    # Get all users and check emails are unique
    all_users = session.exec(select(User)).all()
    emails = [user.email for user in all_users]

    # All emails should be unique
    assert len(emails) == len(set(emails))


def test_import_names_stored_correctly(client, teacher_token, session):
    """Test that names from CSV are stored exactly as provided."""
    csv_content = create_csv_content(
        [
            {"email": "alice@test.com", "name": "Alice Johnson"},
            {"email": "bob@test.com", "name": "Bob Smith"},
            {"email": "carol@test.com", "name": "Carol O'Brien"},
        ]
    )

    response = client.post(
        "/import/students",
        files={"file": ("students.csv", BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200

    # Verify names match exactly
    alice = session.exec(select(User).where(User.email == "alice@test.com")).first()
    assert alice is not None
    assert alice.name == "Alice Johnson"

    bob = session.exec(select(User).where(User.email == "bob@test.com")).first()
    assert bob is not None
    assert bob.name == "Bob Smith"

    carol = session.exec(select(User).where(User.email == "carol@test.com")).first()
    assert carol is not None
    assert carol.name == "Carol O'Brien"
