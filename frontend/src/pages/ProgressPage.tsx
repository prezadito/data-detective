import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { progressService } from '@/services/progressService';
import { ProgressBar, ChallengeList } from '@/components/progress';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { showApiErrorToast } from '@/utils/toast';
import type { ProgressSummaryResponse } from '@/types';

export function ProgressPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [progress, setProgress] = useState<ProgressSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<number | null>(null);

  // Fetch progress on mount
  useEffect(() => {
    async function fetchProgress() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await progressService.getMyProgress();
        setProgress(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load progress';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchProgress();
  }, []);

  // Handle challenge click - navigate to practice page
  const handleChallengeClick = (unitId: number, challengeId: number) => {
    navigate(`/practice?unit=${unitId}&challenge=${challengeId}`);
  };

  // Filter progress items by selected unit
  const filteredItems = selectedUnit
    ? progress?.progress_items.filter((item) => item.unit_id === selectedUnit)
    : progress?.progress_items;

  // Get unique unit IDs for filter
  const availableUnits = progress
    ? Array.from(new Set(progress.progress_items.map((item) => item.unit_id))).sort()
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <span className="mr-3">📊</span>
                Your Progress
              </h1>
              <p className="text-gray-600 mt-2">
                Track your learning journey and see how far you've come!
              </p>
            </div>
            {user && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Student</p>
                <p className="font-medium text-gray-900">{user.name}</p>
              </div>
            )}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
              <span className="ml-3 text-gray-600">Loading progress...</span>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <div className="flex items-start">
                <span className="text-red-500 mr-2 mt-0.5">⚠</span>
                <div>
                  <p className="text-sm font-medium text-red-800">Error loading progress</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Progress Summary */}
          {progress && !isLoading && !error && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Total Points */}
                <div className="bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-lg p-6 text-white shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-yellow-100 text-sm font-medium">Total Points</p>
                      <p className="text-4xl font-bold mt-1">
                        {progress.summary.total_points}
                      </p>
                    </div>
                    <span className="text-5xl">🏆</span>
                  </div>
                </div>

                {/* Challenges Completed */}
                <div className="bg-gradient-to-br from-green-400 to-green-500 rounded-lg p-6 text-white shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm font-medium">
                        Challenges Completed
                      </p>
                      <p className="text-4xl font-bold mt-1">
                        {progress.summary.total_completed}
                      </p>
                    </div>
                    <span className="text-5xl">✅</span>
                  </div>
                </div>

                {/* Completion Rate */}
                <div className="bg-gradient-to-br from-blue-400 to-blue-500 rounded-lg p-6 text-white shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100 text-sm font-medium">Completion Rate</p>
                      <p className="text-4xl font-bold mt-1">
                        {Math.round(progress.summary.completion_percentage)}%
                      </p>
                    </div>
                    <span className="text-5xl">📈</span>
                  </div>
                </div>
              </div>

              {/* Overall Progress Bar */}
              <div className="bg-gray-50 rounded-lg p-6">
                <ProgressBar
                  current={progress.summary.total_completed}
                  total={7}
                  label="Overall Progress"
                  size="lg"
                />
              </div>
            </div>
          )}
        </div>

        {/* Challenge List */}
        {progress && !isLoading && !error && (
          <div>
            {/* Filter Bar */}
            {availableUnits.length > 1 && (
              <div className="bg-white rounded-lg shadow p-4 mb-6">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-700">Filter by unit:</span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedUnit(null)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedUnit === null
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      All Units
                    </button>
                    {availableUnits.map((unitId) => (
                      <button
                        key={unitId}
                        onClick={() => setSelectedUnit(unitId)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          selectedUnit === unitId
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Unit {unitId}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Challenge List */}
            <ChallengeList
              progressItems={filteredItems || []}
              onChallengeClick={handleChallengeClick}
              totalChallenges={7}
            />
          </div>
        )}
      </main>
    </div>
  );
}
