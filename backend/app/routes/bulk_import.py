"""
Bulk student import routes - CSV file upload for teachers.
"""

import csv
import secrets
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.auth import get_current_user, require_teacher, hash_password
from app.schemas import BulkImportResponse, BulkImportError, ImportedStudent
from pydantic import ValidationError


router = APIRouter(prefix="/import", tags=["Import"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _validate_csv_headers(fieldnames: list[str]) -> None:
    """
    Validate that CSV has required columns.

    Args:
        fieldnames: List of column names from CSV header

    Raises:
        HTTPException: 400 if required columns missing
    """
    required = {"email", "name"}
    provided = set(fieldnames) if fieldnames else set()

    missing = required - provided

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(missing)}",
        )


def _generate_password() -> str:
    """
    Generate a secure random password.

    Returns:
        Random password string (16+ characters)
    """
    return secrets.token_urlsafe(16)


def _check_existing_email(email: str, session: Session) -> bool:
    """
    Check if email already exists in database.

    Args:
        email: Email to check
        session: Database session

    Returns:
        True if email exists, False otherwise
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    return user is not None


# ============================================================================
# API ENDPOINT
# ============================================================================


@router.post("/students", response_model=BulkImportResponse, status_code=200)
async def import_students(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Import multiple students from a CSV file (teachers only).

    CSV file should contain two columns:
    - email: Student email address (required, must be valid email)
    - name: Student name (required, 1-100 characters)

    The endpoint will:
    1. Parse the CSV file
    2. Validate each row
    3. Check for duplicate emails (in file and in database)
    4. Generate random temporary passwords for each new student
    5. Hash passwords with bcrypt
    6. Create student accounts
    7. Return detailed report with success count, errors, and generated passwords

    Duplicate emails and validation errors are reported but don't fail the entire import.

    Args:
        file: CSV file uploaded by teacher
        current_user: Authenticated user (must be teacher)
        _: Teacher role check (dependency)
        session: Database session

    Returns:
        BulkImportResponse with summary and detailed results

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if not a teacher
        HTTPException: 400 if file is empty or missing required columns
    """
    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Parse CSV
    try:
        text_content = content.decode("utf-8")
        csv_file = StringIO(text_content)
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None or not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Validate headers
        _validate_csv_headers(list(reader.fieldnames))

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    # Process rows
    imported_students = []
    errors = []
    seen_emails = set()
    users_to_create = []

    for row_num, row in enumerate(reader, start=2):  # start=2 (skip header)
        email = row.get("email", "").strip()
        name = row.get("name", "").strip()

        try:
            # Validate email and name using Pydantic
            from app.schemas import StudentImportRow

            validated_row = StudentImportRow(email=email, name=name)

            # Check for duplicate in current file
            if validated_row.email in seen_emails:
                errors.append(
                    BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error="Duplicate email in file (already processed above)",
                    )
                )
                continue

            seen_emails.add(validated_row.email)

            # Check for existing email in database
            if _check_existing_email(validated_row.email, session):
                errors.append(
                    BulkImportError(
                        row_number=row_num,
                        email=validated_row.email,
                        error="Email already exists in database",
                    )
                )
                continue

            # Generate password and hash it
            plain_password = _generate_password()
            password_hash = hash_password(plain_password)

            # Create user object (but don't add to session yet)
            user = User(
                email=validated_row.email,
                name=validated_row.name,
                password_hash=password_hash,
                role="student",
            )

            users_to_create.append(user)
            imported_students.append(
                ImportedStudent(
                    email=validated_row.email,
                    name=validated_row.name,
                    temporary_password=plain_password,
                )
            )

        except ValidationError as e:
            # Extract first error message
            error_msg = "Invalid data"
            if e.errors():
                first_error = e.errors()[0]
                field = first_error.get("loc", [None])[0] or "unknown"
                error_msg = (
                    f"Invalid {field}: {first_error.get('msg', 'Invalid value')}"
                )

            errors.append(
                BulkImportError(
                    row_number=row_num, email=email if email else None, error=error_msg
                )
            )

    # Commit all users at once
    if users_to_create:
        try:
            session.add_all(users_to_create)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Database error during import: {str(e)}",
            )

    # Build response
    # Count skipped as any duplicate-related errors (in file or in database)
    skipped_errors = [
        e
        for e in errors
        if "already exists" in e.error.lower() or "duplicate" in e.error.lower()
    ]
    failed_errors = [
        e
        for e in errors
        if "already exists" not in e.error.lower()
        and "duplicate" not in e.error.lower()
    ]

    return BulkImportResponse(
        message=f"Import completed: {len(imported_students)} students imported successfully",
        successful=len(imported_students),
        skipped=len(skipped_errors),
        failed=len(failed_errors),
        imported_students=imported_students,
        errors=errors,
    )
