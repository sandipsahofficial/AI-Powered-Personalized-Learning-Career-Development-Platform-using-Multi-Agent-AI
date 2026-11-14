import { apiClient } from './api';
import { LoginCredentials, RegisterCredentials, TokenResponse, User } from '../types/auth';

export const authService = {
  async register(data: RegisterCredentials): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/users/me');
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
