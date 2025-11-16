import { useDatabaseContext } from '@/contexts/DatabaseContext';

/**
 * Hook to access the in-browser SQL database
 *
 * Provides access to the sql.js database instance and query execution.
 * Must be used within a DatabaseProvider.
 *
 * @example
 * ```tsx
 * const { db, executeQuery, isReady } = useDatabase();
 *
 * if (isReady) {
 *   const result = executeQuery('SELECT * FROM movies');
 *   console.log(result.values);
 * }
 * ```
 */
export function useDatabase() {
  const context = useDatabaseContext();

  if (context === undefined) {
    throw new Error('useDatabase must be used within a DatabaseProvider');
  }

  return context;
}
