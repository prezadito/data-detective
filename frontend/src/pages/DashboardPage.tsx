import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useDatabase } from '@/hooks/useDatabase';
import { Navigation } from '@/components/navigation/Navigation';
import { QueryEditor } from '@/components/query';
import { ChallengeCard } from '@/components/challenge';
import { challengeService } from '@/services/challengeService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { ChallengeDetail } from '@/types';

export function DashboardPage() {
  const { user } = useAuth();
  const { isLoading, error } = useDatabase();
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [challengeLoading, setChallengeLoading] = useState(true);
  const [challengeError, setChallengeError] = useState<string | null>(null);

  // Fetch a sample challenge (Unit 1, Challenge 1) on mount
  useEffect(() => {
    async function fetchChallenge() {
      try {
        setChallengeLoading(true);
        const data = await challengeService.getChallengeDetail(1, 1);
        setChallenge(data);
      } catch (err) {
        setChallengeError(err instanceof Error ? err.message : 'Failed to load challenge');
      } finally {
        setChallengeLoading(false);
      }
    }

    fetchChallenge();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
              <p className="text-sm text-blue-700">
                <strong>User ID:</strong> {user?.id}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Email:</strong> {user?.email}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Role:</strong> {user?.role}
              </p>
            </div>
          </div>
        </div>

        {/* Database Status */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4">
              <p className="text-sm text-yellow-700">Loading database...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <p className="text-sm text-red-700">
                <strong>Database Error:</strong> {error.message}
              </p>
            </div>
          </div>
        )}

        {/* Challenge Card Demo */}
        <div className="mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Challenge Display Demo
          </h3>

          {challengeLoading && (
            <div className="bg-white rounded-lg shadow p-12 flex items-center justify-center">
              <LoadingSpinner />
              <span className="ml-3 text-gray-600">Loading challenge...</span>
            </div>
          )}

          {challengeError && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="border-l-4 border-red-500 bg-red-50 p-4">
                <p className="text-sm text-red-700">
                  <strong>Error:</strong> {challengeError}
                </p>
              </div>
            </div>
          )}

          {challenge && (
            <ChallengeCard
              challenge={challenge}
              showHints={true}
              showSchema={true}
              showExpectedOutput={true}
              showSampleQuery={user?.role === 'teacher'}
              onHintsUsedChange={(count) => {
                console.log('Hints used:', count);
              }}
            />
          )}
        </div>

        {/* SQL Query Editor */}
        <QueryEditor
          initialQuery="SELECT * FROM movies LIMIT 10;"
          onQueryExecute={(result) => {
            console.log('Query executed:', result);
          }}
        />
      </main>
    </div>
  );
}
