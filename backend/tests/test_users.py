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
    """Test getting another user by ID with authentication (teacher accessing another user)."""
    # Create teacher and student
    token1 = create_user_and_get_token(
        client, "user1@test.com", "password123", "User One", "teacher"
    )

    client.post(
        "/auth/register",
        json={
            "email": "user2@test.com",
            "name": "User Two",
            "password": "password123",
            "role": "student",
        },
    )

    # Teacher gets student's data
    response = client.get("/users/2", headers={"Authorization": f"Bearer {token1}"})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user2@test.com"
    assert data["name"] == "User Two"
    assert data["role"] == "student"


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
    """Test getting non-existent user by ID (teacher can check, gets 404)."""
    # Create teacher and get token
    token = create_user_and_get_token(
        client, "finder@test.com", "password123", "Finder User", "teacher"
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


# ============================================================================
# PUT /users/me TESTS (PROFILE UPDATE)
# ============================================================================


def test_update_current_user_success(client: TestClient):
    """Test updating current user's name successfully."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "update@test.com", "password123", "Original Name", "student"
    )

    # Update user name
    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have updated name
    assert data["name"] == "Updated Name"
    assert data["email"] == "update@test.com"
    assert data["role"] == "student"


def test_update_current_user_returns_updated_data(client: TestClient):
    """Test that update response contains the new name."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "return@test.com", "password123", "Old Name", "teacher"
    )

    # Update user name
    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )

    assert response.status_code == 200
    data = response.json()

    # Response should contain updated name
    assert data["name"] == "New Name"
    assert "id" in data
    assert "email" in data
    assert "role" in data
    assert "created_at" in data


def test_update_current_user_persists_changes(client: TestClient, session: Session):
    """Test that name update is actually persisted to database."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "persist@test.com", "password123", "Before Update", "student"
    )

    # Update user name
    client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "After Update"},
    )

    # Read from database to verify persistence
    statement = select(User).where(User.email == "persist@test.com")
    user = session.exec(statement).first()

    assert user is not None
    assert user.name == "After Update"


def test_update_does_not_change_other_fields(client: TestClient, session: Session):
    """Test that updating name doesn't change email, role, or other fields."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "fields@test.com", "password123", "Original Name", "teacher"
    )

    # Get user before update
    statement = select(User).where(User.email == "fields@test.com")
    user_before = session.exec(statement).first()
    original_email = user_before.email
    original_role = user_before.role
    original_id = user_before.id
    original_created_at = user_before.created_at

    # Update user name
    client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )

    # Get user after update
    session.expire_all()  # Refresh session
    user_after = session.exec(statement).first()

    # Name should change
    assert user_after.name == "New Name"

    # Other fields should NOT change
    assert user_after.email == original_email
    assert user_after.role == original_role
    assert user_after.id == original_id
    assert user_after.created_at == original_created_at


def test_update_current_user_no_token(client: TestClient):
    """Test updating user without authentication token."""
    response = client.put("/users/me", json={"name": "New Name"})

    assert response.status_code == 401
    assert "detail" in response.json()


def test_update_current_user_invalid_token(client: TestClient):
    """Test updating user with invalid token."""
    response = client.put(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
        json={"name": "New Name"},
    )

    assert response.status_code == 401
    assert "detail" in response.json()


def test_update_current_user_name_too_short(client: TestClient):
    """Test that empty name is rejected."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "short@test.com", "password123", "Valid Name", "student"
    )

    # Try to update with empty name
    response = client.put(
        "/users/me", headers={"Authorization": f"Bearer {token}"}, json={"name": ""}
    )

    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_update_current_user_name_too_long(client: TestClient):
    """Test that name longer than 100 characters is rejected."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "long@test.com", "password123", "Valid Name", "student"
    )

    # Try to update with 101 character name
    long_name = "a" * 101

    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": long_name},
    )

    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_update_current_user_idempotent(client: TestClient):
    """Test that updating with same name twice works (idempotent)."""
    # Create user and get token
    token = create_user_and_get_token(
        client, "idempotent@test.com", "password123", "Original", "student"
    )

    # Update name first time
    response1 = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )

    # Update name second time with same value
    response2 = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )

    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200

    # Both should return same name
    assert response1.json()["name"] == "New Name"
    assert response2.json()["name"] == "New Name"


# ============================================================================
# GET /users TESTS (LIST ALL USERS - TEACHER ONLY)
# ============================================================================


