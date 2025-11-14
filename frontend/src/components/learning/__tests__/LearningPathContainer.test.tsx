/**
 * LearningPathContainer Tests
 * Story 4.4: Component tests for learning path visualization and progress tracking
 * Tests AC13-AC17: Visualization, interaction, and progress persistence
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LearningPathContainer } from '../LearningPathContainer';
import { LearningPath } from '../../../types/learning';

// Mock localStorage
const localStorageMock = (() => {
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
  value: localStorageMock,
});

// Mock fetch
global.fetch = vi.fn();

const mockLearningPath: LearningPath = {
  id: 1,
  user_id: 1,
  topic: 'Procedimientos de Reembolsos',
  user_level: 'beginner',
  title: 'Ruta de Aprendizaje: Reembolsos',
  steps: [
    {
      step_number: 1,
      title: 'Conceptos Básicos',
      document_id: 1,
      why_this_step: 'Fundamentos esenciales',
      estimated_time_minutes: 15,
    },
    {
      step_number: 2,
      title: 'Procedimientos',
      document_id: 2,
      why_this_step: 'Aplicación práctica',
      estimated_time_minutes: 25,
    },
    {
      step_number: 3,
      title: 'Casos Avanzados',
      document_id: 3,
      why_this_step: 'Situaciones complejas',
      estimated_time_minutes: 30,
    },
  ],
  estimated_time_hours: (15 + 25 + 30) / 60,
  content_json: '{}',
  created_at: '2025-11-14T12:00:00Z',
};

describe('LearningPathContainer (Story 4.4)', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
    localStorage.setItem('auth_token', 'test-token');
  });

  // AC13: Display learning path
  describe('AC13: Display Learning Path', () => {
    it('should load and display learning path data', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockLearningPath.title)).toBeInTheDocument();
      });

      expect(screen.getByText(`Tema: ${mockLearningPath.topic}`)).toBeInTheDocument();
    });

    it('should display error message if path not found', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      });

      render(
        <LearningPathContainer pathId={999} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });
    });

    it('should handle network errors gracefully', async () => {
      (global.fetch as any).mockRejectedValueOnce(
        new Error('Network error')
      );

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });
    });
  });

  // AC14: Display roadmap with visual progress indicators
  describe('AC14: Roadmap Visualization', () => {
    it('should display all steps in timeline', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        mockLearningPath.steps.forEach(step => {
          expect(screen.getByText(step.title)).toBeInTheDocument();
        });
      });
    });

    it('should display step numbers and metadata', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText('15 minutos')).toBeInTheDocument();
        expect(screen.getByText('25 minutos')).toBeInTheDocument();
        expect(screen.getByText('30 minutos')).toBeInTheDocument();
      });
    });
  });

  // AC15: Click on step to navigate
  describe('AC15: Step Interactivity', () => {
    it('should have clickable step cards', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        const buttons = screen.getAllByText(/Ver Documento →/i);
        expect(buttons.length).toBeGreaterThan(0);
      });
    });
  });

  // AC16: Progress tracking with localStorage
  describe('AC16: Progress Tracking and Persistence', () => {
    it('should save progress to localStorage when checkbox toggled', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      const { container } = render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockLearningPath.title)).toBeInTheDocument();
      });

      // Find and click first checkbox
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes.length).toBeGreaterThan(0);

      fireEvent.click(checkboxes[0]);

      // Check localStorage was updated
      const saved = localStorage.getItem(`learning_path_1_progress`);
      expect(saved).toBeTruthy();

      const progress = JSON.parse(saved!);
      expect(progress.completed[0]).toBe(true);
    });

    it('should recover progress from localStorage on load', async () => {
      const savedProgress = {
        pathId: '1',
        completed: [true, false, true],
        completedCount: 2,
        lastUpdated: Date.now(),
      };

      localStorage.setItem(
        `learning_path_1_progress`,
        JSON.stringify(savedProgress)
      );

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      const { container } = render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockLearningPath.title)).toBeInTheDocument();
      });

      // Verify checkboxes reflect saved state
      const checkboxes = container.querySelectorAll(
        'input[type="checkbox"]'
      ) as NodeListOf<HTMLInputElement>;

      expect(checkboxes[0].checked).toBe(true);
      expect(checkboxes[1].checked).toBe(false);
      expect(checkboxes[2].checked).toBe(true);
    });

    it('should update progress count dynamically', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      const { container } = render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockLearningPath.title)).toBeInTheDocument();
      });

      // Verify initial progress shows 0/3
      expect(screen.getByText('0 de 3 completados')).toBeInTheDocument();
      expect(screen.getByText('0% completado')).toBeInTheDocument();

      // Mark first step as complete
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      fireEvent.click(checkboxes[0]);

      // Verify updated progress
      await waitFor(() => {
        expect(screen.getByText('1 de 3 completados')).toBeInTheDocument();
      });
    });
  });

  // AC17: Calculate total estimated time
  describe('AC17: Time Estimation', () => {
    it('should calculate and display total estimated time', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={vi.fn()} />
      );

      await waitFor(() => {
        const totalMinutes = mockLearningPath.steps.reduce(
          (sum, step) => sum + step.estimated_time_minutes,
          0
        );
        const hours = (totalMinutes / 60).toFixed(1);
        expect(
          screen.getByText(new RegExp(`${hours} horas`))
        ).toBeInTheDocument();
      });
    });
  });

  // Back button functionality
  describe('Navigation', () => {
    it('should call onBackClick when back button clicked', async () => {
      const onBackClick = vi.fn();

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockLearningPath,
      });

      render(
        <LearningPathContainer pathId={1} onBackClick={onBackClick} />
      );

      await waitFor(() => {
        expect(screen.getByText(mockLearningPath.title)).toBeInTheDocument();
      });

      const backButton = screen.getByText('← Volver');
      fireEvent.click(backButton);

      expect(onBackClick).toHaveBeenCalled();
    });
  });
});
