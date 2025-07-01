// src/hooks/useCheckOwnership.ts
import { useAuthStore } from '../stores/authStore';

export function useCheckOwnership(authorUsername?: string): boolean {
    const { user, isLoggedIn } = useAuthStore();

    if (!isLoggedIn || !user || !authorUsername) {
        return false;
    }

    return user.username === authorUsername;
}