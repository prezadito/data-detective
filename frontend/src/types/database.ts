import type { Database as SqlJsDatabase } from 'sql.js';

/**
 * sql.js Database instance type
 */
export type Database = SqlJsDatabase;

/**
 * Result from executing a SQL query
 */
export interface QueryResult {
  /**
   * Column names in the result set
   */
  columns: string[];

  /**
   * Result rows (array of arrays)
   */
  values: unknown[][];

  /**
   * Number of rows returned
   */
  rowCount: number;
}

/**
 * Database error with context
 */
export interface DatabaseError {
  /**
   * Error message
   */
  message: string;

  /**
   * SQL query that caused the error (if available)
   */
  query?: string;

  /**
   * Original error object
   */
  originalError?: unknown;
}

/**
 * Query history entry
 */
export interface QueryHistoryEntry {
  /**
   * Unique ID for this query execution
   */
  id: string;

  /**
   * SQL query that was executed
   */
  query: string;

  /**
   * Timestamp when query was executed
   */
  timestamp: Date;

  /**
   * Whether the query executed successfully
   */
  success: boolean;

  /**
   * Error message if query failed
   */
  error?: string;

  /**
   * Number of rows returned (if successful)
   */
  rowCount?: number;

  /**
   * Execution time in milliseconds
   */
  executionTime?: number;
}

/**
 * Movie table row
 */
export interface Movie {
  id: number;
  title: string;
  genre: string;
  release_year: number;
  rating: number;
}

/**
 * Student table row
 */
export interface Student {
  id: number;
  name: string;
  grade: number;
  gpa: number;
  favorite_subject: string;
}

/**
 * Video game table row
 */
export interface VideoGame {
  id: number;
  title: string;
  platform: string;
  genre: string;
  release_year: number;
  price: number;
}
