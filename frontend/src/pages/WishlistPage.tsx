// src/pages/WishlistPage.tsx
import {useEffect} from 'react';
import {useWishlistStore} from '../stores/useWishlistStore';
import {Link} from 'react-router-dom';
import {AddToWishlistButton} from '../components/AddToWishlistButton'; // Для удаления

export function WishlistPage() {
    const {wishlistItems, isLoading, fetchWishlist} = useWishlistStore();

    useEffect(() => {
        fetchWishlist();
    }, [fetchWishlist]);

    if (isLoading && wishlistItems.length === 0) {
        return <div className="text-center text-white">Загрузка списка желаний...</div>;
    }

    return (
        <div>
            <h1 className="text-3xl font-bold text-white mb-6">Список желаний</h1>
            {wishlistItems.length === 0 ? (
                <div className="text-center text-slate-400">
                    <p>Вы еще не добавили ни одного товара в избранное.</p>
                    <Link to="/" className="mt-4 inline-block text-cyan-400 hover:underline">Перейти в каталог</Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                    {wishlistItems.map(({product}) => (
                        <Link to={`/products/${product.id}`} key={product.id} className="group relative">
                            <div className="overflow-hidden rounded-lg bg-slate-800">
                                <img
                                    src={product.thumbnail ? `${import.meta.env.VITE_API_BASE_URL}${product.thumbnail}` : ''}
                                    alt={product.title}
                                    className="h-64 w-full object-cover transition-transform group-hover:scale-105"
                                />
                                <div className="p-4">
                                    <h3 className="font-semibold text-white">{product.title}</h3>
                                    <p className="mt-2 text-lg font-bold text-green-400">{product.price_with_discount} руб.</p>
                                </div>
                            </div>
                            <AddToWishlistButton productId={product.id}/>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}