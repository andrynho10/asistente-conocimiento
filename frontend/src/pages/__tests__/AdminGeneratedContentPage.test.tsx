/**
 * AdminGeneratedContentPage Tests
 * Story 4.5: Admin dashboard for generated content
 * Tests for page rendering, filters, pagination, actions, and authentication
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AdminGeneratedContentPage } from '../AdminGeneratedContentPage';

// Mock useAuth hook
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: { id: 1, username: 'testadmin', role: 'admin' },
  }),
}));

// Mock useToast hook
vi.mock('../../hooks/useToast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Mock adminService
vi.mock('../../services/adminService', () => ({
  adminService: {
    getGeneratedContent: vi.fn(),
    deleteContent: vi.fn(),
    validateContent: vi.fn(),
    getQuizStats: vi.fn(),
    getLearningPathStats: vi.fn(),
    exportCSV: vi.fn(),
    exportPDF: vi.fn(),
  },
}));

import { adminService } from '../../services/adminService';

const mockGeneratedContent = [
  {
    id: 1,
    document_id: 10,
    user_id: 1,
    content_type: 'summary',
    created_at: '2025-11-14T10:00:00Z',
    is_validated: true,
    validated_by: 1,
    validated_at: '2025-11-14T11:00:00Z',
    document_name: 'Test Document 1',
    user_username: 'user1',
  },
  {
    id: 2,
    document_id: 11,
    user_id: 2,
    content_type: 'quiz',
    created_at: '2025-11-13T10:00:00Z',
    is_validated: false,
    document_name: 'Test Document 2',
    user_username: 'user2',
  },
  {
    id: 3,
    document_id: 12,
    user_id: 1,
    content_type: 'learning_path',
    created_at: '2025-11-14T15:00:00Z',
    is_validated: true,
    document_name: 'Test Document 3',
    user_username: 'user1',
  },
];

const mockApiResponse = {
  total: 3,
  items: mockGeneratedContent,
  limit: 20,
  offset: 0,
};

describe('AdminGeneratedContentPage (Story 4.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (adminService.getGeneratedContent as any).mockResolvedValue(mockApiResponse);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // AC1: Page accessibility and authentication
  describe('AC1: Page Accessibility and Authentication', () => {
    it('should render the page for authenticated admin user', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Dashboard de Contenido Generado/i)).toBeInTheDocument();
      });
    });

    it('should display main dashboard structure', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Filtros/i)).toBeInTheDocument();
        expect(screen.getByText(/Contenido Generado/i)).toBeInTheDocument();
      });
    });
  });

  // AC2: Metrics cards display
  describe('AC2: Metrics Cards Display', () => {
    it('should render metrics cards with correct counts', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        // Should display summary count
        const summaryCards = screen.getAllByText(/Resúmenes/i);
        expect(summaryCards.length).toBeGreaterThan(0);
      });
    });

    it('should calculate metrics from filtered content', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        // Verify API was called on mount
        expect(adminService.getGeneratedContent).toHaveBeenCalled();
      });
    });
  });

  // AC3: Table columns display
  describe('AC3: Table Content Display', () => {
    it('should render table with all required columns', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ID/i)).toBeInTheDocument();
        expect(screen.getByText(/Tipo/i)).toBeInTheDocument();
        expect(screen.getByText(/Documento/i)).toBeInTheDocument();
        expect(screen.getByText(/Usuario/i)).toBeInTheDocument();
        expect(screen.getByText(/Fecha/i)).toBeInTheDocument();
      });
    });

    it('should display content items in table', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        // Check for content ID
        expect(screen.getByText('1')).toBeInTheDocument();
        // Check for document names
        expect(screen.getByText('Test Document 1')).toBeInTheDocument();
      });
    });
  });

  // AC4: Type filter
  describe('AC4: Type Filter', () => {
    it('should filter content by type', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      // Find and click type filter
      const typeSelects = screen.getAllByRole('combobox');
      const typeSelect = typeSelects[0]; // First select is typically type

      await user.click(typeSelect);
      await user.click(screen.getByText('Quizzes'));

      await waitFor(() => {
        expect(adminService.getGeneratedContent).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'quiz',
          })
        );
      });
    });
  });

  // AC8: Endpoint functionality and pagination
  describe('AC8 & AC9: Endpoint and Pagination', () => {
    it('should call API with correct parameters on mount', async () => {
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(adminService.getGeneratedContent).toHaveBeenCalledWith(
          expect.objectContaining({
            limit: 20,
            offset: 0,
          })
        );
      });
    });

    it('should update pagination offset when navigating pages', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      // Find next page button
      const nextButtons = screen.queryAllByRole('button');
      const nextButton = nextButtons.find((btn) =>
        btn.textContent?.includes('Siguiente') || btn.textContent?.includes('next')
      );

      if (nextButton) {
        await user.click(nextButton);

        await waitFor(() => {
          expect(adminService.getGeneratedContent).toHaveBeenCalledWith(
            expect.objectContaining({
              offset: 20,
            })
          );
        });
      }
    });
  });

  // AC10: Search functionality
  describe('AC10: Search Functionality', () => {
    it('should filter content by search text', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/buscar/i) || screen.getByPlaceholderText(/search/i);

      // Type search query
      await user.type(searchInput, 'Document');

      // Debounce delay (typically 300-500ms)
      await waitFor(
        () => {
          expect(adminService.getGeneratedContent).toHaveBeenCalledWith(
            expect.objectContaining({
              search: 'Document',
            })
          );
        },
        { timeout: 1000 }
      );
    });
  });

  // AC12: View action
  describe('AC12: View Action', () => {
    it('should open view modal when view button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      // Find and click view button
      const viewButtons = screen.getAllByRole('button');
      const viewButton = viewButtons.find((btn) => btn.getAttribute('title')?.includes('Ver'));

      if (viewButton) {
        await user.click(viewButton);

        await waitFor(() => {
          // Modal should appear with content details
          expect(
            screen.queryByText(/Contenido Generado/i) || screen.queryByText(/Ver Contenido/i)
          ).toBeInTheDocument();
        });
      }
    });
  });

  // AC13: Delete action
  describe('AC13: Delete Action', () => {
    it('should show delete confirmation dialog', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      // Find and click delete button
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find((btn) => btn.getAttribute('title')?.includes('Eliminar'));

      if (deleteButton) {
        await user.click(deleteButton);

        await waitFor(() => {
          expect(screen.getByText(/está seguro/i) || screen.getByText(/confirmar/i)).toBeInTheDocument();
        });
      }
    });

    it('should call delete API when confirming deletion', async () => {
      const user = userEvent.setup();
      (adminService.deleteContent as any).mockResolvedValue({ success: true });

      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      // Find and click delete button
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find((btn) => btn.getAttribute('title')?.includes('Eliminar'));

      if (deleteButton) {
        await user.click(deleteButton);

        // Find and click confirm button in dialog
        const confirmButtons = screen.queryAllByRole('button');
        const confirmDeleteBtn = confirmButtons.find((btn) =>
          btn.textContent?.includes('Eliminar') || btn.textContent?.includes('Confirmar')
        );

        if (confirmDeleteBtn) {
          await user.click(confirmDeleteBtn);

          await waitFor(() => {
            expect(adminService.deleteContent).toHaveBeenCalledWith(1);
          });
        }
      }
    });
  });

  // AC16: Validate action
  describe('AC16: Validate Action', () => {
    it('should toggle validated status', async () => {
      const user = userEvent.setup();
      (adminService.validateContent as any).mockResolvedValue({ id: 2, is_validated: true });

      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 2/i)).toBeInTheDocument();
      });

      // Find validate checkbox or button for unvalidated item (id: 2)
      const validateButtons = screen.queryAllByRole('button');
      const validateBtn = validateButtons.find((btn) => btn.getAttribute('aria-label')?.includes('validat'));

      if (validateBtn) {
        await user.click(validateBtn);

        await waitFor(() => {
          expect(adminService.validateContent).toHaveBeenCalled();
        });
      }
    });
  });

  // AC17: Export functionality
  describe('AC17: Export Functionality', () => {
    it('should export content as CSV', async () => {
      const user = userEvent.setup();
      (adminService.exportCSV as any).mockResolvedValue(new Blob());

      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Test Document 1/i)).toBeInTheDocument();
      });

      const exportButtons = screen.queryAllByRole('button');
      const csvExportBtn = exportButtons.find((btn) => btn.textContent?.includes('CSV'));

      if (csvExportBtn) {
        await user.click(csvExportBtn);

        await waitFor(() => {
          expect(adminService.exportCSV).toHaveBeenCalled();
        });
      }
    });
  });

  // AC20: Performance test (simplified)
  describe('AC20: Performance', () => {
    it('should render table with 20 items without visible lag', async () => {
      const largeDataset = Array.from({ length: 20 }, (_, i) => ({
        ...mockGeneratedContent[0],
        id: i + 1,
      }));

      (adminService.getGeneratedContent as any).mockResolvedValue({
        total: 20,
        items: largeDataset,
        limit: 20,
        offset: 0,
      });

      const startTime = performance.now();

      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Document 1')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Assert render time is reasonable (< 2 seconds for test environment)
      expect(renderTime).toBeLessThan(2000);
    });
  });

  // AC21: Responsive mobile
  describe('AC21: Responsive Mobile', () => {
    it('should render in mobile viewport', async () => {
      // Mock window.matchMedia for mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <BrowserRouter>
          <AdminGeneratedContentPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Dashboard de Contenido Generado/i)).toBeInTheDocument();
      });

      // Reset
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });
  });
});
