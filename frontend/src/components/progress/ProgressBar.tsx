export interface ProgressBarProps {
  /**
   * Current progress value
   */
  current: number;

  /**
   * Maximum/total value
   */
  total: number;

  /**
   * Optional label to display
   */
  label?: string;

  /**
   * Show percentage text
   * @default true
   */
  showPercentage?: boolean;

  /**
   * Show fraction text (e.g., "3/7")
   * @default true
   */
  showFraction?: boolean;

  /**
   * Size variant
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * ProgressBar component displays completion progress with visual bar
 */
export function ProgressBar({
  current,
  total,
  label,
  showPercentage = true,
  showFraction = true,
  size = 'md',
}: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  const heightClass = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6',
  }[size];

  const textSizeClass = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }[size];

  return (
    <div className="w-full">
      {/* Label and stats */}
      {(label || showFraction || showPercentage) && (
        <div className="flex items-center justify-between mb-2">
          <span className={`font-medium text-gray-700 ${textSizeClass}`}>
            {label}
          </span>
          <div className={`flex items-center space-x-2 text-gray-600 ${textSizeClass}`}>
            {showFraction && (
              <span>
                {current}/{total}
              </span>
            )}
            {showPercentage && (
              <span className="font-semibold">{percentage}%</span>
            )}
          </div>
        </div>
      )}

      {/* Progress bar */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClass}`}>
        <div
          className={`h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out ${
            percentage === 100 ? 'from-green-500 to-green-600' : ''
          }`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={current}
          aria-valuemin={0}
          aria-valuemax={total}
          aria-label={label || 'Progress'}
        />
      </div>

      {/* Completion badge */}
      {percentage === 100 && (
        <div className="mt-2 flex items-center justify-center">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            <span className="mr-1">🎉</span>
            Complete!
          </span>
        </div>
      )}
    </div>
  );
}

ProgressBar.displayName = 'ProgressBar';
