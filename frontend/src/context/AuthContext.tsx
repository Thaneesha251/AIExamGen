import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, LoginCredentials, UserRole } from '@/types/auth';
import { UserProfileUpdateData } from '@/types/user';
import { authService } from '@/services/authService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateProfile: (profileData: UserProfileUpdateData) => Promise<User>;
  userRole: UserRole | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const res = await authService.getMe();
      if (res && res.success && res.data) {
        setUser(res.data);
        localStorage.setItem('user', JSON.stringify(res.data));
      } else {
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    } catch {
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    setIsLoading(true);
    try {
      const res = await authService.login(credentials);
      if (res && res.success && res.data) {
        const { access_token, user: rawUser } = res.data;
        localStorage.setItem('token', access_token);

        // Fetch full profile from /me to ensure complete user schema
        const meRes = await authService.getMe();
        const fullUser = meRes.data;
        setUser(fullUser);
        localStorage.setItem('user', JSON.stringify(fullUser));
        return fullUser;
      } else {
        throw new Error('Invalid response from authentication server');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    await fetchCurrentUser();
  };

  const updateProfile = async (profileData: UserProfileUpdateData): Promise<User> => {
    const res = await authService.updateOwnProfile(profileData);
    if (res && res.success && res.data) {
      setUser(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
      return res.data;
    }
    throw new Error('Failed to update profile');
  };

  const userRole = user?.role?.name || (user as any)?.role || null;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
        updateProfile,
        userRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
