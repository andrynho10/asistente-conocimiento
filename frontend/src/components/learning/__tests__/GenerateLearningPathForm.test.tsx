/**
 * GenerateLearningPathForm Tests
 * Story 4.4: Form tests for learning path generation
 * Tests AC1-AC2, AC18: Form validation, submission, and error handling
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { GenerateLearningPathForm } from '../GenerateLearningPathForm';

// Mock fetch
global.fetch = vi.fn();

// Mock useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

const mockLocalStorage = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('GenerateLearningPathForm (Story 4.4)', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    mockLocalStorage.setItem('auth_token', 'test-token');
    vi.clearAllMocks();
  });

  // AC1-AC2: Form validation
  describe('Form Validation', () => {
    it('should render form with topic input and user level dropdown', () => {
      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      expect(screen.getByPlaceholderText(/ej: procedimientos/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue('Intermedio')).toBeInTheDocument();
    });

    it('should not allow submission with empty topic', async () => {
      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const submitButton = screen.getByText('Generar Ruta');
      expect(submitButton).toBeDisabled();
    });

    it('should validate minimum topic length (AC2)', async () => {
      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);

      await userEvent.type(topicInput, 'abc'); // Too short

      const submitButton = screen.getByText('Generar Ruta');
      expect(submitButton).toBeDisabled();

      // Show error when trying to submit
      fireEvent.click(submitButton);
    });

    it('should allow submission with valid topic', async () => {
      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      await userEvent.type(topicInput, 'procedimientos de reembolsos');

      const submitButton = screen.getByText('Generar Ruta');
      expect(submitButton).not.toBeDisabled();
    });
  });

  // AC1: Endpoint call with parameters
  describe('API Integration', () => {
    it('should call POST /api/ia/generate/learning-path with correct parameters', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          learning_path_id: 1,
          title: 'Test Path',
          steps: [],
          estimated_time_hours: 1,
        }),
      });

      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      const userLevelSelect = screen.getByDisplayValue('Intermedio');

      await userEvent.type(topicInput, 'procedimientos de reembolsos');
      fireEvent.change(userLevelSelect, { target: { value: 'beginner' } });

      const submitButton = screen.getByText('Generar Ruta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/ia/generate/learning-path',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              Authorization: 'Bearer test-token',
            }),
            body: JSON.stringify({
              topic: 'procedimientos de reembolsos',
              user_level: 'beginner',
            }),
          })
        );
      });
    });

    it('should show loading state during generation', async () => {
      (global.fetch as any).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      await userEvent.type(topicInput, 'procedimientos de reembolsos');

      const submitButton = screen.getByText('Generar Ruta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Generando...')).toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully (AC12)', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          detail: "No se encontraron documentos suficientes sobre 'tema inexistente'.",
        }),
      });

      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      await userEvent.type(topicInput, 'tema inexistente muy específico');

      const submitButton = screen.getByText('Generar Ruta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/No se encontraron documentos suficientes/i)
        ).toBeInTheDocument();
      });
    });

    it('should show success message and redirect on successful generation', async () => {
      const onSuccess = vi.fn();

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          learning_path_id: 42,
          title: 'Test Path',
          steps: [],
          estimated_time_hours: 1,
        }),
      });

      render(
        <BrowserRouter>
          <GenerateLearningPathForm onSuccess={onSuccess} />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      await userEvent.type(topicInput, 'procedimientos de reembolsos');

      const submitButton = screen.getByText('Generar Ruta');
      fireEvent.click(submitButton);

      await waitFor(
        () => {
          expect(
            screen.getByText(/Ruta de aprendizaje generada exitosamente/i)
          ).toBeInTheDocument();
        },
        { timeout: 2000 }
      );

      // Wait for redirect
      await waitFor(
        () => {
          expect(onSuccess).toHaveBeenCalledWith(42);
        },
        { timeout: 2000 }
      );
    });
  });

  // AC18: Authentication requirement
  describe('Authentication', () => {
    it('should require valid token before submitting', async () => {
      mockLocalStorage.clear(); // Remove token

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(/ej: procedimientos/i);
      await userEvent.type(topicInput, 'procedimientos de reembolsos');

      const submitButton = screen.getByText('Generar Ruta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/No estás autenticado/i)).toBeInTheDocument();
      });
    });
  });

  // Form interaction
  describe('User Level Selection', () => {
    it('should allow selecting different user levels', async () => {
      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const userLevelSelect = screen.getByDisplayValue('Intermedio');

      fireEvent.change(userLevelSelect, { target: { value: 'advanced' } });
      expect(userLevelSelect).toHaveValue('advanced');

      fireEvent.change(userLevelSelect, { target: { value: 'beginner' } });
      expect(userLevelSelect).toHaveValue('beginner');
    });

    it('should allow form submission with valid topic', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          learning_path_id: 1,
          title: 'Test Path',
          steps: [],
          estimated_time_hours: 1,
        }),
      });

      render(
        <BrowserRouter>
          <GenerateLearningPathForm />
        </BrowserRouter>
      );

      const topicInput = screen.getByPlaceholderText(
        /ej: procedimientos/i
      ) as HTMLInputElement;

      // Type valid topic
      await userEvent.type(topicInput, 'procedimientos de reembolsos');
      expect(topicInput.value).toBe('procedimientos de reembolsos');

      const submitButton = screen.getByText('Generar Ruta');
      // Button should be enabled when topic is 5+ characters
      expect(submitButton).not.toBeDisabled();
    });
  });
});
