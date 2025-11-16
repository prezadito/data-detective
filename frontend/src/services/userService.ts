import { api } from '@/services/api';
import type { User, UpdateUserRequest } from '@/types';

/**
 * User service for profile management
 */
export const userService = {
  /**
   * Get current authenticated user's profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get('users/me').json<User>();
    return response;
  },

  /**
   * Update current user's profile (name only)
   */
  async updateUserProfile(data: UpdateUserRequest): Promise<User> {
    const response = await api.put('users/me', {
      json: data,
    }).json<User>();
    return response;
  },
};
