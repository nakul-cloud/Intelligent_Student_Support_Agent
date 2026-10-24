import axios from 'axios';
import { useAuthStore } from '../store/useAuthStore';

// Use relative API path to benefit from Vite proxy or direct backend port
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Shared Axios instance with Bearer token injection and global error interceptor.
 * Adheres to Dependency Inversion Principle (DIP):
 * High-level services rely on this abstraction rather than raw fetch or isolated configs.
 */
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // Agent turns can take multiple seconds for tool execution
});

// Request interceptor: Auto-inject JWT Bearer token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 Unauthorized globally
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().clearAuth();
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
