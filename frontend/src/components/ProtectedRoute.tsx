// src/components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

/**
 * Компонент для защиты маршрутов.
 * Если пользователь не авторизован — перенаправляет на главную страницу.
 * Сохраняет целевой URL, чтобы после входа вернуть пользователя обратно.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isLoggedIn } = useAuthStore();
    const location = useLocation();

    if (!isLoggedIn) {
        // Перенаправляем на главную, сохраняя исходный путь в state
        return <Navigate to="/" state={{ from: location }} replace />;
    }

    return <>{children}</>;
}
