/**
 * LearningPathContainer Component
 * Story 4.4: Main container for displaying learning path
 * Handles data fetching, progress tracking, and orchestration
 */

import React, { useState, useEffect } from 'react';
import { LearningPath, LearningPathProgress } from '../../types/learning';
import { LearningPathTimeline } from './LearningPathTimeline';
import { Card } from '../ui/card';

interface LearningPathContainerProps {
  pathId: number;
  onBackClick: () => void;
}

export const LearningPathContainer: React.FC<LearningPathContainerProps> = ({
  pathId,
  onBackClick,
}) => {
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [progress, setProgress] = useState<boolean[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load learning path data
  useEffect(() => {
    const loadLearningPath = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/ia/learning-path/${pathId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('No se pudo cargar la ruta de aprendizaje');
        }

        const data: LearningPath = await response.json();
        setLearningPath(data);

        // Load progress from localStorage
        const savedProgress = localStorage.getItem(`learning_path_${pathId}_progress`);
        if (savedProgress) {
          const parsed: LearningPathProgress = JSON.parse(savedProgress);
          setProgress(parsed.completed);
        } else {
          // Initialize with all unchecked
          setProgress(new Array(data.steps.length).fill(false));
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setIsLoading(false);
      }
    };

    loadLearningPath();
  }, [pathId]);

  // Save progress to localStorage whenever it changes
  useEffect(() => {
    if (learningPath && progress.length > 0) {
      const progressData: LearningPathProgress = {
        pathId: pathId.toString(),
        completed: progress,
        completedCount: progress.filter(p => p).length,
        lastUpdated: Date.now(),
      };
      localStorage.setItem(
        `learning_path_${pathId}_progress`,
        JSON.stringify(progressData)
      );
    }
  }, [progress, pathId, learningPath]);

  const handleStepToggle = (stepIndex: number) => {
    const newProgress = [...progress];
    newProgress[stepIndex] = !newProgress[stepIndex];
    setProgress(newProgress);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <Card className="max-w-2xl mx-auto p-6">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-red-600">Error</h1>
            <p className="text-gray-600">{error}</p>
            <button
              onClick={onBackClick}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Volver
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (!learningPath) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <Card className="max-w-2xl mx-auto p-6">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-gray-900">No encontrado</h1>
            <p className="text-gray-600">La ruta de aprendizaje no existe</p>
            <button
              onClick={onBackClick}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Volver
            </button>
          </div>
        </Card>
      </div>
    );
  }

  const completedCount = progress.filter(p => p).length;
  const completionPercentage = Math.round((completedCount / learningPath.steps.length) * 100);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4" data-testid="learning-path-container">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{learningPath.title}</h1>
            <p className="text-gray-600 mt-2">Tema: {learningPath.topic}</p>
            <p className="text-sm text-gray-500 mt-1">
              Nivel: {learningPath.user_level} •
              Tiempo estimado: {learningPath.estimated_time_hours.toFixed(1)} horas
            </p>
          </div>
          <button
            onClick={onBackClick}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            ← Volver
          </button>
        </div>

        {/* Progress Bar */}
        <Card className="p-6">
          <div className="space-y-2">
            <div className="flex justify-between">
              <h2 className="font-semibold text-gray-900">Progreso</h2>
              <span className="text-sm font-medium text-gray-600">
                {completedCount} de {learningPath.steps.length} completados
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-green-500 h-3 rounded-full transition-all duration-300"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">{completionPercentage}% completado</p>
          </div>
        </Card>

        {/* Timeline */}
        <LearningPathTimeline
          steps={learningPath.steps}
          progress={progress}
          onStepToggle={handleStepToggle}
        />
      </div>
    </div>
  );
};
