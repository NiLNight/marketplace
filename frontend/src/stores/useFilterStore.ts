// src/stores/useFilterStore.ts
import {create} from 'zustand';
import {devtools} from 'zustand/middleware';

export interface FilterStore {
    category: number | null;
    searchTerm: string;
    minPrice: string;
    maxPrice: string;
    ordering: string;

    setCategory: (id: number | null) => void;
    setSearchTerm: (term: string) => void;
    setMinPrice: (price: string) => void;
    setMaxPrice: (price: string) => void;
    setOrdering: (order: string) => void;
}

const defaultOrdering = '-popularity_score';

export const useFilterStore = create<FilterStore>()(
    devtools(
        (set, get) => ({ // <-- Добавляем `get` для доступа к текущему состоянию
            category: null,
            searchTerm: '',
            minPrice: '',
            maxPrice: '',
            ordering: defaultOrdering,
            setCategory: (id) => {
                set({category: id}, false, 'SET_CATEGORY');
            },
            // Вот ключевое изменение:
            setSearchTerm: (term) => {
                const previousTerm = get().searchTerm;
                // Если пользователь начал поиск (раньше поле было пустым)
                if (!previousTerm && term) {
                    set({searchTerm: term, ordering: ''}, false, 'START_SEARCH'); // Сбрасываем сортировку
                }
                // Если пользователь очистил поиск
                else if (previousTerm && !term) {
                    set({searchTerm: term, ordering: defaultOrdering}, false, 'CLEAR_SEARCH'); // Возвращаем сортировку по умолчанию
                }
                // Во всех остальных случаях просто меняем поисковый запрос
                else {
                    set({searchTerm: term}, false, 'SET_SEARCH_TERM');
                }
            },
            setMinPrice: (price) => set({minPrice: price}, false, 'SET_MIN_PRICE'),
            setMaxPrice: (price) => set({maxPrice: price}, false, 'SET_MAX_PRICE'),
            setOrdering: (order) => set({ordering: order}, false, 'SET_ORDERING'),
        }),
        {name: 'ProductFilterStore'}
    )
);