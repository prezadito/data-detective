"""
Test authentication endpoints.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch

# Import models at module level so SQLModel knows about them
from app.models import User  # noqa: F401


@pytest.fixture(name="engine")
def engine_fixture():
    """
    Create a test database engine that persists for the test.
    Uses StaticPool to ensure all connections share the same in-memory database.
    """
    # Use StaticPool to ensure all sessions share the same in-memory database
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


def test_register_new_user(client: TestClient):
    """Test registering a new user."""
    response = client.post(
        "/auth/register",
        json={
            "email": "student@school.edu",
            "name": "Test Student",
            "password": "securepassword123",
            "role": "student",
        },
    )

    assert response.status_code == 201
    data = response.json()

    # Check response contains user data
    assert data["email"] == "student@school.edu"
    assert data["name"] == "Test Student"
    assert data["role"] == "student"
    assert "id" in data

    # CRITICAL: Password should NOT be in response!
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client: TestClient):
    """Test that registering with duplicate email fails."""
    user_data = {
        "email": "duplicate@school.edu",
        "name": "First User",
        "password": "password123",
        "role": "student",
    }

    # First registration should succeed
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with same email should fail
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


def test_register_invalid_email(client: TestClient):
    """Test that invalid email format is rejected."""
    response = client.post(
        "/auth/register",
        json={
            "email": "notanemail",
            "name": "Test User",
            "password": "password123",
            "role": "student",
        },
    )

    assert response.status_code == 422  # Validation error


def test_register_missing_fields(client: TestClient):
    """Test that missing required fields are rejected."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@school.edu",
            # Missing name, password, role
        },
    )

    assert response.status_code == 422  # Validation error


def test_password_is_hashed(client: TestClient, session: Session):
    """Test that passwords are hashed, not stored in plain text."""
    from sqlmodel import select

    password = "myplainpassword"

    # Register user
    response = client.post(
        "/auth/register",
        json={
            "email": "hash@test.com",
            "name": "Hash Test",
            "password": password,
            "role": "student",
        },
    )

    assert response.status_code == 201

    # Get user from database
    statement = select(User).where(User.email == "hash@test.com")
    user = session.exec(statement).first()

    # Password should be hashed (not equal to plain text!)
    assert user.password_hash != password

    # Hash should start with bcrypt prefix
    assert user.password_hash.startswith("$2b$")

    # Verify the hash works
    from app.auth import verify_password

    assert verify_password(password, user.password_hash) is True
    assert verify_password("wrongpassword", user.password_hash) is False
