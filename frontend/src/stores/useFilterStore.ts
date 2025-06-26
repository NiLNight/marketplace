// src/stores/useFilterStore.ts

import {create} from 'zustand';
import {devtools} from 'zustand/middleware';

// 1. Определяем интерфейс (тип) для нашего хранилища.
// Это гарантирует, что мы не ошибемся в названиях полей.
export interface FilterStore {
    // Состояние фильтров
    category: number | null;
    searchTerm: string;
    minPrice: string; // Храним как строку, так как input возвращает строку
    maxPrice: string;
    ordering: string;

    // Функции для изменения состояния
    setCategory: (id: number | null) => void;
    setSearchTerm: (term: string) => void;
    setMinPrice: (price: string) => void;
    setMaxPrice: (price: string) => void;
    setOrdering: (order: string) => void;
}

// 2. Создаем само хранилище с помощью Zustand
export const useFilterStore = create<FilterStore>()(
    // `devtools` — это обертка для удобной отладки в браузере с Redux DevTools
    devtools(
        (set) => ({
            // Начальные значения фильтров
            category: null,
            searchTerm: '',
            minPrice: '',
            maxPrice: '',
            ordering: '-popularity_score', // Значение по умолчанию

            // Реализация функций-сеттеров
            // `set` — это функция Zustand, которая безопасно обновляет состояние
            setCategory: (id) => set({category: id}, false, 'SET_CATEGORY'),
            setSearchTerm: (term) => set({searchTerm: term}, false, 'SET_SEARCH_TERM'),
            setMinPrice: (price) => set({minPrice: price}, false, 'SET_MIN_PRICE'),
            setMaxPrice: (price) => set({maxPrice: price}, false, 'SET_MAX_PRICE'),
            setOrdering: (order) => set({ordering: order}, false, 'SET_ORDERING'),
        }),
        {name: 'ProductFilterStore'} // Имя для отладочной панели
    )
);