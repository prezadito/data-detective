import type { ReactNode } from 'react';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}

/**
 * Consistent container for chart components
 * Provides title, subtitle, and standardized styling
 */
export function ChartContainer({ title, subtitle, children, className = '' }: ChartContainerProps) {
  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
      </div>
      <div className="bg-gray-50 rounded-lg p-4">
        {children}
      </div>
    </div>
  );
}

ChartContainer.displayName = 'ChartContainer';
