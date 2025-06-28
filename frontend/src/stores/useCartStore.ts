// src/stores/useCartStore.ts
import {create} from 'zustand';
import {devtools} from 'zustand/middleware';
import apiClient from '../api';
import toast from 'react-hot-toast';

// Типы на основе вашего OpenAPI
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
    updateItemQuantity: (productId: number, quantity: number) => Promise<void>;
    removeFromCart: (productId: number) => Promise<void>;
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
                // Просто вызываем. Бэкенд вернет либо корзину юзера, либо из сессии.
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
            const newItems = originalItems.map(item =>
                item.product.id === productId ? {...item, quantity} : item
            ).filter(item => item.quantity > 0);

            const newTotal = newItems.reduce((sum, item) => sum + item.quantity, 0);
            set({items: newItems, total_items: newTotal});

            try {
                await apiClient.patch(`/carts/${productId}/`, {quantity});
            } catch (error: any) {
                set({items: originalItems, total_items: originalItems.reduce((sum, item) => sum + item.quantity, 0)});
                toast.error(error.response?.data?.error || "Не удалось обновить товар");
            }
        },

        removeFromCart: async (productId: number) => {
            const originalItems = get().items;
            const newItems = originalItems.filter(item => item.product.id !== productId);
            const newTotal = newItems.reduce((sum, item) => sum + item.quantity, 0);
            set({items: newItems, total_items: newTotal});

            try {
                await apiClient.delete(`/carts/delete/${productId}/`);
            } catch (error: any) {
                set({items: originalItems, total_items: originalItems.reduce((sum, item) => sum + item.quantity, 0)});
                toast.error(error.response?.data?.error || "Не удалось удалить товар");
            }
        },
    }),
    {name: 'CartStore'}
));