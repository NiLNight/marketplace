// src/stores/authStore.ts
import { create } from 'zustand';
import apiClient from '../api'; // Импортируем наш настроенный клиент
import { devtools } from 'zustand/middleware';

// Тип для данных пользователя, которые приходят с бэкенда
interface User {
  id: number;
  username: string;
  email: string;
}

// Тип для всего состояния аутентификации
interface AuthState {
  user: User | null;
  isLoggedIn: boolean;
  isLoading: boolean; // Для отслеживания проверки статуса при загрузке приложения
  error: string | null; // Для хранения сообщений об ошибках

  // Асинхронная функция для проверки, авторизован ли пользователь
  checkAuth: () => Promise<void>;

  // Функция для логина
  login: (data: { email: string; password: string }) => Promise<void>;

  // Функция для выхода
  logout: () => Promise<void>;

  // Функция для регистрации
  register: (data: {username: string, email: string; password: string }) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(devtools(
  (set) => ({
    user: null,
    isLoggedIn: false,
    isLoading: true, // Изначально true, пока мы не проверим статус
    error: null,

    checkAuth: async () => {
      set({ isLoading: true });
      try {
        const response = await apiClient.get('/user/profile/');
        // Если запрос успешен, значит, пользователь авторизован
        set({ user: response.data, isLoggedIn: true, isLoading: false, error: null });
      } catch (error) {
        // Если ошибка (скорее всего 401), значит, не авторизован
        set({ user: null, isLoggedIn: false, isLoading: false });
      }
    },

    login: async (loginData) => {
        set({ isLoading: true, error: null });
        try {
            const response = await apiClient.post('/user/login/', loginData);
            // Бэкенд возвращает данные в поле `user`
            set({ user: response.data.user, isLoggedIn: true, isLoading: false });
        } catch (error: any) {
            // Сохраняем сообщение об ошибке для отображения в UI
            const errorMessage = error.response?.data?.error || 'Произошла ошибка входа';
            set({ error: errorMessage, isLoading: false });
            throw error; // Пробрасываем ошибку, чтобы компонент мог на нее отреагировать
        }
    },

    logout: async () => {
        set({ isLoading: true });
        try {
            await apiClient.post('/user/logout/');
            set({ user: null, isLoggedIn: false, isLoading: false });
        } catch (error) {
            // Даже если произошла ошибка, выходим из системы на фронте
            set({ user: null, isLoggedIn: false, isLoading: false });
        }
    },

    register: async (registerData) => {
        set({ isLoading: true, error: null });
        try {
            await apiClient.post('/user/register/', registerData);
            set({ isLoading: false });
            // Здесь не логиним пользователя, т.к. требуется подтверждение
        } catch(error: any) {
            const errorMessage = error.response?.data?.error || error.response?.data?.email?.[0] || 'Ошибка регистрации';
            set({ error: errorMessage, isLoading: false });
            throw error;
        }
    }
  }), { name: 'AuthStore' }
));