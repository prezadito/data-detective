import { api } from '@/services/api';
import type { LoginCredentials, AuthResponse, User } from '@/types';
import { getUserFromToken } from '@/utils/jwt';

const ACCESS_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Authentication service
 */
export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<User> {
    const response = await api.post('auth/login', {
      json: credentials,
    }).json<AuthResponse>();

    // Store tokens
    localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);

    // Extract user from token
    const user = getUserFromToken(response.access_token);

    if (!user) {
      throw new Error('Failed to decode user from token');
    }

    // Fetch full user details if needed
    // For now, return user from token
    return {
      ...user,
      created_at: new Date().toISOString(), // Will be replaced when we fetch from API
    };
  },

  /**
   * Logout the current user
   */
  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (refreshToken) {
      try {
        // Call logout endpoint to revoke refresh token
        await api.post('auth/logout', {
          json: { refresh_token: refreshToken },
        });
      } catch (error) {
        console.error('Logout API call failed:', error);
        // Continue with local cleanup even if API call fails
      }
    }

    // Clear tokens from localStorage
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Get the current access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Get the current refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },

  /**
   * Get current user from token
   */
  getCurrentUser(): User | null {
    const token = this.getAccessToken();

    if (!token) {
      return null;
    }

    const user = getUserFromToken(token);

    if (!user) {
      return null;
    }

    return {
      ...user,
      created_at: new Date().toISOString(),
    };
  },

  /**
   * Refresh the access token using refresh token
   */
  async refreshAccessToken(): Promise<string> {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('auth/refresh', {
      json: { refresh_token: refreshToken },
    }).json<{ access_token: string; token_type: string }>();

    // Store new access token
    localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);

    return response.access_token;
  },
};
