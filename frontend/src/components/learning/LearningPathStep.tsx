/**
 * LearningPathStep Component
 * Story 4.4: Individual step card in learning path timeline
 * Displays step info, checkbox, and navigation to document/quiz
 */

import React, { useState } from 'react';
import { LearningPathStep as StepType } from '../../types/learning';
import { Card } from '../ui/card';

interface LearningPathStepProps {
  step: StepType;
  stepIndex: number;
  isCompleted: boolean;
  isCurrent: boolean;
  onToggle: () => void;
}

export const LearningPathStep: React.FC<LearningPathStepProps> = ({
  step,
  stepIndex,
  isCompleted,
  isCurrent,
  onToggle,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Check if this is a quiz step (document_id might be -1 or special indicator)
  // For now, we'll treat all as document steps
  const isQuizStep = false;

  return (
    <Card
      className={`p-6 transition-all duration-200 ${
        isCurrent ? 'ring-2 ring-blue-400 shadow-md' : ''
      } ${isHovered ? 'shadow-lg' : 'shadow'}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="space-y-4">
        {/* Title */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
            <p className="text-sm text-gray-600 mt-1">{step.why_this_step}</p>
          </div>

          {/* Checkbox */}
          <input
            type="checkbox"
            checked={isCompleted}
            onChange={onToggle}
            className="w-6 h-6 text-green-600 rounded border-gray-300 cursor-pointer flex-shrink-0 mt-1"
            aria-label={`Marcar paso ${step.step_number} como completado`}
          />
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">⏱</span>
            <span className="text-gray-700 font-medium">
              {step.estimated_time_minutes} minutos
            </span>
          </div>

          {isQuizStep && (
            <div className="flex items-center gap-2">
              <span className="text-blue-500">📝</span>
              <span className="text-blue-700 font-medium">Quiz</span>
            </div>
          )}

          {!isQuizStep && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">📄</span>
              <span className="text-gray-700 font-medium">
                Documento {step.document_id}
              </span>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-2">
          {isQuizStep ? (
            <button className="flex-1 px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium rounded-lg transition-colors text-sm">
              Ir al Quiz →
            </button>
          ) : (
            <button className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors text-sm">
              Ver Documento →
            </button>
          )}
        </div>

        {/* Completion badge */}
        {isCompleted && (
          <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
            <span>✓</span>
            <span>Completado</span>
          </div>
        )}
      </div>
    </Card>
  );
};
