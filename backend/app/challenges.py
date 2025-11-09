"""
Hardcoded challenge definitions for MVP.
In production, these would come from a database.
"""

from typing import Optional, Dict, Tuple, Any
import re

# Dictionary of challenges
# Key: (unit_id, challenge_id)
# Value: {title, points, description, sample_solution}
CHALLENGES: Dict[Tuple[int, int], Dict[str, Any]] = {
    # Unit 1: SELECT Basics
    (1, 1): {
        "title": "SELECT All Columns",
        "points": 100,
        "description": "Write a SELECT statement to get all columns from the users table",
        "sample_solution": "SELECT * FROM users",
    },
    (1, 2): {
        "title": "SELECT Specific Columns",
        "points": 150,
        "description": "Select only name and email from users",
        "sample_solution": "SELECT name, email FROM users",
    },
    (1, 3): {
        "title": "WHERE Clause",
        "points": 200,
        "description": "Filter users where age > 18",
        "sample_solution": "SELECT * FROM users WHERE age > 18",
    },
    # Unit 2: JOINs
    (2, 1): {
        "title": "INNER JOIN",
        "points": 250,
        "description": "Join users and orders tables",
        "sample_solution": "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id",
    },
    (2, 2): {
        "title": "LEFT JOIN",
        "points": 300,
        "description": "Show all users and their orders (if any)",
        "sample_solution": "SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id",
    },
    # Unit 3: Aggregations
    (3, 1): {
        "title": "COUNT Function",
        "points": 200,
        "description": "Count total number of users",
        "sample_solution": "SELECT COUNT(*) FROM users",
    },
    (3, 2): {
        "title": "GROUP BY",
        "points": 350,
        "description": "Count users by role",
        "sample_solution": "SELECT role, COUNT(*) FROM users GROUP BY role",
    },
}


def get_challenge(unit_id: int, challenge_id: int) -> Optional[Dict[str, Any]]:
    """
    Get challenge definition by unit_id and challenge_id.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID within the unit

    Returns:
        Challenge definition dict or None if not found
    """
    return CHALLENGES.get((unit_id, challenge_id))


def challenge_exists(unit_id: int, challenge_id: int) -> bool:
    """
    Check if a challenge exists.

    Args:
        unit_id: Unit ID
        challenge_id: Challenge ID

    Returns:
        True if challenge exists, False otherwise
    """
    return (unit_id, challenge_id) in CHALLENGES


def normalize_query(query: str) -> str:
    """
    Normalize SQL query for comparison.

    Performs:
    - Convert to lowercase
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space
    - Remove comments (-- and /* */)

    Args:
        query: SQL query string

    Returns:
        Normalized query string
    """
    # Convert to lowercase
    query = query.lower()

    # Remove single-line comments (-- ...)
    query = re.sub(r"--.*?$", "", query, flags=re.MULTILINE)

    # Remove multi-line comments (/* ... */)
    query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

    # Strip leading/trailing whitespace
    query = query.strip()

    # Collapse multiple spaces/newlines to single space
    query = re.sub(r"\s+", " ", query)

    return query


def validate_query(student_query: str, expected_query: str) -> bool:
    """
    Validate student query against expected query.

    Normalizes both queries and compares them.

    Args:
        student_query: Student's submitted SQL query
        expected_query: Expected/sample solution query

    Returns:
        True if queries match (after normalization), False otherwise
    """
    normalized_student = normalize_query(student_query)
    normalized_expected = normalize_query(expected_query)
    return normalized_student == normalized_expected
