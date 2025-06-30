// src/hooks/useCheckUserReview.ts
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api';
import { useAuthStore } from '../stores/authStore';

interface Review {
    id: number;
    user: string;
}

interface ApiResponse {
    results: Review[];
}

// Запрашиваем список отзывов и ищем в нем свой
const checkReview = async (productId: number, username: string | undefined): Promise<boolean> => {
    if (!username) return false;

    const { data } = await apiClient.get<ApiResponse>(`/reviews/${productId}/`);
    return data.results.some(review => review.user === username);
};

export function useCheckUserReview(productId: number) {
    const { user, isLoggedIn } = useAuthStore();

    const { data: hasReviewed } = useQuery({
        queryKey: ['userReview', productId, user?.username],
        queryFn: () => checkReview(productId, user?.username),
        // Запрос выполняется только если пользователь залогинен
        enabled: isLoggedIn,
    });

    return { hasReviewed: hasReviewed ?? false };
}