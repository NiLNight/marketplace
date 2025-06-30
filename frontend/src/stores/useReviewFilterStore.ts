// src/stores/useReviewFilterStore.ts
import { create } from 'zustand';

interface ReviewFilterState {
    ordering: string;
    setOrdering: (ordering: string) => void;
}

export const useReviewFilterStore = create<ReviewFilterState>((set) => ({
    // По умолчанию сортируем по дате (сначала новые)
    ordering: '-created',
    setOrdering: (newOrdering) => set({ ordering: newOrdering }),
}));