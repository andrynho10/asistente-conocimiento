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
