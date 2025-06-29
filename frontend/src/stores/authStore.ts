// src/stores/authStore.ts
import {create} from 'zustand';
import apiClient from '../api';
import {devtools} from 'zustand/middleware';

interface ApiError {
    response?: {
        data?: {
            error?: string;
            username?: string[]; // Ошибка валидации для поля username
            email?: string[]; // Ошибка валидации для поля email
        };
    };
}

interface UserProfile {
    public_id: string;
    phone: string | null;
    birth_date: string | null;
    avatar: string | null;
}

interface User {
    username: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
    profile: UserProfile;
}

interface UserProfileUpdateData {
    phone?: string | null;
    birth_date?: string | null;
    avatar?: File; // При отправке это будет файл
}

interface UserUpdateData {
    username?: string;
    first_name?: string;
    last_name?: string;
    profile?: UserProfileUpdateData;
}

interface AuthState {
    user: User | null;
    isLoggedIn: boolean;
    isLoading: boolean;
    error: string | null;

    checkAuth: () => Promise<void>;
    login: (data: { email: string; password: string }) => Promise<void>;
    logout: () => Promise<void>;
    register: (data: { username: string, email: string; password: string }) => Promise<void>;
    updateProfile: (data: UserUpdateData) => Promise<void>; // <-- Тип аргумента обновлен
}

let refreshIntervalId: number | null = null;
const REFRESH_INTERVAL = (15 * 60 - 30) * 1000;

const startProactiveTokenRefresh = () => {
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
    }
    refreshIntervalId = window.setInterval(async () => {
        console.log('Proactively refreshing token...');
        try {
            await apiClient.post('/api/token/refresh/');
        } catch (error) {
            console.error("Proactive refresh failed, user might be logged out soon.", error);
            // Интерцептор обработает полный выход из системы, если refresh token тоже истек
        }
    }, REFRESH_INTERVAL);
};

const stopProactiveTokenRefresh = () => {
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
        refreshIntervalId = null;
    }
};


export const useAuthStore = create<AuthState>()(devtools(
    (set) => ({
        user: null,
        isLoggedIn: false,
        isLoading: true,
        error: null,

        checkAuth: async () => {
            set({isLoading: true});
            try {
                const response = await apiClient.get<User>('/user/profile/');
                set({user: response.data, isLoggedIn: true, isLoading: false, error: null});
                startProactiveTokenRefresh();
            } catch {
                set({user: null, isLoggedIn: false, isLoading: false});
                stopProactiveTokenRefresh();
            }
        },

        login: async (loginData) => {
            set({isLoading: true, error: null});
            try {
                const response = await apiClient.post('/user/login/', loginData);
                const userData = response.data.user || response.data;
                set({user: userData, isLoggedIn: true, isLoading: false});
                startProactiveTokenRefresh();
            } catch (error) {
                const apiError = error as ApiError;
                const errorMessage = apiError.response?.data?.error || 'Произошла ошибка входа';
                set({error: errorMessage, isLoading: false});
                throw error;
            }
        },

        logout: async () => {
            set({isLoading: true});
            stopProactiveTokenRefresh();
            try {
                await apiClient.post('/user/logout/');
            } catch (error) {
                console.error("Logout failed on server, but logging out on client.", error)
            } finally {
                set({user: null, isLoggedIn: false, isLoading: false});
            }
        },

        register: async (registerData) => {
            set({isLoading: true, error: null});
            try {
                await apiClient.post('/user/register/', registerData);
                set({isLoading: false});
            } catch (error) {
                const apiError = error as ApiError;
                const errorMessage = apiError.response?.data?.error || apiError.response?.data?.email?.[0] || 'Ошибка регистрации';
                set({error: errorMessage, isLoading: false});
                throw error;
            }
        },
        updateProfile: async (data: UserUpdateData) => {
            set({isLoading: true, error: null});

            const formData = new FormData();

            // Проверяем каждое поле перед добавлением
            if (data.username) formData.append('username', data.username);
            if (data.first_name || data.first_name === '') formData.append('first_name', data.first_name);
            if (data.last_name || data.last_name === '') formData.append('last_name', data.last_name);

            if (data.profile) {
                if (data.profile.phone || data.profile.phone === '') formData.append('profile.phone', data.profile.phone);
                if (data.profile.birth_date || data.profile.birth_date === '') formData.append('profile.birth_date', data.profile.birth_date);
                if (data.profile.avatar) {
                    formData.append('profile.avatar', data.profile.avatar);
                }
            }

            try {
                const response = await apiClient.patch<User>('/user/profile/', formData, { // <-- Указываем тип ответа
                    headers: {'Content-Type': 'multipart/form-data'},
                });
                // Обновляем данные пользователя в сторе
                set({user: response.data, isLoading: false, error: null});
            } catch (error) {
                const apiError = error as ApiError;
                const errorMessage = apiError.response?.data?.username?.[0] || apiError.response?.data?.error || "Не удалось обновить профиль";
                set({isLoading: false, error: errorMessage});
                throw new Error(errorMessage);
            }
        },
    }),
    {name: 'AuthStore'}
));