// src/stores/useWishlistStore.ts
import {create} from 'zustand';
import {devtools} from 'zustand/middleware';
import apiClient from '../api';
import toast from 'react-hot-toast';

// Тип элемента из API, когда мы запрашиваем полный список
export interface WishlistItem {
    id: number | null;
    product: {
        id: number;
        title: string;
        price: string;
        price_with_discount: number;
        thumbnail: string | null;
        rating_avg: number;
    };
}

interface WishlistState {
    wishlistIds: Set<number>; // Храним только ID для быстрой проверки
    wishlistItems: WishlistItem[]; // Храним полные данные для страницы списка желаний
    isLoading: boolean;

    fetchWishlist: () => Promise<void>;
    toggleWishlist: (productId: number) => Promise<void>;
}

export const useWishlistStore = create<WishlistState>()(devtools(
    (set, get) => ({
        wishlistIds: new Set(),
        wishlistItems: [],
        isLoading: false,

        fetchWishlist: async () => {
            set({isLoading: true});
            try {
                const response = await apiClient.get<WishlistItem[]>('/wishlists/');
                const items = response.data;
                const ids = new Set(items.map(item => item.product.id));
                set({wishlistItems: items, wishlistIds: ids, isLoading: false});
            } catch (error) {
                console.error("Failed to fetch wishlist", error);
                set({isLoading: false});
            }
        },

        toggleWishlist: async (productId: number) => {
            const {wishlistIds, fetchWishlist} = get();
            const isInWishlist = wishlistIds.has(productId);

            // Оптимистичное обновление
            const newWishlistIds = new Set(wishlistIds);
            if (isInWishlist) {
                newWishlistIds.delete(productId);
            } else {
                newWishlistIds.add(productId);
            }
            set({wishlistIds: newWishlistIds});

            try {
                if (isInWishlist) {
                    await apiClient.delete(`/wishlists/delete/${productId}/`);
                    toast.success('Удалено из избранного');
                } else {
                    await apiClient.post('/wishlists/add/', {product_id: productId});
                    toast.success('Добавлено в избранное');
                }
                // После успешной операции обновляем полные данные
                await fetchWishlist();
            } catch (error) {
                console.error("Failed to toggle wishlist", error);
                // Откатываем изменения в UI в случае ошибки
                set({wishlistIds});
                toast.error('Произошла ошибка');
            }
        },
    }),
    {name: 'WishlistStore'}
));