import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { userService } from '@/services/userService';
import { StudentTable } from '@/components/teacher/StudentTable';
import { showApiErrorToast } from '@/utils/toast';
import type { StudentListResponse } from '@/types';

export function StudentListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [data, setData] = useState<StudentListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get query params from URL or defaults
  const sortBy = (searchParams.get('sort') as 'name' | 'points' | 'date') || 'name';
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 50; // Fixed page size
  const searchQuery = searchParams.get('search') || '';

  // Calculate offset from page
  const offset = (page - 1) * pageSize;

  // Fetch students on mount and when params change
  useEffect(() => {
    async function fetchStudents() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await userService.getStudents({
          role: 'student',
          sort: sortBy,
          offset,
          limit: pageSize,
        });
        setData(response);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load students';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchStudents();
  }, [sortBy, offset, pageSize]);

  // Handle sort change
  const handleSortChange = (newSort: 'name' | 'points' | 'date') => {
    setSearchParams({
      sort: newSort,
      page: '1', // Reset to first page on sort change
      ...(searchQuery && { search: searchQuery }),
    });
  };

  // Handle search change
  const handleSearchChange = (query: string) => {
    if (query) {
      setSearchParams({
        sort: sortBy,
        page: '1', // Reset to first page on search
        search: query,
      });
    } else {
      setSearchParams({
        sort: sortBy,
        page: '1',
      });
    }
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setSearchParams({
      sort: sortBy,
      page: newPage.toString(),
      ...(searchQuery && { search: searchQuery }),
    });
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Calculate pagination
  const totalPages = data ? Math.ceil(data.total_count / pageSize) : 0;
  const showPagination = totalPages > 1;

  // Handle student click
  const handleStudentClick = (studentId: number) => {
    navigate(`/teacher/students/${studentId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <span className="mr-3">👥</span>
                Students
              </h1>
              <p className="text-gray-600 mt-2">
                View and manage all students in your class
              </p>
            </div>
            {user && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Teacher</p>
                <p className="font-medium text-gray-900">{user.name}</p>
              </div>
            )}
          </div>

          {/* Search Bar */}
          <div className="mb-6">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full px-4 py-3 pl-11 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <div className="absolute left-3 top-3.5 text-gray-400">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Stats Summary */}
          {data && !isLoading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm text-blue-600 font-medium">
                  Total Students
                </div>
                <div className="text-2xl font-bold text-blue-900 mt-1">
                  {data.total_count}
                </div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm text-green-600 font-medium">
                  Active Students
                </div>
                <div className="text-2xl font-bold text-green-900 mt-1">
                  {data.students.filter((s) => s.challenges_completed > 0).length}
                </div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="text-sm text-yellow-600 font-medium">
                  Average Progress
                </div>
                <div className="text-2xl font-bold text-yellow-900 mt-1">
                  {data.students.length > 0
                    ? Math.round(
                        (data.students.reduce(
                          (sum, s) => sum + s.challenges_completed,
                          0
                        ) /
                          data.students.length /
                          7) *
                          100
                      )
                    : 0}
                  %
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <div className="flex items-start">
                <span className="text-red-500 mr-2 mt-0.5">⚠</span>
                <div>
                  <p className="text-sm font-medium text-red-800">
                    Error loading students
                  </p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Student Table */}
        <StudentTable
          students={data?.students || []}
          isLoading={isLoading}
          sortBy={sortBy}
          onSortChange={handleSortChange}
          searchQuery={searchQuery}
          onStudentClick={handleStudentClick}
        />

        {/* Pagination */}
        {showPagination && !isLoading && !error && (
          <div className="mt-6 bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              {/* Page Info */}
              <div className="text-sm text-gray-600">
                Showing {offset + 1} to{' '}
                {Math.min(offset + pageSize, data?.total_count || 0)} of{' '}
                {data?.total_count || 0} students
              </div>

              {/* Page Buttons */}
              <div className="flex items-center space-x-2">
                {/* Previous Button */}
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    page === 1
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Previous
                </button>

                {/* Page Numbers */}
                <div className="hidden md:flex items-center space-x-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => {
                      // Show first page, last page, current page, and pages around current
                      return (
                        p === 1 ||
                        p === totalPages ||
                        Math.abs(p - page) <= 1
                      );
                    })
                    .map((p, idx, arr) => {
                      // Add ellipsis if there's a gap
                      const showEllipsis = idx > 0 && p - arr[idx - 1] > 1;
                      return (
                        <div key={p} className="flex items-center">
                          {showEllipsis && (
                            <span className="px-2 text-gray-400">...</span>
                          )}
                          <button
                            onClick={() => handlePageChange(p)}
                            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                              p === page
                                ? 'bg-blue-600 text-white'
                                : 'text-gray-700 hover:bg-gray-100'
                            }`}
                          >
                            {p}
                          </button>
                        </div>
                      );
                    })}
                </div>

                {/* Mobile Page Indicator */}
                <div className="md:hidden text-sm text-gray-600">
                  Page {page} of {totalPages}
                </div>

                {/* Next Button */}
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === totalPages}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    page === totalPages
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
