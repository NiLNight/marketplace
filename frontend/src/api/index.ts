// src/api/index.ts
import axios from 'axios';

// Получаем базовый URL из переменных окружения
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true, // Включаем отправку cookies с каждым запросом
});

// Добавим интерцептор для ответов, чтобы глобально обрабатывать ошибки
apiClient.interceptors.response.use(
    (response) => response, // Если ответ успешный, просто возвращаем его
    (error) => {
        // Если бэкенд вернул ошибку, она будет здесь
        // Мы можем логировать ее или делать что-то еще
        // Пока просто пробрасываем ошибку дальше, чтобы ее можно было поймать в компонентах
        return Promise.reject(error);
    }
);

export default apiClient;