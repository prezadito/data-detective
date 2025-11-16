/**
 * Hardcoded hints for challenges
 * Matches backend CHALLENGES dict in app/challenges.py
 *
 * TODO: Move this to backend and include in ChallengeDetail response
 * Last updated: 2025-11-16
 *
 * Key format: "unitId-challengeId"
 * Value: [hint1, hint2, hint3]
 */

type HintKey = `${number}-${number}`;

export const CHALLENGE_HINTS: Record<HintKey, [string, string, string]> = {
  // Unit 1: SELECT Basics
  '1-1': [
    'Use the SELECT keyword to choose columns',
    'The asterisk (*) means "all columns"',
    'Try: SELECT * FROM users',
  ],
  '1-2': [
    'List the column names separated by commas',
    'Column names come after SELECT and before FROM',
    'Try: SELECT name, email FROM users',
  ],
  '1-3': [
    'Use the WHERE clause to filter rows',
    'The greater than operator is >',
    'Try: SELECT * FROM users WHERE age > 18',
  ],

  // Unit 2: JOINs
  '2-1': [
    'Use INNER JOIN to combine two tables',
    'The ON keyword specifies how tables are related',
    'Try: SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id',
  ],
  '2-2': [
    'LEFT JOIN shows all rows from the left table',
    'Rows without matches get NULL values',
    'Try: SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id',
  ],

  // Unit 3: Aggregations
  '3-1': [
    'COUNT(*) counts all rows',
    'Aggregate functions return a single value',
    'Try: SELECT COUNT(*) FROM users',
  ],
  '3-2': [
    'GROUP BY groups rows with the same values',
    'Use it with aggregate functions like COUNT',
    'Try: SELECT role, COUNT(*) FROM users GROUP BY role',
  ],
};

/**
 * Get hints for a challenge
 * Returns default hints if challenge not found
 */
export function getChallengeHints(
  unitId: number,
  challengeId: number
): [string, string, string] {
  const key: HintKey = `${unitId}-${challengeId}`;
  return (
    CHALLENGE_HINTS[key] || [
      'No hint available',
      'No hint available',
      'No hint available',
    ]
  );
}
