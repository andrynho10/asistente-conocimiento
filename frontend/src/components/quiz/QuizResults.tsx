/**
 * QuizResults Component
 * Story 4.3 AC12-AC14: Display quiz results with score, badge, and action buttons
 */

import React from 'react';
import { RotateCcw, ArrowLeft, FileText } from 'lucide-react';
import { QuestionResultCard } from './QuestionResult';
import type { QuizSubmissionResponse, Quiz } from '../../types/quiz';

interface QuizResultsProps {
  results: QuizSubmissionResponse;
  quiz?: Quiz;
  onRetry: () => void;
  onBackToDocument: () => void;
  onViewOtherQuizzes: () => void;
}

export const QuizResults: React.FC<QuizResultsProps> = ({
  results,
  quiz,
  onRetry,
  onBackToDocument,
  onViewOtherQuizzes,
}) => {
  const isPassed = results.passed;
  const percentage = Math.round(results.percentage);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 py-8">
      {/* Score Card */}
      <div
        className={`rounded-lg p-8 text-center space-y-4 ${
          isPassed
            ? 'bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-200'
            : 'bg-gradient-to-br from-yellow-50 to-yellow-100 border-2 border-yellow-200'
        }`}
      >
        {/* Badge */}
        <div
          className={`inline-block px-6 py-3 rounded-full text-lg font-bold ${
            isPassed
              ? 'bg-green-200 text-green-900'
              : 'bg-yellow-200 text-yellow-900'
          }`}
        >
          {isPassed ? '¡Aprobado!' : 'No aprobado'}
        </div>

        {/* Score Display */}
        <div className="space-y-2">
          <div className="text-5xl font-bold text-gray-900">
            {percentage}%
          </div>
          <div className="text-lg text-gray-700">
            {results.score} de {results.total_questions} preguntas correctas
          </div>
        </div>

        {/* Status Message */}
        <p className="text-sm text-gray-600">
          {isPassed
            ? 'Excelente trabajo. Has demostrado una buena comprensión del contenido.'
            : 'Sigue estudiando. Revisa las respuestas incorrectas y vuelve a intentarlo.'}
        </p>
      </div>

      {/* Detailed Results */}
      <div className="space-y-6">
        <h3 className="text-2xl font-bold text-gray-900">Desglose por pregunta</h3>

        {/* Results List */}
        <div className="space-y-4">
          {results.results.map((result) => (
            <QuestionResultCard
              key={result.question_number}
              result={result}
              questionText={
                quiz?.questions[result.question_number - 1]?.question
              }
            />
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-8 border-t border-gray-200">
        {/* Retry Button */}
        <button
          onClick={onRetry}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          <RotateCcw className="w-5 h-5" />
          <span>Reintentar Quiz</span>
        </button>

        {/* Back to Document Button */}
        <button
          onClick={onBackToDocument}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Volver al Documento</span>
        </button>

        {/* View Other Quizzes Button */}
        <button
          onClick={onViewOtherQuizzes}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          <FileText className="w-5 h-5" />
          <span>Ver otros Quizzes</span>
        </button>
      </div>
    </div>
  );
};
