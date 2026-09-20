import { apiClient } from './api';
import {
  UserCreateData,
  UserUpdateData,
  UserFilterOptions,
  UserListResponseData,
} from '@/types/user';
import { User, UserRole } from '@/types/auth';

export const userService = {
  getUsers: async (filters: UserFilterOptions = {}): Promise<{ success: boolean; data: UserListResponseData }> => {
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    if (filters.role) params.append('role', filters.role);
    if (filters.is_active !== undefined) params.append('is_active', String(filters.is_active));
    if (filters.page) params.append('page', String(filters.page));
    if (filters.page_size) params.append('page_size', String(filters.page_size));

    const res = await apiClient.get(`/users?${params.toString()}`);
    return res.data;
  },

  getUserById: async (id: string): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.get(`/users/${id}`);
    return res.data;
  },

  createUser: async (userData: UserCreateData): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.post('/users', userData);
    return res.data;
  },

  updateUser: async (id: string, updateData: UserUpdateData): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.patch(`/users/${id}`, updateData);
    return res.data;
  },

  deactivateUser: async (id: string) => {
    const res = await apiClient.delete(`/users/${id}`);
    return res.data;
  },

  updateUserStatus: async (id: string, isActive: boolean): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.patch(`/users/${id}/status`, { is_active: isActive });
    return res.data;
  },

  updateUserRole: async (id: string, role: UserRole): Promise<{ success: boolean; data: User }> => {
    const res = await apiClient.patch(`/users/${id}/role`, { role });
    return res.data;
  },
};
