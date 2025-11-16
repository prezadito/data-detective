import { useState, useEffect } from 'react';
import { useDatabase } from '@/hooks/useDatabase';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { QueryResult } from '@/types/database';

export interface ExpectedOutputProps {
  /**
   * SQL query to execute and display results
   */
  query: string | null;

  /**
   * Whether to show the query text
   * @default false (students shouldn't see the solution query)
   */
  showQuery?: boolean;

  /**
   * Maximum number of rows to display
   * @default 5
   */
  maxRows?: number;
}

/**
 * ExpectedOutput component executes a sample query and displays the results
 * Used to show students what the correct output should look like
 */
export function ExpectedOutput({
  query,
  showQuery = false,
  maxRows = 5,
}: ExpectedOutputProps) {
  const { executeQuery, isReady } = useDatabase();
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Execute query when component mounts or query changes
   */
  useEffect(() => {
    if (!query || !isReady) {
      setResult(null);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const queryResult = executeQuery(query);
      setResult(queryResult);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [query, isReady, executeQuery]);

  // Query is null (student view without sample_solution)
  if (!query) {
    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">🎯</span>
            Expected Output
          </h3>
        </div>
        <div className="p-4">
          <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
            <p className="text-sm text-blue-700">
              Complete the challenge to see the expected output
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Database not ready
  if (!isReady) {
    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">🎯</span>
            Expected Output
          </h3>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
            <span className="ml-2 text-sm text-gray-600">
              Loading database...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">🎯</span>
            Expected Output
          </h3>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
            <span className="ml-2 text-sm text-gray-600">
              Executing query...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Error state (should not happen with valid sample_solution)
  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">🎯</span>
            Expected Output
          </h3>
        </div>
        <div className="p-4">
          <div className="border-l-4 border-red-500 bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700 mt-1 font-mono">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // Success state with results
  if (result) {
    const displayRows = result.values.slice(0, maxRows);
    const hasMoreRows = result.rowCount > maxRows;

    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center">
            <span className="mr-2">🎯</span>
            Expected Output
          </h3>
        </div>

        <div className="p-4">
          {/* Optional: Show query text (for teachers) */}
          {showQuery && (
            <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-xs text-gray-600 mb-1">Sample Query:</p>
              <code className="text-xs font-mono text-gray-800">{query}</code>
            </div>
          )}

          {/* Results table */}
          {result.rowCount > 0 ? (
            <>
              <div className="overflow-x-auto border border-gray-200 rounded-md">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      {result.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {displayRows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50">
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap"
                          >
                            {cell === null ? (
                              <span className="text-gray-400 italic">NULL</span>
                            ) : (
                              String(cell)
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Row count info */}
              <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
                <span>
                  Showing {displayRows.length} of {result.rowCount} row
                  {result.rowCount !== 1 ? 's' : ''}
                </span>
                {hasMoreRows && (
                  <span className="text-blue-600">
                    +{result.rowCount - maxRows} more rows
                  </span>
                )}
              </div>
            </>
          ) : (
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="text-sm text-blue-700">Query returns 0 rows</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

ExpectedOutput.displayName = 'ExpectedOutput';
