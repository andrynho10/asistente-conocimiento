import axios, { AxiosError, AxiosInstance } from 'axios';
import { getToken } from '@/utils/storage';

// Configurar base URL del backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Respuesta del API de consulta a IA
 */
export interface QueryResponse {
  query: string;
  answer: string;
  sources: Array<{
    document_id: number;
    title: string;
    relevance_score: number;
  }>;
  response_time_ms: number;
}

/**
 * Error response from API
 */
interface ApiErrorResponse {
  error?: {
    message?: string;
  };
  detail?: string;
}

/**
 * Crear instancia de axios con autenticación JWT
 */
export const createIaApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Interceptor para agregar JWT token a todas las request
  client.interceptors.request.use(
    (config) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  return client;
};

const iaClient = createIaApiClient();

/**
 * Envía una consulta al servicio de IA
 * @param query - Texto de la pregunta (10-500 caracteres)
 * @param contextMode - Modo de contexto: 'documents' o 'search'
 * @param topK - Número de documentos de contexto (default: 3)
 * @returns Respuesta con answer y sources
 * @throws Error con mensaje específico según código HTTP
 */
export const queryAI = async (
  query: string,
  contextMode: 'documents' | 'search' = 'documents',
  topK: number = 3
): Promise<QueryResponse> => {
  try {
    const response = await iaClient.post<QueryResponse>('/api/ia/query', {
      query,
      context_mode: contextMode,
      top_k: topK,
      temperature: 0.7,
      max_tokens: 500,
    });

    return response.data;
  } catch (error) {
    // Manejar errores específicos por código HTTP
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiErrorResponse>;
      const status = axiosError.response?.status;
      const errorData = axiosError.response?.data;

      // Mensaje de error por defecto
      let errorMessage = 'Error al procesar tu consulta. Intenta nuevamente.';

      // Manejar códigos de error específicos
      if (status === 400) {
        // Validación
        errorMessage =
          errorData?.error?.message ||
          errorData?.detail ||
          'Formato de consulta inválido. Asegúrate de tener entre 10 y 500 caracteres.';
      } else if (status === 401) {
        // Unauthorized
        errorMessage = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
      } else if (status === 429) {
        // Rate limit
        errorMessage =
          '🚫 Has realizado muchas consultas. Espera un momento antes de continuar.';
      } else if (status === 503) {
        // Service unavailable
        errorMessage =
          '⚠️ El servicio de IA está temporalmente no disponible. Intenta en unos minutos.';
      } else if (status === 504) {
        // Gateway timeout
        errorMessage =
          '⏱️ La consulta tardó demasiado. Intenta con una pregunta más específica.';
      } else if (status === 500) {
        // Server error
        errorMessage =
          'Error interno del servidor. Por favor, contacta al administrador.';
      } else if (axiosError.code === 'ECONNABORTED' || axiosError.message.includes('timeout')) {
        errorMessage = '⏱️ La consulta tardó demasiado. Intenta nuevamente.';
      } else if (axiosError.code === 'ERR_NETWORK' || !axiosError.response) {
        errorMessage =
          'Error de conexión. Verifica tu conexión a internet e intenta nuevamente.';
      }

      throw new Error(errorMessage);
    }

    // Error desconocido
    throw new Error('Ocurrió un error inesperado. Por favor, intenta nuevamente.');
  }
};

/**
 * Obtener health status del servicio de IA
 */
export const getIaHealth = async (): Promise<{ status: string }> => {
  try {
    const response = await iaClient.get('/api/ia/health');
    return response.data;
  } catch (error) {
    throw new Error('No se puede conectar con el servicio de IA');
  }
};

/**
 * Learning Path Generation Response
 */
export interface LearningPathStep {
  step_number: number;
  title: string;
  document_id: number;
  why_this_step: string;
  estimated_time_minutes: number;
}

export interface GenerateLearningPathResponse {
  learning_path_id: number;
  title: string;
  steps: LearningPathStep[];
  total_steps: number;
  estimated_time_hours: number;
  user_level: 'beginner' | 'intermediate' | 'advanced';
  generated_at: string;
}

export interface LearningPath {
  id: number;
  user_id: number;
  topic: string;
  user_level: 'beginner' | 'intermediate' | 'advanced';
  title: string;
  steps: LearningPathStep[];
  estimated_time_hours: number;
  content_json: string;
  created_at: string;
}

/**
 * Generar una ruta de aprendizaje personalizada
 * @param topic - Tema para el que generar la ruta (mínimo 5 caracteres)
 * @param userLevel - Nivel del usuario: 'beginner', 'intermediate' o 'advanced'
 * @returns Learning path generado con steps
 * @throws Error con mensaje específico según código HTTP
 */
export const generateLearningPath = async (
  topic: string,
  userLevel: 'beginner' | 'intermediate' | 'advanced' = 'intermediate'
): Promise<GenerateLearningPathResponse> => {
  try {
    const response = await iaClient.post<GenerateLearningPathResponse>(
      '/api/ia/generate/learning-path',
      {
        topic,
        user_level: userLevel,
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiErrorResponse>;
      const status = axiosError.response?.status;
      const errorData = axiosError.response?.data;

      let errorMessage = 'Error al generar la ruta de aprendizaje. Intenta nuevamente.';

      if (status === 400) {
        // Validación
        errorMessage =
          errorData?.detail ||
          errorData?.error?.message ||
          'Tema inválido. Verifica que tenga al menos 5 caracteres.';
      } else if (status === 401) {
        errorMessage = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
      } else if (status === 429) {
        errorMessage =
          '🚫 Has generado muchas rutas. Espera un momento antes de continuar.';
      } else if (status === 503) {
        errorMessage =
          '⚠️ El servicio de IA está temporalmente no disponible. Intenta en unos minutos.';
      } else if (status === 504) {
        errorMessage =
          '⏱️ La generación tardó demasiado. Intenta con un tema más específico.';
      } else if (status === 500) {
        errorMessage =
          'Error interno del servidor. Por favor, contacta al administrador.';
      }

      throw new Error(errorMessage);
    }

    throw new Error('Ocurrió un error inesperado. Por favor, intenta nuevamente.');
  }
};

/**
 * Obtener una ruta de aprendizaje generada
 * @param pathId - ID de la ruta de aprendizaje
 * @returns Datos completos de la ruta de aprendizaje
 * @throws Error si no se encuentra o no hay autorización
 */
export const getLearningPath = async (pathId: number): Promise<LearningPath> => {
  try {
    const response = await iaClient.get<LearningPath>(
      `/api/ia/learning-path/${pathId}`
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiErrorResponse>;
      const status = axiosError.response?.status;
      const errorData = axiosError.response?.data;

      let errorMessage = 'Error al cargar la ruta de aprendizaje.';

      if (status === 404) {
        errorMessage = 'La ruta de aprendizaje no existe.';
      } else if (status === 401) {
        errorMessage = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
      } else if (status === 403) {
        errorMessage = 'No tienes acceso a esta ruta de aprendizaje.';
      }

      throw new Error(errorMessage);
    }

    throw new Error('Error de conexión. Intenta nuevamente.');
  }
};
