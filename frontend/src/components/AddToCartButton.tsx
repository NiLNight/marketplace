// src/components/AddToCartButton.tsx
import { useState } from 'react';
import { ShoppingCart } from 'lucide-react';
import { useCartStore } from '../stores/useCartStore';

interface AddToCartButtonProps {
    productId: number;
    className?: string;
}

export function AddToCartButton({ productId, className }: AddToCartButtonProps) {
    const addToCart = useCartStore((state) => state.addToCart);
    const [isLoading, setIsLoading] = useState(false);

    const handleClick = async (e: React.MouseEvent) => {
        e.preventDefault(); // Предотвращаем переход по ссылке, если кнопка внутри Link
        e.stopPropagation(); // Останавливаем всплытие события

        setIsLoading(true);
        try {
            await addToCart(productId, 1);
            alert('Товар добавлен в корзину!'); // Простое уведомление для пользователя
        } catch (error) {
            alert(error instanceof Error ? error.message : 'Произошла ошибка');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={isLoading}
            className={`flex w-full items-center justify-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-600 ${className}`}
        >
            <ShoppingCart size={18} />
            <span>{isLoading ? 'Добавление...' : 'В корзину'}</span>
        </button>
    );
}