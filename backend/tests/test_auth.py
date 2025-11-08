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


# ============================================================================
# LOGIN TESTS
# ============================================================================


def test_login_success(client: TestClient):
    """Test successful login returns access token."""
    # First register a user
    register_data = {
        "email": "login@test.com",
        "name": "Login Test",
        "password": "securepass123",
        "role": "student",
    }
    client.post("/auth/register", json=register_data)

    # Now login with correct credentials
    login_data = {"email": "login@test.com", "password": "securepass123"}
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()

    # Should return access token and token type
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password fails with 401."""
    # Register a user
    register_data = {
        "email": "wrongpass@test.com",
        "name": "Wrong Pass Test",
        "password": "correctpassword",
        "role": "student",
    }
    client.post("/auth/register", json=register_data)

    # Attempt login with wrong password
    login_data = {"email": "wrongpass@test.com", "password": "wrongpassword"}
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 401
    data = response.json()
    # Error message should be generic (don't leak info about user existence)
    assert "detail" in data
    assert "incorrect" in data["detail"].lower()


def test_login_user_not_found(client: TestClient):
    """Test login with non-existent email fails with 401."""
    # Attempt login with email that doesn't exist
    login_data = {
        "email": "nonexistent@test.com",
        "password": "somepassword",
    }
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 401
    data = response.json()
    # Error should be same as wrong password (prevent user enumeration)
    assert "detail" in data
    assert "incorrect" in data["detail"].lower()


def test_login_invalid_email_format(client: TestClient):
    """Test login with invalid email format fails with 422."""
    login_data = {"email": "notanemail", "password": "somepassword"}
    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 422  # Validation error


def test_login_missing_credentials(client: TestClient):
    """Test login with missing fields fails with 422."""
    # Missing password
    response1 = client.post("/auth/login", json={"email": "test@test.com"})
    assert response1.status_code == 422

    # Missing email
    response2 = client.post("/auth/login", json={"password": "testpass"})
    assert response2.status_code == 422


def test_token_contains_user_info(client: TestClient):
    """Test that JWT token contains correct user information."""
    from jose import jwt
    from app.auth import SECRET_KEY, ALGORITHM

    # Register and login
    register_data = {
        "email": "token@test.com",
        "name": "Token Test",
        "password": "testpass123",
        "role": "teacher",
    }
    client.post("/auth/register", json=register_data)

    login_data = {"email": "token@test.com", "password": "testpass123"}
    response = client.post("/auth/login", json=login_data)

    token = response.json()["access_token"]

    # Decode and verify token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # Token should contain user info
    assert "sub" in payload  # Subject (standard JWT claim for user identifier)
    assert payload["sub"] == "token@test.com"
    assert "user_id" in payload
    assert "role" in payload
    assert payload["role"] == "teacher"
    assert "exp" in payload  # Expiration


def test_last_login_updated(client: TestClient, session: Session):
    """Test that last_login timestamp is updated on successful login."""
    from sqlmodel import select
    from datetime import datetime

    # Register user
    register_data = {
        "email": "lastlogin@test.com",
        "name": "Last Login Test",
        "password": "testpass123",
        "role": "student",
    }
    client.post("/auth/register", json=register_data)

    # Get user from database - last_login should be None initially
    statement = select(User).where(User.email == "lastlogin@test.com")
    user_before = session.exec(statement).first()
    assert user_before.last_login is None

    # Login
    login_data = {"email": "lastlogin@test.com", "password": "testpass123"}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    # Refresh session and check last_login was updated
    session.expire_all()  # Clear session cache
    user_after = session.exec(statement).first()
    assert user_after.last_login is not None
    assert isinstance(user_after.last_login, datetime)
