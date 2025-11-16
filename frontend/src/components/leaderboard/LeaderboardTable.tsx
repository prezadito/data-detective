import type { LeaderboardEntry } from '@/types';

export interface LeaderboardTableProps {
  /**
   * Array of leaderboard entries
   */
  entries: LeaderboardEntry[];

  /**
   * Current user's ID to highlight their row
   */
  currentUserId?: number;

  /**
   * Current user's name to match against entries
   */
  currentUserName?: string;

  /**
   * Whether data is loading
   * @default false
   */
  isLoading?: boolean;
}

/**
 * LeaderboardTable component displays student rankings
 */
export function LeaderboardTable({
  entries,
  currentUserName,
  isLoading = false,
}: LeaderboardTableProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-12 text-center">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto"></div>
          </div>
          <p className="text-gray-600 mt-4">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <div className="text-gray-400 text-6xl mb-4" role="img" aria-label="Trophy">🏆</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No rankings yet
        </h3>
        <p className="text-gray-600">
          Be the first to complete challenges and climb the leaderboard!
        </p>
      </div>
    );
  }

  /**
   * Get trophy icon for top 3
   */
  const getTrophyIcon = (rank: number): string | null => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return null;
  };

  /**
   * Get accessible label for trophy
   */
  const getTrophyLabel = (rank: number): string => {
    if (rank === 1) return 'First place';
    if (rank === 2) return 'Second place';
    if (rank === 3) return 'Third place';
    return `Rank ${rank}`;
  };

  /**
   * Check if entry is current user
   */
  const isCurrentUser = (entry: LeaderboardEntry): boolean => {
    return entry.student_name === currentUserName;
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200" aria-label="Student leaderboard rankings">
          <thead className="bg-gray-100">
            <tr>
              <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Rank
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Student
              </th>
              <th scope="col" className="px-6 py-4 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                Points
              </th>
              <th scope="col" className="px-6 py-4 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                Challenges
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {entries.map((entry) => {
              const trophy = getTrophyIcon(entry.rank);
              const isCurrent = isCurrentUser(entry);

              return (
                <tr
                  key={`${entry.rank}-${entry.student_name}`}
                  className={`transition-colors ${
                    isCurrent
                      ? 'bg-blue-50 border-l-4 border-blue-500'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  {/* Rank */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {trophy ? (
                        <span className="text-3xl mr-2" role="img" aria-label={getTrophyLabel(entry.rank)}>
                          {trophy}
                        </span>
                      ) : (
                        <span className="text-lg font-bold text-gray-700 w-8">
                          {entry.rank}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Student Name */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span
                        className={`text-sm font-medium ${
                          isCurrent ? 'text-blue-900' : 'text-gray-900'
                        }`}
                      >
                        {entry.student_name}
                      </span>
                      {isCurrent && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                          You
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Points */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <span className="text-yellow-500 mr-1" aria-hidden="true">🏆</span>
                      <span className="text-sm font-bold text-gray-900">
                        {entry.total_points}
                      </span>
                      <span className="sr-only">points</span>
                    </div>
                  </td>

                  {/* Challenges Completed */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <span className="text-green-500 mr-1" aria-hidden="true">✓</span>
                      <span className="text-sm text-gray-700">
                        {entry.challenges_completed}
                      </span>
                      <span className="sr-only">challenges completed</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden divide-y divide-gray-200" role="list" aria-label="Student leaderboard rankings">
        {entries.map((entry) => {
          const trophy = getTrophyIcon(entry.rank);
          const isCurrent = isCurrentUser(entry);

          return (
            <div
              key={`${entry.rank}-${entry.student_name}`}
              role="listitem"
              className={`p-4 ${
                isCurrent ? 'bg-blue-50 border-l-4 border-blue-500' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center">
                  {trophy ? (
                    <span className="text-2xl mr-2" role="img" aria-label={getTrophyLabel(entry.rank)}>
                      {trophy}
                    </span>
                  ) : (
                    <span className="text-lg font-bold text-gray-700 w-8">
                      {entry.rank}
                    </span>
                  )}
                  <div>
                    <div className="flex items-center">
                      <span
                        className={`text-sm font-medium ${
                          isCurrent ? 'text-blue-900' : 'text-gray-900'
                        }`}
                      >
                        {entry.student_name}
                      </span>
                      {isCurrent && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                          You
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm mt-2">
                <div className="flex items-center">
                  <span className="text-yellow-500 mr-1" aria-hidden="true">🏆</span>
                  <span className="font-bold text-gray-900">
                    {entry.total_points} points
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-1" aria-hidden="true">✓</span>
                  <span className="text-gray-700">
                    {entry.challenges_completed} completed
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

LeaderboardTable.displayName = 'LeaderboardTable';
