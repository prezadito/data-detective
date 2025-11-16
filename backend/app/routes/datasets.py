"""
Dataset routes - CSV upload and management for teachers.
"""

import json
import re
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlmodel import Session, select, func, text
from datetime import datetime

from app.database import get_session
from app.models import Dataset, CustomChallenge, User
from app.auth import get_current_user, require_teacher
from app.schemas import (
    DatasetResponse,
    DatasetListResponse,
    DatasetListItem,
    DatasetDetailResponse,
    DatasetSchema,
    ColumnSchema,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])

# ============================================================================
# CONSTANTS
# ============================================================================

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_ROWS = 10_000
MAX_COLUMNS = 50
MIN_COLUMNS = 1

# SQL keywords to block as column names
SQL_KEYWORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TABLE",
    "INDEX",
    "VIEW",
    "PROCEDURE",
    "FUNCTION",
    "TRIGGER",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def sanitize_identifier(name: str) -> str:
    """
    Sanitize table/column name to prevent SQL injection.

    Args:
        name: Identifier to sanitize

    Returns:
        Sanitized name

    Raises:
        ValueError: If name is invalid
    """
    # Must start with letter or underscore, contain only alphanumeric and underscore
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid identifier '{name}': must start with letter/underscore "
            f"and contain only alphanumeric characters and underscores"
        )

    # Check length
    if len(name) > 64:
        raise ValueError(f"Identifier '{name}' too long (max 64 characters)")

    # Block SQL keywords
    if name.upper() in SQL_KEYWORDS:
        raise ValueError(f"Identifier '{name}' is a reserved SQL keyword")

    return name


def infer_column_type(series: pd.Series) -> str:
    """
    Infer SQLite column type from pandas Series.

    Args:
        series: Pandas Series

    Returns:
        SQLite type name: INTEGER, REAL, or TEXT
    """
    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(series):
        return "REAL"
    else:
        return "TEXT"


def create_table_from_dataframe(
    table_name: str, df: pd.DataFrame, session: Session
) -> dict:
    """
    Create a table from a pandas DataFrame.

    Args:
        table_name: Name of table to create
        df: DataFrame with data
        session: Database session

    Returns:
        Dictionary with schema information

    Raises:
        ValueError: If table creation fails
    """
    # Sanitize table name
    table_name = sanitize_identifier(table_name)

    # Build schema
    columns = []
    for col_name in df.columns:
        sanitized_name = sanitize_identifier(col_name)
        col_type = infer_column_type(df[col_name])
        columns.append({"name": sanitized_name, "type": col_type})

    # Build CREATE TABLE statement
    column_defs = [f"{col['name']} {col['type']}" for col in columns]
    create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"

    # Execute CREATE TABLE
    session.exec(text(create_sql))
    session.commit()

    # Insert data using pandas to_sql
    # Use the session's connection/engine
    connection = session.connection()
    df.to_sql(table_name, connection, if_exists="append", index=False)

    return {"columns": columns}


