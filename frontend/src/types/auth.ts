export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  token: string;
  user_id: number;
  role: string;
}

export interface User {
  id: number;
  username: string;
  role: string;
}

export interface DecodedToken {
  user_id: number;
  role: string;
  exp: number;
  iat: number;
  type: string;
}

export interface AuthError {
  error: {
    code: string;
    message: string;
  };
}
