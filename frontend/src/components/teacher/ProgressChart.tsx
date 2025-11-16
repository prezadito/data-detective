import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { UnitDetail } from '@/types';

interface ProgressChartProps {
  units: UnitDetail[];
}

/**
 * Progress chart showing completion and success rate per unit
 */
export function ProgressChart({ units }: ProgressChartProps) {
  // Transform data for recharts
  const chartData = units.map((unit) => {
    const totalChallengesInUnit = {
      1: 3, // Unit 1: SELECT Basics (3 challenges)
      2: 2, // Unit 2: JOINs (2 challenges)
      3: 2, // Unit 3: Aggregations (2 challenges)
    }[unit.unit_id] || 0;

    const completedCount = unit.challenges.length;
    const completionPercentage = totalChallengesInUnit > 0
      ? Math.round((completedCount / totalChallengesInUnit) * 100)
      : 0;

    // Calculate average success rate for this unit
    const avgSuccessRate = completedCount > 0
      ? Math.round(
          unit.challenges.reduce((sum, c) => sum + c.metrics.success_rate, 0) /
            completedCount
        )
      : 0;

    return {
      name: `Unit ${unit.unit_id}`,
      completion: completionPercentage,
      successRate: avgSuccessRate,
    };
  });

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            formatter={(value: number) => `${value}%`}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderRadius: '8px',
              padding: '8px',
            }}
          />
          <Legend />
          <Bar
            dataKey="completion"
            fill="#3b82f6"
            name="Completion %"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="successRate"
            fill="#10b981"
            name="Success Rate %"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

ProgressChart.displayName = 'ProgressChart';
