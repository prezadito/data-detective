"""
Test refresh token functionality.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch
from datetime import timedelta, datetime, timezone

# Import models at module level so SQLModel knows about them
from app.models import User, RefreshToken  # noqa: F401


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


def create_user_and_login(
    client: TestClient, email: str, password: str, name: str, role: str
) -> dict:
    """
    Helper function to register and login a user.

    Args:
        client: TestClient instance
        email: User email
        password: User password
        name: User name
        role: User role

    Returns:
        Dict with access_token, refresh_token, token_type
    """
    # Register user
    client.post(
        "/auth/register",
        json={"email": email, "name": name, "password": password, "role": role},
    )

    # Login and get tokens
    response = client.post("/auth/login", json={"email": email, "password": password})

    return response.json()


# ============================================================================
# LOGIN MODIFICATION TESTS
# ============================================================================


def test_login_returns_both_tokens(client: TestClient):
    """Test that login returns both access_token and refresh_token."""
    # Register user
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "password123",
            "role": "student",
        },
    )

    # Login
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check both tokens are present
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data

    # Check tokens are non-empty strings
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0

    # Check token type
    assert data["token_type"] == "bearer"

    # Tokens should be different
    assert data["access_token"] != data["refresh_token"]


# ============================================================================
# TOKEN STORAGE TESTS
# ============================================================================


def test_refresh_token_is_stored_in_database(client: TestClient, session: Session):
    """Test that refresh token is stored in database after login."""
    tokens = create_user_and_login(
        client, "storage@test.com", "password123", "Storage Test", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Query database for refresh token
    statement = select(RefreshToken).where(RefreshToken.token == refresh_token)
    db_token = session.exec(statement).first()

    # Token should exist
    assert db_token is not None
    assert db_token.token == refresh_token
    assert db_token.user_id == 1  # First user
    assert db_token.revoked is False
    assert db_token.expires_at is not None


def test_refresh_token_has_correct_expiration(client: TestClient, session: Session):
    """Test that refresh token has correct expiration (~7 days)."""
    from jose import jwt
    from app.auth import SECRET_KEY, ALGORITHM

    tokens = create_user_and_login(
        client, "expiry@test.com", "password123", "Expiry Test", "teacher"
    )

    refresh_token = tokens["refresh_token"]

    # Decode token to check expiration
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

    assert "exp" in payload
    assert "sub" in payload  # User ID in subject

    # Check expiration is roughly 7 days from now
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    time_diff = exp_datetime - now

    # Should be between 6.9 and 7.1 days
    assert 6.9 * 24 * 60 * 60 < time_diff.total_seconds() < 7.1 * 24 * 60 * 60


# ============================================================================
# REFRESH ENDPOINT TESTS
# ============================================================================


def test_refresh_with_valid_token_success(client: TestClient):
    """Test refreshing access token with valid refresh token."""
    tokens = create_user_and_login(
        client, "refresh@test.com", "password123", "Refresh Test", "student"
    )

    refresh_token = tokens["refresh_token"]
    original_access_token = tokens["access_token"]

    # Refresh the token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()

    # Should return new access token
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # New access token should be different from original
    assert data["access_token"] != original_access_token

    # New access token should work for protected endpoints
    me_response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me_response.status_code == 200


def test_refresh_with_invalid_token(client: TestClient):
    """Test refresh with malformed/invalid token."""
    response = client.post("/auth/refresh", json={"refresh_token": "invalid-token"})

    assert response.status_code == 401
    assert "detail" in response.json()


def test_refresh_with_expired_token(client: TestClient, session: Session):
    """Test refresh with expired token."""
    from app.auth import create_access_token

    # Create user
    client.post(
        "/auth/register",
        json={
            "email": "expired@test.com",
            "name": "Expired Test",
            "password": "password123",
            "role": "student",
        },
    )

    # Create expired refresh token
    expired_token = create_access_token(
        data={"sub": "1", "type": "refresh"},
        expires_delta=timedelta(days=-1),  # Already expired
    )

    # Store in database
    db_token = RefreshToken(
        token=expired_token,
        user_id=1,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        revoked=False,
    )
    session.add(db_token)
    session.commit()

    # Try to refresh with expired token
    response = client.post("/auth/refresh", json={"refresh_token": expired_token})

    assert response.status_code == 401
    assert "detail" in response.json()


def test_refresh_with_revoked_token(client: TestClient, session: Session):
    """Test refresh with revoked token."""
    tokens = create_user_and_login(
        client, "revoked@test.com", "password123", "Revoked Test", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Manually revoke token in database
    statement = select(RefreshToken).where(RefreshToken.token == refresh_token)
    db_token = session.exec(statement).first()
    db_token.revoked = True
    session.add(db_token)
    session.commit()

    # Try to refresh with revoked token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "revoked" in data["detail"].lower()


def test_refresh_with_nonexistent_token(client: TestClient):
    """Test refresh with valid JWT but not in database."""
    from app.auth import create_access_token

    # Create valid JWT but don't store in database
    fake_token = create_access_token(
        data={"sub": "999", "type": "refresh"}, expires_delta=timedelta(days=7)
    )

    # Try to refresh
    response = client.post("/auth/refresh", json={"refresh_token": fake_token})

    assert response.status_code == 401


def test_refresh_with_deleted_user(client: TestClient, session: Session):
    """Test refresh when user has been deleted."""
    tokens = create_user_and_login(
        client, "deleted@test.com", "password123", "Deleted User", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Delete user from database
    statement = select(User).where(User.email == "deleted@test.com")
    user = session.exec(statement).first()
    session.delete(user)
    session.commit()

    # Try to refresh
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401


# ============================================================================
# LOGOUT ENDPOINT TESTS
# ============================================================================


def test_logout_revokes_token(client: TestClient, session: Session):
    """Test that logout revokes the refresh token."""
    tokens = create_user_and_login(
        client, "logout@test.com", "password123", "Logout Test", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Logout
    response = client.post("/auth/logout", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # Check token is revoked in database
    statement = select(RefreshToken).where(RefreshToken.token == refresh_token)
    db_token = session.exec(statement).first()
    assert db_token.revoked is True


def test_logout_prevents_future_refresh(client: TestClient):
    """Test that after logout, token cannot be used for refresh."""
    tokens = create_user_and_login(
        client, "prevent@test.com", "password123", "Prevent Test", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Logout
    logout_response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200

    # Try to refresh with logged-out token
    refresh_response = client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 401
    assert "revoked" in refresh_response.json()["detail"].lower()


def test_logout_with_invalid_token(client: TestClient):
    """Test logout with invalid token."""
    response = client.post("/auth/logout", json={"refresh_token": "invalid-token"})

    assert response.status_code == 401


def test_logout_with_already_revoked_token(client: TestClient):
    """Test logout with already revoked token (idempotent)."""
    tokens = create_user_and_login(
        client, "idempotent@test.com", "password123", "Idempotent Test", "student"
    )

    refresh_token = tokens["refresh_token"]

    # Logout once
    response1 = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert response1.status_code == 200

    # Try to logout again
    response2 = client.post("/auth/logout", json={"refresh_token": refresh_token})

    # Should fail (token not valid)
    assert response2.status_code == 401


# ============================================================================
# MULTIPLE TOKENS TESTS
# ============================================================================


def test_multiple_refresh_tokens_per_user(client: TestClient, session: Session):
    """Test that user can have multiple valid refresh tokens (different sessions)."""
    # Register user once
    client.post(
        "/auth/register",
        json={
            "email": "multi@test.com",
            "name": "Multi Session",
            "password": "password123",
            "role": "student",
        },
    )

    # Login twice (simulating two devices)
    login1 = client.post(
        "/auth/login", json={"email": "multi@test.com", "password": "password123"}
    )
    login2 = client.post(
        "/auth/login", json={"email": "multi@test.com", "password": "password123"}
    )

    token1 = login1.json()["refresh_token"]
    token2 = login2.json()["refresh_token"]

    # Tokens should be different
    assert token1 != token2

    # Both should work
    refresh1 = client.post("/auth/refresh", json={"refresh_token": token1})
    refresh2 = client.post("/auth/refresh", json={"refresh_token": token2})

    assert refresh1.status_code == 200
    assert refresh2.status_code == 200

    # Revoke one
    client.post("/auth/logout", json={"refresh_token": token1})

    # First should fail, second should still work
    refresh1_after = client.post("/auth/refresh", json={"refresh_token": token1})
    refresh2_after = client.post("/auth/refresh", json={"refresh_token": token2})

    assert refresh1_after.status_code == 401
    assert refresh2_after.status_code == 200
