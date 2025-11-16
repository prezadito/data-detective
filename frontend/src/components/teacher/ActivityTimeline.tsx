import type { ActivityLogEntry } from '@/types';

interface ActivityTimelineProps {
  activities: ActivityLogEntry[];
}

/**
 * Display timeline of student activity (attempts and hints)
 */
export function ActivityTimeline({ activities }: ActivityTimelineProps) {
  // Format relative time
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
    if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
    if (diffDays < 7) return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Format absolute time for tooltip
  const formatAbsoluteTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  // Get icon and color for activity type
  const getActivityStyle = (entry: ActivityLogEntry) => {
    if (entry.action_type === 'hint') {
      return {
        icon: '💡',
        bgColor: 'bg-blue-100',
        borderColor: 'border-blue-300',
        textColor: 'text-blue-800',
      };
    }

    // For attempts, check if successful
    const isCorrect = entry.details.includes('correct');
    return {
      icon: isCorrect ? '✓' : '📝',
      bgColor: isCorrect ? 'bg-green-100' : 'bg-gray-100',
      borderColor: isCorrect ? 'border-green-300' : 'border-gray-300',
      textColor: isCorrect ? 'text-green-800' : 'text-gray-800',
    };
  };

  if (activities.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-500 text-lg">No activity recorded yet</p>
        <p className="text-gray-400 text-sm mt-2">
          Student activity will appear here once they start attempting challenges
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {activities.map((entry, index) => {
        const style = getActivityStyle(entry);
        const isLast = index === activities.length - 1;

        return (
          <div key={index} className="relative flex items-start">
            {/* Timeline line */}
            {!isLast && (
              <div className="absolute left-5 top-12 w-0.5 h-full bg-gray-200" />
            )}

            {/* Timeline dot/icon */}
            <div
              className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-full ${style.bgColor} ${style.borderColor} border-2 flex items-center justify-center`}
            >
              <span className="text-lg">{style.icon}</span>
            </div>

            {/* Content */}
            <div className="ml-4 flex-1 pb-8">
              {/* Time */}
              <div
                className="text-xs text-gray-500 mb-1"
                title={formatAbsoluteTime(entry.timestamp)}
              >
                {formatRelativeTime(entry.timestamp)}
              </div>

              {/* Card */}
              <div className={`rounded-lg border ${style.borderColor} ${style.bgColor} p-4`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className={`font-semibold ${style.textColor} mb-1`}>
                      {entry.details}
                    </h4>
                    <p className={`text-sm ${style.textColor} opacity-80`}>
                      Unit {entry.unit_id}, Challenge {entry.challenge_id}: {entry.challenge_title}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

ActivityTimeline.displayName = 'ActivityTimeline';
