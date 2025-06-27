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
        (set, get) => ({
            category: null,
            searchTerm: '',
            minPrice: '',
            maxPrice: '',
            ordering: defaultOrdering,
            setCategory: (id) => {
                set({category: id}, false, 'SET_CATEGORY');
            },
            setSearchTerm: (term) => {
                const previousTerm = get().searchTerm;
                if (!previousTerm && term) {
                    set({searchTerm: term, ordering: ''}, false, 'START_SEARCH');
                } else if (previousTerm && !term) {
                    set({searchTerm: term, ordering: defaultOrdering}, false, 'CLEAR_SEARCH');
                } else {
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