/**
 * Learning Path Types
 * Story 4.4: Type definitions for learning path generation and visualization
 */

export type UserLevel = 'beginner' | 'intermediate' | 'advanced';

export interface LearningPathStep {
  step_number: number;
  title: string;
  document_id: number;
  why_this_step: string;
  estimated_time_minutes: number;
}

export interface LearningPath {
  id: number;
  user_id: number;
  topic: string;
  user_level: UserLevel;
  title: string;
  steps: LearningPathStep[];
  estimated_time_hours: number;
  content_json: string;
  created_at: string;
}

export interface LearningPathGenerationRequest {
  topic: string;
  user_level: UserLevel;
}

export interface LearningPathGenerationResponse {
  learning_path_id: number;
  title: string;
  steps: LearningPathStep[];
  total_steps: number;
  estimated_time_hours: number;
  user_level: UserLevel;
  generated_at: string;
}

export interface LearningPathProgress {
  pathId: string;
  completed: boolean[];
  completedCount: number;
  lastUpdated: number;
}
