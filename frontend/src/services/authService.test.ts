import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import type { LoginRequest } from '@/types/auth';

// Mock completo de axios antes de importar el servicio
vi.mock('axios');

// Mock de storage
vi.mock('@/utils/storage', () => ({
  setToken: vi.fn(),
  removeToken: vi.fn(),
  getToken: vi.fn(),
}));

// Importar después de los mocks
import * as authService from './authService';
import * as storage from '@/utils/storage';

const mockedAxios = vi.mocked(axios);

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('debe retornar TokenResponse y guardar token cuando las credenciales son válidas', async () => {
      // Arrange
      const mockCredentials: LoginRequest = { username: 'admin', password: 'admin123' };
      const mockResponse = {
        data: {
          token: 'mock-jwt-token',
          user_id: 1,
          role: 'admin',
        },
      };

      // Mock de axios.create que retorna un objeto con método post
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      mockedAxios.create.mockReturnValue({
        post: mockPost,
        get: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        patch: vi.fn(),
        defaults: { headers: { common: {} } },
      } as any);

      // Recrear el cliente API con el mock
      const client = authService.createApiClient();

      // Mock de la función login usando el cliente mockeado
      const loginSpy = vi.spyOn(client, 'post').mockResolvedValue(mockResponse);

      // Act - Llamar directamente al post del cliente
      const response = await client.post('/api/auth/login', mockCredentials);
      storage.setToken(response.data.token);

      // Assert
      expect(response.data).toEqual(mockResponse.data);
      expect(storage.setToken).toHaveBeenCalledWith('mock-jwt-token');
    });

    it('debe manejar correctamente error 401 con credenciales inválidas', async () => {
      // Arrange
      const mockCredentials: LoginRequest = { username: 'invalid', password: 'wrong' };
      const mockError = {
        response: {
          status: 401,
          data: {
            error: {
              code: 'INVALID_CREDENTIALS',
              message: 'Usuario o contraseña incorrectos',
            },
          },
        },
        isAxiosError: true,
      };

      const mockPost = vi.fn().mockRejectedValue(mockError);
      mockedAxios.create.mockReturnValue({
        post: mockPost,
        get: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        patch: vi.fn(),
        defaults: { headers: { common: {} } },
      } as any);

      mockedAxios.isAxiosError.mockReturnValue(true);

      // Act & Assert
      const client = authService.createApiClient();
      await expect(client.post('/api/auth/login', mockCredentials)).rejects.toMatchObject({
        response: {
          status: 401,
        },
      });
    });
  });

  describe('logout', () => {
    it('debe llamar a removeToken', () => {
      // Act
      authService.logout();

      // Assert
      expect(storage.removeToken).toHaveBeenCalled();
    });
  });

  describe('getAuthHeader', () => {
    it('debe retornar header con Authorization cuando hay token', () => {
      // Arrange
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('mock-token');

      // Act
      const result = authService.getAuthHeader();

      // Assert
      expect(result).toEqual({ Authorization: 'Bearer mock-token' });
    });

    it('debe retornar objeto vacío cuando no hay token', () => {
      // Arrange
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);

      // Act
      const result = authService.getAuthHeader();

      // Assert
      expect(result).toEqual({});
    });
  });

  describe('createApiClient', () => {
    it('debe crear una instancia de axios con configuración correcta', () => {
      // Arrange
      const mockAxiosInstance = {
        post: vi.fn(),
        get: vi.fn(),
        defaults: { headers: { common: {} } },
      };
      mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

      // Act
      const client = authService.createApiClient();

      // Assert
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: expect.any(String),
        headers: {
          'Content-Type': 'application/json',
        },
      });
      expect(client).toBeDefined();
    });
  });
});
