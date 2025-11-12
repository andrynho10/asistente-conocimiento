import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import type { LoginRequest, User, TokenResponse } from '@/types/auth';
import * as authService from '@/services/authService';
import { getToken, decodeToken, removeToken } from '@/utils/storage';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<TokenResponse>;
  logout: () => void;
  checkAuth: () => void;
}

/**
 * Hook personalizado para gestionar autenticación
 * Proporciona estado de usuario, login, logout y verificación de auth
 */
export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  /**
   * Verifica si hay un token válido en sessionStorage al montar
   */
  const checkAuth = () => {
    const token = getToken();
    if (token) {
      const decodedUser = decodeToken(token);
      if (decodedUser) {
        setUser(decodedUser);
      } else {
        // Token inválido o expirado
        removeToken();
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setIsLoading(false);
  };

  /**
   * Verificar autenticación al montar el componente
   */
  useEffect(() => {
    checkAuth();
  }, []);

  /**
   * Mutation para login usando React Query
   */
  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data: TokenResponse) => {
      // Decodificar token y setear usuario
      const token = data.token;
      const decodedUser = decodeToken(token);
      if (decodedUser) {
        setUser(decodedUser);
      }
    },
    onError: (error: Error) => {
      // Error manejado en el componente que llama login
      console.error('Login error:', error.message);
    },
  });

  /**
   * Función de login
   */
  const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
    return loginMutation.mutateAsync(credentials);
  };

  /**
   * Función de logout
   */
  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return {
    user,
    isAuthenticated: user !== null,
    isLoading: loginMutation.isPending || isLoading,
    login,
    logout,
    checkAuth,
  };
};
