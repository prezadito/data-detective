import type { ChallengeProgressDetail } from '@/types';

interface ChallengeProgressCardProps {
  challenge: ChallengeProgressDetail;
}

/**
 * Display detailed progress for a single challenge
 */
export function ChallengeProgressCard({ challenge }: ChallengeProgressCardProps) {
  const { metrics } = challenge;

  // Format timestamp
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Get status indicator
  const getStatusIndicator = () => {
    if (metrics.success_rate >= 70) {
      return { icon: '✓', color: 'text-green-600', label: 'Completed' };
    }
    if (metrics.success_rate < 30 && metrics.total_attempts > 3) {
      return { icon: '⚠', color: 'text-red-600', label: 'Struggling' };
    }
    if (metrics.total_attempts > 0) {
      return { icon: '○', color: 'text-yellow-600', label: 'In Progress' };
    }
    return { icon: '○', color: 'text-gray-400', label: 'Not Started' };
  };

  const status = getStatusIndicator();

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className={`text-lg ${status.color}`}>{status.icon}</span>
            <h4 className="font-semibold text-gray-900">{challenge.title}</h4>
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">{challenge.description}</p>
        </div>
        <div className="ml-4 text-right">
          <div className="text-lg font-bold text-blue-600">{challenge.points}</div>
          <div className="text-xs text-gray-500">points</div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-2 mb-3 text-center">
        <div className="bg-gray-50 rounded p-2">
          <div className="text-sm font-bold text-gray-900">{metrics.total_attempts}</div>
          <div className="text-xs text-gray-600">Attempts</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-sm font-bold text-gray-900">
            {Math.round(metrics.success_rate)}%
          </div>
          <div className="text-xs text-gray-600">Success</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-sm font-bold text-gray-900">{metrics.total_hints_used}</div>
          <div className="text-xs text-gray-600">Hints</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-sm font-bold text-gray-900">{metrics.correct_attempts}</div>
          <div className="text-xs text-gray-600">Correct</div>
        </div>
      </div>

      {/* Attempt Bar */}
      {metrics.total_attempts > 0 && (
        <div className="mb-2">
          <div className="flex items-center space-x-1 h-2">
            {challenge.attempts.slice(0, 10).map((attempt, idx) => (
              <div
                key={idx}
                className={`flex-1 h-full rounded-sm ${
                  attempt.is_correct ? 'bg-green-500' : 'bg-red-300'
                }`}
                title={attempt.is_correct ? 'Correct' : 'Incorrect'}
              />
            ))}
            {metrics.total_attempts > 10 && (
              <span className="text-xs text-gray-500 ml-1">
                +{metrics.total_attempts - 10} more
              </span>
            )}
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Attempt history</span>
            <span>Last: {formatTime(metrics.last_attempted)}</span>
          </div>
        </div>
      )}

      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <span className={`text-xs font-medium ${status.color}`}>{status.label}</span>
        {metrics.total_attempts === 0 && (
          <span className="text-xs text-gray-400">No attempts yet</span>
        )}
      </div>
    </div>
  );
}

ChallengeProgressCard.displayName = 'ChallengeProgressCard';
