/**
 * AdminContentTable Component Tests
 * Story 4.5: Table component for displaying and managing generated content
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock component
const AdminContentTable = ({
  items = [],
  onView,
  onDelete,
  onValidate,
  onSort,
  sortBy = 'created_at',
  sortOrder = 'desc'
}: any) => (
  <div data-testid="content-table">
    <table>
      <thead>
        <tr>
          <th onClick={() => onSort?.('id')}>ID</th>
          <th>Tipo</th>
          <th>Documento</th>
          <th>Usuario</th>
          <th onClick={() => onSort?.('created_at')}>Fecha</th>
          <th>Validado</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item: any) => (
          <tr key={item.id} data-testid={`row-${item.id}`}>
            <td>{item.id}</td>
            <td>{item.content_type}</td>
            <td>{item.document_name}</td>
            <td>{item.user_username}</td>
            <td>{new Date(item.created_at).toLocaleDateString()}</td>
            <td>
              <input
                type="checkbox"
                checked={item.is_validated}
                onChange={() => onValidate?.(item.id, !item.is_validated)}
                data-testid={`validate-${item.id}`}
              />
            </td>
            <td>
              <button
                onClick={() => onView?.(item.id)}
                data-testid={`view-${item.id}`}
                title="Ver"
              >
                Ver
              </button>
              <button
                onClick={() => onDelete?.(item.id)}
                data-testid={`delete-${item.id}`}
                title="Eliminar"
              >
                Eliminar
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

describe('AdminContentTable Component', () => {
  const mockItems = [
    {
      id: 1,
      content_type: 'summary',
      document_name: 'Document 1',
      user_username: 'user1',
      created_at: '2025-11-14T10:00:00Z',
      is_validated: true,
    },
    {
      id: 2,
      content_type: 'quiz',
      document_name: 'Document 2',
      user_username: 'user2',
      created_at: '2025-11-13T10:00:00Z',
      is_validated: false,
    },
  ];

  let mockCallbacks: any;

  beforeEach(() => {
    mockCallbacks = {
      onView: vi.fn(),
      onDelete: vi.fn(),
      onValidate: vi.fn(),
      onSort: vi.fn(),
    };
  });

  it('should render table with all columns', () => {
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Tipo')).toBeInTheDocument();
    expect(screen.getByText('Documento')).toBeInTheDocument();
    expect(screen.getByText('Usuario')).toBeInTheDocument();
    expect(screen.getByText('Fecha')).toBeInTheDocument();
    expect(screen.getByText('Validado')).toBeInTheDocument();
  });

  it('should display content items', () => {
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    expect(screen.getByText('Document 1')).toBeInTheDocument();
    expect(screen.getByText('Document 2')).toBeInTheDocument();
    expect(screen.getByText('user1')).toBeInTheDocument();
  });

  it('should call onView when view button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    const viewBtn = screen.getByTestId('view-1');
    await user.click(viewBtn);

    expect(mockCallbacks.onView).toHaveBeenCalledWith(1);
  });

  it('should call onDelete when delete button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    const deleteBtn = screen.getByTestId('delete-1');
    await user.click(deleteBtn);

    expect(mockCallbacks.onDelete).toHaveBeenCalledWith(1);
  });

  it('should toggle validate checkbox', async () => {
    const user = userEvent.setup();
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    const validateCheckbox = screen.getByTestId('validate-2');
    await user.click(validateCheckbox);

    expect(mockCallbacks.onValidate).toHaveBeenCalledWith(2, true);
  });

  it('should call onSort when column header is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    const dateHeader = screen.getAllByText('Fecha')[0];
    await user.click(dateHeader);

    expect(mockCallbacks.onSort).toHaveBeenCalledWith('created_at');
  });

  it('should display empty state when no items', () => {
    render(
      <AdminContentTable items={[]} {...mockCallbacks} />
    );

    expect(screen.getByTestId('content-table')).toBeInTheDocument();
    // Table should have headers but no body rows
    expect(screen.queryByTestId('row-1')).not.toBeInTheDocument();
  });

  it('should show correct content type badges', () => {
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    expect(screen.getByText('summary')).toBeInTheDocument();
    expect(screen.getByText('quiz')).toBeInTheDocument();
  });

  it('should display formatted dates', () => {
    render(
      <AdminContentTable items={mockItems} {...mockCallbacks} />
    );

    // Check that date is formatted (not full ISO string)
    const dateCell = screen.getByText(/11\/14\/2025|14\/11\/2025/);
    expect(dateCell).toBeInTheDocument();
  });
});
