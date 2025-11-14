/**
 * QuizQuestionCard Component
 * Story 4.3 AC3-AC4: Display question and answer options
 */

import React from 'react';
import type { QuizQuestion } from '../../types/quiz';

interface QuizQuestionCardProps {
  question: QuizQuestion;
  currentAnswer?: string;
  onAnswerChange: (answer: string) => void;
  disabled?: boolean;
}

const answerLabels = ['A', 'B', 'C', 'D'];

export const QuizQuestionCard: React.FC<QuizQuestionCardProps> = ({
  question,
  currentAnswer,
  onAnswerChange,
  disabled = false,
}) => {
  return (
    <div className="space-y-6 w-full">
      {/* Question Text */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-gray-900 leading-relaxed">
          {question.question}
        </h3>
        {question.difficulty && (
          <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${
            question.difficulty === 'basic'
              ? 'bg-green-100 text-green-800'
              : question.difficulty === 'intermediate'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}>
            {question.difficulty === 'basic' && 'Básico'}
            {question.difficulty === 'intermediate' && 'Intermedio'}
            {question.difficulty === 'advanced' && 'Avanzado'}
          </span>
        )}
      </div>

      {/* Answer Options */}
      <div className="space-y-3">
        {question.options.map((option, index) => (
          <label
            key={index}
            className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
          >
            <input
              type="radio"
              name="answer"
              value={answerLabels[index]}
              checked={currentAnswer === answerLabels[index]}
              onChange={(e) => onAnswerChange(e.target.value)}
              disabled={disabled}
              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500"
            />
            <span className="ml-4 flex-1">
              <span className="font-semibold text-gray-700">{answerLabels[index]}.</span>
              <span className="ml-2 text-gray-800">{option}</span>
            </span>
          </label>
        ))}
      </div>
    </div>
  );
};
