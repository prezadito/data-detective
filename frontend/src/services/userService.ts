import { api } from '@/services/api';
import type { User, UpdateUserRequest, StudentListResponse, StudentListParams } from '@/types';

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

  /**
   * Get list of students with statistics (teachers only)
   */
  async getStudents(params?: StudentListParams): Promise<StudentListResponse> {
    const searchParams = new URLSearchParams();

    if (params?.role) {
      searchParams.append('role', params.role);
    }
    if (params?.sort) {
      searchParams.append('sort', params.sort);
    }
    if (params?.offset !== undefined) {
      searchParams.append('offset', params.offset.toString());
    }
    if (params?.limit !== undefined) {
      searchParams.append('limit', params.limit.toString());
    }

    const url = `users${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    const response = await api.get(url).json<StudentListResponse>();
    return response;
  },

  /**
   * Get specific student details by ID (teachers only)
   */
  async getStudentById(userId: number, detailed: boolean = false): Promise<User> {
    const searchParams = new URLSearchParams();
    if (detailed) {
      searchParams.append('detailed', 'true');
    }

    const url = `users/${userId}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    const response = await api.get(url).json<User>();
    return response;
  },
};
