/**
 * Admin Types
 *
 * TypeScript interfaces and types for admin dashboard.
 */

export type ContentType = 'summary' | 'quiz' | 'learning_path';

export interface GeneratedContent {
  id: number;
  document_id: number;
  user_id: number;
  content_type: ContentType;
  content_json?: Record<string, any>;
  created_at: string;
  is_validated: boolean;
  validated_by?: number;
  validated_at?: string;
  deleted_at?: string;
  document_name?: string;
  user_username?: string;
}

export interface GeneratedContentFilters {
  type?: ContentType;
  document_id?: number;
  user_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  limit: number;
  offset: number;
  sort_by: 'id' | 'created_at' | 'content_type';
  sort_order: 'asc' | 'desc';
}

export interface GeneratedContentListResponse {
  total: number;
  items: GeneratedContent[];
  limit: number;
  offset: number;
}

export interface QuizStats {
  quiz_id: number;
  total_attempts: number;
  avg_score_percentage: number;
  pass_rate: number;
  most_difficult_question?: {
    number: number;
    correct_rate: number;
  };
}

export interface LearningPathStats {
  path_id: number;
  total_views: number;
  completed_count: number;
  completion_rate: number;
  most_skipped_step?: string;
}

export interface AdminMetrics {
  total_summaries: number;
  total_quizzes: number;
  total_learning_paths: number;
  this_week: number;
}

export interface AdminAuditLog {
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: number;
  details?: Record<string, any>;
  ip_address?: string;
  timestamp: string;
}

export type AdminAction =
  | 'VALIDATE_CONTENT'
  | 'DELETE_CONTENT'
  | 'VIEW_CONTENT'
  | 'EXPORT_CONTENT';
