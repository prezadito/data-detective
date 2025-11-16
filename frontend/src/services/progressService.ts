import { api } from '@/services/api';
import type {
  ProgressSummaryResponse,
  ChallengeSubmitRequest,
  ProgressResponse,
} from '@/types';

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

  /**
   * Submit a challenge solution
   * Validates and submits student's SQL query for a specific challenge
   */
  async submitChallenge(
    request: ChallengeSubmitRequest
  ): Promise<ProgressResponse> {
    const response = await api
      .post('progress/submit', {
        json: request,
      })
      .json<ProgressResponse>();
    return response;
  },
};
