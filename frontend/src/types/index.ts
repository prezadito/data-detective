/**
 * User related types
 */
export interface User {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export type UserRole = 'teacher' | 'student';

/**
 * User update request
 */
export interface UpdateUserRequest {
  name: string;
}

/**
 * Authentication types
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  role: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  refresh_token: string;
}

export interface DecodedToken {
  sub: string;      // email
  user_id: number;
  role: string;
  exp: number;      // expiration timestamp
  iat: number;      // issued at timestamp
  jti: string;      // JWT ID
}

/**
 * Challenge related types
 */
export interface Challenge {
  id: number;
  title: string;
  description: string;
  difficulty: ChallengeDifficulty;
  dataset_path: string;
  correct_query: string;
  points: number;
  created_at: string;
}

export type ChallengeDifficulty = 'easy' | 'medium' | 'hard';

/**
 * Submission related types
 */
export interface Submission {
  id: number;
  challenge_id: number;
  student_id: number;
  query: string;
  is_correct: boolean;
  submitted_at: string;
  feedback?: string;
}

export interface SubmitQueryRequest {
  challenge_id: number;
  query: string;
}

export interface SubmitQueryResponse {
  is_correct: boolean;
  feedback: string;
  points_earned?: number;
}

/**
 * Progress related types
 */
export interface StudentProgress {
  student_id: number;
  total_points: number;
  challenges_completed: number;
  challenges_attempted: number;
  accuracy_rate: number;
}

export interface ProgressSummaryStats {
  total_points: number;
  total_completed: number;
  completion_percentage: number;
}

export interface ProgressDetailResponse {
  id: number;
  user_id: number;
  unit_id: number;
  challenge_id: number;
  points_earned: number;
  hints_used: number;
  completed_at: string;
  query: string;
  challenge_title: string;
}

export interface ProgressSummaryResponse {
  summary: ProgressSummaryStats;
  progress_items: ProgressDetailResponse[];
}

/**
 * API Error response
 */
export interface ApiError {
  detail: string;
}

/**
 * Validation error for form fields
 */
export interface ValidationError {
  loc: string[];  // Field location (e.g., ["body", "email"])
  msg: string;    // Error message
  type: string;   // Error type (e.g., "value_error.email")
}

/**
 * Detailed API error response with validation errors
 */
export interface ApiErrorDetail {
  detail: string | ValidationError[];
}

/**
 * HTTP Error from ky
 */
export interface HTTPError extends Error {
  response: Response;
}

/**
 * Leaderboard types
 */
export interface LeaderboardEntry {
  rank: number;
  student_name: string;
  total_points: number;
  challenges_completed: number;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
}

/**
 * Pagination types
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
