import axios, { AxiosError, AxiosInstance } from 'axios';
import type { LoginRequest, TokenResponse, AuthError } from '@/types/auth';
import { setToken, removeToken } from '@/utils/storage';

// Configurar base URL del backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Función para crear instancia de axios (exportada para testing)
export const createApiClient = (): AxiosInstance => {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

// Crear instancia de axios con configuración base
const apiClient = createApiClient();

/**
 * Realiza login con credenciales de usuario
 * @param credentials - Username y password
 * @returns TokenResponse con token, user_id y role
 * @throws Error con mensaje específico si falla
 */
export const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
  try {
    const response = await apiClient.post<TokenResponse>('/api/auth/login', credentials);

    // Guardar token en sessionStorage
    setToken(response.data.token);

    return response.data;
  } catch (error) {
    // Manejar errores de autenticación
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<AuthError>;

      if (axiosError.response?.status === 401) {
        // Error de credenciales inválidas
        const errorMessage = axiosError.response.data?.error?.message || 'Usuario o contraseña incorrectos';
        throw new Error(errorMessage);
      }

      // Otros errores de red o servidor
      throw new Error('Error al conectar con el servidor. Intenta nuevamente.');
    }

    // Error desconocido
    throw new Error('Ocurrió un error inesperado. Intenta nuevamente.');
  }
};

/**
 * Realiza logout eliminando el token
 */
export const logout = (): void => {
  removeToken();
};

/**
 * Obtiene el token actual del sessionStorage
 * Útil para agregarlo a headers de requests protegidos
 */
export const getAuthHeader = (): { Authorization: string } | {} => {
  const token = sessionStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};
