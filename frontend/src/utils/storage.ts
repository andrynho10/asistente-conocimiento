import type { User, DecodedToken } from '@/types/auth';

const TOKEN_KEY = 'auth_token';

/**
 * Guarda el token JWT en sessionStorage
 */
export const setToken = (token: string): void => {
  sessionStorage.setItem(TOKEN_KEY, token);
};

/**
 * Recupera el token JWT de sessionStorage
 */
export const getToken = (): string | null => {
  return sessionStorage.getItem(TOKEN_KEY);
};

/**
 * Elimina el token JWT de sessionStorage
 */
export const removeToken = (): void => {
  sessionStorage.removeItem(TOKEN_KEY);
};

/**
 * Decodifica el payload de un token JWT (base64)
 * Nota: Esto NO valida la firma del token, solo extrae el payload
 */
export const decodeToken = (token: string): User | null => {
  try {
    // JWT tiene 3 partes separadas por puntos: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.error('Token JWT inválido: formato incorrecto');
      return null;
    }

    // Decodificar el payload (segunda parte)
    const payload = parts[1];
    const decodedPayload = atob(payload);
    const parsedPayload: DecodedToken = JSON.parse(decodedPayload);

    // Verificar si el token ha expirado
    const now = Math.floor(Date.now() / 1000);
    if (parsedPayload.exp && parsedPayload.exp < now) {
      console.warn('Token JWT ha expirado');
      return null;
    }

    // Convertir a User
    return {
      id: parsedPayload.user_id,
      username: '', // El token no incluye username, se debe obtener del backend si es necesario
      role: parsedPayload.role,
    };
  } catch (error) {
    console.error('Error al decodificar token JWT:', error);
    return null;
  }
};

/**
 * Verifica si hay un token válido en sessionStorage
 */
export const hasValidToken = (): boolean => {
  const token = getToken();
  if (!token) return false;

  const user = decodeToken(token);
  return user !== null;
};
