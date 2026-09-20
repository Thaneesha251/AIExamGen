import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request Interceptor: Attach JWT token when available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Uniform Error Handling & 401 token cleanup
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error?.message ||
      error.message ||
      'An unexpected error occurred';

    const customError = {
      message: typeof message === 'string' ? message : JSON.stringify(message),
      status: error.response?.status,
      details: error.response?.data?.error?.details || error.response?.data || {},
    };

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }

    return Promise.reject(customError);
  }
);

export const checkBackendHealth = async () => {
  try {
    const res = await apiClient.get('/health');
    return res.data;
  } catch (error) {
    return {
      success: false,
      status: 'unreachable',
      error,
    };
  }
};
