interface MetricsCardProps {
  icon: string;
  label: string;
  value: string | number;
  subtitle?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'gray';
}

/**
 * Reusable metrics card for displaying student statistics
 */
export function MetricsCard({
  icon,
  label,
  value,
  subtitle,
  color = 'blue',
}: MetricsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    gray: 'bg-gray-50 text-gray-600 border-gray-200',
  };

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs font-medium uppercase tracking-wide opacity-75">
          {label}
        </span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <div className="text-sm mt-1 opacity-75">{subtitle}</div>}
    </div>
  );
}

MetricsCard.displayName = 'MetricsCard';
