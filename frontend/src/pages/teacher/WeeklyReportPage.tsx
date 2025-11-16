import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { reportService } from '@/services/reportService';
import { TeacherLayout } from '@/components/teacher/TeacherLayout';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MetricsCard } from '@/components/teacher/MetricsCard';
import { showApiErrorToast } from '@/utils/toast';
import type { WeeklyReportResponse } from '@/types';

export function WeeklyReportPage() {
  const { user } = useAuth();
  const [data, setData] = useState<WeeklyReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch weekly report data on mount
  useEffect(() => {
    async function fetchWeeklyReport() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await reportService.getWeeklyReport();
        setData(response);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load weekly report';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchWeeklyReport();
  }, []);

  // Breadcrumbs
  const breadcrumbs = [
    { label: 'Dashboard', path: '/teacher/dashboard' },
    { label: 'Reports', path: '/teacher/reports/weekly' },
    { label: 'Weekly' },
  ];

  // Loading state
  if (isLoading) {
    return (
      <TeacherLayout breadcrumbs={breadcrumbs}>
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <LoadingSpinner />
          <p className="text-gray-600 mt-4">Loading weekly report...</p>
        </div>
      </TeacherLayout>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <TeacherLayout breadcrumbs={breadcrumbs}>
        <div className="bg-white rounded-lg shadow-lg p-12">
          <div className="border-l-4 border-red-500 bg-red-50 p-4">
            <div className="flex items-start">
              <span className="text-red-500 mr-2 mt-0.5">⚠</span>
              <div>
                <p className="text-sm font-medium text-red-800">
                  Error loading weekly report
                </p>
                <p className="text-sm text-red-700 mt-1">
                  {error || 'Weekly report data not available'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout breadcrumbs={breadcrumbs}>
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <span className="mr-3">📊</span>
                Weekly Progress Report
              </h1>
              <p className="text-gray-600 mt-2">
                Activity summary for the past 7 days
              </p>
            </div>
            {user && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Teacher</p>
                <p className="font-medium text-gray-900">{user.name}</p>
              </div>
            )}
          </div>

          {/* Generated timestamp */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Generated: {new Date(data.generated_at).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Data is cached for 1 hour. Refresh the page to get the latest data.
            </p>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricsCard
            icon="👥"
            label="Active Students"
            value={data.students_active}
            subtitle="Past 7 days"
            color="blue"
          />
          <MetricsCard
            icon="✓"
            label="Total Completions"
            value={data.total_completions}
            subtitle="Challenges completed"
            color="green"
          />
          <MetricsCard
            icon="📊"
            label="Avg Points"
            value={Math.round(data.avg_points_per_student)}
            subtitle="Per active student"
            color="gray"
          />
          <MetricsCard
            icon="🏆"
            label="Top Performer"
            value={
              data.top_performers.length > 0
                ? data.top_performers[0].points_this_week
                : 0
            }
            subtitle={
              data.top_performers.length > 0
                ? data.top_performers[0].student_name
                : 'No data'
            }
            color="yellow"
          />
        </div>

        {/* Top Performers Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="mr-2">🏆</span>
              Top Performers
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Students with the highest points earned this week
            </p>
          </div>

          {data.top_performers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Rank
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Student Name
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Completions
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Points
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.top_performers.map((student, index) => (
                    <tr
                      key={index}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">
                            {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : ''}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {index + 1}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {student.student_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {student.completions_this_week}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">
                          {student.points_this_week}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-500">
                📭 No student completions this week
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Encourage students to start challenges!
              </p>
            </div>
          )}
        </div>

        {/* Struggling Students Section */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="mr-2">⚠️</span>
              Students Needing Support
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Students with fewer than 3 completions this week
            </p>
          </div>

          {data.struggling_students.length > 0 ? (
            <div className="overflow-x-auto">
              <div
                className="mb-4 p-4 bg-yellow-50 border-l-4 border-yellow-400"
                role="alert"
              >
                <p className="text-sm text-yellow-800 font-medium">
                  {data.struggling_students.length} student(s) may need
                  additional support
                </p>
              </div>

              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Student Name
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Completions
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      Points
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.struggling_students.map((student, index) => (
                    <tr
                      key={index}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {student.student_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {student.completions_this_week}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {student.points_this_week}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-green-50 rounded-lg border-2 border-green-200">
              <p className="text-lg font-semibold text-green-800">
                🎉 Great work!
              </p>
              <p className="text-sm text-green-700 mt-2">
                All active students completed 3 or more challenges this week
              </p>
            </div>
          )}
        </div>
      </div>
    </TeacherLayout>
  );
}
