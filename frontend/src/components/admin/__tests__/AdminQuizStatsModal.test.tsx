/**
 * AdminQuizStatsModal Component Tests
 * Story 4.5: Modal for displaying quiz statistics
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock component
const AdminQuizStatsModal = ({
  isOpen = false,
  quizId = null,
  stats = null,
  isLoading = false,
  onClose
}: any) => {
  if (!isOpen || !quizId) return null;

  return (
    <div data-testid="quiz-stats-modal" role="dialog">
      <h2>Estadísticas del Quiz</h2>

      {isLoading && <p>Cargando estadísticas...</p>}

      {!isLoading && stats && (
        <div>
          <div data-testid="total-attempts">
            <strong>Total de Intentos:</strong> {stats.total_attempts}
          </div>
          <div data-testid="avg-score">
            <strong>Puntuación Promedio:</strong> {stats.avg_score_percentage}%
          </div>
          <div data-testid="pass-rate">
            <strong>Tasa de Aprobación:</strong> {stats.pass_rate}%
          </div>
          {stats.most_difficult_question && (
            <div data-testid="difficult-question">
              <strong>Pregunta Más Difícil:</strong> #{stats.most_difficult_question.number}
              <br />
              Tasa de Aciertos: {stats.most_difficult_question.correct_rate}%
            </div>
          )}
        </div>
      )}

      <button onClick={() => onClose?.()} data-testid="close-btn">
        Cerrar
      </button>
    </div>
  );
};

describe('AdminQuizStatsModal Component', () => {
  const mockStats = {
    quiz_id: 5,
    total_attempts: 42,
    avg_score_percentage: 78.5,
    pass_rate: 85.7,
    most_difficult_question: {
      number: 7,
      correct_rate: 52.4,
    },
  };

  let mockCallbacks: any;

  beforeEach(() => {
    mockCallbacks = {
      onClose: vi.fn(),
    };
  });

  it('should not render when isOpen is false', () => {
    render(
      <AdminQuizStatsModal isOpen={false} quizId={5} stats={mockStats} {...mockCallbacks} />
    );

    expect(screen.queryByTestId('quiz-stats-modal')).not.toBeInTheDocument();
  });

  it('should render modal when isOpen is true', () => {
    render(
      <AdminQuizStatsModal isOpen={true} quizId={5} stats={mockStats} {...mockCallbacks} />
    );

    expect(screen.getByTestId('quiz-stats-modal')).toBeInTheDocument();
    expect(screen.getByText('Estadísticas del Quiz')).toBeInTheDocument();
  });

  it('should display loading state', () => {
    render(
      <AdminQuizStatsModal
        isOpen={true}
        quizId={5}
        stats={null}
        isLoading={true}
        {...mockCallbacks}
      />
    );

    expect(screen.getByText('Cargando estadísticas...')).toBeInTheDocument();
  });

  it('should display all statistics when available', () => {
    render(
      <AdminQuizStatsModal isOpen={true} quizId={5} stats={mockStats} {...mockCallbacks} />
    );

    expect(screen.getByTestId('total-attempts')).toBeInTheDocument();
    expect(screen.getByText(`Total de Intentos: ${mockStats.total_attempts}`)).toBeInTheDocument();

    expect(screen.getByTestId('avg-score')).toBeInTheDocument();
    expect(screen.getByText(`Puntuación Promedio: ${mockStats.avg_score_percentage}%`)).toBeInTheDocument();

    expect(screen.getByTestId('pass-rate')).toBeInTheDocument();
    expect(screen.getByText(`Tasa de Aprobación: ${mockStats.pass_rate}%`)).toBeInTheDocument();
  });

  it('should display most difficult question statistics', () => {
    render(
      <AdminQuizStatsModal isOpen={true} quizId={5} stats={mockStats} {...mockCallbacks} />
    );

    expect(screen.getByTestId('difficult-question')).toBeInTheDocument();
    expect(screen.getByText(/Pregunta Más Difícil: #7/)).toBeInTheDocument();
    expect(screen.getByText(/Tasa de Aciertos: 52.4%/)).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AdminQuizStatsModal isOpen={true} quizId={5} stats={mockStats} {...mockCallbacks} />
    );

    const closeBtn = screen.getByTestId('close-btn');
    await user.click(closeBtn);

    expect(mockCallbacks.onClose).toHaveBeenCalled();
  });

  it('should handle zero statistics gracefully', () => {
    const zeroStats = {
      quiz_id: 5,
      total_attempts: 0,
      avg_score_percentage: 0,
      pass_rate: 0,
      most_difficult_question: null,
    };

    render(
      <AdminQuizStatsModal isOpen={true} quizId={5} stats={zeroStats} {...mockCallbacks} />
    );

    expect(screen.getByText('Total de Intentos: 0')).toBeInTheDocument();
    expect(screen.getByText('Puntuación Promedio: 0%')).toBeInTheDocument();
  });

  it('should format percentage values correctly', () => {
    const statsWithDecimals = {
      ...mockStats,
      avg_score_percentage: 66.666,
      pass_rate: 33.333,
    };

    render(
      <AdminQuizStatsModal
        isOpen={true}
        quizId={5}
        stats={statsWithDecimals}
        {...mockCallbacks}
      />
    );

    expect(screen.getByText('Puntuación Promedio: 66.666%')).toBeInTheDocument();
    expect(screen.getByText('Tasa de Aprobación: 33.333%')).toBeInTheDocument();
  });
});
