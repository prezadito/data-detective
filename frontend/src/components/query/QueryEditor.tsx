import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { useDatabase } from '@/hooks/useDatabase';
import { Button } from '@/components/ui/Button';
import { progressService } from '@/services/progressService';
import { validateQueryResults } from '@/utils/validateQuery';
import { showSuccessToast, showErrorToast, showApiErrorToast } from '@/utils/toast';
import type { QueryResult } from '@/types/database';
import type { ProgressResponse } from '@/types';

export interface QueryEditorProps {
  /**
   * Initial query to populate the editor
   */
  initialQuery?: string;

  /**
   * Callback when a query is successfully executed
   */
  onQueryExecute?: (result: QueryResult) => void;

  /**
   * Whether to show query history
   * @default true
   */
  showHistory?: boolean;

  /**
   * Maximum number of history entries to display
   * @default 5
   */
  maxHistoryEntries?: number;

  /**
   * Expected query for validation (sample solution)
   * If provided, enables submit functionality
   */
  expectedQuery?: string;

  /**
   * Unit ID for challenge submission
   */
  unitId?: number;

  /**
   * Challenge ID for challenge submission
   */
  challengeId?: number;

  /**
   * Number of hints used for this challenge
   * @default 0
   */
  hintsUsed?: number;

  /**
   * Callback when challenge is successfully submitted
   */
  onSubmitSuccess?: (progress: ProgressResponse) => void;
}

