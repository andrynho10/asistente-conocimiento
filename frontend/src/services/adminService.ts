/**
 * Admin Service
 *
 * API service for admin dashboard operations.
 * Handles all calls to /api/admin endpoints.
 */

import axios, { AxiosInstance } from 'axios';
import { getToken } from '@/utils/storage';

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

interface GeneratedContentResponse {
  total: number;
  items: any[];
  limit: number;
  offset: number;
}

interface QuizStatsResponse {
  quiz_id: number;
  total_attempts: number;
  avg_score_percentage: number;
  pass_rate: number;
  most_difficult_question?: any;
}

interface LearningPathStatsResponse {
  path_id: number;
  total_views: number;
  completed_count: number;
  completion_rate: number;
  most_skipped_step?: string;
}

class AdminService {
  private apiClient: AxiosInstance;

  constructor() {
    this.apiClient = axios.create({
      baseURL: '/api/admin',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add authorization header to all requests
    this.apiClient.interceptors.request.use((config) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle responses
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle common errors
        if (error.response?.status === 403) {
          throw new Error('No tienes permisos para acceder a esta sección');
        }
        if (error.response?.status === 401) {
          // Redirect to login
          window.location.href = '/login';
        }
        throw error;
      }
    );
  }

  /**
   * Get generated content with filters and pagination
   */
  async getGeneratedContent(
    filters: FilterOptions
  ): Promise<GeneratedContentResponse> {
    try {
      const params = {
        limit: filters.limit,
        offset: filters.offset,
        sort_by: filters.sort_by,
        sort_order: filters.sort_order,
        ...(filters.type && { type: filters.type }),
        ...(filters.document_id && { document_id: filters.document_id }),
        ...(filters.user_id && { user_id: filters.user_id }),
        ...(filters.date_from && { date_from: filters.date_from }),
        ...(filters.date_to && { date_to: filters.date_to }),
        ...(filters.search && { search: filters.search }),
      };

      const response = await this.apiClient.get<GeneratedContentResponse>(
        '/generated-content',
        { params }
      );

      return response.data;
    } catch (error) {
      console.error('Error fetching generated content:', error);
      throw error;
    }
  }

  /**
   * Validate or unvalidate content
   */
  async validateContent(
    contentId: number,
    isValidated: boolean
  ): Promise<any> {
    try {
      const response = await this.apiClient.put(
        `/generated-content/${contentId}/validate`,
        { is_validated: isValidated }
      );
      return response.data;
    } catch (error) {
      console.error('Error validating content:', error);
      throw error;
    }
  }

  /**
   * Delete (soft delete) content
   */
  async deleteContent(contentId: number): Promise<void> {
    try {
      await this.apiClient.delete(`/generated-content/${contentId}`);
    } catch (error) {
      console.error('Error deleting content:', error);
      throw error;
    }
  }

  /**
   * Get quiz statistics
   */
  async getQuizStats(quizId: number): Promise<QuizStatsResponse> {
    try {
      const response = await this.apiClient.get<QuizStatsResponse>(
        `/quiz/${quizId}/stats`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching quiz stats:', error);
      throw error;
    }
  }

  /**
   * Get learning path statistics
   */
  async getLearningPathStats(
    pathId: number
  ): Promise<LearningPathStatsResponse> {
    try {
      const response = await this.apiClient.get<LearningPathStatsResponse>(
        `/learning-path/${pathId}/stats`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching learning path stats:', error);
      throw error;
    }
  }

  /**
   * Export content as CSV or PDF
   */
  async exportContent(
    format: 'csv' | 'pdf',
    filters?: Partial<FilterOptions>
  ): Promise<string> {
    try {
      const params = {
        format,
        ...(filters?.type && { type: filters.type }),
        ...(filters?.document_id && { document_id: filters.document_id }),
        ...(filters?.user_id && { user_id: filters.user_id }),
      };

      const response = await this.apiClient.get('/generated-content/export', {
        params,
        responseType: 'blob',
      });

      // Create blob and download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `generated_content_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return link.download;
    } catch (error) {
      console.error('Error exporting content:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const adminService = new AdminService();
