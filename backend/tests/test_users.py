"""
Test protected user endpoints.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch
from datetime import timedelta

# Import models at module level so SQLModel knows about them
from app.models import User  # noqa: F401


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


# ============================================================================
# GET /users/me TESTS
# ============================================================================


def test_get_current_user_success(client: TestClient):
    """Test getting current user with valid token."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "current@test.com", "password123", "Current User", "student"
    )

    # Get current user with token
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    # Verify user data
    assert data["email"] == "current@test.com"
    assert data["name"] == "Current User"
    assert data["role"] == "student"
    assert "id" in data
    assert "created_at" in data

    # Should not include password
    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without authentication token."""
    response = client.get("/users/me")

    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with malformed/invalid token."""
    response = client.get(
        "/users/me", headers={"Authorization": "Bearer invalid-token-here"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "credential" in data["detail"].lower()


def test_get_current_user_expired_token(client: TestClient):
    """Test getting current user with expired token."""
    from app.auth import create_access_token

    # Create user first
    client.post(
        "/auth/register",
        json={
            "email": "expired@test.com",
            "name": "Expired User",
            "password": "password123",
            "role": "student",
        },
    )

    # Create expired token (already expired)
    expired_token = create_access_token(
        data={"sub": "expired@test.com", "user_id": 1, "role": "student"},
        expires_delta=timedelta(minutes=-1),  # Negative = already expired
    )

    # Try to use expired token
    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_current_user_token_for_deleted_user(client: TestClient, session: Session):
    """Test using valid token after user has been deleted."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "deleted@test.com", "password123", "Deleted User", "student"
    )

    # Delete user from database
    statement = select(User).where(User.email == "deleted@test.com")
    user = session.exec(statement).first()
    session.delete(user)
    session.commit()

    # Try to use token (valid but user doesn't exist)
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_current_user_malformed_authorization_header(client: TestClient):
    """Test with malformed Authorization header (not 'Bearer <token>')."""
    # Create user and token
    token = create_user_and_get_token(
        client, "malformed@test.com", "password123", "Malformed User", "student"
    )

    # Use incorrect header format (missing 'Bearer')
    response = client.get("/users/me", headers={"Authorization": token})

    assert response.status_code == 401


# ============================================================================
# GET /users/{user_id} TESTS
# ============================================================================


def test_get_user_by_id_success(client: TestClient):
    """Test getting another user by ID with authentication."""
    # Create two users
    token1 = create_user_and_get_token(
        client, "user1@test.com", "password123", "User One", "student"
    )

    client.post(
        "/auth/register",
        json={
            "email": "user2@test.com",
            "name": "User Two",
            "password": "password123",
            "role": "teacher",
        },
    )

    # User1 gets User2's data
    response = client.get("/users/2", headers={"Authorization": f"Bearer {token1}"})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user2@test.com"
    assert data["name"] == "User Two"
    assert data["role"] == "teacher"


def test_get_user_by_id_self(client: TestClient):
    """Test getting own user data by ID."""
    # Create user
    token = create_user_and_get_token(
        client, "self@test.com", "password123", "Self User", "student"
    )

    # Get own user data by ID
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "self@test.com"
    assert data["name"] == "Self User"


def test_get_user_by_id_no_token(client: TestClient):
    """Test getting user by ID without authentication."""
    response = client.get("/users/1")

    assert response.status_code == 401


def test_get_user_by_id_not_found(client: TestClient):
    """Test getting non-existent user by ID."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "finder@test.com", "password123", "Finder User", "student"
    )

    # Try to get non-existent user
    response = client.get("/users/99999", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# ============================================================================
# TOKEN PAYLOAD VALIDATION TESTS
# ============================================================================


def test_get_current_user_with_missing_claims(client: TestClient):
    """Test token with missing required claims (user_id)."""
    from jose import jwt
    from app.auth import SECRET_KEY, ALGORITHM

    # Create user first
    client.post(
        "/auth/register",
        json={
            "email": "missing@test.com",
            "name": "Missing Claims",
            "password": "password123",
            "role": "student",
        },
    )

    # Create token missing 'user_id' claim
    bad_token = jwt.encode(
        {
            "sub": "missing@test.com",
            "role": "student",
            # Missing 'user_id' claim!
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    # Try to use token with missing claims
    response = client.get("/users/me", headers={"Authorization": f"Bearer {bad_token}"})

    assert response.status_code == 401
    assert "detail" in response.json()
