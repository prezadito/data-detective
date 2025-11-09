"""
Hardcoded challenge definitions for MVP.
In production, these would come from a database.
"""

from typing import Optional, Dict, Tuple, Any

# Dictionary of challenges
# Key: (unit_id, challenge_id)
# Value: {title, points, description}
CHALLENGES: Dict[Tuple[int, int], Dict[str, Any]] = {
    # Unit 1: SELECT Basics
    (1, 1): {
        "title": "SELECT All Columns",
        "points": 100,
        "description": "Write a SELECT statement to get all columns from the users table",
    },
    (1, 2): {
        "title": "SELECT Specific Columns",
        "points": 150,
        "description": "Select only name and email from users",
    },
    (1, 3): {
        "title": "WHERE Clause",
        "points": 200,
        "description": "Filter users where age > 18",
    },
    # Unit 2: JOINs
    (2, 1): {
        "title": "INNER JOIN",
        "points": 250,
        "description": "Join users and orders tables",
    },
    (2, 2): {
        "title": "LEFT JOIN",
        "points": 300,
        "description": "Show all users and their orders (if any)",
    },
    # Unit 3: Aggregations
    (3, 1): {
        "title": "COUNT Function",
        "points": 200,
        "description": "Count total number of users",
    },
    (3, 2): {
        "title": "GROUP BY",
        "points": 350,
        "description": "Count users by role",
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
