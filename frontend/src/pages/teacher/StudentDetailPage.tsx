import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { userService } from '@/services/userService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MetricsCard } from '@/components/teacher/MetricsCard';
import { ProgressChart } from '@/components/teacher/ProgressChart';
import { StrugglingAreasAlert } from '@/components/teacher/StrugglingAreasAlert';
import { ChallengeProgressCard } from '@/components/teacher/ChallengeProgressCard';
import { ActivityTimeline } from '@/components/teacher/ActivityTimeline';
import { AttemptCard } from '@/components/teacher/AttemptCard';
import { detectStrugglingAreas } from '@/utils/studentAnalysis';
import { showApiErrorToast } from '@/utils/toast';
import type { StudentDetailResponse } from '@/types';

type TabType = 'overview' | 'progress' | 'activity' | 'attempts';

export function StudentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<StudentDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [expandedUnits, setExpandedUnits] = useState<Set<number>>(new Set([1, 2, 3]));
  const [expandedChallenges, setExpandedChallenges] = useState<Set<string>>(new Set());

  // Fetch student detail data on mount
  useEffect(() => {
    async function fetchStudentDetail() {
      if (!id) {
        setError('Student ID is required');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const response = await userService.getStudentById(parseInt(id, 10), true);
        setData(response);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load student details';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchStudentDetail();
  }, [id]);

  // Handle back button
  const handleBack = () => {
    navigate('/teacher/students');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <LoadingSpinner />
            <p className="text-gray-600 mt-4">Loading student details...</p>
          </div>
        </main>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-lg p-12">
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <div className="flex items-start">
                <span className="text-red-500 mr-2 mt-0.5">⚠</span>
                <div>
                  <p className="text-sm font-medium text-red-800">
                    Error loading student details
                  </p>
                  <p className="text-sm text-red-700 mt-1">
                    {error || 'Student not found'}
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={handleBack}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              ← Back to Students
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          {/* Back Button */}
          <button
            onClick={handleBack}
            className="mb-4 flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <span className="mr-1">←</span>
            <span className="text-sm font-medium">Back to Students</span>
          </button>

          {/* Student Info & Quick Stats */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            {/* Left: Student Info */}
            <div className="flex items-center mb-4 md:mb-0">
              <div className="flex-shrink-0 h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-blue-600 font-bold text-2xl">
                  {data.user.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-gray-900">{data.user.name}</h1>
                <p className="text-sm text-gray-600">{data.user.email}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Joined {new Date(data.user.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Right: Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {data.metrics.total_points}
                </div>
                <div className="text-xs text-gray-600">Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round((data.metrics.total_challenges_completed / 7) * 100)}%
                </div>
                <div className="text-xs text-gray-600">Complete</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(data.metrics.overall_success_rate)}%
                </div>
                <div className="text-xs text-gray-600">Success</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex overflow-x-auto" aria-label="Tabs">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'progress', label: 'Progress', icon: '📈' },
                { id: 'activity', label: 'Activity', icon: '🕒' },
                { id: 'attempts', label: 'Attempts', icon: '📝' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`
                    flex-1 md:flex-none whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm transition-colors
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {activeTab === 'overview' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Overview</h2>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                <MetricsCard
                  icon="🏆"
                  label="Total Points"
                  value={data.metrics.total_points}
                  color="blue"
                />
                <MetricsCard
                  icon="📊"
                  label="Completion"
                  value={`${Math.round((data.metrics.total_challenges_completed / 7) * 100)}%`}
                  subtitle={`${data.metrics.total_challenges_completed}/7 challenges`}
                  color={
                    data.metrics.total_challenges_completed >= 6
                      ? 'green'
                      : data.metrics.total_challenges_completed >= 3
                      ? 'blue'
                      : 'yellow'
                  }
                />
                <MetricsCard
                  icon="✓"
                  label="Success Rate"
                  value={`${Math.round(data.metrics.overall_success_rate)}%`}
                  subtitle={`${data.metrics.total_attempts} total attempts`}
                  color={
                    data.metrics.overall_success_rate >= 70
                      ? 'green'
                      : data.metrics.overall_success_rate >= 50
                      ? 'yellow'
                      : 'red'
                  }
                />
                <MetricsCard
                  icon="📝"
                  label="Total Attempts"
                  value={data.metrics.total_attempts}
                  color="gray"
                />
                <MetricsCard
                  icon="🔄"
                  label="Avg Attempts"
                  value={data.metrics.average_attempts_per_challenge.toFixed(1)}
                  subtitle="per challenge"
                  color={
                    data.metrics.average_attempts_per_challenge <= 2
                      ? 'green'
                      : data.metrics.average_attempts_per_challenge <= 4
                      ? 'yellow'
                      : 'red'
                  }
                />
                <MetricsCard
                  icon="💡"
                  label="Hints Used"
                  value={data.metrics.total_hints_used}
                  subtitle={
                    data.metrics.total_challenges_completed > 0
                      ? `${(data.metrics.total_hints_used / data.metrics.total_challenges_completed).toFixed(1)} per challenge`
                      : undefined
                  }
                  color="blue"
                />
              </div>

              {/* Progress Chart */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Progress by Unit
                </h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <ProgressChart units={data.units} />
                </div>
              </div>

              {/* Struggling Areas */}
              <div>
                <StrugglingAreasAlert
                  areas={detectStrugglingAreas(
                    data.metrics,
                    data.units,
                    data.activity_log
                  )}
                />
              </div>
            </div>
          )}

          {activeTab === 'progress' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Progress by Unit</h2>

              {/* Unit Accordions */}
              <div className="space-y-4">
                {data.units.map((unit) => {
                  const isExpanded = expandedUnits.has(unit.unit_id);
                  const totalChallengesInUnit = {
                    1: 3,
                    2: 2,
                    3: 2,
                  }[unit.unit_id] || 0;
                  const completedCount = unit.challenges.length;

                  return (
                    <div
                      key={unit.unit_id}
                      className="border border-gray-200 rounded-lg overflow-hidden"
                    >
                      {/* Accordion Header */}
                      <button
                        onClick={() => {
                          const newExpanded = new Set(expandedUnits);
                          if (isExpanded) {
                            newExpanded.delete(unit.unit_id);
                          } else {
                            newExpanded.add(unit.unit_id);
                          }
                          setExpandedUnits(newExpanded);
                        }}
                        className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">
                            {isExpanded ? '▼' : '▶'}
                          </span>
                          <div className="text-left">
                            <h3 className="font-semibold text-gray-900">
                              {unit.unit_title}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {completedCount}/{totalChallengesInUnit} completed
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div className="text-2xl font-bold text-gray-900">
                              {Math.round((completedCount / totalChallengesInUnit) * 100)}%
                            </div>
                            <div className="text-xs text-gray-600">Complete</div>
                          </div>
                        </div>
                      </button>

                      {/* Accordion Content */}
                      {isExpanded && (
                        <div className="p-6 bg-white space-y-4">
                          {unit.challenges.length > 0 ? (
                            unit.challenges.map((challenge) => (
                              <ChallengeProgressCard
                                key={`${challenge.unit_id}-${challenge.challenge_id}`}
                                challenge={challenge}
                              />
                            ))
                          ) : (
                            <div className="text-center py-8 text-gray-500">
                              <p>No challenges completed in this unit yet</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">Recent Activity</h2>
              <p className="text-sm text-gray-600 mb-6">
                Showing {data.activity_log.length} most recent actions (attempts and hints)
              </p>
              <ActivityTimeline activities={data.activity_log} />
            </div>
          )}

          {activeTab === 'attempts' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-6">All Attempts</h2>

              {/* Grouped by Challenge */}
              <div className="space-y-4">
                {data.units.map((unit) =>
                  unit.challenges.map((challenge) => {
                    if (challenge.attempts.length === 0) return null;

                    const challengeKey = `${unit.unit_id}-${challenge.challenge_id}`;
                    const isExpanded = expandedChallenges.has(challengeKey);

                    return (
                      <div
                        key={challengeKey}
                        className="border border-gray-200 rounded-lg overflow-hidden"
                      >
                        {/* Accordion Header */}
                        <button
                          onClick={() => {
                            const newExpanded = new Set(expandedChallenges);
                            if (isExpanded) {
                              newExpanded.delete(challengeKey);
                            } else {
                              newExpanded.add(challengeKey);
                            }
                            setExpandedChallenges(newExpanded);
                          }}
                          className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-lg">
                              {isExpanded ? '▼' : '▶'}
                            </span>
                            <div className="text-left">
                              <h3 className="font-semibold text-gray-900">
                                {unit.unit_title}: {challenge.title}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {challenge.attempts.length} attempts •{' '}
                                {challenge.metrics.total_hints_used} hints used •{' '}
                                {Math.round(challenge.metrics.success_rate)}% success rate
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <div className="text-sm font-bold text-gray-900">
                                {challenge.metrics.correct_attempts}/
                                {challenge.metrics.total_attempts}
                              </div>
                              <div className="text-xs text-gray-600">Correct</div>
                            </div>
                          </div>
                        </button>

                        {/* Accordion Content */}
                        {isExpanded && (
                          <div className="p-6 bg-white space-y-4">
                            {challenge.attempts.map((attempt, index) => (
                              <AttemptCard
                                key={index}
                                attempt={attempt}
                                attemptNumber={index + 1}
                              />
                            ))}

                            {/* Hints Summary */}
                            {challenge.hints.length > 0 && (
                              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <h4 className="font-semibold text-blue-900 mb-2">
                                  💡 Hints Accessed ({challenge.hints.length})
                                </h4>
                                <div className="space-y-1 text-sm text-blue-800">
                                  {challenge.hints.map((hint, idx) => (
                                    <div key={idx}>
                                      Level {hint.hint_level} hint •{' '}
                                      {new Date(hint.accessed_at).toLocaleString()}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* No Attempts Message */}
              {data.units.every((unit) =>
                unit.challenges.every((c) => c.attempts.length === 0)
              ) && (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <p className="text-gray-500 text-lg">No attempts recorded yet</p>
                  <p className="text-gray-400 text-sm mt-2">
                    Attempts will appear here once the student starts working on challenges
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

StudentDetailPage.displayName = 'StudentDetailPage';
