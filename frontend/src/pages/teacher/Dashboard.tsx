import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TeacherLayout } from '@/components/teacher/TeacherLayout';
import { MetricsCard } from '@/components/teacher/MetricsCard';
import { ExportButton } from '@/components/teacher/ExportButton';
import { ImportModal } from '@/components/teacher/ImportModal';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { userService } from '@/services/userService';
import { showApiErrorToast } from '@/utils/toast';
import type { StudentListResponse } from '@/types';

export function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<StudentListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Fetch student data for metrics
  const fetchStudents = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await userService.getStudents({
        role: 'student',
        limit: 1000, // Get all students
      });
      setData(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
      await showApiErrorToast(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  // Calculate metrics
  const totalStudents = data?.total_count || 0;
  const activeStudents =
    data?.students.filter((s) => s.challenges_completed > 0).length || 0;

  const avgCompletionRate =
    data && data.students.length > 0
      ? Math.round(
          (data.students.reduce(
            (sum, s) => sum + (s.challenges_completed / 7) * 100,
            0
          ) /
            data.students.length)
        )
      : 0;

  const atRiskStudents =
    data?.students.filter((s) => {
      const completionRate = (s.challenges_completed / 7) * 100;
      const hasActivity = s.challenges_completed > 0;
      return hasActivity && completionRate < 30;
    }).length || 0;

  // Handle import success - refresh data
  const handleImportSuccess = () => {
    fetchStudents();
  };

  // Breadcrumbs
  const breadcrumbs = [{ label: 'Dashboard' }];

  // Loading state
  if (isLoading) {
    return (
      <TeacherLayout breadcrumbs={breadcrumbs}>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <LoadingSpinner />
            <p className="text-gray-600 mt-4">Loading dashboard...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <TeacherLayout breadcrumbs={breadcrumbs}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="border-l-4 border-red-500 bg-red-50 p-4">
            <div className="flex items-start">
              <span className="text-red-500 mr-2 mt-0.5">⚠</span>
              <div>
                <p className="text-sm font-medium text-red-800">
                  Error loading dashboard
                </p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout breadcrumbs={breadcrumbs}>
      {/* Welcome Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Welcome to Your Dashboard
        </h1>
        <p className="text-sm sm:text-base text-gray-600 mt-2">
          Monitor your class progress and manage students
        </p>
      </div>

      {/* Key Metrics */}
      <div className="mb-6 sm:mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">
          Class Overview
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <MetricsCard
            icon="👥"
            label="Total Students"
            value={totalStudents}
            subtitle={`${activeStudents} active`}
            color="blue"
          />
          <MetricsCard
            icon="✅"
            label="Active Students"
            value={activeStudents}
            subtitle={`${totalStudents > 0 ? Math.round((activeStudents / totalStudents) * 100) : 0}% of total`}
            color="green"
          />
          <MetricsCard
            icon="📈"
            label="Avg Completion"
            value={`${avgCompletionRate}%`}
            subtitle="Across all challenges"
            color={
              avgCompletionRate >= 70
                ? 'green'
                : avgCompletionRate >= 50
                ? 'yellow'
                : 'red'
            }
          />
          <MetricsCard
            icon="🚨"
            label="At-Risk Students"
            value={atRiskStudents}
            subtitle="< 30% completion"
            color={atRiskStudents > 0 ? 'red' : 'green'}
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-6 sm:mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {/* Import Students */}
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-white rounded-lg shadow p-4 sm:p-6 hover:shadow-lg transition-shadow text-left group min-h-[120px] active:bg-gray-50"
          >
            <div className="text-2xl sm:text-3xl mb-2 sm:mb-3">📤</div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1 group-hover:text-blue-600">
              Import Students
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Bulk upload student roster
            </p>
          </button>

          {/* Export Data */}
          <div className="bg-white rounded-lg shadow p-4 sm:p-6 hover:shadow-lg transition-shadow min-h-[120px]">
            <div className="text-2xl sm:text-3xl mb-2 sm:mb-3">📥</div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1">
              Export Data
            </h3>
            <p className="text-xs sm:text-sm text-gray-600 mb-3">
              Download student data
            </p>
            <ExportButton variant="outline" size="sm" />
          </div>

          {/* View Analytics */}
          <button
            onClick={() => navigate('/teacher/analytics')}
            className="bg-white rounded-lg shadow p-4 sm:p-6 hover:shadow-lg transition-shadow text-left group min-h-[120px] active:bg-gray-50"
          >
            <div className="text-2xl sm:text-3xl mb-2 sm:mb-3">📊</div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1 group-hover:text-blue-600">
              View Analytics
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Class-wide performance insights
            </p>
          </button>

          {/* View Reports */}
          <button
            onClick={() => navigate('/teacher/reports/weekly')}
            className="bg-white rounded-lg shadow p-4 sm:p-6 hover:shadow-lg transition-shadow text-left group min-h-[120px] active:bg-gray-50"
          >
            <div className="text-2xl sm:text-3xl mb-2 sm:mb-3">📝</div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1 group-hover:text-blue-600">
              Weekly Report
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              View this week's progress
            </p>
          </button>
        </div>
      </div>

      {/* Alerts */}
      {(atRiskStudents > 0 || avgCompletionRate < 50) && (
        <div className="mb-6 sm:mb-8">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3 sm:mb-4">
            Alerts
          </h2>
          <div className="space-y-3 sm:space-y-4">
            {/* At-Risk Students Alert */}
            {atRiskStudents > 0 && (
              <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-3 sm:p-4">
                <div className="flex items-start">
                  <span className="text-red-500 text-lg sm:text-xl mr-2 sm:mr-3 flex-shrink-0">
                    🚨
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm sm:text-base font-semibold text-red-900">
                      {atRiskStudents} Student{atRiskStudents !== 1 ? 's' : ''}{' '}
                      Need Attention
                    </h3>
                    <p className="text-xs sm:text-sm text-red-700 mt-1">
                      {atRiskStudents === 1
                        ? 'A student has'
                        : 'Some students have'}{' '}
                      less than 30% completion rate and may need additional
                      support.
                    </p>
                    <button
                      onClick={() => navigate('/teacher/analytics')}
                      className="text-xs sm:text-sm font-medium text-red-600 hover:text-red-800 mt-2 min-h-[44px] py-2 block"
                    >
                      View details →
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Low Engagement Alert */}
            {avgCompletionRate < 50 && (
              <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-3 sm:p-4">
                <div className="flex items-start">
                  <span className="text-yellow-500 text-lg sm:text-xl mr-2 sm:mr-3 flex-shrink-0">
                    ⚠
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm sm:text-base font-semibold text-yellow-900">
                      Low Class Engagement
                    </h3>
                    <p className="text-xs sm:text-sm text-yellow-700 mt-1">
                      Average completion rate is {avgCompletionRate}%. Consider
                      reviewing challenge difficulty or providing additional
                      support.
                    </p>
                    <button
                      onClick={() => navigate('/teacher/analytics')}
                      className="text-xs sm:text-sm font-medium text-yellow-600 hover:text-yellow-800 mt-2 min-h-[44px] py-2 block"
                    >
                      View analytics →
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Success Message - No Alerts */}
      {atRiskStudents === 0 && avgCompletionRate >= 50 && totalStudents > 0 && (
        <div className="mb-6 sm:mb-8">
          <div className="bg-green-50 border-l-4 border-green-500 rounded-lg p-3 sm:p-4">
            <div className="flex items-start">
              <span className="text-green-500 text-lg sm:text-xl mr-2 sm:mr-3 flex-shrink-0">
                ✅
              </span>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm sm:text-base font-semibold text-green-900">
                  Class Performing Well
                </h3>
                <p className="text-xs sm:text-sm text-green-700 mt-1">
                  Your students are making good progress! Average completion
                  rate is {avgCompletionRate}%.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={handleImportSuccess}
      />
    </TeacherLayout>
  );
}

Dashboard.displayName = 'Dashboard';
