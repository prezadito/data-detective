import { api } from '@/services/api';
import type { ProgressSummaryResponse } from '@/types';

/**
 * Progress service for tracking student progress
 */
export const progressService = {
  /**
   * Get current user's progress summary
   */
  async getMyProgress(): Promise<ProgressSummaryResponse> {
    const response = await api.get('progress/me').json<ProgressSummaryResponse>();
    return response;
  },
};
