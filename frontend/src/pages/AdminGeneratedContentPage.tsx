/**
 * Admin Generated Content Dashboard Page
 *
 * Main page for administrators to view, filter, validate, and manage
 * AI-generated content (summaries, quizzes, learning paths).
 *
 * Features:
 * - Metrics cards showing total counts
 * - Advanced filtering (type, date range, document, user, search)
 * - Paginated table with sortable columns
 * - Inline actions (view, validate, delete)
 * - Export functionality (CSV/PDF)
 * - Responsive mobile layout
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Download, Eye, Trash2, Check, X } from 'lucide-react';

// UI Components
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

// Services
import { adminService } from '@/services/adminService';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';

// Types
interface GeneratedContent {
  id: number;
  document_id: number;
  user_id: number;
  content_type: 'summary' | 'quiz' | 'learning_path';
  created_at: string;
  is_validated: boolean;
  validated_by?: number;
  validated_at?: string;
  document_name?: string;
  user_username?: string;
}

interface FilterOptions {
  type?: string;
  document_id?: number;
  user_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  limit: number;
  offset: number;
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

interface MetricsData {
  total_summaries: number;
  total_quizzes: number;
  total_learning_paths: number;
  this_week: number;
}

interface ViewModalState {
  isOpen: boolean;
  content: GeneratedContent | null;
  contentData?: any;
  stats?: any;
  statsLoading?: boolean;
}

interface DeleteConfirmState {
  isOpen: boolean;
  contentId: number | null;
  isDeleting: boolean;
}

export const AdminGeneratedContentPage: React.FC = () => {
  // Auth & Navigation
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const { toast } = useToast();

  // Page State
  const [isLoading, setIsLoading] = useState(true);
  const [contents, setContents] = useState<GeneratedContent[]>([]);
  const [total, setTotal] = useState(0);

  // Metrics
  const [metrics, setMetrics] = useState<MetricsData>({
    total_summaries: 0,
    total_quizzes: 0,
    total_learning_paths: 0,
    this_week: 0,
  });

  // Filters
  const [filters, setFilters] = useState<FilterOptions>({
    type: undefined,
    document_id: undefined,
    user_id: undefined,
    date_from: undefined,
    date_to: undefined,
    search: undefined,
    limit: 20,
    offset: 0,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  // Modals
  const [viewModal, setViewModal] = useState<ViewModalState>({
    isOpen: false,
    content: null,
  });

  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
    isOpen: false,
    contentId: null,
    isDeleting: false,
  });

  // Authorization Check
  useEffect(() => {
    if (!authLoading && (!user || user.role !== 'admin')) {
      navigate('/403');
    }
  }, [user, authLoading, navigate]);

  // Load content with current filters
  const loadContent = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await adminService.getGeneratedContent(filters);
      setContents(response.items);
      setTotal(response.total);

      // Calculate metrics
      const summaries = response.items.filter(
        (c) => c.content_type === 'summary'
      ).length;
      const quizzes = response.items.filter(
        (c) => c.content_type === 'quiz'
      ).length;
      const paths = response.items.filter(
        (c) => c.content_type === 'learning_path'
      ).length;

      // Calculate this week count
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      const thisWeek = response.items.filter((c) => {
        const created = new Date(c.created_at);
        return created >= weekAgo;
      }).length;

      setMetrics({
        total_summaries: summaries,
        total_quizzes: quizzes,
        total_learning_paths: paths,
        this_week: thisWeek,
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load generated content',
      });
    } finally {
      setIsLoading(false);
    }
  }, [filters, toast]);

  // Load content on mount and when filters change
  useEffect(() => {
    if (user?.role === 'admin') {
      loadContent();
    }
  }, [filters, user, loadContent]);

  // Handle filter changes
  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      offset: 0, // Reset to first page when filters change
    }));
  };

  // Handle search with debounce
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);
  const handleSearch = (value: string) => {
    if (searchTimer) clearTimeout(searchTimer);
    const timer = setTimeout(() => {
      handleFilterChange('search', value || undefined);
    }, 300);
    setSearchTimer(timer);
  };

  // Handle pagination
  const handlePageChange = (direction: 'prev' | 'next') => {
    setFilters((prev) => ({
      ...prev,
      offset:
        direction === 'next'
          ? prev.offset + prev.limit
          : Math.max(0, prev.offset - prev.limit),
    }));
  };

  // Handle sorting
  const handleSort = (column: string) => {
    setFilters((prev) => ({
      ...prev,
      sort_by: column,
      sort_order: prev.sort_order === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Handle view content
  const handleView = async (content: GeneratedContent) => {
    setViewModal({
      isOpen: true,
      content,
      contentData: null,
      stats: null,
      statsLoading: true,
    });

    // Load stats if content is quiz or learning path
    try {
      let stats = null;
      if (content.content_type === 'quiz') {
        stats = await adminService.getQuizStats(content.id);
      } else if (content.content_type === 'learning_path') {
        stats = await adminService.getLearningPathStats(content.id);
      }

      setViewModal((prev) => ({
        ...prev,
        stats,
        statsLoading: false,
      }));
    } catch (error) {
      console.error('Error loading stats:', error);
      setViewModal((prev) => ({
        ...prev,
        statsLoading: false,
      }));
    }
  };

  // Handle validate content
  const handleValidate = async (contentId: number, isValidated: boolean) => {
    try {
      await adminService.validateContent(contentId, !isValidated);
      toast({
        title: 'Success',
        description: `Content marked as ${!isValidated ? 'validated' : 'unvalidated'}`,
      });
      loadContent();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to validate content',
      });
    }
  };

  // Handle delete content
  const handleDeleteConfirm = (contentId: number) => {
    setDeleteConfirm({
      isOpen: true,
      contentId,
      isDeleting: false,
    });
  };

  const handleDeleteExecute = async () => {
    if (!deleteConfirm.contentId) return;

    try {
      setDeleteConfirm((prev) => ({ ...prev, isDeleting: true }));
      await adminService.deleteContent(deleteConfirm.contentId);
      toast({
        title: 'Success',
        description: 'Content deleted successfully',
      });
      setDeleteConfirm({ isOpen: false, contentId: null, isDeleting: false });
      loadContent();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete content',
      });
      setDeleteConfirm((prev) => ({ ...prev, isDeleting: false }));
    }
  };

  // Handle export
  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const filename = await adminService.exportContent(format, filters);
      toast({
        title: 'Success',
        description: `Content exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to export as ${format.toUpperCase()}`,
      });
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get content type badge color
  const getTypeBadgeVariant = (type: string) => {
    switch (type) {
      case 'summary':
        return 'bg-blue-100 text-blue-800';
      case 'quiz':
        return 'bg-purple-100 text-purple-800';
      case 'learning_path':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // If not authorized, component won't render due to navigate
  if (authLoading || !user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.ceil(total / filters.limit);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Contenido Generado por IA
        </h1>
        <p className="text-gray-600 mt-1">
          Monitorea y gestiona todo el contenido generado automáticamente
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          title="Total Resúmenes"
          value={metrics.total_summaries}
          icon="📄"
          color="blue"
        />
        <MetricCard
          title="Total Quizzes"
          value={metrics.total_quizzes}
          icon="❓"
          color="purple"
        />
        <MetricCard
          title="Total Rutas"
          value={metrics.total_learning_paths}
          icon="🗺️"
          color="green"
        />
        <MetricCard
          title="Esta Semana"
          value={metrics.this_week}
          icon="📅"
          color="orange"
        />
      </div>

      {/* Filters */}
      <Card className="p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Filtros</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Contenido
            </label>
            <Select
              value={filters.type || ''}
              onValueChange={(value) =>
                handleFilterChange('type', value || undefined)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todos</SelectItem>
                <SelectItem value="summary">Resúmenes</SelectItem>
                <SelectItem value="quiz">Quizzes</SelectItem>
                <SelectItem value="learning_path">Rutas de Aprendizaje</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Date From Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Desde
            </label>
            <Input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) =>
                handleFilterChange('date_from', e.target.value || undefined)
              }
            />
          </div>

          {/* Date To Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Hasta
            </label>
            <Input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) =>
                handleFilterChange('date_to', e.target.value || undefined)
              }
            />
          </div>

          {/* Search Filter */}
          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Búsqueda (ID, Documento, Usuario)
            </label>
            <Input
              placeholder="Buscar..."
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full"
            />
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            className="gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
            className="gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar PDF
          </Button>
        </div>
      </Card>

      {/* Content Table */}
      <Card className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : contents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <AlertCircle className="w-12 h-12 mb-4 opacity-50" />
            <p>No hay contenido para mostrar</p>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('id')}
                    >
                      ID {filters.sort_by === 'id' && (filters.sort_order === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Documento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('created_at')}
                    >
                      Fecha {filters.sort_by === 'created_at' && (filters.sort_order === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {contents.map((content) => (
                    <tr key={content.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{content.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge className={getTypeBadgeVariant(content.content_type)}>
                          {content.content_type === 'summary'
                            ? 'Resumen'
                            : content.content_type === 'quiz'
                            ? 'Quiz'
                            : 'Ruta'}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                        {content.document_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {content.user_username || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                        {formatDate(content.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {content.is_validated ? (
                          <Badge variant="default" className="bg-green-600">
                            ✓ Validado
                          </Badge>
                        ) : (
                          <Badge variant="outline">Pendiente</Badge>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <button
                          onClick={() => handleView(content)}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg hover:bg-blue-50 text-blue-600"
                          title="Ver"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() =>
                            handleValidate(content.id, content.is_validated)
                          }
                          className={`inline-flex items-center justify-center w-8 h-8 rounded-lg ${
                            content.is_validated
                              ? 'hover:bg-red-50 text-red-600'
                              : 'hover:bg-green-50 text-green-600'
                          }`}
                          title={
                            content.is_validated
                              ? 'Desmarcar validado'
                              : 'Marcar validado'
                          }
                        >
                          {content.is_validated ? (
                            <X className="w-4 h-4" />
                          ) : (
                            <Check className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDeleteConfirm(content.id)}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-lg hover:bg-red-50 text-red-600"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Mostrando {filters.offset + 1} a{' '}
                {Math.min(filters.offset + filters.limit, total)} de {total}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange('prev')}
                  disabled={filters.offset === 0}
                >
                  Anterior
                </Button>
                <div className="flex items-center px-3 py-1 bg-gray-100 rounded">
                  {currentPage} / {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange('next')}
                  disabled={
                    filters.offset + filters.limit >= total
                  }
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* View Modal */}
      <Dialog open={viewModal.isOpen} onOpenChange={(open) => {
        if (!open) setViewModal({ isOpen: false, content: null });
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Ver Contenido</DialogTitle>
            {viewModal.content && (
              <DialogDescription>
                ID: {viewModal.content.id} | Tipo:{' '}
                {viewModal.content.content_type}
              </DialogDescription>
            )}
          </DialogHeader>

          {viewModal.content && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Documento</p>
                  <p className="font-medium">
                    {viewModal.content.document_name || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Usuario</p>
                  <p className="font-medium">
                    {viewModal.content.user_username || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Fecha</p>
                  <p className="font-medium">
                    {formatDate(viewModal.content.created_at)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Estado</p>
                  <p className="font-medium">
                    {viewModal.content.is_validated
                      ? '✓ Validado'
                      : 'Pendiente'}
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
                <p className="text-sm text-gray-600 mb-2">Contenido:</p>
                <pre className="text-xs whitespace-pre-wrap">
                  {viewModal.contentData
                    ? JSON.stringify(viewModal.contentData, null, 2)
                    : 'Contenido no disponible'}
                </pre>
              </div>

              {/* Stats Section for Quiz and Learning Path */}
              {(viewModal.content.content_type === 'quiz' ||
                viewModal.content.content_type === 'learning_path') && (
                <div className="border-t pt-4 mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-3">
                    Estadísticas
                  </p>
                  {viewModal.statsLoading ? (
                    <div className="flex items-center justify-center h-20">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    </div>
                  ) : viewModal.stats ? (
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {viewModal.content.content_type === 'quiz' ? (
                        <>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Intentos Totales</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.total_attempts || 0}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Score Promedio</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.avg_score_percentage?.toFixed(1) ||
                                '0.0'}
                              %
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Tasa de Aprobación</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.pass_rate?.toFixed(1) || '0.0'}%
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Pregunta Difícil</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.most_difficult_question || 'N/A'}
                            </p>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Visualizaciones</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.total_views || 0}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Completados</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.completed_count || 0}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Tasa Completación</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.completion_rate?.toFixed(1) || '0.0'}
                              %
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-gray-600">Paso Saltado Más</p>
                            <p className="text-lg font-bold">
                              {viewModal.stats.most_skipped_step || 'N/A'}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">
                      No hay estadísticas disponibles
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setViewModal({ isOpen: false, content: null })}
            >
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteConfirm.isOpen}
        onOpenChange={(open) => {
          if (!open)
            setDeleteConfirm({ isOpen: false, contentId: null, isDeleting: false });
        }}
      >
        <AlertDialogContent>
          <AlertDialogTitle>Eliminar Contenido</AlertDialogTitle>
          <AlertDialogDescription>
            ¿Estás seguro de que deseas eliminar este contenido? No se puede
            deshacer esta acción.
          </AlertDialogDescription>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteExecute}
              disabled={deleteConfirm.isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleteConfirm.isDeleting ? 'Eliminando...' : 'Eliminar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

/**
 * Metric Card Component
 */
interface MetricCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    purple: 'bg-purple-50 border-purple-200',
    green: 'bg-green-50 border-green-200',
    orange: 'bg-orange-50 border-orange-200',
  };

  return (
    <Card className={`p-6 border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </Card>
  );
};
