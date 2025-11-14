/**
 * QuizContainer Component
 * Story 4.3: Main quiz controller component
 * Orchestrates quiz flow: load → answer → submit → results
 */

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { QuizProgress } from './QuizProgress';
import { QuizQuestionCard } from './QuizQuestion';
import { QuizResults } from './QuizResults';
import { useQuizStore } from '../../store/quizStore';
import { useQuizStore as useLocalQuizStore } from '../../store/quizStore';
import * as quizService from '../../services/quizService';
import type { Quiz } from '../../types/quiz';

interface QuizContainerProps {
  quizId: number;
  onBackClick?: () => void;
}

export const QuizContainer: React.FC<QuizContainerProps> = ({
  quizId,
  onBackClick,
}) => {
  const store = useQuizStore();
  const [localError, setLocalError] = useState<string | null>(null);
  const [showValidationError, setShowValidationError] = useState(false);

  // Load quiz data on mount
  useEffect(() => {
    const loadQuiz = async () => {
      try {
        store.setLoading(true);
        store.setError(null);
        setLocalError(null);

        const quiz = await quizService.getQuiz(quizId);
        store.setQuizData(quiz);

        // Try to restore from localStorage
        const savedProgress = getProgressFromLocalStorage(quizId);
        if (savedProgress && isProgressValid(savedProgress)) {
          store.setAnswers(savedProgress.answers);
          store.setCurrentQuestion(savedProgress.currentQuestion);
        } else {
          store.setCurrentQuestion(0);
          store.setAnswers({});
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error cargando quiz';
        store.setError(message);
        setLocalError(message);
      } finally {
        store.setLoading(false);
      }
    };

    if (!store.quizData) {
      loadQuiz();
    }
  }, [quizId, store]);

  // Save progress to localStorage on change
  useEffect(() => {
    if (store.quizData && store.answers) {
      saveProgressToLocalStorage(quizId, {
        currentQuestion: store.currentQuestion,
        answers: store.answers,
        startTime: Date.now(),
      });
    }
  }, [store.answers, store.currentQuestion, quizId, store.quizData]);

  const handleNextQuestion = () => {
    // Validate current question is answered
    if (!store.answers[String(store.currentQuestion + 1)]) {
      setShowValidationError(true);
      setTimeout(() => setShowValidationError(false), 3000);
      return;
    }

    if (store.quizData && store.currentQuestion < store.quizData.total_questions - 1) {
      store.setCurrentQuestion(store.currentQuestion + 1);
      setShowValidationError(false);
    }
  };

  const handlePreviousQuestion = () => {
    if (store.currentQuestion > 0) {
      store.setCurrentQuestion(store.currentQuestion - 1);
      setShowValidationError(false);
    }
  };

  const handleAnswerChange = (answer: string) => {
    store.setAnswer(store.currentQuestion + 1, answer);
  };

  const handleSubmitQuiz = async () => {
    try {
      // Validate all questions answered
      if (!store.quizData || Object.keys(store.answers).length !== store.quizData.total_questions) {
        setLocalError('Debes responder todas las preguntas');
        return;
      }

      store.setLoading(true);
      const results = await quizService.submitQuiz(quizId, store.answers);
      store.setResultsData(results);
      store.setCompleted(true);

      // Clear localStorage after submission
      clearProgressFromLocalStorage(quizId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Error enviando quiz';
      setLocalError(message);
      store.setError(message);
    } finally {
      store.setLoading(false);
    }
  };

  const handleRetryQuiz = () => {
    store.resetQuiz();
    store.setCompleted(false);
    // Reload quiz data
    if (store.quizData) {
      store.setCurrentQuestion(0);
      store.setAnswers({});
    }
  };

  // Loading state
  if (store.loading && !store.quizData) {
    return (
      <div className="w-full max-w-2xl mx-auto p-8 text-center">
        <div className="inline-block">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        </div>
        <p className="mt-4 text-gray-600">Cargando quiz...</p>
      </div>
    );
  }

  // Error state
  if (localError && !store.quizData) {
    return (
      <div className="w-full max-w-2xl mx-auto p-8 text-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 font-medium">{localError}</p>
        </div>
        {onBackClick && (
          <button
            onClick={onBackClick}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Volver
          </button>
        )}
      </div>
    );
  }

  // Results view
  if (store.completed && store.resultsData) {
    return (
      <QuizResults
        results={store.resultsData}
        quiz={store.quizData || undefined}
        onRetry={handleRetryQuiz}
        onBackToDocument={onBackClick || (() => {})}
        onViewOtherQuizzes={onBackClick || (() => {})}
      />
    );
  }

  // Quiz view
  if (!store.quizData) {
    return null;
  }

  const currentQuestion = store.quizData.questions[store.currentQuestion];
  const isLastQuestion = store.currentQuestion === store.quizData.total_questions - 1;
  const currentAnswer = store.answers[String(store.currentQuestion + 1)];

  return (
    <div className="w-full max-w-2xl mx-auto p-8 space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{store.quizData.title}</h1>
            {store.quizData && (
              <p className="text-sm text-gray-600 mt-1">
                Dificultad: {store.quizData.difficulty === 'basic' ? 'Básico' : store.quizData.difficulty === 'intermediate' ? 'Intermedio' : 'Avanzado'}
              </p>
            )}
          </div>
          {onBackClick && (
            <button
              onClick={onBackClick}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-6 h-6 text-gray-600" />
            </button>
          )}
        </div>

        {/* Progress */}
        <QuizProgress
          currentQuestion={store.currentQuestion}
          totalQuestions={store.quizData.total_questions}
          estimatedMinutes={store.quizData.estimated_minutes}
        />
      </div>

      {/* Question */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <QuizQuestionCard
          question={currentQuestion}
          currentAnswer={currentAnswer}
          onAnswerChange={handleAnswerChange}
        />
      </div>

      {/* Validation Error */}
      {showValidationError && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-orange-700 text-sm font-medium">
            ⚠️ Por favor selecciona una respuesta para continuar
          </p>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex gap-4 justify-between">
        <button
          onClick={handlePreviousQuestion}
          disabled={store.currentQuestion === 0}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
            store.currentQuestion === 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <ChevronLeft className="w-5 h-5" />
          <span>Anterior</span>
        </button>

        {!isLastQuestion ? (
          <button
            onClick={handleNextQuestion}
            disabled={store.loading}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
              store.loading
                ? 'bg-blue-400 text-white cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <span>Siguiente</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        ) : (
          <button
            onClick={handleSubmitQuiz}
            disabled={store.loading}
            className={`px-8 py-3 rounded-lg font-medium transition-colors ${
              store.loading
                ? 'bg-green-400 text-white cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {store.loading ? 'Enviando...' : 'Finalizar Quiz'}
          </button>
        )}
      </div>

      {/* Local error message */}
      {localError && store.quizData && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{localError}</p>
        </div>
      )}
    </div>
  );
};

// localStorage helpers
function getProgressFromLocalStorage(quizId: number) {
  try {
    const key = `quiz_progress_${quizId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function saveProgressToLocalStorage(
  quizId: number,
  progress: { currentQuestion: number; answers: Record<string, string>; startTime: number }
) {
  try {
    const key = `quiz_progress_${quizId}`;
    localStorage.setItem(
      key,
      JSON.stringify({
        ...progress,
        savedAt: Date.now(),
      })
    );
  } catch {
    // Silently fail if localStorage not available
  }
}

function clearProgressFromLocalStorage(quizId: number) {
  try {
    const key = `quiz_progress_${quizId}`;
    localStorage.removeItem(key);
  } catch {
    // Silently fail
  }
}

function isProgressValid(progress: any): boolean {
  if (!progress || !progress.savedAt) return false;
  // Check if progress is older than 7 days
  const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
  return Date.now() - progress.savedAt < sevenDaysMs;
}
