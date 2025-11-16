import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useAuth } from '@/contexts/AuthContext';
import { analyticsService } from '@/services/analyticsService';
import { userService } from '@/services/userService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MetricsCard } from '@/components/teacher/MetricsCard';
import { ChartContainer } from '@/components/teacher/ChartContainer';
import { showApiErrorToast } from '@/utils/toast';
import type { ClassAnalyticsResponse, StudentWithStats } from '@/types';

export function AnalyticsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<ClassAnalyticsResponse | null>(null);
  const [atRiskStudents, setAtRiskStudents] = useState<StudentWithStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch analytics data on mount
  useEffect(() => {
    async function fetchAnalytics() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await analyticsService.getClassAnalytics();
        setData(response);

        // Fetch student list to identify at-risk students
        const studentsResponse = await userService.getStudents({
          role: 'student',
          limit: 1000, // Get all students
        });

        // Identify at-risk students: low success rate, low completion
        const atRisk = studentsResponse.students.filter((student) => {
          const completionRate = (student.challenges_completed / 7) * 100;
          const hasActivity = student.total_points > 0;
          return hasActivity && completionRate < 30; // Less than 30% completion
        });

        setAtRiskStudents(atRisk);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load analytics';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnalytics();
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <LoadingSpinner />
            <p className="text-gray-600 mt-4">Loading class analytics...</p>
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
                    Error loading analytics
                  </p>
                  <p className="text-sm text-red-700 mt-1">
                    {error || 'Analytics data not available'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Transform weekly trends for chart
  const weeklyTrendsData = data.weekly_trends.map((trend) => ({
    week: new Date(trend.week_start_date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    completions: trend.completions,
    points: trend.total_points_earned,
    students: trend.unique_students,
  }));

  // Transform challenge data for chart
  const challengeData = data.challenges.map((challenge) => ({
    name: challenge.challenge_title.length > 20
      ? challenge.challenge_title.substring(0, 20) + '...'
      : challenge.challenge_title,
    fullName: challenge.challenge_title,
    successRate: Math.round(challenge.success_rate),
    attempts: challenge.total_attempts,
    correctAttempts: challenge.correct_attempts,
  }));

  // Custom bar color based on success rate
  const getBarColor = (successRate: number) => {
    if (successRate >= 70) return '#10b981'; // green
    if (successRate >= 50) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <span className="mr-3">📊</span>
                Class Analytics
              </h1>
              <p className="text-gray-600 mt-2">
                Comprehensive insights into class performance and trends
              </p>
            </div>
            {user && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Teacher</p>
                <p className="font-medium text-gray-900">{user.name}</p>
              </div>
            )}
          </div>

          {/* Cache Info */}
          <div className="text-xs text-gray-500 mt-4">
            Generated: {new Date(data.generated_at).toLocaleString()} •
            Cache expires: {new Date(data.cache_expires_at).toLocaleTimeString()}
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Key Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsCard
              icon="👥"
              label="Total Students"
              value={data.metrics.total_students}
              subtitle={`${data.metrics.active_students} active`}
              color="blue"
            />
            <MetricsCard
              icon="📊"
              label="Avg Completion"
              value={`${Math.round(data.metrics.avg_completion_rate)}%`}
              subtitle={`${data.metrics.total_challenges_completed} total completions`}
              color={
                data.metrics.avg_completion_rate >= 70
                  ? 'green'
                  : data.metrics.avg_completion_rate >= 50
                  ? 'yellow'
                  : 'red'
              }
            />
            <MetricsCard
              icon="🏆"
              label="Median Points"
              value={data.metrics.median_points}
              subtitle={`P25: ${data.metrics.percentile_25} • P75: ${data.metrics.percentile_75}`}
              color="blue"
            />
            <MetricsCard
              icon="✓"
              label="Success Rate"
              value={`${Math.round(data.metrics.avg_success_rate)}%`}
              subtitle={`${data.metrics.total_attempts} total attempts`}
              color={
                data.metrics.avg_success_rate >= 70
                  ? 'green'
                  : data.metrics.avg_success_rate >= 50
                  ? 'yellow'
                  : 'red'
              }
            />
          </div>
        </div>

        {/* Weekly Trends Chart */}
        <div className="mb-8">
          <ChartContainer
            title="Weekly Trends"
            subtitle="Completions and points earned over the past 4 weeks"
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={weeklyTrendsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis yAxisId="left" label={{ value: 'Completions', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Points', angle: 90, position: 'insideRight' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #ccc',
                    borderRadius: '8px',
                    padding: '8px',
                  }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="completions"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Completions"
                  dot={{ r: 4 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="points"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Points Earned"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Challenge Performance Chart */}
        <div className="mb-8">
          <ChartContainer
            title="Challenge Performance"
            subtitle="Success rate for each challenge across all students"
          >
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={challengeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                />
                <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #ccc',
                    borderRadius: '8px',
                    padding: '8px',
                  }}
                  formatter={(value: number, name: string, props: any) => {
                    if (name === 'Success Rate') {
                      return [
                        `${value}% (${props.payload.correctAttempts}/${props.payload.attempts})`,
                        props.payload.fullName,
                      ];
                    }
                    return [value, name];
                  }}
                />
                <Bar
                  dataKey="successRate"
                  name="Success Rate"
                  radius={[4, 4, 0, 0]}
                  fill="#3b82f6"
                >
                  {challengeData.map((entry, index) => (
                    <rect
                      key={`bar-${index}`}
                      fill={getBarColor(entry.successRate)}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Difficulty Distribution */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Difficulty Distribution
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Easiest Challenges */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-4 flex items-center">
                <span className="mr-2">✓</span>
                Easiest Challenges
              </h3>
              <div className="space-y-3">
                {data.difficulty_distribution.easiest_challenges.map((challenge, index) => (
                  <div
                    key={`${challenge.unit_id}-${challenge.challenge_id}`}
                    className="bg-green-50 border border-green-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold text-green-700">
                        #{index + 1}
                      </span>
                      <span className="text-2xl font-bold text-green-900">
                        {Math.round(challenge.success_rate)}%
                      </span>
                    </div>
                    <h4 className="font-semibold text-green-900 mb-1">
                      {challenge.challenge_title}
                    </h4>
                    <p className="text-sm text-green-700">
                      {challenge.total_attempts} attempts • {challenge.correct_attempts} correct
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Hardest Challenges */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center">
                <span className="mr-2">⚠</span>
                Hardest Challenges
              </h3>
              <div className="space-y-3">
                {data.difficulty_distribution.hardest_challenges.map((challenge, index) => (
                  <div
                    key={`${challenge.unit_id}-${challenge.challenge_id}`}
                    className="bg-red-50 border border-red-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold text-red-700">
                        #{index + 1}
                      </span>
                      <span className="text-2xl font-bold text-red-900">
                        {Math.round(challenge.success_rate)}%
                      </span>
                    </div>
                    <h4 className="font-semibold text-red-900 mb-1">
                      {challenge.challenge_title}
                    </h4>
                    <p className="text-sm text-red-700">
                      {challenge.total_attempts} attempts • {challenge.correct_attempts} correct •{' '}
                      {challenge.avg_hints_per_attempt.toFixed(1)} avg hints
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* At-Risk Students */}
        {atRiskStudents.length > 0 && (
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <span className="mr-2">🚨</span>
                At-Risk Students
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Students with less than 30% completion rate who may need additional support
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Student
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Completion
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Points
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {atRiskStudents.map((student) => (
                      <tr key={student.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{student.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{student.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm">
                            <span className="font-medium text-red-600">
                              {Math.round((student.challenges_completed / 7) * 100)}%
                            </span>
                            <span className="text-gray-500 ml-1">
                              ({student.challenges_completed}/7)
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{student.total_points}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => navigate(`/teacher/students/${student.id}`)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            View Details →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* No At-Risk Students */}
        {atRiskStudents.length === 0 && data.metrics.active_students > 0 && (
          <div className="mb-8">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center">
                <span className="text-green-500 text-2xl mr-3">✓</span>
                <div>
                  <h3 className="font-semibold text-green-900">
                    No At-Risk Students
                  </h3>
                  <p className="text-sm text-green-700 mt-1">
                    All active students are making good progress!
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

AnalyticsPage.displayName = 'AnalyticsPage';
