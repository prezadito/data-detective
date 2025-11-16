import { api } from '@/services/api';
import type { WeeklyReportResponse } from '@/types';

/**
 * Report service for weekly progress summaries (teachers only)
 */
export const reportService = {
  /**
   * Get weekly progress report showing:
   * - Students active in past 7 days
   * - Total completions and average points
   * - Top 5 performers by points
   * - Struggling students (<3 completions)
   *
   * Results are cached on the backend for 1 hour.
   * Teachers only - returns 403 for students.
   *
   * @returns WeeklyReportResponse with aggregated metrics
   */
  async getWeeklyReport(): Promise<WeeklyReportResponse> {
    const response = await api.get('reports/weekly').json<WeeklyReportResponse>();
    return response;
  },
};
