/**
 * LearningPathTimeline Component
 * Story 4.4: Vertical timeline visualization for learning path steps
 * Displays steps with progress indicators and navigation
 */

import React from 'react';
import { LearningPathStep } from '../../types/learning';
import { LearningPathStep as StepComponent } from './LearningPathStep';

interface LearningPathTimelineProps {
  steps: LearningPathStep[];
  progress: boolean[];
  onStepToggle: (stepIndex: number) => void;
}

export const LearningPathTimeline: React.FC<LearningPathTimelineProps> = ({
  steps,
  progress,
  onStepToggle,
}) => {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => {
        const isCompleted = progress[index];
        const isCurrent = index === 0 || (progress[index - 1] && !isCompleted);

        return (
          <div key={step.step_number} className="relative flex gap-6">
            {/* Timeline connector */}
            <div className="flex flex-col items-center">
              {/* Circle indicator */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-white transition-all duration-300 ${
                  isCompleted
                    ? 'bg-green-500'
                    : isCurrent
                      ? 'bg-blue-600 ring-4 ring-blue-200'
                      : 'bg-gray-400'
                }`}
              >
                {isCompleted ? '✓' : step.step_number}
              </div>

              {/* Vertical line to next step */}
              {index < steps.length - 1 && (
                <div
                  className={`w-1 flex-grow mt-2 mb-2 transition-colors duration-300 ${
                    isCompleted ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                  style={{ minHeight: '100px' }}
                />
              )}
            </div>

            {/* Step card */}
            <div className="flex-1">
              <StepComponent
                step={step}
                stepIndex={index}
                isCompleted={isCompleted}
                isCurrent={isCurrent}
                onToggle={() => onStepToggle(index)}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
