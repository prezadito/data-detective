import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { leaderboardService } from '@/services/leaderboardService';
import { LeaderboardTable } from '@/components/leaderboard';
import { Button } from '@/components/ui/Button';
import { showApiErrorToast } from '@/utils/toast';
import type { LeaderboardResponse } from '@/types';

const AUTO_REFRESH_INTERVAL = 30000; // 30 seconds

export function LeaderboardPage() {
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // Fetch leaderboard data
  const fetchLeaderboard = useCallback(async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      const data = await leaderboardService.getLeaderboard();
      setLeaderboard(data);
      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load leaderboard';
      setError(errorMessage);
      if (isManualRefresh) {
        await showApiErrorToast(err);
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefreshEnabled) return;

    const interval = setInterval(() => {
      fetchLeaderboard();
    }, AUTO_REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchLeaderboard]);

  // Manual refresh handler
  const handleManualRefresh = () => {
    fetchLeaderboard(true);
  };

  // Format last updated time
  const formatLastUpdated = (date: Date): string => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);

    if (seconds < 10) return 'just now';
    if (seconds < 60) return `${seconds} seconds ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="mb-4 md:mb-0">
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <span className="mr-3">🏆</span>
                Leaderboard
              </h1>
              <p className="text-gray-600 mt-2">
                See where you rank among all students
              </p>
            </div>

            <div className="flex flex-col space-y-2">
              {/* Refresh Controls */}
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleManualRefresh}
                  disabled={isRefreshing}
                  isLoading={isRefreshing}
                >
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </Button>

                <button
                  onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    autoRefreshEnabled
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {autoRefreshEnabled ? '🔄 Auto-refresh: ON' : '⏸️ Auto-refresh: OFF'}
                </button>
              </div>

              {/* Last Updated */}
              {lastUpdated && !isLoading && (
                <p className="text-xs text-gray-500 text-right">
                  Updated {formatLastUpdated(lastUpdated)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <div className="flex items-start">
                <span className="text-red-500 mr-2 mt-0.5">⚠</span>
                <div>
                  <p className="text-sm font-medium text-red-800">
                    Error loading leaderboard
                  </p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Leaderboard Table */}
        <LeaderboardTable
          entries={leaderboard?.entries || []}
          currentUserId={user?.id}
          currentUserName={user?.name}
          isLoading={isLoading}
        />

        {/* Info Banner */}
        {!isLoading && leaderboard && leaderboard.entries.length > 0 && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start">
              <span className="text-blue-500 mr-3 text-2xl">💡</span>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-blue-900 mb-1">
                  Keep Learning!
                </h3>
                <p className="text-sm text-blue-700">
                  Complete more challenges to earn points and climb the leaderboard. The
                  leaderboard shows the top 100 students and updates automatically every
                  30 seconds.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
