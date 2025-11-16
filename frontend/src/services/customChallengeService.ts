/**
 * Custom Challenge service - API calls for teacher-created challenges
 */

import { api } from './api';
import type {
  CustomChallengeCreate,
  CustomChallengeUpdate,
  CustomChallengeResponse,
  CustomChallengeListResponse,
  CustomChallengeDetailResponse,
} from '@/types';

export const customChallengeService = {
  /**
   * Create a new custom challenge
   * @param data - Challenge creation data
   * @returns Created challenge
   */
  async createChallenge(
    data: CustomChallengeCreate
  ): Promise<CustomChallengeResponse> {
    return await api
      .post('challenges/custom', {
        json: data,
      })
      .json<CustomChallengeResponse>();
  },

  /**
   * Get list of custom challenges for current teacher
   * @param params - Filter and pagination parameters
   * @returns List of custom challenges
   */
  async getChallenges(params?: {
    dataset_id?: number;
    is_active?: boolean;
    offset?: number;
    limit?: number;
  }): Promise<CustomChallengeListResponse> {
    const searchParams: Record<string, string | number | boolean> = {};

    if (params?.dataset_id !== undefined) {
      searchParams.dataset_id = params.dataset_id;
    }
    if (params?.is_active !== undefined) {
      searchParams.is_active = params.is_active;
    }
    if (params?.offset !== undefined) {
      searchParams.offset = params.offset;
    }
    if (params?.limit !== undefined) {
      searchParams.limit = params.limit;
    }

    return await api
      .get('challenges/custom', {
        searchParams,
      })
      .json<CustomChallengeListResponse>();
  },

  /**
   * Get detailed custom challenge information
   * @param challengeId - Challenge ID
   * @returns Challenge details with expected output
   */
  async getChallengeDetail(
    challengeId: number
  ): Promise<CustomChallengeDetailResponse> {
    return await api
      .get(`challenges/custom/${challengeId}`)
      .json<CustomChallengeDetailResponse>();
  },

  /**
   * Update a custom challenge
   * @param challengeId - Challenge ID
   * @param data - Fields to update
   * @returns Updated challenge
   */
  async updateChallenge(
    challengeId: number,
    data: CustomChallengeUpdate
  ): Promise<CustomChallengeResponse> {
    return await api
      .put(`challenges/custom/${challengeId}`, {
        json: data,
      })
      .json<CustomChallengeResponse>();
  },

  /**
   * Delete a custom challenge
   * @param challengeId - Challenge ID
   * @returns Success message
   */
  async deleteChallenge(challengeId: number): Promise<{ message: string }> {
    return await api.delete(`challenges/custom/${challengeId}`).json();
  },

  /**
   * Test a SQL query against a dataset
   * This is useful for the challenge builder to preview expected output
   * Note: This would require a new backend endpoint for query testing
   * For now, challenges must be created to see output
   */
  // async testQuery(datasetId: number, query: string): Promise<any[]> {
  //   return await api
  //     .post(`datasets/${datasetId}/test-query`, {
  //       json: { query },
  //     })
  //     .json();
  // },
};
