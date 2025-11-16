import type { StrugglingArea } from '@/types';

interface StrugglingAreasAlertProps {
  areas: StrugglingArea[];
}

/**
 * Display struggling areas and recommendations for a student
 */
export function StrugglingAreasAlert({ areas }: StrugglingAreasAlertProps) {
  if (areas.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start">
          <span className="text-green-600 text-xl mr-3">✓</span>
          <div>
            <h3 className="text-sm font-medium text-green-800">
              Student is doing well!
            </h3>
            <p className="text-sm text-green-700 mt-1">
              No significant areas of concern detected.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🔵';
      default:
        return '⚪';
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-900 mb-3">
        Areas Needing Attention ({areas.length})
      </h3>

      {areas.map((area, index) => (
        <div key={index} className={`border rounded-lg p-4 ${area.color}`}>
          <div className="flex items-start">
            <span className="text-lg mr-3">{getSeverityIcon(area.severity)}</span>
            <div className="flex-1">
              <h4 className="text-sm font-semibold mb-1">{area.message}</h4>
              <p className="text-sm opacity-90">
                <span className="font-medium">Recommendation:</span> {area.recommendation}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

StrugglingAreasAlert.displayName = 'StrugglingAreasAlert';
