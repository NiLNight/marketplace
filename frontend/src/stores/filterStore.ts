// src/stores/filterStore.ts
import { create } from 'zustand';

// Описываем, что будет храниться
interface FilterState {
  activeCategoryId: number | null; // null означает "Все товары"
  setActiveCategoryId: (id: number | null) => void;
}

// Создаем хранилище
export const useFilterStore = create<FilterState>((set) => ({
  activeCategoryId: null, // Изначально не выбрана ни одна категория
  setActiveCategoryId: (id) => set({ activeCategoryId: id }),
}));