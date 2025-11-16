import { useState } from 'react';
import { SchemaView } from './SchemaView';
import { ExpectedOutput } from './ExpectedOutput';
import { HintSystem } from './HintSystem';
import { getChallengeHints } from '@/data/challengeHints';
import type { ChallengeDetail } from '@/types';

export interface ChallengeCardProps {
  /**
   * Challenge data to display
   */
  challenge: ChallengeDetail;

  /**
   * Display variant
   * @default 'full'
   */
  variant?: 'full' | 'preview' | 'list-item';

  /**
   * Whether to show hint system
   * @default true
   */
  showHints?: boolean;

  /**
   * Whether to show schema viewer
   * @default true
   */
  showSchema?: boolean;

  /**
   * Whether to show expected output
   * @default true
   */
  showExpectedOutput?: boolean;

  /**
   * Whether to show sample query (teachers only)
   * @default false
   */
  showSampleQuery?: boolean;

  /**
   * Callback when hints_used changes
   */
  onHintsUsedChange?: (hintsUsed: number) => void;

  /**
   * Initial hints used (for resuming)
   * @default 0
   */
  initialHintsUsed?: number;
}

/**
 * ChallengeCard component displays challenge information with hints, schema, and expected output
 * Main container that orchestrates all challenge-related sub-components
 */
export function ChallengeCard({
  challenge,
  variant = 'full',
  showHints = true,
  showSchema = true,
  showExpectedOutput = true,
  showSampleQuery = false,
  onHintsUsedChange,
  initialHintsUsed = 0,
}: ChallengeCardProps) {
  const [hintsUsed, setHintsUsed] = useState(initialHintsUsed);

  // Get hints for this challenge
  const hints = getChallengeHints(challenge.unit_id, challenge.challenge_id);

  /**
   * Handle hint usage changes
   */
  function handleHintsUsedChange(count: number) {
    setHintsUsed(count);
    onHintsUsedChange?.(count);
  }

  // For MVP, only implement 'full' variant
  // TODO: Add 'preview' and 'list-item' variants in future
  if (variant !== 'full') {
    console.warn(`Variant '${variant}' not yet implemented. Using 'full' variant.`);
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Challenge Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-blue-200 text-sm font-medium">
                Unit {challenge.unit_id}
              </span>
              <span className="text-blue-200">•</span>
              <span className="text-blue-200 text-sm font-medium">
                Challenge {challenge.challenge_id}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white flex items-center">
              <span className="mr-2">🎯</span>
              {challenge.title}
            </h2>
          </div>
          <div className="ml-4 flex-shrink-0">
            <div className="bg-yellow-400 text-yellow-900 px-4 py-2 rounded-lg font-bold text-lg shadow-md">
              🏆 {challenge.points} pts
            </div>
          </div>
        </div>
      </div>

      {/* Challenge Description */}
      <div className="px-6 py-4 border-b border-gray-200">
        <p className="text-gray-700 leading-relaxed">{challenge.description}</p>
      </div>

      {/* Challenge Statistics */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-6 text-sm text-gray-600">
          <div className="flex items-center">
            <span className="mr-2">📊</span>
            <span>
              <strong>{challenge.completion_rate.toFixed(1)}%</strong> completion
            </span>
          </div>
          <div className="flex items-center">
            <span className="mr-2">📈</span>
            <span>
              Avg <strong>{challenge.avg_attempts.toFixed(1)}</strong> attempts
            </span>
          </div>
          <div className="flex items-center">
            <span className="mr-2">✅</span>
            <span>
              <strong>{challenge.success_count}</strong> of{' '}
              <strong>{challenge.total_attempts}</strong> successful
            </span>
          </div>
        </div>
      </div>

      {/* Schema View */}
      {showSchema && (
        <div className="px-6 py-4 border-b border-gray-200">
          <SchemaView defaultExpanded={false} />
        </div>
      )}

      {/* Expected Output */}
      {showExpectedOutput && (
        <div className="px-6 py-4 border-b border-gray-200">
          <ExpectedOutput
            query={challenge.sample_solution}
            showQuery={showSampleQuery}
            maxRows={5}
          />
        </div>
      )}

      {/* Hint System */}
      {showHints && (
        <div className="px-6 py-4">
          <HintSystem
            unitId={challenge.unit_id}
            challengeId={challenge.challenge_id}
            hints={hints}
            onHintsUsedChange={handleHintsUsedChange}
            initialHintsUsed={initialHintsUsed}
          />
        </div>
      )}

      {/* Debug info (only in development) */}
      {import.meta.env.DEV && (
        <div className="px-6 py-2 bg-gray-100 border-t border-gray-200">
          <details className="text-xs text-gray-600">
            <summary className="cursor-pointer font-medium">
              Debug Info (dev only)
            </summary>
            <div className="mt-2 space-y-1 font-mono">
              <div>Unit ID: {challenge.unit_id}</div>
              <div>Challenge ID: {challenge.challenge_id}</div>
              <div>Hints Used: {hintsUsed}</div>
              <div>Has Sample Solution: {challenge.sample_solution ? 'Yes' : 'No'}</div>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}

ChallengeCard.displayName = 'ChallengeCard';
