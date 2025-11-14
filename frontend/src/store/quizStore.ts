/**
 * Quiz State Store - Zustand state management
 * Story 4.3: Quiz Interface Implementation
 */

import { create } from 'zustand';
import type { QuizState, Quiz, QuizSubmissionResponse } from '../types/quiz';

export interface QuizStore extends QuizState {
  setCurrentQuestion: (question: number) => void;
  setAnswer: (questionNumber: number, answer: string) => void;
  setQuizData: (quiz: Quiz | null) => void;
  setResultsData: (results: QuizSubmissionResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCompleted: (completed: boolean) => void;
  resetQuiz: () => void;
  setAnswers: (answers: Record<string, string>) => void;
}

// Initial state
const initialState: QuizState = {
  currentQuestion: 0,
  answers: {},
  quizData: null,
  resultsData: null,
  loading: false,
  error: null,
  completed: false,
};

/**
 * Quiz Zustand Store
 * Manages quiz state including current question, answers, results
 * Story 4.3: AC7 (state), AC8 (navigation)
 */
export const useQuizStore = create<QuizStore>((set) => ({
  ...initialState,

  setCurrentQuestion: (question: number) =>
    set({ currentQuestion: question }),

  setAnswer: (questionNumber: number, answer: string) =>
    set((state) => ({
      answers: {
        ...state.answers,
        [String(questionNumber)]: answer,
      },
    })),

  setQuizData: (quiz: Quiz | null) => set({ quizData: quiz }),

  setResultsData: (results: QuizSubmissionResponse | null) =>
    set({ resultsData: results }),

  setLoading: (loading: boolean) => set({ loading }),

  setError: (error: string | null) => set({ error }),

  setCompleted: (completed: boolean) => set({ completed }),

  setAnswers: (answers: Record<string, string>) => set({ answers }),

  resetQuiz: () => set(initialState),
}));
