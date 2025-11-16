import initSqlJs from 'sql.js';
import type { Database, QueryResult, DatabaseError } from '@/types/database';

/**
 * Schema SQL for creating tables
 */
const SCHEMA_SQL = `
-- Movies table
CREATE TABLE IF NOT EXISTS movies (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  genre TEXT,
  release_year INTEGER,
  rating REAL
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  grade INTEGER,
  gpa REAL,
  favorite_subject TEXT
);

-- Video games table
CREATE TABLE IF NOT EXISTS video_games (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  platform TEXT,
  genre TEXT,
  release_year INTEGER,
  price REAL
);
`;

/**
 * Sample data for movies table
 */
const MOVIES_DATA = `
INSERT INTO movies (id, title, genre, release_year, rating) VALUES
  (1, 'The Shawshank Redemption', 'Drama', 1994, 9.3),
  (2, 'The Dark Knight', 'Action', 2008, 9.0),
  (3, 'Inception', 'Sci-Fi', 2010, 8.8),
  (4, 'Pulp Fiction', 'Crime', 1994, 8.9),
  (5, 'Forrest Gump', 'Drama', 1994, 8.8),
  (6, 'The Matrix', 'Sci-Fi', 1999, 8.7),
  (7, 'Goodfellas', 'Crime', 1990, 8.7),
  (8, 'The Silence of the Lambs', 'Thriller', 1991, 8.6),
  (9, 'Interstellar', 'Sci-Fi', 2014, 8.6),
  (10, 'The Green Mile', 'Drama', 1999, 8.6);
`;

/**
 * Sample data for students table
 */
const STUDENTS_DATA = `
INSERT INTO students (id, name, grade, gpa, favorite_subject) VALUES
  (1, 'Emma Johnson', 6, 3.9, 'Math'),
  (2, 'Liam Smith', 7, 3.7, 'Science'),
  (3, 'Olivia Brown', 5, 3.8, 'English'),
  (4, 'Noah Davis', 8, 3.6, 'History'),
  (5, 'Ava Wilson', 6, 4.0, 'Math'),
  (6, 'Ethan Martinez', 7, 3.5, 'Art'),
  (7, 'Sophia Garcia', 5, 3.9, 'Science'),
  (8, 'Mason Anderson', 8, 3.8, 'Math'),
  (9, 'Isabella Taylor', 6, 3.7, 'English'),
  (10, 'Lucas Thomas', 7, 3.6, 'Science');
`;

/**
 * Sample data for video_games table
 */
const VIDEO_GAMES_DATA = `
INSERT INTO video_games (id, title, platform, genre, release_year, price) VALUES
  (1, 'The Legend of Zelda: Breath of the Wild', 'Nintendo Switch', 'Adventure', 2017, 59.99),
  (2, 'God of War', 'PlayStation 5', 'Action', 2018, 49.99),
  (3, 'Elden Ring', 'PC', 'RPG', 2022, 59.99),
  (4, 'Halo Infinite', 'Xbox Series X', 'Shooter', 2021, 59.99),
  (5, 'Animal Crossing: New Horizons', 'Nintendo Switch', 'Simulation', 2020, 59.99),
  (6, 'Spider-Man: Miles Morales', 'PlayStation 5', 'Action', 2020, 49.99),
  (7, 'Minecraft', 'PC', 'Sandbox', 2011, 26.95),
  (8, 'Forza Horizon 5', 'Xbox Series X', 'Racing', 2021, 59.99),
  (9, 'Super Mario Odyssey', 'Nintendo Switch', 'Platformer', 2017, 59.99),
  (10, 'Cyberpunk 2077', 'PC', 'RPG', 2020, 29.99);
`;

/**
 * Initialize sql.js and create a new in-memory database
 */
export async function initializeDatabase(): Promise<Database> {
  try {
    // Initialize sql.js with wasm file from public directory
    const SQL = await initSqlJs({
      locateFile: (file: string) => `/${file}`,
    });

    // Create new in-memory database
    const db = new SQL.Database();

    // Load schema and sample data
    loadSchema(db);

    return db;
  } catch (error) {
    const dbError: DatabaseError = {
      message: 'Failed to initialize database',
      originalError: error,
    };
    throw dbError;
  }
}

/**
 * Load database schema and sample data
 */
function loadSchema(db: Database): void {
  try {
    // Create tables
    db.run(SCHEMA_SQL);

    // Insert sample data
    db.run(MOVIES_DATA);
    db.run(STUDENTS_DATA);
    db.run(VIDEO_GAMES_DATA);
  } catch (error) {
    const dbError: DatabaseError = {
      message: 'Failed to load database schema',
      originalError: error,
    };
    throw dbError;
  }
}

/**
 * Execute a SQL query and return results
 *
 * @param db - Database instance
 * @param query - SQL query to execute
 * @returns Query results with columns and values
 */
export function executeQuery(db: Database, query: string): QueryResult {
  try {
    // Execute query
    const results = db.exec(query);

    // If no results, return empty result
    if (results.length === 0) {
      return {
        columns: [],
        values: [],
        rowCount: 0,
      };
    }

    // Get first result set (most queries return single result set)
    const result = results[0];

    return {
      columns: result.columns,
      values: result.values,
      rowCount: result.values.length,
    };
  } catch (error) {
    const dbError: DatabaseError = {
      message: error instanceof Error ? error.message : 'Unknown database error',
      query,
      originalError: error,
    };
    throw dbError;
  }
}

/**
 * Check if a query is a SELECT statement (read-only)
 *
 * @param query - SQL query to check
 * @returns True if query is a SELECT statement
 */
export function isSelectQuery(query: string): boolean {
  const trimmed = query.trim().toLowerCase();
  return trimmed.startsWith('select');
}

/**
 * Sanitize query by removing comments and extra whitespace
 *
 * @param query - SQL query to sanitize
 * @returns Sanitized query
 */
export function sanitizeQuery(query: string): string {
  return query
    .replace(/--.*$/gm, '') // Remove single-line comments
    .replace(/\/\*[\s\S]*?\*\//g, '') // Remove multi-line comments
    .trim();
}
