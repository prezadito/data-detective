"""
Test password reset request functionality.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
import re

# Import models at module level so SQLModel knows about them
from app.models import User, RefreshToken, PasswordResetToken  # noqa: F401


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


def create_test_user(
    client: TestClient, email: str = "test@example.com", password: str = "password123"
):
    """
    Helper function to create a test user.

    Args:
        client: TestClient instance
        email: User email
        password: User password

    Returns:
        Response from registration
    """
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Test User",
            "password": password,
            "role": "student",
        },
    )


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================


def test_password_reset_request_with_valid_email(client: TestClient):
    """Test password reset request with valid registered email."""
    # Create user first
    create_test_user(client, "user@example.com", "password123")

    # Request password reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "user@example.com"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should have message and token
    assert "message" in data
    assert "reset_token" in data
    assert isinstance(data["message"], str)
    assert isinstance(data["reset_token"], str)
    assert len(data["reset_token"]) > 0


def test_password_reset_request_returns_token(client: TestClient):
    """Test that password reset returns a non-empty token."""
    # Create user
    create_test_user(client, "user2@example.com", "password123")

    # Request reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "user2@example.com"}
    )

    assert response.status_code == 200
    data = response.json()

    # Token should be substantial length (url-safe token)
    assert len(data["reset_token"]) > 20
    assert data["reset_token"] != ""


def test_password_reset_token_is_stored_in_database(
    client: TestClient, session: Session
):
    """Test that reset token is stored in database with correct user_id."""
    # Create user
    create_test_user(client, "dbtest@example.com", "password123")

    # Request reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "dbtest@example.com"}
    )

    reset_token = response.json()["reset_token"]

    # Query database for reset token
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == reset_token
    )
    db_token = session.exec(statement).first()

    # Token should exist
    assert db_token is not None
    assert db_token.token == reset_token
    assert db_token.user_id == 1  # First user
    assert db_token.used is False
    assert db_token.expires_at is not None


# ============================================================================
# EXPIRATION TESTS
# ============================================================================


def test_password_reset_token_has_correct_expiration(
    client: TestClient, session: Session
):
    """Test that reset token expires in ~1 hour."""
    # Create user
    create_test_user(client, "expiry@example.com", "password123")

    # Request reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "expiry@example.com"}
    )

    reset_token = response.json()["reset_token"]

    # Get token from database
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == reset_token
    )
    db_token = session.exec(statement).first()

    # Check expiration is roughly 1 hour from now
    now = datetime.now(timezone.utc)
    # SQLite stores naive datetime, make it aware
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc)
    time_diff = expires_at_aware - now

    # Should be between 59 and 61 minutes (allowing for test execution time)
    assert 59 * 60 < time_diff.total_seconds() < 61 * 60


# ============================================================================
# UNIQUENESS TESTS
# ============================================================================


def test_multiple_requests_generate_different_tokens(client: TestClient):
    """Test that multiple reset requests generate different tokens."""
    # Create user
    create_test_user(client, "multi@example.com", "password123")

    # Request reset twice
    response1 = client.post(
        "/auth/password-reset-request", json={"email": "multi@example.com"}
    )
    response2 = client.post(
        "/auth/password-reset-request", json={"email": "multi@example.com"}
    )

    token1 = response1.json()["reset_token"]
    token2 = response2.json()["reset_token"]

    # Tokens should be different
    assert token1 != token2
    assert len(token1) > 20
    assert len(token2) > 20


def test_token_is_url_safe(client: TestClient):
    """Test that token contains only URL-safe characters."""
    # Create user
    create_test_user(client, "urlsafe@example.com", "password123")

    # Request reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "urlsafe@example.com"}
    )

    token = response.json()["reset_token"]

    # URL-safe tokens should only contain: A-Z, a-z, 0-9, -, _
    url_safe_pattern = r"^[A-Za-z0-9_-]+$"
    assert re.match(url_safe_pattern, token)


# ============================================================================
# SINGLE-USE TESTS
# ============================================================================


def test_token_initially_unused(client: TestClient, session: Session):
    """Test that newly created token has used=False."""
    # Create user
    create_test_user(client, "unused@example.com", "password123")

    # Request reset
    response = client.post(
        "/auth/password-reset-request", json={"email": "unused@example.com"}
    )

    reset_token = response.json()["reset_token"]

    # Check database
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == reset_token
    )
    db_token = session.exec(statement).first()

    # Should be unused
    assert db_token.used is False


# ============================================================================
# SECURITY TESTS (CRITICAL!)
# ============================================================================


def test_password_reset_request_with_nonexistent_email(client: TestClient):
    """Test that non-existent email still returns 200 (prevents user enumeration)."""
    # Do NOT create user

    # Request reset for non-existent email
    response = client.post(
        "/auth/password-reset-request", json={"email": "nonexistent@example.com"}
    )

    # Should still return 200 (security!)
    assert response.status_code == 200
    data = response.json()

    # Should have same response structure
    assert "message" in data
    assert "reset_token" in data

    # Token should be empty string (no token created)
    assert data["reset_token"] == ""


def test_nonexistent_email_does_not_create_token(client: TestClient, session: Session):
    """Test that requesting reset for non-existent email doesn't create token in DB."""
    # Request reset for non-existent email
    client.post("/auth/password-reset-request", json={"email": "fake@example.com"})

    # Check database - should have no tokens
    statement = select(PasswordResetToken)
    tokens = session.exec(statement).all()

    assert len(tokens) == 0


