import { api } from '@/services/api';
import type {
  AllChallengesResponse,
  UnitChallenges,
  ChallengeDetail,
  HintAccessRequest,
  HintAccessResponse,
} from '@/types';

/**
 * Challenge service for fetching challenges and accessing hints
 */
export const challengeService = {
  /**
   * Get all challenges across all units with statistics
   */
  async getAllChallenges(): Promise<AllChallengesResponse> {
    const response = await api.get('challenges').json<AllChallengesResponse>();
    return response;
  },

  /**
   * Get all challenges in a specific unit
   */
  async getUnitChallenges(unitId: number): Promise<UnitChallenges> {
    const response = await api
      .get(`challenges/${unitId}`)
      .json<UnitChallenges>();
    return response;
  },

  /**
   * Get detailed information about a specific challenge
   */
  async getChallengeDetail(
    unitId: number,
    challengeId: number
  ): Promise<ChallengeDetail> {
    const response = await api
      .get(`challenges/${unitId}/${challengeId}`)
      .json<ChallengeDetail>();
    return response;
  },

  /**
   * Track hint access (students only)
   * Records when a student accesses a hint for analytics
   */
  async accessHint(
    unitId: number,
    challengeId: number,
    hintLevel: number
  ): Promise<HintAccessResponse> {
    const request: HintAccessRequest = {
      unit_id: unitId,
      challenge_id: challengeId,
      hint_level: hintLevel,
    };

    const response = await api
      .post('hints/access', {
        json: request,
      })
      .json<HintAccessResponse>();

    return response;
  },
};
