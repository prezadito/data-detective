import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { customChallengeService } from '@/services/customChallengeService';
import type { CustomChallengeListItem } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function ChallengeLibraryPage() {
  const navigate = useNavigate();
  const [challenges, setChallenges] = useState<CustomChallengeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    loadChallenges();
  }, [filterActive]);

  const loadChallenges = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await customChallengeService.getChallenges({
        is_active: filterActive,
      });
      setChallenges(response.challenges);
    } catch (err) {
      setError('Failed to load challenges');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"? This will also delete all student progress on this challenge.`)) {
      return;
    }

    try {
      await customChallengeService.deleteChallenge(id);
      await loadChallenges();
    } catch (err) {
      alert('Failed to delete challenge');
      console.error(err);
    }
  };

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    try {
      await customChallengeService.updateChallenge(id, {
        is_active: !currentStatus,
      });
      await loadChallenges();
    } catch (err) {
      alert('Failed to update challenge');
      console.error(err);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'hard':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-600">{error}</p>
        <Button onClick={loadChallenges}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">My Custom Challenges</h1>
          <p className="text-gray-600 mt-2">Manage your custom SQL challenges</p>
        </div>
        <Button onClick={() => navigate('/challenges/custom/new')}>
          Create Challenge
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="mb-6 flex gap-2">
        <Button
          variant={filterActive === undefined ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilterActive(undefined)}
        >
          All
        </Button>
        <Button
          variant={filterActive === true ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilterActive(true)}
        >
          Active
        </Button>
        <Button
          variant={filterActive === false ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilterActive(false)}
        >
          Inactive
        </Button>
      </div>

      {challenges.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">
            {filterActive === undefined
              ? 'No challenges yet'
              : filterActive
              ? 'No active challenges'
              : 'No inactive challenges'}
          </h3>
          <p className="text-gray-600 mb-4">
            {filterActive === undefined
              ? 'Create your first custom challenge to get started'
              : 'Try changing the filter'}
          </p>
          {filterActive === undefined && (
            <Button onClick={() => navigate('/challenges/custom/new')}>
              Create Your First Challenge
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {challenges.map((challenge) => (
            <div
              key={challenge.id}
              className={`bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow ${
                !challenge.is_active ? 'opacity-60' : ''
              }`}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-1 line-clamp-2">
                    {challenge.title}
                  </h3>
                  <p className="text-sm text-gray-600">{challenge.dataset_name}</p>
                </div>
                {!challenge.is_active && (
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                    Inactive
                  </span>
                )}
              </div>

              {/* Badges */}
              <div className="flex gap-2 mb-4">
                <span
                  className={`text-xs px-2 py-1 rounded capitalize ${getDifficultyColor(
                    challenge.difficulty
                  )}`}
                >
                  {challenge.difficulty}
                </span>
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">
                  {challenge.points} pts
                </span>
              </div>

              {/* Stats */}
              <div className="space-y-2 text-sm text-gray-500 mb-4 pb-4 border-b">
                <div className="flex justify-between">
                  <span>Submissions:</span>
                  <span className="font-medium">{challenge.submission_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Success Rate:</span>
                  <span className="font-medium">
                    {challenge.completion_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="font-medium">
                    {new Date(challenge.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/challenges/custom/${challenge.id}`)}
                >
                  View
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggleActive(challenge.id, challenge.is_active)}
                >
                  {challenge.is_active ? 'Deactivate' : 'Activate'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/challenges/custom/${challenge.id}/edit`)}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(challenge.id, challenge.title)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