# ============================================================================
# EDGE CASES
# ============================================================================


def test_password_reset_request_invalid_email_format(client: TestClient):
    """Test that invalid email format returns 422."""
    # Request reset with invalid email
    response = client.post(
        "/auth/password-reset-request", json={"email": "not-an-email"}
    )

    # Should return 422 Unprocessable Entity (Pydantic validation)
    assert response.status_code == 422


# ============================================================================
# PASSWORD RESET CONFIRMATION TESTS
# ============================================================================


# ----------------------------------------------------------------------------
# Helper function for confirmation tests
# ----------------------------------------------------------------------------


def create_user_and_get_reset_token(
    client: TestClient,
    email: str = "reset@example.com",
    password: str = "oldpassword123",
) -> str:
    """
    Helper to create user and get reset token.

    Args:
        client: TestClient instance
        email: User email
        password: User password

    Returns:
        Reset token string
    """
    # Create user
    create_test_user(client, email, password)

    # Request reset
    response = client.post("/auth/password-reset-request", json={"email": email})

    return response.json()["reset_token"]


# ----------------------------------------------------------------------------
# Basic Functionality Tests
# ----------------------------------------------------------------------------


def test_password_reset_confirm_success(client: TestClient):
    """Test successful password reset with valid token."""
    # Get reset token
    reset_token = create_user_and_get_reset_token(client)

    # Confirm password reset
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "newpassword123"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have success message
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_password_reset_confirm_updates_password(client: TestClient, session: Session):
    """Test that password reset actually updates the user's password in database."""
    from app.auth import verify_password

    email = "update@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword123"

    # Create user and get reset token
    reset_token = create_user_and_get_reset_token(client, email, old_password)

    # Get user's current password hash
    statement = select(User).where(User.email == email)
    user_before = session.exec(statement).first()
    old_hash = user_before.password_hash

    # Confirm password reset
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": new_password},
    )

    # Get user again and check password hash changed
    session.expire_all()  # Refresh session to get updated data
    user_after = session.exec(statement).first()
    new_hash = user_after.password_hash

    # Hash should have changed
    assert old_hash != new_hash

    # New password should verify against new hash
    assert verify_password(new_password, new_hash)

    # Old password should NOT verify against new hash
    assert not verify_password(old_password, new_hash)


def test_password_reset_confirm_marks_token_as_used(
    client: TestClient, session: Session
):
    """Test that password reset marks the token as used in database."""
    # Get reset token
    reset_token = create_user_and_get_reset_token(client)

    # Confirm password reset
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "newpassword123"},
    )

    # Check token in database
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == reset_token
    )
    db_token = session.exec(statement).first()

    # Token should be marked as used
    assert db_token is not None
    assert db_token.used is True


def test_user_can_login_with_new_password(client: TestClient):
    """Test that user can login with new password after reset."""
    email = "logintest@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword123"

    # Create user and reset password
    reset_token = create_user_and_get_reset_token(client, email, old_password)
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": new_password},
    )

    # Try to login with new password
    response = client.post(
        "/auth/login", json={"email": email, "password": new_password}
    )

    # Should succeed
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_user_cannot_login_with_old_password(client: TestClient):
    """Test that old password no longer works after reset."""
    email = "oldpassfail@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword123"

    # Create user and reset password
    reset_token = create_user_and_get_reset_token(client, email, old_password)
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": new_password},
    )

    # Try to login with old password
    response = client.post(
        "/auth/login", json={"email": email, "password": old_password}
    )

    # Should fail
    assert response.status_code == 401
    assert "detail" in response.json()


# ----------------------------------------------------------------------------
# Token Validation Tests
# ----------------------------------------------------------------------------


