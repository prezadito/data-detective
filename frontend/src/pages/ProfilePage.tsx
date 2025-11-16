import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApi } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { userService } from '@/services/userService';
import { progressService } from '@/services/progressService';
import { leaderboardService } from '@/services/leaderboardService';
import type { User, ProgressSummaryResponse, LeaderboardResponse } from '@/types';

export function ProfilePage() {
  const { user: authUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [userRank, setUserRank] = useState<number | null>(null);

  // Fetch user profile
  const {
    data: user,
    isLoading: isLoadingUser,
    error: userError,
    execute: fetchUser,
  } = useApi<User, []>(userService.getCurrentUser);

  // Fetch progress stats (non-critical - don't show error toast)
  const {
    data: progressData,
    isLoading: isLoadingProgress,
    error: progressError,
    execute: fetchProgress,
  } = useApi<ProgressSummaryResponse, []>(progressService.getMyProgress, {
    showErrorToast: false,
  });

  // Fetch leaderboard to calculate rank (non-critical - don't show error toast)
  const {
    data: leaderboardData,
    isLoading: isLoadingLeaderboard,
    execute: fetchLeaderboard,
  } = useApi<LeaderboardResponse, []>(leaderboardService.getLeaderboard, {
    showErrorToast: false,
  });

  // Update profile
  const { execute: updateProfile, isLoading: isUpdating } = useApi(
    userService.updateUserProfile,
    {
      successMessage: 'Profile updated successfully!',
      onSuccess: () => {
        setIsEditing(false);
        // Re-fetch user data to ensure sync
        fetchUser();
      },
    }
  );

  // Load data on mount
  useEffect(() => {
    fetchUser();
    fetchProgress();
    fetchLeaderboard();
  }, []);

  // Calculate user rank when leaderboard data is available
  useEffect(() => {
    if (leaderboardData && authUser) {
      const entry = leaderboardData.entries.find(
        (e) => e.student_name === authUser.name
      );
      setUserRank(entry?.rank || null);
    }
  }, [leaderboardData, authUser]);

  // Initialize edited name when user data loads
  useEffect(() => {
    if (user) {
      setEditedName(user.name);
    }
  }, [user]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedName(user?.name || '');
  };

  const handleSave = async () => {
    if (!editedName.trim()) {
      return;
    }
    await updateProfile({ name: editedName.trim() });
  };

  // Only block on critical user data loading
  // Loading state - only show if user data hasn't loaded yet
  if (isLoadingUser && !user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSpinner size="lg" text="Loading profile..." />
        </main>
      </div>
    );
  }

  // Error state - only error out if critical user data fails
  // Progress and leaderboard errors are non-fatal
  if (userError || !user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-900 mb-2">
              Error Loading Profile
            </h2>
            <p className="text-red-700">
              Unable to load your profile. Please try again later.
            </p>
          </div>
        </main>
      </div>
    );
  }

  // Format date
  const joinedDate = new Date(user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
          <p className="mt-2 text-gray-600">
            Manage your account information and view your progress
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* User Info Card */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">
                Account Information
              </h2>
              {!isEditing && (
                <Button onClick={handleEdit} variant="outline" size="sm">
                  Edit Name
                </Button>
              )}
            </div>

            <div className="space-y-4">
              {/* Name Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                {isEditing ? (
                  <div className="flex gap-2">
                    <Input
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      placeholder="Enter your name"
                      className="flex-1"
                    />
                    <Button
                      onClick={handleSave}
                      size="sm"
                      isLoading={isUpdating}
                      disabled={!editedName.trim()}
                    >
                      Save
                    </Button>
                    <Button
                      onClick={handleCancel}
                      variant="outline"
                      size="sm"
                      disabled={isUpdating}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <p className="text-gray-900 text-lg">{user.name}</p>
                )}
              </div>

              {/* Email Field (readonly) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <p className="text-gray-900">{user.email}</p>
              </div>

              {/* Role Field (readonly) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 capitalize">
                  {user.role}
                </span>
              </div>

              {/* Joined Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Member Since
                </label>
                <p className="text-gray-900">{joinedDate}</p>
              </div>
            </div>
          </div>

          {/* Stats Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              My Statistics
            </h2>

            {isLoadingProgress ? (
              <LoadingSpinner size="sm" text="Loading stats..." />
            ) : progressError ? (
              <div className="border-l-4 border-orange-500 bg-orange-50 p-4">
                <p className="text-sm font-medium text-orange-700">
                  Unable to load statistics
                </p>
                <p className="text-xs text-orange-600 mt-1">
                  Your progress data could not be loaded at this time.
                </p>
              </div>
            ) : progressData ? (
              <div className="space-y-4">
                {/* Total Points */}
                <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
                  <p className="text-sm font-medium text-blue-700 uppercase tracking-wide">
                    Total Points
                  </p>
                  <p className="text-3xl font-bold text-blue-900 mt-1">
                    {progressData.summary.total_points}
                  </p>
                </div>

                {/* Challenges Completed */}
                <div className="border-l-4 border-green-500 bg-green-50 p-4">
                  <p className="text-sm font-medium text-green-700 uppercase tracking-wide">
                    Challenges Completed
                  </p>
                  <p className="text-3xl font-bold text-green-900 mt-1">
                    {progressData.summary.total_completed}
                    <span className="text-lg text-green-700"> / 7</span>
                  </p>
                </div>

                {/* Completion Percentage */}
                <div className="border-l-4 border-purple-500 bg-purple-50 p-4">
                  <p className="text-sm font-medium text-purple-700 uppercase tracking-wide">
                    Completion
                  </p>
                  <p className="text-3xl font-bold text-purple-900 mt-1">
                    {progressData.summary.completion_percentage.toFixed(0)}%
                  </p>
                </div>

                {/* Leaderboard Rank */}
                {user.role === 'student' && (
                  <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4">
                    <p className="text-sm font-medium text-yellow-700 uppercase tracking-wide">
                      Leaderboard Rank
                    </p>
                    <p className="text-3xl font-bold text-yellow-900 mt-1">
                      {isLoadingLeaderboard ? (
                        <span className="text-lg">Loading...</span>
                      ) : userRank ? (
                        `#${userRank}`
                      ) : (
                        <span className="text-lg text-yellow-700">
                          Not ranked
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="border-l-4 border-gray-500 bg-gray-50 p-4">
                <p className="text-sm font-medium text-gray-700">
                  No progress yet
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  Complete challenges to see your statistics here.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
