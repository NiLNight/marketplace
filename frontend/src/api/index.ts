// src/api/index.ts
import axios, {AxiosError} from 'axios';
import {useAuthStore} from '../stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
});

let isRefreshing = false;
let failedQueue: { resolve: (value: unknown) => void; reject: (reason?: any) => void; }[] = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config;
        if (!originalRequest) {
            return Promise.reject(error);
        }

        // 1. Проверяем, что это ошибка 401.
        // 2. Убеждаемся, что это НЕ запрос на обновление токена (чтобы избежать цикла).
        if (error.response?.status === 401 && originalRequest.url !== '/api/token/refresh/') {
            // @ts-ignore
            if (originalRequest._retry) {
                return Promise.reject(error);
            }

            if (isRefreshing) {
                return new Promise(function (resolve, reject) {
                    failedQueue.push({resolve, reject});
                }).then(() => {
                    // @ts-ignore
                    return apiClient(originalRequest);
                });
            }

            // @ts-ignore
            originalRequest._retry = true;
            isRefreshing = true;

            try {
                await apiClient.post('/api/token/refresh/');
                processQueue(null, 'new_token');
                // @ts-ignore
                return apiClient(originalRequest);
            } catch (refreshError: any) {
                processQueue(refreshError, null);

                // Выполняем выход из системы, только если пользователь БЫЛ залогинен
                if (useAuthStore.getState().isLoggedIn) {
                    useAuthStore.getState().logout();
                }

                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;