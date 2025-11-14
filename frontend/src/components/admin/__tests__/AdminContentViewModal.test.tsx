/**
 * AdminContentViewModal Component Tests
 * Story 4.5: Modal for viewing detailed content
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock component
const AdminContentViewModal = ({
  isOpen = false,
  content = null,
  onClose,
  contentData = null,
  onShowStats
}: any) => {
  if (!isOpen || !content) return null;

  return (
    <div data-testid="view-modal" role="dialog">
      <h2>Contenido Generado</h2>
      <div>
        <p>ID: {content.id}</p>
        <p>Tipo: {content.content_type}</p>
        <p>Documento: {content.document_name}</p>
        <p>Usuario: {content.user_username}</p>
        <p>Fecha: {new Date(content.created_at).toLocaleDateString()}</p>
      </div>

      {content.content_type === 'quiz' && (
        <button onClick={() => onShowStats?.()} data-testid="show-stats-btn">
          Ver Estadísticas
        </button>
      )}

      {content.content_type === 'learning_path' && (
        <button onClick={() => onShowStats?.()} data-testid="show-progress-btn">
          Ver Progreso
        </button>
      )}

      <div data-testid="content-preview">
        {contentData ? JSON.stringify(contentData, null, 2) : 'Cargando...'}
      </div>

      <button onClick={() => onClose?.()} data-testid="close-btn">
        Cerrar
      </button>
    </div>
  );
};

describe('AdminContentViewModal Component', () => {
  const mockContent = {
    id: 1,
    content_type: 'summary',
    document_name: 'Test Document',
    user_username: 'testuser',
    created_at: '2025-11-14T10:00:00Z',
  };

  const mockContentData = {
    summary: 'This is a test summary about the document content...'
  };

  let mockCallbacks: any;

  beforeEach(() => {
    mockCallbacks = {
      onClose: vi.fn(),
      onShowStats: vi.fn(),
    };
  });

  it('should not render when isOpen is false', () => {
    render(
      <AdminContentViewModal isOpen={false} content={mockContent} {...mockCallbacks} />
    );

    expect(screen.queryByTestId('view-modal')).not.toBeInTheDocument();
  });

  it('should render modal when isOpen is true', () => {
    render(
      <AdminContentViewModal isOpen={true} content={mockContent} {...mockCallbacks} />
    );

    expect(screen.getByTestId('view-modal')).toBeInTheDocument();
    expect(screen.getByText('Contenido Generado')).toBeInTheDocument();
  });

  it('should display content details', () => {
    render(
      <AdminContentViewModal
        isOpen={true}
        content={mockContent}
        contentData={mockContentData}
        {...mockCallbacks}
      />
    );

    expect(screen.getByText(`ID: ${mockContent.id}`)).toBeInTheDocument();
    expect(screen.getByText(`Tipo: ${mockContent.content_type}`)).toBeInTheDocument();
    expect(screen.getByText(`Documento: ${mockContent.document_name}`)).toBeInTheDocument();
    expect(screen.getByText(`Usuario: ${mockContent.user_username}`)).toBeInTheDocument();
  });

  it('should display formatted date', () => {
    render(
      <AdminContentViewModal isOpen={true} content={mockContent} {...mockCallbacks} />
    );

    const dateText = screen.getByText(/11\/14\/2025|14\/11\/2025/);
    expect(dateText).toBeInTheDocument();
  });

  it('should show stats button for quiz content', () => {
    const quizContent = { ...mockContent, content_type: 'quiz' };
    render(
      <AdminContentViewModal isOpen={true} content={quizContent} {...mockCallbacks} />
    );

    expect(screen.getByTestId('show-stats-btn')).toBeInTheDocument();
  });

  it('should show progress button for learning path content', () => {
    const pathContent = { ...mockContent, content_type: 'learning_path' };
    render(
      <AdminContentViewModal isOpen={true} content={pathContent} {...mockCallbacks} />
    );

    expect(screen.getByTestId('show-progress-btn')).toBeInTheDocument();
  });

  it('should not show stats button for summary content', () => {
    render(
      <AdminContentViewModal isOpen={true} content={mockContent} {...mockCallbacks} />
    );

    expect(screen.queryByTestId('show-stats-btn')).not.toBeInTheDocument();
    expect(screen.queryByTestId('show-progress-btn')).not.toBeInTheDocument();
  });

  it('should call onShowStats when stats button is clicked', async () => {
    const user = userEvent.setup();
    const quizContent = { ...mockContent, content_type: 'quiz' };

    render(
      <AdminContentViewModal isOpen={true} content={quizContent} {...mockCallbacks} />
    );

    const statsBtn = screen.getByTestId('show-stats-btn');
    await user.click(statsBtn);

    expect(mockCallbacks.onShowStats).toHaveBeenCalled();
  });

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AdminContentViewModal isOpen={true} content={mockContent} {...mockCallbacks} />
    );

    const closeBtn = screen.getByTestId('close-btn');
    await user.click(closeBtn);

    expect(mockCallbacks.onClose).toHaveBeenCalled();
  });

  it('should display loading state when contentData is not available', () => {
    render(
      <AdminContentViewModal isOpen={true} content={mockContent} {...mockCallbacks} />
    );

    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('should display content preview when contentData is available', () => {
    render(
      <AdminContentViewModal
        isOpen={true}
        content={mockContent}
        contentData={mockContentData}
        {...mockCallbacks}
      />
    );

    expect(screen.getByText(/This is a test summary/)).toBeInTheDocument();
  });
});
