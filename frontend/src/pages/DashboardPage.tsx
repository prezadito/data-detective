import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useDatabase } from '@/hooks/useDatabase';
import { Navigation } from '@/components/navigation/Navigation';

export function DashboardPage() {
  const { user } = useAuth();
  const { executeQuery, isReady, isLoading, error, queryHistory } = useDatabase();
  const [queryResult, setQueryResult] = useState<{ columns: string[]; values: unknown[][] } | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  const runTestQuery = () => {
    try {
      setQueryError(null);
      const result = executeQuery('SELECT * FROM movies');
      setQueryResult(result);
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="text-sm text-blue-700">
                <strong>User ID:</strong> {user?.id}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Email:</strong> {user?.email}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Role:</strong> {user?.role}
              </p>
            </div>
          </div>
        </div>

        {/* Database Test Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">SQL Database Test</h3>

          {/* Database Status */}
          <div className="mb-4">
            {isLoading && (
              <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4">
                <p className="text-sm text-yellow-700">Loading database...</p>
              </div>
            )}
            {error && (
              <div className="border-l-4 border-red-500 bg-red-50 p-4">
                <p className="text-sm text-red-700">
                  <strong>Database Error:</strong> {error.message}
                </p>
              </div>
            )}
            {isReady && (
              <div className="border-l-4 border-green-500 bg-green-50 p-4">
                <p className="text-sm text-green-700">
                  <strong>Database Ready!</strong> sql.js initialized successfully.
                </p>
              </div>
            )}
          </div>

          {/* Test Query Button */}
          {isReady && (
            <div className="space-y-4">
              <button
                onClick={runTestQuery}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Run Test Query: SELECT * FROM movies
              </button>

              {/* Query Error */}
              {queryError && (
                <div className="border-l-4 border-red-500 bg-red-50 p-4">
                  <p className="text-sm text-red-700">
                    <strong>Query Error:</strong> {queryError}
                  </p>
                </div>
              )}

              {/* Query Results */}
              {queryResult && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b">
                    <p className="text-sm font-medium text-gray-700">
                      Results: {queryResult.values.length} rows
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-100">
                        <tr>
                          {queryResult.columns.map((col) => (
                            <th
                              key={col}
                              className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {queryResult.values.map((row, i) => (
                          <tr key={i}>
                            {row.map((cell, j) => (
                              <td key={j} className="px-4 py-2 text-sm text-gray-900">
                                {String(cell)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Query History */}
              {queryHistory.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Query History</h4>
                  <div className="space-y-2">
                    {queryHistory.slice(0, 5).map((entry) => (
                      <div
                        key={entry.id}
                        className={`border-l-4 p-3 ${
                          entry.success ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'
                        }`}
                      >
                        <p className="text-xs text-gray-600 mb-1">
                          {entry.timestamp.toLocaleTimeString()} • {entry.executionTime?.toFixed(2)}ms
                        </p>
                        <code className="text-sm font-mono">{entry.query}</code>
                        {entry.success && (
                          <p className="text-xs text-green-700 mt-1">✓ {entry.rowCount} rows</p>
                        )}
                        {!entry.success && (
                          <p className="text-xs text-red-700 mt-1">✗ {entry.error}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
