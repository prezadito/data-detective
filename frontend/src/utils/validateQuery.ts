import type { QueryResult } from '@/types/database';

/**
 * Validation result with success flag and message
 */
export interface ValidationResult {
  isValid: boolean;
  message: string;
}

/**
 * Compare two query results for equality
 * Validates that student query produces same output as expected query
 *
 * @param studentResult - Result from student's query execution
 * @param expectedResult - Expected result from correct query
 * @returns Validation result with success flag and descriptive message
 */
export function validateQueryResults(
  studentResult: QueryResult,
  expectedResult: QueryResult
): ValidationResult {
  // Check if column count matches
  if (studentResult.columns.length !== expectedResult.columns.length) {
    return {
      isValid: false,
      message: `Column count mismatch. Expected ${expectedResult.columns.length} columns, got ${studentResult.columns.length}.`,
    };
  }

  // Check if column names match (case-sensitive)
  for (let i = 0; i < expectedResult.columns.length; i++) {
    if (studentResult.columns[i] !== expectedResult.columns[i]) {
      return {
        isValid: false,
        message: `Column name mismatch at position ${i + 1}. Expected "${expectedResult.columns[i]}", got "${studentResult.columns[i]}".`,
      };
    }
  }

  // Check if row count matches
  if (studentResult.rowCount !== expectedResult.rowCount) {
    return {
      isValid: false,
      message: `Row count mismatch. Expected ${expectedResult.rowCount} rows, got ${studentResult.rowCount}.`,
    };
  }

  // Check if values match (order-sensitive)
  for (let rowIndex = 0; rowIndex < expectedResult.values.length; rowIndex++) {
    const studentRow = studentResult.values[rowIndex];
    const expectedRow = expectedResult.values[rowIndex];

    for (let colIndex = 0; colIndex < expectedRow.length; colIndex++) {
      const studentValue = studentRow[colIndex];
      const expectedValue = expectedRow[colIndex];

      // Handle null comparison
      if (studentValue === null && expectedValue === null) {
        continue;
      }

      if (studentValue === null || expectedValue === null) {
        return {
          isValid: false,
          message: `Value mismatch at row ${rowIndex + 1}, column ${colIndex + 1}. Expected "${expectedValue}", got "${studentValue}".`,
        };
      }

      // Compare values with type coercion (numbers vs strings)
      // eslint-disable-next-line eqeqeq
      if (studentValue != expectedValue) {
        return {
          isValid: false,
          message: `Value mismatch at row ${rowIndex + 1}, column ${colIndex + 1}. Expected "${expectedValue}", got "${studentValue}".`,
        };
      }
    }
  }

  // All checks passed
  return {
    isValid: true,
    message: 'Query results match expected output!',
  };
}

/**
 * Check if a query result is empty (no rows returned)
 *
 * @param result - Query result to check
 * @returns True if result has no rows
 */
export function isEmptyResult(result: QueryResult): boolean {
  return result.rowCount === 0;
}
