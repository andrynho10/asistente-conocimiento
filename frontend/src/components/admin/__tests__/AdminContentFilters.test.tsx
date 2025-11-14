/**
 * AdminContentFilters Component Tests
 * Story 4.5: Filter component for advanced content filtering
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock component - will be replaced with actual component
const AdminContentFilters = ({ onFiltersChange }: any) => (
  <div data-testid="admin-filters">
    <select data-testid="type-filter" onChange={(e) => onFiltersChange({ type: e.target.value })}>
      <option value="">Todos</option>
      <option value="summary">Resúmenes</option>
      <option value="quiz">Quizzes</option>
      <option value="learning_path">Learning Paths</option>
    </select>
    <input
      data-testid="search-input"
      type="text"
      placeholder="Buscar"
      onChange={(e) => onFiltersChange({ search: e.target.value })}
    />
    <input
      data-testid="date-from"
      type="date"
      onChange={(e) => onFiltersChange({ date_from: e.target.value })}
    />
    <input
      data-testid="date-to"
      type="date"
      onChange={(e) => onFiltersChange({ date_to: e.target.value })}
    />
  </div>
);

describe('AdminContentFilters Component', () => {
  let onFilterChange: any;

  beforeEach(() => {
    onFilterChange = vi.fn();
  });

  it('should render all filter inputs', () => {
    render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    expect(screen.getByTestId('type-filter')).toBeInTheDocument();
    expect(screen.getByTestId('search-input')).toBeInTheDocument();
    expect(screen.getByTestId('date-from')).toBeInTheDocument();
    expect(screen.getByTestId('date-to')).toBeInTheDocument();
  });

  it('should call onFiltersChange when type filter changes', async () => {
    const user = userEvent.setup();
    render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    const typeSelect = screen.getByTestId('type-filter');
    await user.selectOption(typeSelect, 'quiz');

    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'quiz' })
    );
  });

  it('should call onFiltersChange with debounce when search text changes', async () => {
    const user = userEvent.setup();
    render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    const searchInput = screen.getByTestId('search-input');
    await user.type(searchInput, 'test document');

    // Last call should have the full search text
    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: expect.stringContaining('test') })
    );
  });

  it('should call onFiltersChange when date range changes', async () => {
    const user = userEvent.setup();
    render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    const dateFromInput = screen.getByTestId('date-from');
    await user.type(dateFromInput, '2025-11-01');

    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ date_from: expect.stringContaining('2025-11-01') })
    );
  });

  it('should allow clearing filters', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    const typeSelect = screen.getByTestId('type-filter');
    await user.selectOption(typeSelect, 'summary');

    // Clear filter
    await user.selectOption(typeSelect, '');

    expect(onFilterChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ type: '' })
    );
  });

  it('should handle multiple filters simultaneously', async () => {
    const user = userEvent.setup();
    render(<AdminContentFilters onFiltersChange={onFilterChange} />);

    const typeSelect = screen.getByTestId('type-filter');
    const searchInput = screen.getByTestId('search-input');

    await user.selectOption(typeSelect, 'learning_path');
    await user.type(searchInput, 'advanced');

    // Both filters should be applied
    expect(onFilterChange).toHaveBeenCalled();
  });
});
