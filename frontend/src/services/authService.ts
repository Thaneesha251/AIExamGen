import { apiClient } from './api';
import {
  LoginCredentials,
  RegisterCredentials,
  ChangePasswordCredentials,
  AuthApiResponse,
  User,
} from '@/types/auth';
import { UserProfileUpdateData } from '@/types/user';

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthApiResponse> => {
    const res = await apiClient.post<AuthApiResponse>('/auth/login', credentials);
    return res.data;
  },

  register: async (credentials: RegisterCredentials) => {
    const res = await apiClient.post('/auth/register', credentials);
    return res.data;
  },

  getMe: async (): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore errors on logout network call
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },

  changePassword: async (passData: ChangePasswordCredentials) => {
    const res = await apiClient.post('/auth/change-password', passData);
    return res.data;
  },

  updateOwnProfile: async (profileData: UserProfileUpdateData) => {
    const res = await apiClient.patch('/users/me', profileData);
    return res.data;
  },
};
