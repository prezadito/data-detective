import { api } from '@/services/api';
import type { LeaderboardResponse } from '@/types';

/**
 * Leaderboard service for gamification
 */
export const leaderboardService = {
  /**
   * Get the public leaderboard (top 100 students)
   */
  async getLeaderboard(): Promise<LeaderboardResponse> {
    const response = await api.get('leaderboard').json<LeaderboardResponse>();
    return response;
  },
};
