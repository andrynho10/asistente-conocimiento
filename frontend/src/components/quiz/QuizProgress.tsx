/**
 * QuizProgress Component
 * Story 4.3 AC2, AC18: Display progress bar with "Question X of Y" and time estimate
 */

import React from 'react';

interface QuizProgressProps {
  currentQuestion: number;
  totalQuestions: number;
  estimatedMinutes?: number;
}

export const QuizProgress: React.FC<QuizProgressProps> = ({
  currentQuestion,
  totalQuestions,
  estimatedMinutes,
}) => {
  const progress = ((currentQuestion + 1) / totalQuestions) * 100;
  const remainingQuestions = totalQuestions - currentQuestion;
  const remainingMinutes = Math.ceil((remainingQuestions / totalQuestions) * (estimatedMinutes || 5));

  return (
    <div className="w-full space-y-2">
      {/* Progress Information */}
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">
          Pregunta {currentQuestion + 1} de {totalQuestions}
        </span>
        {estimatedMinutes && (
          <span className="text-sm text-gray-500">
            Tiempo estimado: ~{remainingMinutes}min
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Progress Text */}
      <div className="text-xs text-gray-500 text-right">
        {Math.round(progress)}% completado
      </div>
    </div>
  );
};
