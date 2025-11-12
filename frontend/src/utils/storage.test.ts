import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setToken, getToken, removeToken, decodeToken, hasValidToken } from './storage';

describe('storage utils', () => {
  beforeEach(() => {
    // Limpiar sessionStorage antes de cada test
    sessionStorage.clear();
  });

  describe('setToken', () => {
    it('debe guardar el token en sessionStorage', () => {
      const token = 'test-token';
      setToken(token);
      expect(sessionStorage.getItem('auth_token')).toBe(token);
    });
  });

  describe('getToken', () => {
    it('debe recuperar el token de sessionStorage', () => {
      const token = 'test-token';
      sessionStorage.setItem('auth_token', token);
      expect(getToken()).toBe(token);
    });

    it('debe retornar null si no hay token', () => {
      expect(getToken()).toBeNull();
    });
  });

  describe('removeToken', () => {
    it('debe eliminar el token de sessionStorage', () => {
      sessionStorage.setItem('auth_token', 'test-token');
      removeToken();
      expect(sessionStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('decodeToken', () => {
    it('debe decodificar un token JWT válido', () => {
      // Token JWT simulado: header.payload.signature
      // Payload: { "user_id": 1, "role": "admin", "exp": 9999999999 }
      const payload = btoa(JSON.stringify({ user_id: 1, role: 'admin', exp: 9999999999 }));
      const token = `header.${payload}.signature`;

      const result = decodeToken(token);

      expect(result).toEqual({
        id: 1,
        username: '',
        role: 'admin',
      });
    });

    it('debe retornar null si el token tiene formato inválido', () => {
      const invalidToken = 'invalid-token';

      // Espiar console.error para evitar ruido en los logs
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const result = decodeToken(invalidToken);

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('debe retornar null si el token ha expirado', () => {
      // Token con exp en el pasado
      const payload = btoa(JSON.stringify({ user_id: 1, role: 'admin', exp: 1000000 }));
      const token = `header.${payload}.signature`;

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const result = decodeToken(token);

      expect(result).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalledWith('Token JWT ha expirado');

      consoleWarnSpy.mockRestore();
    });
  });

  describe('hasValidToken', () => {
    it('debe retornar true si hay un token válido', () => {
      const payload = btoa(JSON.stringify({ user_id: 1, role: 'admin', exp: 9999999999 }));
      const token = `header.${payload}.signature`;
      sessionStorage.setItem('auth_token', token);

      expect(hasValidToken()).toBe(true);
    });

    it('debe retornar false si no hay token', () => {
      expect(hasValidToken()).toBe(false);
    });

    it('debe retornar false si el token es inválido', () => {
      sessionStorage.setItem('auth_token', 'invalid-token');

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(hasValidToken()).toBe(false);

      consoleErrorSpy.mockRestore();
    });
  });
});
