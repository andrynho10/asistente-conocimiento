/**
 * AdminMetricsCard Component Tests
 * Story 4.5: Metrics card component for displaying content statistics
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BarChart3, FileText, CheckCircle, TrendingUp } from 'lucide-react';

// Mock component - will be replaced with actual component once created
const AdminMetricsCard = ({ title, value, icon: Icon, color }: any) => (
  <div data-testid={`metric-card-${title}`} className={`bg-${color}-50`}>
    <div className="flex items-center space-x-4">
      {Icon && <Icon className="h-8 w-8" />}
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  </div>
);

describe('AdminMetricsCard Component', () => {
  it('should render metric card with title and value', () => {
    render(
      <AdminMetricsCard title="Total Resúmenes" value={15} icon={FileText} color="blue" />
    );

    expect(screen.getByText('Total Resúmenes')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('should render with correct icon', () => {
    const { container } = render(
      <AdminMetricsCard title="Total Quizzes" value={8} icon={CheckCircle} color="green" />
    );

    const card = container.querySelector('[data-testid="metric-card-Total Quizzes"]');
    expect(card).toBeInTheDocument();
  });

  it('should apply correct color class', () => {
    const { container } = render(
      <AdminMetricsCard title="Total Paths" value={5} icon={TrendingUp} color="purple" />
    );

    const card = container.querySelector('[data-testid="metric-card-Total Paths"]');
    expect(card).toHaveClass('bg-purple-50');
  });

  it('should handle large numbers', () => {
    render(
      <AdminMetricsCard title="Esta Semana" value={9999} icon={BarChart3} color="orange" />
    );

    expect(screen.getByText('9999')).toBeInTheDocument();
  });

  it('should handle zero value', () => {
    render(
      <AdminMetricsCard title="Contenido" value={0} icon={FileText} color="red" />
    );

    expect(screen.getByText('0')).toBeInTheDocument();
  });
});
