// src/utils/url.ts

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Безопасно формирует полный URL для ресурса с бэкенда.
 * Проверяет, не является ли путь уже полным URL.
 * @param relativePath - Относительный путь (например, /media/images/avatar.png)
 * @returns Полный URL или null, если путь не предоставлен.
 */
export function getImageUrl(relativePath: string | null | undefined): string | null {
    if (!relativePath) {
        return null;
    }

    // Если путь уже является полным URL, возвращаем его как есть
    if (relativePath.startsWith('http')) {
        return relativePath;
    }

    // В противном случае, строим полный URL
    return `${API_BASE_URL}${relativePath}`;
}