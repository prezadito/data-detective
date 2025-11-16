import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type {
  Database,
  QueryResult,
  DatabaseError,
  QueryHistoryEntry,
} from '@/types/database';
import {
  initializeDatabase,
  executeQuery as executeQueryService,
} from '@/services/databaseService';

interface DatabaseContextType {
  /**
   * sql.js database instance
   */
  db: Database | null;

  /**
   * Whether the database is currently loading
   */
  isLoading: boolean;

  /**
   * Whether the database is ready to use
   */
  isReady: boolean;

  /**
   * Error that occurred during initialization
   */
  error: DatabaseError | null;

  /**
   * Execute a SQL query
   */
  executeQuery: (query: string) => QueryResult;

  /**
   * Query history (most recent first)
   */
  queryHistory: QueryHistoryEntry[];

  /**
   * Clear query history
   */
  clearHistory: () => void;
}

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

interface DatabaseProviderProps {
  children: ReactNode;
}

export function DatabaseProvider({ children }: DatabaseProviderProps) {
  const [db, setDb] = useState<Database | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<DatabaseError | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistoryEntry[]>([]);

  // Initialize database on mount
  useEffect(() => {
    const init = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const database = await initializeDatabase();
        setDb(database);
      } catch (err) {
        const dbError: DatabaseError = {
          message: err instanceof Error ? err.message : 'Failed to initialize database',
          originalError: err,
        };
        setError(dbError);
        console.error('Database initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  /**
   * Execute a SQL query and track it in history
   */
  const executeQuery = (query: string): QueryResult => {
    if (!db) {
      throw new Error('Database not initialized');
    }

    const startTime = performance.now();
    const historyEntry: QueryHistoryEntry = {
      id: crypto.randomUUID(),
      query,
      timestamp: new Date(),
      success: false,
    };

    try {
      const result = executeQueryService(db, query);
      const executionTime = performance.now() - startTime;

      // Update history entry with success
      historyEntry.success = true;
      historyEntry.rowCount = result.rowCount;
      historyEntry.executionTime = executionTime;

      // Add to history (most recent first)
      setQueryHistory((prev) => [historyEntry, ...prev]);

      return result;
    } catch (err) {
      const executionTime = performance.now() - startTime;

      // Update history entry with error
      historyEntry.success = false;
      historyEntry.error = err instanceof Error ? err.message : 'Unknown error';
      historyEntry.executionTime = executionTime;

      // Add to history (most recent first)
      setQueryHistory((prev) => [historyEntry, ...prev]);

      // Re-throw the error
      throw err;
    }
  };

  /**
   * Clear query history
   */
  const clearHistory = () => {
    setQueryHistory([]);
  };

  const value: DatabaseContextType = {
    db,
    isLoading,
    isReady: !isLoading && !error && db !== null,
    error,
    executeQuery,
    queryHistory,
    clearHistory,
  };

  return (
    <DatabaseContext.Provider value={value}>{children}</DatabaseContext.Provider>
  );
}

export function useDatabaseContext() {
  const context = useContext(DatabaseContext);
  if (context === undefined) {
    throw new Error('useDatabaseContext must be used within a DatabaseProvider');
  }
  return context;
}
