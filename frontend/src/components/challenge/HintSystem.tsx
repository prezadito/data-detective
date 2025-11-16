import { useState } from 'react';
import { challengeService } from '@/services/challengeService';
import { showErrorToast } from '@/utils/toast';
import { Button } from '@/components/ui/Button';

export interface HintSystemProps {
  /**
   * Challenge identifiers for hint tracking
   */
  unitId: number;
  challengeId: number;

  /**
   * Three hint levels (empty string if not available)
   */
  hints: [string, string, string];

  /**
   * Callback when hints_used count changes
   */
  onHintsUsedChange?: (hintsUsed: number) => void;

  /**
   * Initial hints_used count (for resuming challenge)
   * @default 0
   */
  initialHintsUsed?: number;
}

/**
 * HintSystem component provides progressive 3-level hint reveal
 * Tracks hint access in backend for analytics
 */
export function HintSystem({
  unitId,
  challengeId,
  hints,
  onHintsUsedChange,
  initialHintsUsed = 0,
}: HintSystemProps) {
  const [hintsRevealed, setHintsRevealed] = useState<number>(initialHintsUsed);
  const [isRevealing, setIsRevealing] = useState(false);

  /**
   * Reveal the next hint and track in backend
   */
  async function revealNextHint() {
    if (hintsRevealed >= 3) return;

    const nextLevel = hintsRevealed + 1;

    try {
      setIsRevealing(true);

      // Track hint access in backend
      await challengeService.accessHint(unitId, challengeId, nextLevel);

      // Update local state
      setHintsRevealed(nextLevel);

      // Notify parent
      onHintsUsedChange?.(nextLevel);
    } catch (error) {
      showErrorToast('Failed to access hint. Please try again.');
      console.error('Hint access error:', error);
    } finally {
      setIsRevealing(false);
    }
  }

  /**
   * Get button text based on current hint level
   */
  function getButtonText(): string {
    if (hintsRevealed === 0) return 'Show First Hint';
    if (hintsRevealed === 1) return 'Show Second Hint';
    if (hintsRevealed === 2) return 'Show Final Hint';
    return 'All Hints Revealed';
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center">
          <span className="mr-2">💡</span>
          Hints Available
        </h3>
      </div>

      <div className="p-4 space-y-3">
        {/* Hint Level 1 */}
        {hintsRevealed >= 1 ? (
          <article
            className="border-l-4 border-yellow-500 bg-yellow-50 p-4 animate-fadeIn"
            aria-label="Hint 1"
          >
            <div className="flex items-start">
              <span className="text-yellow-600 mr-2 font-semibold">💡 Hint 1:</span>
              <p className="text-sm text-yellow-800">{hints[0]}</p>
            </div>
          </article>
        ) : (
          <div className="border-l-4 border-gray-300 bg-gray-50 p-4">
            <div className="flex items-start">
              <span className="text-gray-400 mr-2">🔒</span>
              <p className="text-sm text-gray-500 italic">
                Hint 1 (Click "Show Hint" to reveal)
              </p>
            </div>
          </div>
        )}

        {/* Hint Level 2 */}
        {hintsRevealed >= 2 ? (
          <article
            className="border-l-4 border-yellow-500 bg-yellow-50 p-4 animate-fadeIn"
            aria-label="Hint 2"
          >
            <div className="flex items-start">
              <span className="text-yellow-600 mr-2 font-semibold">💡 Hint 2:</span>
              <p className="text-sm text-yellow-800">{hints[1]}</p>
            </div>
          </article>
        ) : (
          <div className="border-l-4 border-gray-300 bg-gray-50 p-4">
            <div className="flex items-start">
              <span className="text-gray-400 mr-2">🔒</span>
              <p className="text-sm text-gray-500 italic">
                Hint 2 (Reveal Hint 1 first)
              </p>
            </div>
          </div>
        )}

        {/* Hint Level 3 */}
        {hintsRevealed >= 3 ? (
          <article
            className="border-l-4 border-yellow-500 bg-yellow-50 p-4 animate-fadeIn"
            aria-label="Hint 3"
          >
            <div className="flex items-start">
              <span className="text-yellow-600 mr-2 font-semibold">💡 Hint 3:</span>
              <p className="text-sm text-yellow-800">{hints[2]}</p>
            </div>
          </article>
        ) : (
          <div className="border-l-4 border-gray-300 bg-gray-50 p-4">
            <div className="flex items-start">
              <span className="text-gray-400 mr-2">🔒</span>
              <p className="text-sm text-gray-500 italic">
                Hint 3 (Reveal Hint 2 first)
              </p>
            </div>
          </div>
        )}

        {/* Reveal button */}
        <div className="pt-2">
          <Button
            variant="outline"
            size="md"
            onClick={revealNextHint}
            disabled={hintsRevealed >= 3 || isRevealing}
            isLoading={isRevealing}
            className="w-full"
          >
            {getButtonText()}
          </Button>
        </div>

        {/* Hint counter */}
        <div className="text-center text-xs text-gray-600 pt-2">
          {hintsRevealed} of 3 hints used
        </div>
      </div>
    </div>
  );
}

HintSystem.displayName = 'HintSystem';
