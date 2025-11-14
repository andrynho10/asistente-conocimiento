/**
 * LearningPathPage Component
 * Story 4.4: Main page for displaying learning path
 * Handles route parameters, authentication, and page layout
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LearningPathContainer } from '../components/learning/LearningPathContainer';

export const LearningPathPage: React.FC = () => {
  const { pathId } = useParams<{ pathId: string }>();
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
            Debes iniciar sesión para acceder a las rutas de aprendizaje.
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

  if (!pathId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-lg shadow-md p-8 text-center space-y-4 max-w-md">
          <h1 className="text-2xl font-bold text-gray-900">Error</h1>
          <p className="text-gray-600">
            No se especificó una ruta de aprendizaje válida.
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
    <LearningPathContainer
      pathId={parseInt(pathId, 10)}
      onBackClick={() => navigate(-1)}
    />
  );
};
