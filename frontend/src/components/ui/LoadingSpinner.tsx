import type { HTMLAttributes } from 'react';

export interface LoadingSpinnerProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Size of the spinner
   */
  size?: 'sm' | 'md' | 'lg' | 'xl';

  /**
   * Full screen overlay mode
   */
  fullScreen?: boolean;

  /**
   * Optional text to display below spinner
   */
  text?: string;

  /**
   * Color variant
   */
  variant?: 'primary' | 'secondary' | 'white';
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
};

const colorClasses = {
  primary: 'border-blue-600',
  secondary: 'border-gray-600',
  white: 'border-white',
};

export function LoadingSpinner({
  size = 'md',
  fullScreen = false,
  text,
  variant = 'primary',
  className = '',
  ...props
}: LoadingSpinnerProps) {
  const spinner = (
    <div
      className={`inline-block animate-spin rounded-full border-b-2 ${sizeClasses[size]} ${colorClasses[variant]} ${className}`}
      role="status"
      aria-live="polite"
      aria-label={text || 'Loading'}
      {...props}
    >
      <span className="sr-only">{text || 'Loading...'}</span>
    </div>
  );

  if (fullScreen) {
    return (
      <div
        className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-50 bg-opacity-75"
        role="status"
        aria-live="polite"
      >
        {spinner}
        {text && (
          <p className="mt-4 text-sm font-medium text-gray-700">{text}</p>
        )}
      </div>
    );
  }

  if (text) {
    return (
      <div className="flex flex-col items-center justify-center space-y-3">
        {spinner}
        <p className="text-sm font-medium text-gray-700">{text}</p>
      </div>
    );
  }

  return spinner;
}