export function QueryEditor({
  initialQuery = '',
  onQueryExecute,
  showHistory = true,
  maxHistoryEntries = 5,
  expectedQuery,
  unitId,
  challengeId,
  hintsUsed = 0,
  onSubmitSuccess,
}: QueryEditorProps) {
  const { executeQuery, queryHistory, isReady } = useDatabase();
  const [query, setQuery] = useState(initialQuery);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isValidated, setIsValidated] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Determine if submit functionality is enabled
  const canSubmit = Boolean(expectedQuery && unitId && challengeId);

  // Auto-focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  /**
   * Execute the current query
   */
  const handleRunQuery = () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setError('Please enter a SQL query');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setResult(null);
    setExecutionTime(null);

    try {
      const startTime = performance.now();
      const queryResult = executeQuery(trimmedQuery);
      const endTime = performance.now();

      setResult(queryResult);
      setExecutionTime(endTime - startTime);

      // Call the callback if provided
      onQueryExecute?.(queryResult);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
    } finally {
      setIsExecuting(false);
    }
  };

  /**
   * Clear the query and results
   */
  const handleClear = () => {
    setQuery('');
    setResult(null);
    setError(null);
    setExecutionTime(null);
    textareaRef.current?.focus();
  };

  /**
   * Load a query from history
   */
  const handleLoadQuery = (historyQuery: string) => {
    setQuery(historyQuery);
    setResult(null);
    setError(null);
    setExecutionTime(null);
    setValidationMessage(null);
    setIsValidated(false);
    textareaRef.current?.focus();
  };

  /**
   * Validate query against expected output
   */
  const handleValidate = () => {
    if (!expectedQuery) {
      showErrorToast('No expected query provided for validation');
      return;
    }

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError('Please enter a SQL query');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setValidationMessage(null);
    setIsValidated(false);

    try {
      // Run student's query
      const studentResult = executeQuery(trimmedQuery);

      // Run expected query
      const expectedResult = executeQuery(expectedQuery);

      // Validate results
      const validation = validateQueryResults(studentResult, expectedResult);

      if (validation.isValid) {
        setIsValidated(true);
        setValidationMessage(validation.message);
        setResult(studentResult);
        showSuccessToast('Query is correct! You can now submit.');
      } else {
        setValidationMessage(validation.message);
        setResult(studentResult);
        showErrorToast(validation.message);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      showErrorToast(errorMessage);
    } finally {
      setIsExecuting(false);
    }
  };

  /**
   * Submit challenge to backend
   */
  const handleSubmit = async () => {
    if (!canSubmit) {
      showErrorToast('Submission not configured');
      return;
    }

    if (!isValidated) {
      showErrorToast('Please validate your query first by clicking "Check Answer"');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await progressService.submitChallenge({
        unit_id: unitId!,
        challenge_id: challengeId!,
        query: query.trim(),
        hints_used: hintsUsed,
      });

      showSuccessToast(`Challenge completed! You earned ${response.points_earned} points! 🎉`);
      onSubmitSuccess?.(response);
    } catch (err) {
      await showApiErrorToast(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter: Run query
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRunQuery();
    }

    // Ctrl+K or Cmd+K: Clear
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      handleClear();
    }

    // Escape: Clear error
    if (e.key === 'Escape' && error) {
      setError(null);
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp: Date): string => {
    const now = new Date();
    const diff = now.getTime() - new Date(timestamp).getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return new Date(timestamp).toLocaleString();
  };

  const recentHistory = queryHistory.slice(0, maxHistoryEntries);

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Query Input Section */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">SQL Query Editor</h2>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              disabled={!query && !result && !error}
            >
              Clear
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRunQuery}
              disabled={!isReady || !query.trim() || isExecuting}
              isLoading={isExecuting}
            >
              Run Query
            </Button>
            {canSubmit && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleValidate}
                  disabled={!isReady || !query.trim() || isExecuting || isSubmitting}
                  isLoading={isExecuting}
                >
                  Check Answer
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSubmit}
                  disabled={!isValidated || isSubmitting}
                  isLoading={isSubmitting}
                >
                  Submit
                </Button>
              </>
            )}
          </div>
        </div>

        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter your SQL query here...&#10;&#10;Examples:&#10;  SELECT * FROM movies LIMIT 10;&#10;  SELECT title, rating FROM movies WHERE rating > 8.0;&#10;&#10;Shortcuts: Ctrl+Enter to run, Ctrl+K to clear"
          className="w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
          rows={10}
          disabled={!isReady}
          aria-label="SQL query input"
        />

        {!isReady && (
          <p className="mt-2 text-sm text-yellow-600">
            Database is loading... Please wait.
          </p>
        )}
      </div>

      {/* Validation Message */}
      {validationMessage && !error && (
        <div
          className={`mx-6 mt-6 border-l-4 p-4 ${
            isValidated
              ? 'border-green-500 bg-green-50'
              : 'border-yellow-500 bg-yellow-50'
          }`}
        >
          <div className="flex items-center">
            <span className={`mr-2 ${isValidated ? 'text-green-500' : 'text-yellow-500'}`}>
              {isValidated ? '✓' : '⚠'}
            </span>
            <p className={`text-sm ${isValidated ? 'text-green-700' : 'text-yellow-800'}`}>
              {validationMessage}
            </p>
          </div>
        </div>
      )}

      {/* Success Banner */}
      {result && !error && !validationMessage && (
        <div className="mx-6 mt-6 border-l-4 border-green-500 bg-green-50 p-4">
          <div className="flex items-center">
            <span className="text-green-500 mr-2">✓</span>
            <p className="text-sm text-green-700">
              Query executed successfully
              {executionTime !== null && ` in ${executionTime.toFixed(2)}ms`}
            </p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mx-6 mt-6 border-l-4 border-red-500 bg-red-50 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start">
              <span className="text-red-500 mr-2 mt-0.5">⚠</span>
              <div>
                <p className="text-sm font-medium text-red-800">Query Error</p>
                <p className="text-sm text-red-700 mt-1 font-mono">{error}</p>
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700 transition-colors"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Results Table */}
      {result && result.rowCount > 0 && (
        <div className="p-6">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Results</h3>
            <p className="text-sm text-gray-600">
              {result.rowCount} row{result.rowCount !== 1 ? 's' : ''}
            </p>
          </div>

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
                {result.values.map((row, rowIndex) => (
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
        </div>
      )}

      {/* Empty Results */}
      {result && result.rowCount === 0 && (
        <div className="p-6">
          <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
            <div className="flex items-center">
              <span className="text-blue-500 mr-2">ℹ</span>
              <p className="text-sm text-blue-700">
                Query executed successfully but returned no rows.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Query History */}
      {showHistory && recentHistory.length > 0 && (
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Queries</h3>
          <div className="space-y-2">
            {recentHistory.map((entry) => (
              <div
                key={entry.id}
                className="border border-gray-200 bg-white rounded p-3 cursor-pointer hover:bg-gray-50 hover:border-gray-300 transition-colors"
                onClick={() => handleLoadQuery(entry.query)}
              >
                <div className="flex items-start justify-between mb-1">
                  <code className="text-xs text-gray-700 font-mono flex-1 break-all">
                    {entry.query}
                  </code>
                  <span
                    className={`ml-2 flex-shrink-0 ${
                      entry.success ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {entry.success ? '✓' : '✗'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{formatTimestamp(entry.timestamp)}</span>
                  <div className="flex items-center space-x-2">
                    {entry.success && entry.rowCount !== undefined && (
                      <span>{entry.rowCount} rows</span>
                    )}
                    {entry.executionTime !== undefined && (
                      <span>{entry.executionTime.toFixed(2)}ms</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

QueryEditor.displayName = 'QueryEditor';
