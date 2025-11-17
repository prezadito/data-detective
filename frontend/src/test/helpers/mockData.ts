/**
 * Mock data for tests
 * Reusable mock objects to keep tests DRY
 */

import type {
  User,
  LoginCredentials,
  RegisterData,
  ChallengeDetail,
  ProgressResponse,
} from '@/types';
import type { QueryResult } from '@/types/database';

export const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  role: 'student',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockTeacher: User = {
  id: 2,
  email: 'teacher@example.com',
  name: 'Test Teacher',
  role: 'teacher',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockLoginCredentials: LoginCredentials = {
  email: 'test@example.com',
  password: 'password123',
};

export const mockRegisterData: RegisterData = {
  email: 'newuser@example.com',
  name: 'New User',
  password: 'password123',
  role: 'student',
};

export const mockQueryResult: QueryResult = {
  columns: ['id', 'name', 'email'],
  values: [
    [1, 'Alice', 'alice@example.com'],
    [2, 'Bob', 'bob@example.com'],
    [3, 'Charlie', 'charlie@example.com'],
  ],
  rowCount: 3,
};

export const mockEmptyQueryResult: QueryResult = {
  columns: ['id', 'name'],
  values: [],
  rowCount: 0,
};

export const mockProgressResponse: ProgressResponse = {
  id: 1,
  user_id: 1,
  unit_id: 1,
  challenge_id: 1,
  points_earned: 100,
  hints_used: 0,
  query: 'SELECT * FROM users',
  completed_at: '2024-01-15T12:00:00Z',
};

export const mockChallengeDetail: ChallengeDetail = {
  unit_id: 1,
  challenge_id: 1,
  title: 'SELECT All Columns',
  description: 'Write a query to select all columns from the users table.',
  points: 100,
  sample_solution: 'SELECT * FROM users',
  completion_rate: 75.5,
  avg_attempts: 2.3,
  total_attempts: 100,
  success_count: 75,
};

export const mockChallengeWithHints: ChallengeDetail = {
  ...mockChallengeDetail,
  unit_id: 1,
  challenge_id: 2,
  title: 'Filter Users',
  description: 'Write a query to select users with age greater than 18.',
  points: 150,
  sample_solution: 'SELECT * FROM users WHERE age > 18',
};

/**
 * Create a custom mock user with specific properties
 */
export function createMockUser(overrides: Partial<User> = {}): User {
  return {
    ...mockUser,
    ...overrides,
  };
}

/**
 * Create a custom mock challenge with specific properties
 */
export function createMockChallenge(
  overrides: Partial<ChallengeDetail> = {}
): ChallengeDetail {
  return {
    ...mockChallengeDetail,
    ...overrides,
  };
}
