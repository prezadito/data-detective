import { useState, memo } from 'react';
import type { ProgressDetailResponse } from '@/types';

export interface ChallengeListProps {
  /**
   * Array of progress items (completed challenges)
   */
  progressItems: ProgressDetailResponse[];

  /**
   * Callback when a challenge is clicked
   */
  onChallengeClick?: (unitId: number, challengeId: number) => void;

  /**
   * Total number of challenges in the system
   * @default 7
   */
  totalChallenges?: number;
}

interface UnitGroup {
  unitId: number;
  unitTitle: string;
  challenges: ProgressDetailResponse[];
}

/**
 * ChallengeList component displays completed challenges grouped by unit
 * Memoized to prevent unnecessary re-renders when parent updates
 */
export const ChallengeList = memo(function ChallengeList({
  progressItems,
  onChallengeClick,
}: ChallengeListProps) {
  const [expandedUnits, setExpandedUnits] = useState<Set<number>>(new Set([1]));

  // Group challenges by unit
  const units: UnitGroup[] = [];
  const unitMap = new Map<number, ProgressDetailResponse[]>();

  progressItems.forEach((item) => {
    if (!unitMap.has(item.unit_id)) {
      unitMap.set(item.unit_id, []);
    }
    unitMap.get(item.unit_id)!.push(item);
  });

  // Create unit groups with titles
  unitMap.forEach((challenges, unitId) => {
    const unitTitle = getUnitTitle(unitId);
    units.push({
      unitId,
      unitTitle,
      challenges: challenges.sort((a, b) => a.challenge_id - b.challenge_id),
    });
  });

  // Sort units by ID
  units.sort((a, b) => a.unitId - b.unitId);

  const toggleUnit = (unitId: number) => {
    setExpandedUnits((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(unitId)) {
        newSet.delete(unitId);
      } else {
        newSet.add(unitId);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-4">
      {units.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No challenges completed yet
          </h3>
          <p className="text-gray-600">
            Start solving challenges to see your progress here!
          </p>
        </div>
      ) : (
        units.map((unit) => (
          <div key={unit.unitId} className="bg-white rounded-lg shadow overflow-hidden">
            {/* Unit Header */}
            <button
              onClick={() => toggleUnit(unit.unitId)}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 transition-colors flex items-center justify-between"
            >
              <div className="flex items-center">
                <span className="mr-3 text-2xl">
                  {expandedUnits.has(unit.unitId) ? '📂' : '📁'}
                </span>
                <div className="text-left">
                  <h3 className="font-bold text-lg">{unit.unitTitle}</h3>
                  <p className="text-sm text-blue-200">
                    {unit.challenges.length} challenge{unit.challenges.length !== 1 ? 's' : ''}{' '}
                    completed
                  </p>
                </div>
              </div>
              <span className="text-white text-xl">
                {expandedUnits.has(unit.unitId) ? '▼' : '▶'}
              </span>
            </button>

            {/* Challenge List */}
            {expandedUnits.has(unit.unitId) && (
              <div className="divide-y divide-gray-200">
                {unit.challenges.map((challenge) => (
                  <div
                    key={`${challenge.unit_id}-${challenge.challenge_id}`}
                    className={`px-6 py-4 hover:bg-gray-50 transition-colors ${
                      onChallengeClick ? 'cursor-pointer' : ''
                    }`}
                    onClick={() =>
                      onChallengeClick?.(challenge.unit_id, challenge.challenge_id)
                    }
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <span className="text-green-500 mr-2 text-xl">✓</span>
                          <h4 className="font-medium text-gray-900">
                            {challenge.challenge_title}
                          </h4>
                        </div>
                        <p className="text-sm text-gray-500 mt-1 ml-7">
                          Completed on{' '}
                          {new Date(challenge.completed_at).toLocaleDateString('en-US', {
                            month: 'long',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </p>
                      </div>

                      <div className="flex items-center space-x-4 ml-4">
                        {/* Points earned */}
                        <div className="flex items-center bg-yellow-100 px-3 py-1 rounded-lg">
                          <span className="text-yellow-600 mr-1">🏆</span>
                          <span className="font-bold text-yellow-800">
                            {challenge.points_earned} pts
                          </span>
                        </div>

                        {/* Hints used */}
                        {challenge.hints_used > 0 && (
                          <div className="flex items-center text-gray-600">
                            <span className="mr-1">💡</span>
                            <span className="text-sm">
                              {challenge.hints_used} hint{challenge.hints_used !== 1 ? 's' : ''}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
});

/**
 * Get unit title based on unit ID
 */
function getUnitTitle(unitId: number): string {
  const titles: Record<number, string> = {
    1: 'Unit 1: SELECT Basics',
    2: 'Unit 2: JOINs',
    3: 'Unit 3: Aggregations',
  };
  return titles[unitId] || `Unit ${unitId}`;
}
