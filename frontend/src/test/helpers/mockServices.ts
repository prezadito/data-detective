/**
 * Mock service factory functions
 * Creates consistently mocked services for tests
 */

import { vi } from 'vitest';
import type { User } from '@/types';
import type { QueryResult } from '@/types/database';

/**
 * Create a mock useAuth hook return value
 */
export function createMockUseAuth(overrides: Partial<{
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: ReturnType<typeof vi.fn>;
  register: ReturnType<typeof vi.fn>;
  logout: ReturnType<typeof vi.fn>;
}> = {}) {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  };
}

/**
 * Create a mock useDatabase hook return value
 */
export function createMockUseDatabase(overrides: Partial<{
  db: unknown;
  executeQuery: ReturnType<typeof vi.fn>;
  isReady: boolean;
  queryHistory: Array<{
    id: string;
    query: string;
    timestamp: Date;
    success: boolean;
    rowCount?: number;
    executionTime?: number;
    error?: string;
  }>;
}> = {}) {
  return {
    db: null,
    executeQuery: vi.fn(),
    isReady: true,
    queryHistory: [],
    ...overrides,
  };
}

/**
 * Create a mock navigate function
 */
export function createMockNavigate() {
  return vi.fn();
}

/**
 * Create mock toast utilities
 */
export function createMockToast() {
  return {
    showSuccessToast: vi.fn(),
    showErrorToast: vi.fn(),
    showApiErrorToast: vi.fn(),
  };
}

/**
 * Create a successful query result for executeQuery mock
 */
export function createSuccessfulQueryResult(
  overrides: Partial<QueryResult> = {}
): QueryResult {
  return {
    columns: ['id', 'name'],
    values: [[1, 'Test']],
    rowCount: 1,
    ...overrides,
  };
}

/**
 * Create a query error for executeQuery mock
 */
export function createQueryError(message = 'SQL syntax error') {
  return new Error(message);
}
