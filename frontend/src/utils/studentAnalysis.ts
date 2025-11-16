import type {
  StudentMetrics,
  UnitDetail,
  StrugglingArea,
  ActivityLogEntry,
} from '@/types';

/**
 * Detect struggling areas for a student based on multiple criteria
 */
export function detectStrugglingAreas(
  metrics: StudentMetrics,
  units: UnitDetail[],
  activityLog: ActivityLogEntry[]
): StrugglingArea[] {
  const areas: StrugglingArea[] = [];

  // 1. Low Overall Success Rate
  if (metrics.overall_success_rate < 50 && metrics.total_attempts > 0) {
    areas.push({
      severity: 'high',
      message: `Success rate is ${Math.round(metrics.overall_success_rate)}% (below 50%)`,
      recommendation: 'Consider scheduling a 1-on-1 session to review fundamentals',
      color: 'bg-red-50 text-red-600 border-red-200',
    });
  }

  // 2. High Hint Usage
  const avgHintsPerChallenge =
    metrics.total_challenges_completed > 0
      ? metrics.total_hints_used / metrics.total_challenges_completed
      : 0;

  if (avgHintsPerChallenge > 2 && metrics.total_challenges_completed > 0) {
    areas.push({
      severity: 'medium',
      message: `High hint reliance (avg ${avgHintsPerChallenge.toFixed(1)} hints/challenge)`,
      recommendation: 'Student may benefit from concept review before attempting challenges',
      color: 'bg-blue-50 text-blue-600 border-blue-200',
    });
  }

  // 3. Many Attempts Per Challenge
  if (
    metrics.average_attempts_per_challenge > 4 &&
    metrics.total_challenges_completed > 0
  ) {
    areas.push({
      severity: 'medium',
      message: `Many attempts needed (avg ${metrics.average_attempts_per_challenge.toFixed(1)} per challenge)`,
      recommendation: 'Check if student understands SQL syntax and structure',
      color: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    });
  }

  // 4. Challenge-Specific Struggles
  units.forEach((unit) => {
    unit.challenges.forEach((challenge) => {
      if (
        challenge.metrics.success_rate < 30 &&
        challenge.metrics.total_attempts > 3
      ) {
        areas.push({
          severity: 'high',
          message: `Struggling with: ${challenge.title}`,
          recommendation: `Review ${unit.unit_title} concepts, especially ${challenge.title}`,
          color: 'bg-red-50 text-red-600 border-red-200',
        });
      }
    });
  });

  // 5. No Recent Activity
  if (activityLog.length > 0) {
    const lastActivity = new Date(activityLog[0].timestamp);
    const daysSinceActivity = Math.floor(
      (Date.now() - lastActivity.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysSinceActivity > 7) {
      areas.push({
        severity: 'low',
        message: `No activity in ${daysSinceActivity} days`,
        recommendation: 'Reach out to check on student engagement',
        color: 'bg-gray-50 text-gray-600 border-gray-200',
      });
    }
  } else if (metrics.total_challenges_completed === 0) {
    areas.push({
      severity: 'low',
      message: 'No challenges completed yet',
      recommendation: 'Encourage student to start with Unit 1',
      color: 'bg-gray-50 text-gray-600 border-gray-200',
    });
  }

  // Sort by severity (high -> medium -> low)
  const severityOrder = { high: 0, medium: 1, low: 2 };
  areas.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  return areas;
}
