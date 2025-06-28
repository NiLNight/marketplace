// src/pages/CartPage.tsx
import {useEffect} from 'react';
import {useCartStore} from '../stores/useCartStore';
import {Link, useNavigate} from 'react-router-dom';
import {CartItemRow} from '../components/CartItemRow'; // <-- Импортируем новый компонент

export function CartPage() {
    const {items, isLoading, fetchCart} = useCartStore();

    const navigate = useNavigate();

    useEffect(() => {
        fetchCart();
    }, [fetchCart]);

    if (isLoading && items.length === 0) {
        return <div className="text-center text-white">Загрузка корзины...</div>;
    }

    if (!isLoading && items.length === 0) {
        return (
            <div className="text-center text-white">
                <h1 className="text-3xl font-bold">Ваша корзина пуста</h1>
                <p className="mt-4 text-slate-400">Самое время добавить что-нибудь интересное!</p>
                <Link to="/"
                      className="mt-6 inline-block rounded-md bg-cyan-600 px-6 py-2 text-white transition hover:bg-cyan-700">
                    К каталогу
                </Link>
            </div>
        );
    }

    const totalPrice = items.reduce((sum, item) => sum + item.product.price_with_discount * item.quantity, 0);

    return (
        <div className="mx-auto max-w-4xl text-white">
            <h1 className="mb-8 text-3xl font-bold">Корзина</h1>
            <div className="space-y-4">
                {items.map((item) => (
                    // Используем наш новый компонент для каждой строки
                    <CartItemRow key={item.product.id} item={item}/>
                ))}
            </div>
            <div className="mt-8 flex justify-end gap-8 border-t border-slate-700 pt-6">
                <div className="text-right">
                    <p className="text-xl text-slate-400">Итого:</p>
                    <p className="text-3xl font-bold">{totalPrice.toFixed(2)} руб.</p>
                </div>
                <button
                    onClick={() => navigate('/checkout')}
                    className="rounded-md bg-green-600 px-8 py-3 text-lg font-bold text-white transition hover:bg-green-700"
                >
                    Оформить заказ
                </button>
            </div>
        </div>
    );
}