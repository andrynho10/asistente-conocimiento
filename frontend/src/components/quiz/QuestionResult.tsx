/**
 * QuestionResultCard Component
 * Story 4.3 AC13: Display individual question result with explanation
 */

import React from 'react';
import { Check, X } from 'lucide-react';
import type { QuestionResult } from '../../types/quiz';

interface QuestionResultCardProps {
  result: QuestionResult;
  questionText?: string;
}

const answerLabels = ['A', 'B', 'C', 'D'];

export const QuestionResultCard: React.FC<QuestionResultCardProps> = ({
  result,
  questionText,
}) => {
  const isCorrect = result.is_correct;

  return (
    <div
      className={`border-2 rounded-lg p-5 space-y-4 ${
        isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
      }`}
    >
      {/* Question Number and Status */}
      <div className="flex items-start justify-between">
        <h4 className="font-semibold text-gray-900">
          Pregunta {result.question_number}
        </h4>
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
            isCorrect
              ? 'bg-green-200 text-green-800'
              : 'bg-red-200 text-red-800'
          }`}
        >
          {isCorrect ? (
            <>
              <Check className="w-4 h-4" />
              <span>Correcta</span>
            </>
          ) : (
            <>
              <X className="w-4 h-4" />
              <span>Incorrecta</span>
            </>
          )}
        </div>
      </div>

      {/* Question Text */}
      {questionText && (
        <p className="text-gray-800">{questionText}</p>
      )}

      {/* Answer Comparison */}
      <div className="space-y-3">
        <div className="flex gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-1">Tu respuesta</p>
            <div className="space-y-1">
              <p className="text-lg font-semibold text-gray-900">
                {result.user_answer}
              </p>
              <p className="text-sm text-gray-700">
                {result.user_answer_text}
              </p>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-1">Respuesta correcta</p>
            <div className="space-y-1">
              <p className="text-lg font-semibold text-green-700">
                {result.correct_answer}
              </p>
              <p className="text-sm text-green-700">
                {result.correct_answer_text}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className={`p-3 rounded-lg ${
        isCorrect ? 'bg-green-100' : 'bg-red-100'
      }`}>
        <p className="text-sm font-medium text-gray-700 mb-1">Explicación</p>
        <p className="text-gray-700 text-sm leading-relaxed">
          {result.explanation}
        </p>
      </div>
    </div>
  );
};
