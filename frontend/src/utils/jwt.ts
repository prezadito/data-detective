import { jwtDecode } from 'jwt-decode';
import type { DecodedToken, User, UserRole } from '@/types';

/**
 * Decode a JWT access token and extract user information
 */
export function decodeAccessToken(token: string): DecodedToken | null {
  try {
    return jwtDecode<DecodedToken>(token);
  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    return null;
  }
}

/**
 * Extract user information from a decoded JWT token
 */
export function getUserFromToken(token: string): Omit<User, 'created_at'> | null {
  const decoded = decodeAccessToken(token);

  if (!decoded) {
    return null;
  }

  return {
    id: decoded.user_id,
    email: decoded.sub,
    name: '', // Will need to fetch from API
    role: decoded.role as UserRole,
  };
}

/**
 * Check if a JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  const decoded = decodeAccessToken(token);

  if (!decoded) {
    return true;
  }

  // exp is in seconds, Date.now() is in milliseconds
  return decoded.exp * 1000 < Date.now();
}

/**
 * Get time until token expiration in milliseconds
 */
export function getTokenTimeToExpiry(token: string): number | null {
  const decoded = decodeAccessToken(token);

  if (!decoded) {
    return null;
  }

  return decoded.exp * 1000 - Date.now();
}
