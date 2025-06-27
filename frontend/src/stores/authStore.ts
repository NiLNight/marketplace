// src/stores/authStore.ts
import { create } from 'zustand';
import apiClient from '../api';
import { devtools } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;

  checkAuth: () => Promise<void>;
  login: (data: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: {username: string, email: string; password: string }) => Promise<void>;

  startProactiveTokenRefresh: () => void;
  stopProactiveTokenRefresh: () => void;
}

let refreshIntervalId: number | null = null;
const REFRESH_INTERVAL = 1.2 * 60 * 1000; // 14 минут, чуть меньше времени жизни токена

export const useAuthStore = create<AuthState>()(devtools(
  (set, get) => ({
    user: null,
    isLoggedIn: false,
    isLoading: true,
    error: null,

    startProactiveTokenRefresh: () => {
        if (refreshIntervalId) {
            clearInterval(refreshIntervalId);
        }
        refreshIntervalId = window.setInterval(async () => {
            if (get().isLoggedIn) {
                console.log('Proactively refreshing token by checking auth status...');
                try {
                    // Просто делаем запрос. Интерцептор сделает все остальное, если токен истек.
                    await apiClient.get('/user/profile/');
                } catch (error) {
                    console.error("Proactive check/refresh failed. Interceptor should handle this.", error);
                }
            }
        }, REFRESH_INTERVAL);
    },

    stopProactiveTokenRefresh: () => {
        if (refreshIntervalId) {
            clearInterval(refreshIntervalId);
            refreshIntervalId = null;
        }
    },

    checkAuth: async () => {
      set({ isLoading: true });
      try {
        const response = await apiClient.get('/user/profile/');
        set({ user: response.data, isLoggedIn: true, isLoading: false, error: null });
        get().startProactiveTokenRefresh();
      } catch (error) {
        set({ user: null, isLoggedIn: false, isLoading: false });
        get().stopProactiveTokenRefresh();
      }
    },

    login: async (loginData) => {
        set({ isLoading: true, error: null });
        try {
            const response = await apiClient.post('/user/login/', loginData);
            set({ user: response.data.user, isLoggedIn: true, isLoading: false });
            get().startProactiveTokenRefresh();
        } catch (error: any) {
            const errorMessage = error.response?.data?.error || 'Произошла ошибка входа';
            set({ error: errorMessage, isLoading: false });
            throw error;
        }
    },

    logout: async () => {
        set({ isLoading: true });
        get().stopProactiveTokenRefresh();
        try {
            await apiClient.post('/user/logout/');
        } catch (error) {
            console.error("Logout failed on server, but logging out on client.", error)
        } finally {
            set({ user: null, isLoggedIn: false, isLoading: false });
        }
    },

    register: async (registerData) => {
        set({ isLoading: true, error: null });
        try {
            await apiClient.post('/user/register/', registerData);
            set({ isLoading: false });
        } catch(error: any) {
            const errorMessage = error.response?.data?.error || error.response?.data?.email?.[0] || 'Ошибка регистрации';
            set({ error: errorMessage, isLoading: false });
            throw error;
        }
    }
  }), { name: 'AuthStore' }
));