def test_get_all_users_as_teacher_success(client: TestClient):
    """Test that teacher can successfully list all users."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher User", "teacher"
    )

    # Create some students
    create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )

    # Teacher calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return StudentListResponse with all 3 users
    assert isinstance(data, dict)
    assert "students" in data
    assert "total_count" in data
    assert data["total_count"] == 3
    assert len(data["students"]) == 3


def test_get_all_users_as_student_forbidden(client: TestClient):
    """Test that student gets 403 Forbidden when trying to list users."""
    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student User", "student"
    )

    # Student calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {student_token}"}
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "permission" in data["detail"].lower()


def test_get_all_users_no_token(client: TestClient):
    """Test that GET /users without authentication returns 401."""
    response = client.get("/users")

    assert response.status_code == 401


def test_get_all_users_returns_multiple_users(client: TestClient):
    """Test that GET /users returns array with all user data."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher User", "teacher"
    )

    # Create multiple students
    create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )
    create_user_and_get_token(
        client, "student3@test.com", "password123", "Student Three", "student"
    )

    # Teacher calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return StudentListResponse with 4 users
    assert isinstance(data, dict)
    assert "students" in data
    assert "total_count" in data
    assert data["total_count"] == 4
    assert len(data["students"]) == 4

    # Each user should have required fields
    for user in data["students"]:
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "created_at" in user


