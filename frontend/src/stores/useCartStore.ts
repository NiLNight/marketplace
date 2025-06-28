// src/stores/useCartStore.ts
import {create} from 'zustand';
import {devtools} from 'zustand/middleware';
import apiClient from '../api';

interface Product {
    id: number;
    title: string;
    price_with_discount: number;
    thumbnail: string | null;
}

export interface CartItem {
    id: number | null; // ID может быть null для гостевой корзины
    product: Product;
    quantity: number;
}

interface CartState {
    items: CartItem[];
    total_items: number;
    isLoading: boolean;
    error: string | null;

    fetchCart: () => Promise<void>;
    addToCart: (productId: number, quantity: number) => Promise<void>;
    updateItemQuantity: (productId: number, quantity: number) => Promise<void>; // <-- Новый метод
    removeFromCart: (productId: number) => Promise<void>; // <-- Новый метод
}

export const useCartStore = create<CartState>()(devtools(
    (set, get) => ({
        items: [],
        total_items: 0,
        isLoading: false,
        error: null,

        fetchCart: async () => {
            set({isLoading: true});
            try {
                const response = await apiClient.get<CartItem[]>('/carts/');
                const items = response.data;
                const total_items = items.reduce((sum, item) => sum + item.quantity, 0);
                set({items, total_items, isLoading: false, error: null});
            } catch (error) {
                console.error("Failed to fetch cart", error);
                set({isLoading: false, error: "Не удалось загрузить корзину"});
            }
        },

        addToCart: async (productId: number, quantity: number) => {
            set({isLoading: true});
            try {
                // В вашем API ID товара передается в теле
                await apiClient.post('/carts/add/', {product_id: productId, quantity});
                await get().fetchCart();
            } catch (error: any) {
                const errorMessage = error.response?.data?.error || "Не удалось добавить товар";
                set({isLoading: false, error: errorMessage});
                throw new Error(errorMessage);
            }
        },

        updateItemQuantity: async (productId: number, quantity: number) => {
            const originalItems = get().items;
            // Оптимистичное обновление: сначала меняем UI, потом отправляем запрос
            const newItems = originalItems.map(item =>
                item.product.id === productId ? {...item, quantity} : item
            ).filter(item => item.quantity > 0); // Удаляем, если кол-во 0

            const newTotal = newItems.reduce((sum, item) => sum + item.quantity, 0);
            set({items: newItems, total_items: newTotal});

            try {
                await apiClient.patch(`/carts/${productId}/`, {quantity});
                // Можно сделать fetchCart() для полной синхронизации, но для UX это не всегда нужно
            } catch (error: any) {
                // Если ошибка, откатываем изменения в UI
                set({items: originalItems, total_items: originalItems.reduce((sum, item) => sum + item.quantity, 0)});
                alert(error.response?.data?.error || "Не удалось обновить товар");
            }
        },

        removeFromCart: async (productId: number) => {
            const originalItems = get().items;
            // Оптимистичное обновление
            const newItems = originalItems.filter(item => item.product.id !== productId);
            const newTotal = newItems.reduce((sum, item) => sum + item.quantity, 0);
            set({items: newItems, total_items: newTotal});

            try {
                await apiClient.delete(`/carts/delete/${productId}/`);
            } catch (error: any) {
                // Откатываем изменения
                set({items: originalItems, total_items: originalItems.reduce((sum, item) => sum + item.quantity, 0)});
                alert(error.response?.data?.error || "Не удалось удалить товар");
            }
        },
    }),
    {name: 'CartStore'}
));