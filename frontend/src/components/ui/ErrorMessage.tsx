import { Button } from './Button';
import { isRetryableError } from '@/utils/errors';

interface ErrorMessageProps {
  /**
   * Error object or error message string
   */
  error: unknown | string;

  /**
   * Optional callback for retry action
   * Can return void, Promise<void>, or Promise with any value (e.g., Promise<T | null>)
   */
  onRetry?: () => void | Promise<unknown>;

  /**
   * Optional title for the error message
   * @default "Something went wrong"
   */
  title?: string;

  /**
   * Size variant
   * @default "default"
   */
  size?: 'sm' | 'default' | 'lg';

  /**
   * Optional className for custom styling
   */
  className?: string;

  /**
   * Whether to show the retry button (if onRetry is provided)
   * If not specified, will auto-detect based on error type
   */
  showRetry?: boolean;
}

/**
 * ErrorMessage Component
 *
 * Displays user-friendly error messages with optional retry functionality
 *
 * Features:
 * - Automatically detects retryable errors
 * - Shows retry button for network/timeout errors
 * - Accessible with proper ARIA attributes
 * - Multiple size variants
 *
 * @example
 * ```tsx
 * <ErrorMessage
 *   error={error}
 *   onRetry={() => refetch()}
 *   title="Failed to load data"
 * />
 * ```
 */
export function ErrorMessage({
  error,
  onRetry,
  title = 'Something went wrong',
  size = 'default',
  className = '',
  showRetry,
}: ErrorMessageProps) {
  // Determine if we should show retry button
  const shouldShowRetry =
    showRetry !== undefined
      ? showRetry
      : onRetry !== undefined && isRetryableError(error);

  // Get error message
  const errorMessage = typeof error === 'string'
    ? error
    : error instanceof Error
    ? error.message
    : 'An unexpected error occurred. Please try again.';

  // Size classes
  const sizeClasses = {
    sm: {
      container: 'p-3 rounded-lg',
      icon: 'w-5 h-5',
      title: 'text-sm font-semibold',
      message: 'text-xs',
      button: 'text-xs',
    },
    default: {
      container: 'p-4 rounded-lg',
      icon: 'w-6 h-6',
      title: 'text-base font-semibold',
      message: 'text-sm',
      button: 'text-sm',
    },
    lg: {
      container: 'p-6 rounded-lg',
      icon: 'w-8 h-8',
      title: 'text-lg font-semibold',
      message: 'text-base',
      button: 'text-base',
    },
  };

  const classes = sizeClasses[size];

  return (
    <div
      className={`bg-red-50 border border-red-200 ${classes.container} ${className}`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex gap-3">
        {/* Error Icon */}
        <div className="flex-shrink-0">
          <svg
            className={`${classes.icon} text-red-600`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        {/* Error Content */}
        <div className="flex-1 min-w-0">
          <h3 className={`${classes.title} text-red-800 mb-1`}>
            {title}
          </h3>
          <p className={`${classes.message} text-red-700`}>
            {errorMessage}
          </p>

          {/* Retry Button */}
          {shouldShowRetry && onRetry && (
            <div className="mt-3">
              <Button
                onClick={onRetry}
                variant="outline"
                size="sm"
                className={`${classes.button} border-red-300 text-red-700 hover:bg-red-100`}
              >
                <svg
                  className="w-4 h-4 mr-1.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Try Again
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Inline error message for form fields
 * Simpler variant without retry button
 */
export function InlineErrorMessage({
  message,
  className = '',
}: {
  message: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center gap-2 text-red-600 text-sm mt-1 ${className}`}
      role="alert"
    >
      <svg
        className="w-4 h-4 flex-shrink-0"
        fill="currentColor"
        viewBox="0 0 20 20"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <span>{message}</span>
    </div>
  );
}
