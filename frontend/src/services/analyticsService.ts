import { api } from '@/services/api';
import type { ClassAnalyticsResponse } from '@/types';

/**
 * Analytics service for class-wide statistics (teachers only)
 */
export const analyticsService = {
  /**
   * Get class-wide analytics including:
   * - Overall class metrics (completion rate, points distribution, success rate)
   * - Per-challenge statistics (success rates, attempts, hints usage)
   * - Difficulty distribution (easiest/hardest challenges)
   * - Weekly trends (past 4 weeks)
   *
   * Results are cached on the backend for 1 hour.
   * Teachers only - returns 403 for students.
   *
   * @returns ClassAnalyticsResponse with complete analytics data
   */
  async getClassAnalytics(): Promise<ClassAnalyticsResponse> {
    const response = await api.get('analytics/class').json<ClassAnalyticsResponse>();
    return response;
  },
};
