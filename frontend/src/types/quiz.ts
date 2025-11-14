/**
 * Quiz-related TypeScript types and interfaces
 * Story 4.3: Quiz Interface Implementation
 */

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
  difficulty: 'basic' | 'intermediate' | 'advanced';
}

export interface Quiz {
  quiz_id: number;
  title: string;
  document_id: number;
  questions: QuizQuestion[];
  total_questions: number;
  difficulty: 'basic' | 'intermediate' | 'advanced';
  estimated_minutes: number;
  generated_at: string;
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  user_id: number;
  answers_json: Record<string, string>;
  score: number;
  total_questions: number;
  percentage: number;
  timestamp: string;
}

export interface QuestionResult {
  question_number: number;
  user_answer: string;
  user_answer_text: string;
  correct_answer: string;
  correct_answer_text: string;
  is_correct: boolean;
  explanation: string;
}

export interface QuizSubmissionRequest {
  answers: Record<string, string>;
}

export interface QuizSubmissionResponse {
  quiz_id: number;
  score: number;
  total_questions: number;
  percentage: number;
  passed: boolean;
  results: QuestionResult[];
  submitted_at: string;
}

export interface QuizState {
  currentQuestion: number;
  answers: Record<string, string>;
  quizData: Quiz | null;
  resultsData: QuizSubmissionResponse | null;
  loading: boolean;
  error: string | null;
  completed: boolean;
}

export interface QuizContextType {
  state: QuizState;
  loadQuiz: (quizId: number) => Promise<void>;
  setAnswer: (questionNumber: number, answer: string) => void;
  nextQuestion: () => void;
  previousQuestion: () => void;
  submitQuiz: () => Promise<void>;
  resetQuiz: () => void;
}
