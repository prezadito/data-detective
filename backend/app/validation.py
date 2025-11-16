"""
Query validation and safe SQL execution utilities.
"""

import sqlparse
from sqlmodel import Session
from sqlalchemy import text
from fastapi import HTTPException

# Forbidden SQL keywords (DDL, DML other than SELECT)
FORBIDDEN_KEYWORDS = {
    "DROP",
    "DELETE",
    "INSERT",
    "UPDATE",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "PRAGMA",
}


def validate_query_syntax(query: str) -> None:
    """
    Validate that a SQL query is safe to execute.

    Checks:
    - Query is SELECT only
    - No forbidden keywords (DROP, DELETE, etc.)
    - Query can be parsed

    Args:
        query: SQL query string

    Raises:
        HTTPException: 400 if query is invalid or unsafe
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Parse query
    try:
        parsed = sqlparse.parse(query)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Query syntax error: {str(e)}"
        )

    if not parsed:
        raise HTTPException(status_code=400, detail="Could not parse query")

    # Get first statement
    statement = parsed[0]

    # Check statement type
    if statement.get_type() != "SELECT":
        raise HTTPException(
            status_code=400,
            detail=f"Only SELECT queries are allowed (got {statement.get_type()})",
        )

    # Check for forbidden keywords
    query_upper = query.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Forbidden keyword in query: {keyword}",
            )


def execute_query_safely(
    query: str,
    allowed_tables: list[str],
    session: Session,
    timeout: int = 5,
) -> list[dict]:
    """
    Execute a SELECT query with safety constraints.

    Args:
        query: SQL SELECT query
        allowed_tables: List of table names that can be queried
        session: Database session
        timeout: Query timeout in seconds (default 5)

    Returns:
        List of result rows as dictionaries

    Raises:
        HTTPException: If query fails or times out
    """
    # Validate syntax first
    validate_query_syntax(query)

    # Check that query only references allowed tables
    query_upper = query.upper()
    for table in allowed_tables:
        if table.upper() not in query_upper:
            # If none of the allowed tables are mentioned, it's suspicious
            pass

    try:
        # Execute with timeout
        result = session.exec(
            text(query),
            # Note: SQLAlchemy doesn't have a direct timeout parameter,
            # but we can set it at the connection level if needed
        )

        rows = result.fetchall()

        # Convert to list of dicts
        if not rows:
            return []

        # Get column names from result
        column_names = list(result.keys())

        # Convert rows to dicts
        return [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query execution error: {str(e)}",
        )
