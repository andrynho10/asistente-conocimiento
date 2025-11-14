/**
 * Quiz Service - API client for quiz endpoints
 * Story 4.3: Quiz Interface Implementation
 */

import axios, { AxiosError } from 'axios';
import type {
  Quiz,
  QuizSubmissionRequest,
  QuizSubmissionResponse,
  QuizAttempt,
} from '../types/quiz';

// API base URL from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with JWT authentication
const quizAxios = axios.create({
  baseURL: `${API_URL}/api/ia`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
quizAxios.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Get quiz by ID
 * Retrieves quiz questions without exposing correct answers
 */
export const getQuiz = async (quizId: number): Promise<Quiz> => {
  try {
    const response = await quizAxios.get<Quiz>(`/quiz/${quizId}`);
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;

    if (axiosError.response?.status === 401) {
      throw new Error('Autenticación requerida');
    }

    if (axiosError.response?.status === 404) {
      throw new Error('Quiz no encontrado');
    }

    if (axiosError.response?.status === 403) {
      throw new Error('Acceso denegado a este quiz');
    }

    throw new Error(
      (axiosError.response?.data as any)?.detail ||
      'Error cargando quiz. Intenta de nuevo.'
    );
  }
};

/**
 * Submit quiz answers and get evaluated results
 * Story 4.3 AC9-AC11: Submit answers, get score and results
 */
export const submitQuiz = async (
  quizId: number,
  answers: Record<string, string>
): Promise<QuizSubmissionResponse> => {
  try {
    const request: QuizSubmissionRequest = { answers };
    const response = await quizAxios.post<QuizSubmissionResponse>(
      `/quiz/${quizId}/submit`,
      request
    );
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;

    if (axiosError.response?.status === 401) {
      throw new Error('Autenticación requerida');
    }

    if (axiosError.response?.status === 404) {
      throw new Error('Quiz no encontrado');
    }

    if (axiosError.response?.status === 403) {
      throw new Error('Acceso denegado a este quiz');
    }

    if (axiosError.response?.status === 400) {
      throw new Error(
        (axiosError.response?.data as any)?.detail ||
        'Respuestas inválidas. Verifica todas las preguntas.'
      );
    }

    throw new Error(
      (axiosError.response?.data as any)?.detail ||
      'Error enviando quiz. Intenta de nuevo.'
    );
  }
};

/**
 * Get quiz attempt history for a specific quiz
 * Story 4.3 AC20: Retrieve audit trail of quiz attempts
 */
export const getQuizAttempts = async (quizId: number): Promise<QuizAttempt[]> => {
  try {
    const response = await quizAxios.get<QuizAttempt[]>(
      `/quiz/${quizId}/attempts`
    );
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;

    if (axiosError.response?.status === 401) {
      throw new Error('Autenticación requerida');
    }

    if (axiosError.response?.status === 404) {
      throw new Error('Quiz no encontrado');
    }

    throw new Error(
      (axiosError.response?.data as any)?.detail ||
      'Error cargando historial de intentos'
    );
  }
};

export default {
  getQuiz,
  submitQuiz,
  getQuizAttempts,
};
