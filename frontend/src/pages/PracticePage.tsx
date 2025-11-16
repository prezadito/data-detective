import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { challengeService } from '@/services/challengeService';
import { ChallengeCard } from '@/components/challenge';
import { QueryEditor } from '@/components/query';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { showApiErrorToast, showSuccessToast } from '@/utils/toast';
import type { ChallengeDetail, ProgressResponse } from '@/types';

const TOTAL_UNITS = 3;
const CHALLENGES_PER_UNIT: Record<number, number> = {
  1: 3, // Unit 1: SELECT Basics
  2: 2, // Unit 2: JOINs
  3: 2, // Unit 3: Aggregations
};

export function PracticePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse URL params or use defaults
  const initialUnitId = parseInt(searchParams.get('unit') || '1', 10);
  const initialChallengeId = parseInt(searchParams.get('challenge') || '1', 10);

  const [currentUnitId, setCurrentUnitId] = useState(initialUnitId);
  const [currentChallengeId, setCurrentChallengeId] = useState(initialChallengeId);
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [hintsUsed, setHintsUsed] = useState(0);

  // LocalStorage keys
  const getDraftKey = useCallback((unitId: number, challengeId: number) => {
    return `practice_query_draft_${unitId}_${challengeId}`;
  }, []);

  // Load challenge
  const loadChallenge = useCallback(
    async (unitId: number, challengeId: number) => {
      try {
        setIsLoading(true);
        setError(null);

        const data = await challengeService.getChallengeDetail(unitId, challengeId);
        setChallenge(data);

        // Load saved draft
        const draftKey = getDraftKey(unitId, challengeId);
        const savedDraft = localStorage.getItem(draftKey);
        if (savedDraft) {
          setQuery(savedDraft);
        } else {
          setQuery('');
        }

        // Reset hints
        setHintsUsed(0);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load challenge';
        setError(errorMessage);
        await showApiErrorToast(err);
      } finally {
        setIsLoading(false);
      }
    },
    [getDraftKey]
  );

  // Load challenge when unit/challenge changes
  useEffect(() => {
    loadChallenge(currentUnitId, currentChallengeId);
  }, [currentUnitId, currentChallengeId, loadChallenge]);

  // Update URL when unit/challenge changes
  useEffect(() => {
    setSearchParams({ unit: String(currentUnitId), challenge: String(currentChallengeId) });
    // Save current position
    localStorage.setItem('practice_current_unit', String(currentUnitId));
    localStorage.setItem('practice_current_challenge', String(currentChallengeId));
  }, [currentUnitId, currentChallengeId, setSearchParams]);

  // Auto-save query draft (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query) {
        const draftKey = getDraftKey(currentUnitId, currentChallengeId);
        localStorage.setItem(draftKey, query);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [query, currentUnitId, currentChallengeId, getDraftKey]);

  // Navigation functions
  const canGoPrevious = (): boolean => {
    return !(currentUnitId === 1 && currentChallengeId === 1);
  };

  const canGoNext = (): boolean => {
    const maxChallengesInUnit = CHALLENGES_PER_UNIT[currentUnitId] || 0;
    return !(currentUnitId === TOTAL_UNITS && currentChallengeId === maxChallengesInUnit);
  };

  const goToPreviousChallenge = () => {
    if (!canGoPrevious()) return;

    if (currentChallengeId > 1) {
      setCurrentChallengeId(currentChallengeId - 1);
    } else {
      // Go to last challenge of previous unit
      const prevUnit = currentUnitId - 1;
      const lastChallengeInPrevUnit = CHALLENGES_PER_UNIT[prevUnit] || 1;
      setCurrentUnitId(prevUnit);
      setCurrentChallengeId(lastChallengeInPrevUnit);
    }
  };

  const goToNextChallenge = () => {
    if (!canGoNext()) return;

    const maxChallengesInUnit = CHALLENGES_PER_UNIT[currentUnitId] || 0;

    if (currentChallengeId < maxChallengesInUnit) {
      setCurrentChallengeId(currentChallengeId + 1);
    } else {
      // Go to first challenge of next unit
      setCurrentUnitId(currentUnitId + 1);
      setCurrentChallengeId(1);
    }
  };

  // Handle successful submission
  const handleSubmitSuccess = (progress: ProgressResponse) => {
    // Clear draft
    const draftKey = getDraftKey(currentUnitId, currentChallengeId);
    localStorage.removeItem(draftKey);

    // Show success message
    showSuccessToast(
      `🎉 Congratulations! You earned ${progress.points_earned} points!`
    );

    // Auto-navigate to next challenge after 2 seconds
    if (canGoNext()) {
      setTimeout(() => {
        goToNextChallenge();
      }, 2000);
    }
  };

  // Handle unit selector change
  const handleUnitChange = (unitId: number) => {
    setCurrentUnitId(unitId);
    setCurrentChallengeId(1); // Reset to first challenge
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      // Ctrl/Cmd + → : Next challenge
      if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowRight') {
        e.preventDefault();
        if (canGoNext()) goToNextChallenge();
      }

      // Ctrl/Cmd + ← : Previous challenge
      if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowLeft') {
        e.preventDefault();
        if (canGoPrevious()) goToPreviousChallenge();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentUnitId, currentChallengeId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Controls */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            {/* Unit Selector */}
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Select Unit:</label>
              <div className="flex space-x-2">
                {[1, 2, 3].map((unitId) => (
                  <button
                    key={unitId}
                    onClick={() => handleUnitChange(unitId)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      currentUnitId === unitId
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Unit {unitId}
                  </button>
                ))}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={goToPreviousChallenge}
                disabled={!canGoPrevious()}
              >
                ← Previous
              </Button>
              <span className="text-sm text-gray-600 px-2">
                Challenge {currentChallengeId} of {CHALLENGES_PER_UNIT[currentUnitId]}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={goToNextChallenge}
                disabled={!canGoNext()}
              >
                Next →
              </Button>
            </div>
          </div>

          {/* Keyboard shortcuts hint */}
          <p className="text-xs text-gray-500 mt-3 text-center">
            💡 Tip: Use Ctrl+← and Ctrl+→ to navigate between challenges
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow p-12 flex items-center justify-center">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Loading challenge...</span>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="border-l-4 border-red-500 bg-red-50 p-4">
              <div className="flex items-start">
                <span className="text-red-500 mr-2 mt-0.5">⚠</span>
                <div>
                  <p className="text-sm font-medium text-red-800">Error loading challenge</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Practice Layout */}
        {challenge && !isLoading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Challenge Card */}
            <div>
              <ChallengeCard
                challenge={challenge}
                showHints={true}
                showSchema={true}
                showExpectedOutput={true}
                showSampleQuery={false}
                onHintsUsedChange={(count) => setHintsUsed(count)}
                initialHintsUsed={hintsUsed}
              />
            </div>

            {/* Right: Query Editor */}
            <div>
              <QueryEditor
                key={`${currentUnitId}-${currentChallengeId}`}
                initialQuery={query}
                onQueryExecute={() => {}}
                showHistory={true}
                maxHistoryEntries={5}
                expectedQuery={challenge.sample_solution || undefined}
                unitId={currentUnitId}
                challengeId={currentChallengeId}
                hintsUsed={hintsUsed}
                onSubmitSuccess={handleSubmitSuccess}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
