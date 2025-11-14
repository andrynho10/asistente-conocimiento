/**
 * QuizPage Component
 * Story 4.3: Main page for quiz interface
 * Handles route parameters and authentication
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { QuizContainer } from '../components/quiz/QuizContainer';

export const QuizPage: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  // Check authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="inline-block">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-lg shadow-md p-8 text-center space-y-4 max-w-md">
          <h1 className="text-2xl font-bold text-gray-900">Acceso requerido</h1>
          <p className="text-gray-600">
            Debes iniciar sesión para acceder a los quizzes.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Ir a login
          </button>
        </div>
      </div>
    );
  }

  if (!quizId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-lg shadow-md p-8 text-center space-y-4 max-w-md">
          <h1 className="text-2xl font-bold text-gray-900">Error</h1>
          <p className="text-gray-600">
            No se especificó un quiz válido.
          </p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <QuizContainer
        quizId={parseInt(quizId, 10)}
        onBackClick={() => navigate(-1)}
      />
    </div>
  );
};
