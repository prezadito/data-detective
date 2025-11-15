/**
 * User related types
 */
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
}

export enum UserRole {
  TEACHER = 'teacher',
  STUDENT = 'student',
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
  full_name: string;
  role: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
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

export enum ChallengeDifficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard',
}

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

/**
 * API Error response
 */
export interface ApiError {
  detail: string;
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