def parse_csv_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Parse CSV file content into a DataFrame.

    Args:
        file_content: Raw file bytes
        filename: Original filename

    Returns:
        Parsed DataFrame

    Raises:
        HTTPException: If parsing fails
    """
    try:
        # Try to decode as UTF-8
        text_content = file_content.decode("utf-8")

        # Parse CSV with pandas
        df = pd.read_csv(
            pd.io.common.StringIO(text_content),
            keep_default_na=False,  # Treat empty strings as empty, not NaN
        )

        # Validate row count
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="CSV file is empty (no data rows)")

        if len(df) > MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"CSV file has too many rows ({len(df)}). Maximum is {MAX_ROWS}.",
            )

        # Validate column count
        if len(df.columns) < MIN_COLUMNS:
            raise HTTPException(
                status_code=400,
                detail=f"CSV must have at least {MIN_COLUMNS} column",
            )

        if len(df.columns) > MAX_COLUMNS:
            raise HTTPException(
                status_code=400,
                detail=f"CSV has too many columns ({len(df.columns)}). Maximum is {MAX_COLUMNS}.",
            )

        # Validate column names
        for col in df.columns:
            try:
                sanitize_identifier(str(col))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid column name: {str(e)}",
                )

        return df

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File must be UTF-8 encoded CSV file"
        )
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error reading CSV file: {str(e)}"
        )


def verify_dataset_ownership(
    dataset_id: int, teacher_id: int, session: Session
) -> Dataset:
    """
    Verify that a dataset exists and belongs to the teacher.

    Args:
        dataset_id: Dataset ID
        teacher_id: Teacher user ID
        session: Database session

    Returns:
        Dataset object

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.teacher_id != teacher_id:
        raise HTTPException(
            status_code=403, detail="Access denied: you do not own this dataset"
        )
    return dataset


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Upload a CSV file and create a dataset (teachers only).

    The endpoint will:
    1. Validate file size and format
    2. Parse CSV and infer column types
    3. Create dataset record in database
    4. Create dynamic table with data
    5. Return dataset metadata with schema

    Args:
        file: CSV file (max 5MB, max 10K rows)
        name: User-friendly dataset name
        description: Optional description
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Created dataset with schema

    Raises:
        HTTPException: 400 if validation fails, 413 if file too large
    """
    # Validate filename
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file (.csv)")

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes). Maximum is {MAX_FILE_SIZE} bytes (5MB).",
        )

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse CSV
    df = parse_csv_file(content, file.filename)

    # Create dataset record first (to get auto-generated ID)
    dataset = Dataset(
        teacher_id=current_user.id,
        name=name,
        description=description,
        original_filename=file.filename,
        table_name="",  # Will update after we have ID
        row_count=len(df),
        schema_json="{}",  # Will update after table creation
    )

    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    # Generate table name based on ID
    table_name = f"dataset_{dataset.id}"

    try:
        # Create table and insert data
        schema = create_table_from_dataframe(table_name, df, session)

        # Update dataset with table name and schema
        dataset.table_name = table_name
        dataset.schema_json = json.dumps(schema)
        session.add(dataset)
        session.commit()
        session.refresh(dataset)

    except Exception as e:
        # If table creation fails, rollback and delete dataset record
        session.rollback()
        session.delete(dataset)
        session.commit()
        raise HTTPException(
            status_code=400, detail=f"Failed to create dataset table: {str(e)}"
        )

    # Build response
    schema_obj = DatasetSchema(**json.loads(dataset.schema_json))

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        original_filename=dataset.original_filename,
        table_name=dataset.table_name,
        row_count=dataset.row_count,
        schema=schema_obj,
        created_at=dataset.created_at,
    )


@router.get("", response_model=DatasetListResponse)
def get_datasets(
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get list of datasets created by current teacher.

    Args:
        offset: Pagination offset (default 0)
        limit: Pagination limit (default 50, max 100)
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Paginated list of datasets with challenge counts
    """
    # Limit pagination
    limit = min(limit, 100)

    # Query datasets owned by teacher
    statement = (
        select(Dataset)
        .where(Dataset.teacher_id == current_user.id)
        .offset(offset)
        .limit(limit)
        .order_by(Dataset.created_at.desc())
    )

    datasets = session.exec(statement).all()

    # Get total count
    count_statement = select(func.count()).select_from(Dataset).where(
        Dataset.teacher_id == current_user.id
    )
    total = session.exec(count_statement).one()

    # Build response with challenge counts
    dataset_items = []
    for dataset in datasets:
        # Count challenges using this dataset
        challenge_count_statement = select(func.count()).select_from(
            CustomChallenge
        ).where(CustomChallenge.dataset_id == dataset.id)
        challenge_count = session.exec(challenge_count_statement).one()

        dataset_items.append(
            DatasetListItem(
                id=dataset.id,
                name=dataset.name,
                description=dataset.description,
                row_count=dataset.row_count,
                table_name=dataset.table_name,
                challenge_count=challenge_count,
                created_at=dataset.created_at,
            )
        )

    return DatasetListResponse(total=total, datasets=dataset_items)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_detail(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Get detailed dataset information including sample data.

    Args:
        dataset_id: Dataset ID
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Dataset details with schema and first 10 rows

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    # Verify ownership
    dataset = verify_dataset_ownership(dataset_id, current_user.id, session)

    # Parse schema
    schema_obj = DatasetSchema(**json.loads(dataset.schema_json))

    # Get sample data (first 10 rows)
    try:
        sample_statement = text(f"SELECT * FROM {dataset.table_name} LIMIT 10")
        result = session.exec(sample_statement)
        rows = result.fetchall()

        # Convert to list of dicts
        column_names = [col.name for col in schema_obj.columns]
        sample_data = [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching sample data: {str(e)}"
        )

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        table_name=dataset.table_name,
        row_count=dataset.row_count,
        schema=schema_obj,
        sample_data=sample_data,
        created_at=dataset.created_at,
    )


@router.delete("/{dataset_id}", status_code=200)
def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_teacher),
    session: Session = Depends(get_session),
):
    """
    Delete a dataset and its associated table.

    Also deletes any custom challenges that use this dataset.

    Args:
        dataset_id: Dataset ID
        current_user: Authenticated teacher
        session: Database session

    Returns:
        Success message with counts

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    # Verify ownership
    dataset = verify_dataset_ownership(dataset_id, current_user.id, session)

    # Count associated challenges
    challenge_count_statement = select(func.count()).select_from(
        CustomChallenge
    ).where(CustomChallenge.dataset_id == dataset_id)
    challenge_count = session.exec(challenge_count_statement).one()

    try:
        # Delete associated challenges first (if any)
        if challenge_count > 0:
            delete_challenges_statement = select(CustomChallenge).where(
                CustomChallenge.dataset_id == dataset_id
            )
            challenges = session.exec(delete_challenges_statement).all()
            for challenge in challenges:
                session.delete(challenge)

        # Drop the dynamic table
        drop_statement = text(f"DROP TABLE IF EXISTS {dataset.table_name}")
        session.exec(drop_statement)

        # Delete dataset record
        session.delete(dataset)
        session.commit()

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting dataset: {str(e)}"
        )

    return {
        "message": f"Dataset deleted successfully (removed {challenge_count} associated challenge(s))"
    }
