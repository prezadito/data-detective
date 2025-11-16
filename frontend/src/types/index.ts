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

/**
 * Challenge submission request
 * For POST /progress/submit
 */
export interface ChallengeSubmitRequest {
  unit_id: number;
  challenge_id: number;
  query: string;
  hints_used: number;
}

/**
 * Progress response from challenge submission
 * Returned by POST /progress/submit
 */
export interface ProgressResponse {
  id: number;
  user_id: number;
  unit_id: number;
  challenge_id: number;
  points_earned: number;
  hints_used: number;
  completed_at: string;
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

/**
 * Challenge detail from backend
 * Matches backend ChallengeDetail schema
 */
export interface ChallengeDetail {
  unit_id: number;
  challenge_id: number;
  title: string;
  points: number;
  description: string;
  sample_solution: string | null; // null for students, visible for teachers
  completion_rate: number; // 0-100%
  avg_attempts: number;
  total_attempts: number;
  success_count: number;
}

/**
 * Challenges grouped by unit
 * Matches backend UnitChallenges schema
 */
export interface UnitChallenges {
  unit_id: number;
  unit_title: string; // e.g., "Unit 1: SELECT Basics"
  challenges: ChallengeDetail[];
}

/**
 * All challenges response from GET /challenges
 * Matches backend AllChallengesResponse schema
 */
export interface AllChallengesResponse {
  units: UnitChallenges[];
  generated_at: string;
}

/**
 * Hint access request
 * For POST /hints/access
 */
export interface HintAccessRequest {
  unit_id: number;
  challenge_id: number;
  hint_level: number; // 1, 2, or 3
}

/**
 * Hint access response
 * From POST /hints/access
 */
export interface HintAccessResponse {
  hint_id: number;
  accessed_at: string;
}

/**
 * Database schema types for SchemaView component
 */
export interface TableColumn {
  name: string;
  type: 'INTEGER' | 'TEXT' | 'REAL';
}

export interface TableSchema {
  name: string;
  columns: TableColumn[];
  rowCount: number;
}

/**
 * Dataset types (teacher-uploaded CSV files)
 */
export interface ColumnSchema {
  name: string;
  type: string; // "INTEGER", "REAL", "TEXT"
}

export interface DatasetSchema {
  columns: ColumnSchema[];
}

export interface DatasetCreate {
  name: string;
  description?: string;
}

export interface DatasetResponse {
  id: number;
  name: string;
  description: string | null;
  original_filename: string;
  table_name: string;
  row_count: number;
  schema: DatasetSchema;
  created_at: string;
}

export interface DatasetListItem {
  id: number;
  name: string;
  description: string | null;
  row_count: number;
  table_name: string;
  challenge_count: number;
  created_at: string;
}

export interface DatasetListResponse {
  total: number;
  datasets: DatasetListItem[];
}

export interface DatasetDetailResponse {
  id: number;
  name: string;
  description: string | null;
  table_name: string;
  row_count: number;
  schema: DatasetSchema;
  sample_data: Record<string, any>[]; // Array of row objects
  created_at: string;
}

/**
 * Custom Challenge types (teacher-created challenges)
 */
export interface CustomChallengeCreate {
  dataset_id: number;
  title: string;
  description: string;
  points: number; // 50-500
  difficulty: ChallengeDifficulty;
  expected_query: string;
  hints: [string, string, string]; // Exactly 3 hints
}

export interface CustomChallengeUpdate {
  title?: string;
  description?: string;
  points?: number;
  difficulty?: ChallengeDifficulty;
  expected_query?: string;
  hints?: [string, string, string];
  is_active?: boolean;
}

export interface CustomChallengeResponse {
  id: number;
  dataset_id: number;
  dataset_name: string;
  title: string;
  description: string;
  points: number;
  difficulty: ChallengeDifficulty;
  expected_query: string;
  hints: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomChallengeListItem {
  id: number;
  dataset_id: number;
  dataset_name: string;
  title: string;
  points: number;
  difficulty: ChallengeDifficulty;
  is_active: boolean;
  submission_count: number;
  completion_rate: number; // 0-100%
  created_at: string;
}

export interface CustomChallengeListResponse {
  total: number;
  challenges: CustomChallengeListItem[];
}

export interface CustomChallengeDetailResponse {
  id: number;
  dataset_id: number;
  dataset_name: string;
  title: string;
  description: string;
  points: number;
  difficulty: ChallengeDifficulty;
  expected_query: string;
  hints: string[];
  is_active: boolean;
  expected_output: Record<string, any>[] | null;
  created_at: string;
  updated_at: string;
}
