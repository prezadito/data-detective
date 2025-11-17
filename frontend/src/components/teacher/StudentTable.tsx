import { memo, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { StudentWithStats } from '@/types';

// Helper functions extracted outside component to prevent recreation on every render

/**
 * Calculate completion percentage (out of 7 total challenges)
 */
function getCompletionPercentage(completed: number): number {
  return Math.round((completed / 7) * 100);
}

/**
 * Get color for completion percentage
 */
function getCompletionColor(percentage: number): string {
  if (percentage >= 80) return 'text-green-600 bg-green-50';
  if (percentage >= 50) return 'text-blue-600 bg-blue-50';
  if (percentage >= 20) return 'text-yellow-600 bg-yellow-50';
  return 'text-gray-600 bg-gray-50';
}

/**
 * Format date (e.g., "Jan 15, 2025")
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Calculate days since creation
 */
function getDaysSince(dateString: string): number {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
}

/**
 * Get activity indicator
 */
function getActivityIndicator(createdAt: string): { text: string; color: string } {
  const days = getDaysSince(createdAt);
  if (days <= 1) return { text: 'Active today', color: 'text-green-600' };
  if (days <= 7) return { text: 'Active this week', color: 'text-blue-600' };
  if (days <= 30) return { text: 'Active this month', color: 'text-yellow-600' };
  return { text: `${days} days ago`, color: 'text-gray-600' };
}

export interface StudentTableProps {
  /**
   * Array of students with statistics
   */
  students: StudentWithStats[];

  /**
   * Whether data is loading
   * @default false
   */
  isLoading?: boolean;

  /**
   * Current sort field
   */
  sortBy?: 'name' | 'points' | 'date';

  /**
   * Callback when sort changes
   */
  onSortChange?: (sortBy: 'name' | 'points' | 'date') => void;

  /**
   * Search query for filtering
   */
  searchQuery?: string;

  /**
   * Callback when student is clicked
   */
  onStudentClick?: (studentId: number) => void;
}

/**
 * StudentTable component displays student list with sortable columns
 * Memoized to prevent unnecessary re-renders when parent updates
 */
export const StudentTable = memo(function StudentTable({
  students,
  isLoading = false,
  sortBy = 'name',
  onSortChange,
  searchQuery = '',
  onStudentClick,
}: StudentTableProps) {
  const navigate = useNavigate();

  // Filter students by search query (client-side, memoized to prevent recalculation on every render)
  const filteredStudents = useMemo(() =>
    students.filter((student) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        student.name.toLowerCase().includes(query) ||
        student.email.toLowerCase().includes(query)
      );
    }),
    [students, searchQuery]
  );

  // Get sort icon (memoized since it depends on sortBy prop)
  const getSortIcon = useCallback((field: 'name' | 'points' | 'date'): string => {
    if (sortBy === field) {
      return field === 'points' ? '↓' : '↑';
    }
    return '⇅';
  }, [sortBy]);

  // Handle student click
  const handleStudentClick = (studentId: number) => {
    if (onStudentClick) {
      onStudentClick(studentId);
    } else {
      navigate(`/teacher/students/${studentId}`);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-12 text-center">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto"></div>
          </div>
          <p className="text-gray-600 mt-4">Loading students...</p>
        </div>
      </div>
    );
  }

  if (filteredStudents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <div className="text-gray-400 text-6xl mb-4">👥</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {searchQuery ? 'No students found' : 'No students yet'}
        </h3>
        <p className="text-gray-600">
          {searchQuery
            ? 'Try adjusting your search query'
            : 'Students will appear here once they register'}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th
                className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => onSortChange?.('name')}
              >
                <div className="flex items-center space-x-1">
                  <span>Student</span>
                  <span className="text-gray-500">{getSortIcon('name')}</span>
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Email
              </th>
              <th
                className="px-6 py-4 text-right text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => onSortChange?.('points')}
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Points</span>
                  <span className="text-gray-500">{getSortIcon('points')}</span>
                </div>
              </th>
              <th className="px-6 py-4 text-right text-xs font-medium text-gray-700 uppercase tracking-wider">
                Completion
              </th>
              <th
                className="px-6 py-4 text-right text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => onSortChange?.('date')}
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Last Active</span>
                  <span className="text-gray-500">{getSortIcon('date')}</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredStudents.map((student) => {
              const completionPct = getCompletionPercentage(student.challenges_completed);
              const completionColor = getCompletionColor(completionPct);
              const activity = getActivityIndicator(student.created_at);

              return (
                <tr
                  key={student.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleStudentClick(student.id)}
                >
                  {/* Student Name */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-blue-600 font-medium text-sm">
                          {student.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {student.name}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Email */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-600">{student.email}</div>
                  </td>

                  {/* Points */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <span className="text-yellow-500 mr-1">🏆</span>
                      <span className="text-sm font-bold text-gray-900">
                        {student.total_points}
                      </span>
                    </div>
                  </td>

                  {/* Completion */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${completionColor}`}
                      >
                        {completionPct}%
                      </span>
                      <span className="text-xs text-gray-500 ml-2">
                        ({student.challenges_completed}/7)
                      </span>
                    </div>
                  </td>

                  {/* Last Active */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="text-sm">
                      <div className={`font-medium ${activity.color}`}>
                        {activity.text}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(student.created_at)}
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden divide-y divide-gray-200">
        {filteredStudents.map((student) => {
          const completionPct = getCompletionPercentage(student.challenges_completed);
          const completionColor = getCompletionColor(completionPct);
          const activity = getActivityIndicator(student.created_at);

          return (
            <div
              key={student.id}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => handleStudentClick(student.id)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 font-medium text-sm">
                      {student.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="ml-3">
                    <div className="text-sm font-medium text-gray-900">
                      {student.name}
                    </div>
                    <div className="text-xs text-gray-500">{student.email}</div>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="flex items-center">
                  <span className="text-yellow-500 mr-1">🏆</span>
                  <span className="text-sm">
                    <span className="font-bold text-gray-900">
                      {student.total_points}
                    </span>
                    <span className="text-gray-500"> pts</span>
                  </span>
                </div>
                <div className="flex items-center justify-end">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${completionColor}`}
                  >
                    {completionPct}% ({student.challenges_completed}/7)
                  </span>
                </div>
              </div>

              {/* Activity */}
              <div className="mt-3 text-xs">
                <span className={`font-medium ${activity.color}`}>
                  {activity.text}
                </span>
                <span className="text-gray-500"> • {formatDate(student.created_at)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});