def test_get_all_users_excludes_passwords(client: TestClient):
    """Test that GET /users does not include password fields."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher User", "teacher"
    )

    # Create student
    create_user_and_get_token(
        client, "student@test.com", "password123", "Student User", "student"
    )

    # Teacher calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # No user should have password or password_hash fields
    for user in data["students"]:
        assert "password" not in user
        assert "password_hash" not in user


# ============================================================================
# GET /users/{user_id} PERMISSION TESTS
# ============================================================================


def test_student_can_view_own_profile(client: TestClient):
    """Test that student can view their own profile by ID."""
    # Create student (will be user_id=1)
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student User", "student"
    )

    # Student views their own profile
    response = client.get(
        "/users/1", headers={"Authorization": f"Bearer {student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@test.com"
    assert data["name"] == "Student User"
    assert data["role"] == "student"


def test_student_cannot_view_other_user(client: TestClient):
    """Test that student gets 403 when trying to view another user."""
    # Create two students
    student1_token = create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )

    # Student1 tries to view Student2's profile
    response = client.get(
        "/users/2", headers={"Authorization": f"Bearer {student1_token}"}
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "permission" in data["detail"].lower()


def test_teacher_can_view_any_student(client: TestClient):
    """Test that teacher can view any student's profile."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher User", "teacher"
    )

    # Create student
    client.post(
        "/auth/register",
        json={
            "email": "student@test.com",
            "name": "Student User",
            "password": "password123",
            "role": "student",
        },
    )

    # Teacher views student's profile (user_id=2)
    response = client.get(
        "/users/2", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@test.com"
    assert data["name"] == "Student User"
    assert data["role"] == "student"


def test_teacher_can_view_another_teacher(client: TestClient):
    """Test that teacher can view another teacher's profile."""
    # Create two teachers
    teacher1_token = create_user_and_get_token(
        client, "teacher1@test.com", "password123", "Teacher One", "teacher"
    )
    client.post(
        "/auth/register",
        json={
            "email": "teacher2@test.com",
            "name": "Teacher Two",
            "password": "password123",
            "role": "teacher",
        },
    )

    # Teacher1 views Teacher2's profile
    response = client.get(
        "/users/2", headers={"Authorization": f"Bearer {teacher1_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "teacher2@test.com"
    assert data["role"] == "teacher"


def test_student_cannot_view_teacher(client: TestClient):
    """Test that student cannot view teacher's profile."""
    # Create teacher
    client.post(
        "/auth/register",
        json={
            "email": "teacher@test.com",
            "name": "Teacher User",
            "password": "password123",
            "role": "teacher",
        },
    )

    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student User", "student"
    )

    # Student tries to view teacher's profile (user_id=1)
    response = client.get(
        "/users/1", headers={"Authorization": f"Bearer {student_token}"}
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "permission" in data["detail"].lower()


# ============================================================================
# GET /users WITH FILTERS, SORTING, PAGINATION (NEW TESTS)
# ============================================================================


def test_list_users_with_pagination_default(client: TestClient):
    """Test GET /users with default pagination parameters."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create 3 students
    for i in range(1, 4):
        create_user_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}", "student"
        )

    # Call with no parameters (default: offset=0, limit=10)
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should have pagination structure
    assert "students" in data
    assert "total_count" in data
    assert "offset" in data
    assert "limit" in data

    # Should return 4 users (1 teacher + 3 students)
    assert data["total_count"] == 4
    assert len(data["students"]) == 4
    assert data["offset"] == 0
    assert data["limit"] == 10


def test_list_users_with_role_filter_student(client: TestClient):
    """Test GET /users with role=student filter."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create 3 students and 1 more teacher
    for i in range(1, 4):
        create_user_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}", "student"
        )

    create_user_and_get_token(
        client, "teacher2@test.com", "password123", "Teacher 2", "teacher"
    )

    # Filter by role=student
    response = client.get(
        "/users?role=student", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return students
    assert data["total_count"] == 3
    assert len(data["students"]) == 3
    for student in data["students"]:
        assert student["role"] == "student"


def test_list_users_with_role_filter_teacher(client: TestClient):
    """Test GET /users with role=teacher filter."""
    # Create 2 teachers
    teacher_token = create_user_and_get_token(
        client, "teacher1@test.com", "password123", "Teacher 1", "teacher"
    )
    create_user_and_get_token(
        client, "teacher2@test.com", "password123", "Teacher 2", "teacher"
    )

    # Create 2 students
    for i in range(1, 3):
        create_user_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}", "student"
        )

    # Filter by role=teacher
    response = client.get(
        "/users?role=teacher", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return teachers
    assert data["total_count"] == 2
    assert len(data["students"]) == 2
    for teacher in data["students"]:
        assert teacher["role"] == "teacher"


def test_list_users_sort_by_name(client: TestClient):
    """Test GET /users with sort=name parameter."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Alice", "teacher"
    )

    # Create students with specific names
    create_user_and_get_token(
        client, "charlie@test.com", "password123", "Charlie", "student"
    )
    create_user_and_get_token(client, "bob@test.com", "password123", "Bob", "student")

    # Sort by name
    response = client.get(
        "/users?sort=name", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should be sorted by name
    assert len(data["students"]) == 3
    names = [s["name"] for s in data["students"]]
    assert names == sorted(names)


def test_list_users_sort_by_points(client: TestClient):
    """Test GET /users with sort=points parameter."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create students
    student1_token = create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    student2_token = create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )

    # Student 1 completes 1 challenge (100 points)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student1_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )

    # Student 2 completes 2 challenges (250 points)
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student2_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 1,
            "query": "SELECT * FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student2_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )

    # Sort by points (descending)
    response = client.get(
        "/users?sort=points", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should be sorted by points descending
    students = data["students"]
    points = [s.get("total_points", 0) for s in students]
    # Student2 (250) should come before Student1 (100)
    assert points[0] >= points[1]


def test_list_users_sort_by_date(client: TestClient):
    """Test GET /users with sort=date parameter."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create students
    create_user_and_get_token(
        client, "student1@test.com", "password123", "Student One", "student"
    )
    create_user_and_get_token(
        client, "student2@test.com", "password123", "Student Two", "student"
    )

    # Sort by date (created_at ascending)
    response = client.get(
        "/users?sort=date", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should be sorted by created_at ascending
    students = data["students"]
    dates = [s["created_at"] for s in students]
    assert dates == sorted(dates)


def test_list_users_invalid_sort_parameter(client: TestClient):
    """Test GET /users with invalid sort parameter returns error."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Try with invalid sort parameter
    response = client.get(
        "/users?sort=invalid", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_list_users_pagination_offset(client: TestClient):
    """Test GET /users with offset parameter."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create 5 students
    for i in range(1, 6):
        create_user_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}", "student"
        )

    # Get second page (offset=2, limit=2)
    response = client.get(
        "/users?offset=2&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have pagination info
    assert data["total_count"] == 6  # 1 teacher + 5 students
    assert data["offset"] == 2
    assert data["limit"] == 2
    assert len(data["students"]) == 2


def test_list_users_pagination_limit_enforced(client: TestClient):
    """Test that limit parameter is enforced (max 1000)."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Try to use limit > 1000
    response = client.get(
        "/users?limit=2000",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    # Should return 422 Unprocessable Entity (validation error)
    assert response.status_code == 422


def test_list_users_pagination_total_count_accurate(client: TestClient):
    """Test that total_count is accurate regardless of pagination."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create 5 students
    for i in range(1, 6):
        create_user_and_get_token(
            client, f"student{i}@test.com", "password123", f"Student {i}", "student"
        )

    # Get first page (limit=2)
    response1 = client.get(
        "/users?limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    # Get second page (limit=2, offset=2)
    response2 = client.get(
        "/users?offset=2&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    # Both should report same total_count
    assert response1.json()["total_count"] == 6
    assert response2.json()["total_count"] == 6


def test_student_stats_total_points(client: TestClient):
    """Test that student stats include total_points earned."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Student completes 2 challenges
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
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Find student in list
    student = next(s for s in data["students"] if s["email"] == "student@test.com")
    assert "total_points" in student
    assert (
        student["total_points"] == 250
    )  # 100 + 150 points from challenges (1,1) and (1,2)


def test_student_stats_challenges_completed(client: TestClient):
    """Test that student stats include challenges_completed count."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Student completes 3 challenges
    for i in range(1, 4):
        client.post(
            "/progress/submit",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "unit_id": 1,
                "challenge_id": i,
                "query": "SELECT * FROM users"
                if i == 1
                else "SELECT name, email FROM users"
                if i == 2
                else "SELECT * FROM users WHERE age > 18",
                "hints_used": 0,
            },
        )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Find student in list
    student = next(s for s in data["students"] if s["email"] == "student@test.com")
    assert "challenges_completed" in student
    assert student["challenges_completed"] == 3


def test_student_stats_zero_when_no_progress(client: TestClient):
    """Test that student with no progress shows 0 stats."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student (no progress)
    create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Find student in list
    student = next(s for s in data["students"] if s["email"] == "student@test.com")
    assert student["total_points"] == 0
    assert student["challenges_completed"] == 0


def test_student_stats_multi_challenge_aggregation(client: TestClient):
    """Test that stats correctly aggregate multiple challenges."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Student completes 2 unit 1 challenges and 1 unit 2 challenge
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
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 1,
            "challenge_id": 2,
            "query": "SELECT name, email FROM users",
            "hints_used": 0,
        },
    )
    client.post(
        "/progress/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "unit_id": 2,
            "challenge_id": 1,
            "query": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
            "hints_used": 0,
        },
    )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Find student in list
    student = next(s for s in data["students"] if s["email"] == "student@test.com")
    assert student["total_points"] == 500  # 100 + 150 + 250 from (1,1), (1,2), (2,1)
    assert student["challenges_completed"] == 3


def test_list_users_response_structure(client: TestClient):
    """Test that response has correct structure with required fields."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student
    create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert isinstance(data, dict)
    assert "students" in data
    assert "total_count" in data
    assert "offset" in data
    assert "limit" in data

    # Check student fields
    assert isinstance(data["students"], list)
    for student in data["students"]:
        assert "id" in student
        assert "email" in student
        assert "name" in student
        assert "role" in student
        assert "created_at" in student
        assert "total_points" in student
        assert "challenges_completed" in student
        # Should not include password
        assert "password" not in student
        assert "password_hash" not in student


def test_list_users_response_field_types(client: TestClient):
    """Test that response fields have correct types."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Create student
    create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Get students list
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check types
    assert isinstance(data["students"], list)
    assert isinstance(data["total_count"], int)
    assert isinstance(data["offset"], int)
    assert isinstance(data["limit"], int)

    # Check student field types
    student = data["students"][0]
    assert isinstance(student["id"], int)
    assert isinstance(student["email"], str)
    assert isinstance(student["name"], str)
    assert isinstance(student["role"], str)
    assert isinstance(student["created_at"], str)  # ISO format string
    assert isinstance(student["total_points"], int)
    assert isinstance(student["challenges_completed"], int)


def test_list_users_teacher_can_access(client: TestClient):
    """Test that teacher can access the list students endpoint."""
    # Create teacher
    teacher_token = create_user_and_get_token(
        client, "teacher@test.com", "password123", "Teacher", "teacher"
    )

    # Teacher calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    assert "students" in response.json()


def test_list_users_student_forbidden(client: TestClient):
    """Test that student gets 403 when accessing the list students endpoint."""
    # Create student
    student_token = create_user_and_get_token(
        client, "student@test.com", "password123", "Student", "student"
    )

    # Student calls GET /users
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {student_token}"}
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "permission" in data["detail"].lower()