def test_password_reset_confirm_with_invalid_token(client: TestClient):
    """Test that non-existent token returns 401."""
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": "invalid-token-xyz", "new_password": "newpassword123"},
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_password_reset_confirm_with_expired_token(
    client: TestClient, session: Session
):
    """Test that expired token returns 401."""
    from datetime import timedelta

    # Create user
    create_test_user(client, "expired@example.com")

    # Manually create expired token in database
    expired_token = PasswordResetToken(
        token="expired-token-123",
        user_id=1,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),  # 2 hours ago
        used=False,
    )
    session.add(expired_token)
    session.commit()

    # Try to use expired token
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": "expired-token-123", "new_password": "newpassword123"},
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_password_reset_confirm_with_used_token(client: TestClient):
    """Test that already-used token returns 401."""
    email = "usedtoken@example.com"

    # Get reset token and use it once
    reset_token = create_user_and_get_reset_token(client, email)
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "newpassword123"},
    )

    # Try to use the same token again
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "anotherpassword456"},
    )

    # Should fail
    assert response.status_code == 401
    assert "detail" in response.json()


def test_used_token_stays_invalid_even_if_not_expired(
    client: TestClient, session: Session
):
    """Test that used tokens can't be reused, even if not expired."""
    # Get reset token and use it
    reset_token = create_user_and_get_reset_token(client)
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "newpassword123"},
    )

    # Verify token is marked as used but not expired
    statement = select(PasswordResetToken).where(
        PasswordResetToken.token == reset_token
    )
    db_token = session.exec(statement).first()

    # Should be used
    assert db_token.used is True

    # Should not be expired (created less than 1 hour ago)
    expires_at_aware = db_token.expires_at.replace(tzinfo=timezone.utc)
    assert datetime.now(timezone.utc) < expires_at_aware

    # Try to use again - should still fail
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "anotherpass"},
    )

    assert response.status_code == 401


# ----------------------------------------------------------------------------
# Password Validation Tests
# ----------------------------------------------------------------------------


def test_password_reset_confirm_password_too_short(client: TestClient):
    """Test that password shorter than 8 characters returns 422."""
    reset_token = create_user_and_get_reset_token(client)

    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "short"},
    )

    # Should return 422 Unprocessable Entity (Pydantic validation)
    assert response.status_code == 422


def test_password_reset_confirm_password_too_long(client: TestClient):
    """Test that password longer than 100 characters returns 422."""
    reset_token = create_user_and_get_reset_token(client)

    # Create 101 character password
    long_password = "a" * 101

    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": long_password},
    )

    # Should return 422 Unprocessable Entity (Pydantic validation)
    assert response.status_code == 422


# ----------------------------------------------------------------------------
# Edge Cases
# ----------------------------------------------------------------------------


def test_password_reset_with_deleted_user(client: TestClient, session: Session):
    """Test that token fails if user was deleted."""
    email = "deleteduser@example.com"

    # Create user and get reset token
    reset_token = create_user_and_get_reset_token(client, email)

    # Delete user from database
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    session.delete(user)
    session.commit()

    # Try to use reset token
    response = client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": reset_token, "new_password": "newpassword123"},
    )

    # Should fail
    assert response.status_code == 401


def test_only_used_token_is_marked(client: TestClient, session: Session):
    """Test that when user has multiple tokens, only the used one is marked."""
    email = "multitoken@example.com"

    # Create user
    create_test_user(client, email)

    # Request reset 3 times to get 3 different tokens
    response1 = client.post("/auth/password-reset-request", json={"email": email})
    response2 = client.post("/auth/password-reset-request", json={"email": email})
    response3 = client.post("/auth/password-reset-request", json={"email": email})

    token1 = response1.json()["reset_token"]
    token2 = response2.json()["reset_token"]
    token3 = response3.json()["reset_token"]

    # Use token2
    client.post(
        "/auth/password-reset-confirm",
        json={"reset_token": token2, "new_password": "newpassword123"},
    )

    # Check all tokens in database
    statement1 = select(PasswordResetToken).where(PasswordResetToken.token == token1)
    statement2 = select(PasswordResetToken).where(PasswordResetToken.token == token2)
    statement3 = select(PasswordResetToken).where(PasswordResetToken.token == token3)

    db_token1 = session.exec(statement1).first()
    db_token2 = session.exec(statement2).first()
    db_token3 = session.exec(statement3).first()

    # Only token2 should be marked as used
    assert db_token1.used is False
    assert db_token2.used is True
    assert db_token3.used is False
