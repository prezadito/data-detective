import type { AttemptRecord } from '@/types';

interface AttemptCardProps {
  attempt: AttemptRecord;
  attemptNumber: number;
}

/**
 * Display a single attempt with query and result
 */
export function AttemptCard({ attempt, attemptNumber }: AttemptCardProps) {
  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-600">
            Attempt {attemptNumber}
          </span>
          <span className="text-xs text-gray-500">{formatTimestamp(attempt.attempted_at)}</span>
        </div>
        <div>
          {attempt.is_correct ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
              ✓ Correct
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
              ✗ Incorrect
            </span>
          )}
        </div>
      </div>

      {/* Query */}
      <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
        <pre className="text-sm text-gray-100 font-mono whitespace-pre-wrap break-words">
          {attempt.query}
        </pre>
      </div>
    </div>
  );
}

AttemptCard.displayName = 'AttemptCard';
