// src/components/AddToWishlistButton.tsx
import {Heart} from 'lucide-react';
import {useWishlistStore} from '../stores/useWishlistStore';

interface AddToWishlistButtonProps {
    productId: number;
    className?: string;
}

export function AddToWishlistButton({productId, className}: AddToWishlistButtonProps) {
    const {wishlistIds, toggleWishlist} = useWishlistStore();
    const isInWishlist = wishlistIds.has(productId);

    const handleClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        toggleWishlist(productId);
    };

    return (
        <button
            onClick={handleClick}
            className={`absolute top-2 right-2 rounded-full bg-slate-800/50 p-2 text-white backdrop-blur-sm transition hover:bg-slate-700 ${className}`}
            aria-label={isInWishlist ? 'Удалить из избранного' : 'Добавить в избранное'}
        >
            <Heart
                size={20}
                className={isInWishlist ? 'fill-red-500 text-red-500' : 'fill-transparent'}
            />
        </button>
    );
}