// src/pages/CheckoutPage.tsx
import {useState, useEffect} from 'react';
import {useCartStore} from '../stores/useCartStore';
import {useQuery} from '@tanstack/react-query';
import apiClient from '../api';
import {useNavigate} from 'react-router-dom';
import toast from 'react-hot-toast';

// Типы на основе вашего API
interface City {
    id: number;
    name: string;
}

interface PickupPoint {
    id: number;
    address: string;
    city: City;
}

// Функции для загрузки данных
const fetchCities = async (): Promise<City[]> => {
    const {data} = await apiClient.get('/delivery/city_list/');
    // API возвращает объект с пагинацией, нам нужен массив results
    return data.results || [];
};

const fetchPickupPoints = async (cityId: number | null): Promise<PickupPoint[]> => {
    if (!cityId) return [];
    const {data} = await apiClient.get('/delivery/pickup_points/', {params: {city_id: cityId}});
    return data.results || [];
};

export function CheckoutPage() {
    const {items: cartItems, fetchCart} = useCartStore();
    const navigate = useNavigate();

    const [selectedCity, setSelectedCity] = useState<number | null>(null);
    const [selectedPickupPoint, setSelectedPickupPoint] = useState<number | null>(null);
    const [isPlacingOrder, setIsPlacingOrder] = useState(false);

    // Загрузка корзины при монтировании, если ее нет
    useEffect(() => {
        if (cartItems.length === 0) {
            fetchCart();
        }
    }, [cartItems, fetchCart]);

    // Запросы к API
    const {data: cities, isLoading: isLoadingCities} = useQuery({queryKey: ['cities'], queryFn: fetchCities});
    const {data: pickupPoints, isLoading: isLoadingPoints} = useQuery({
        queryKey: ['pickupPoints', selectedCity],
        queryFn: () => fetchPickupPoints(selectedCity),
        enabled: !!selectedCity, // Запрос выполняется только когда выбран город
    });

    const totalPrice = cartItems.reduce((sum, item) => sum + item.product.price_with_discount * item.quantity, 0);

    const handlePlaceOrder = async () => {
        if (!selectedPickupPoint) {
            toast.error('Пожалуйста, выберите пункт выдачи.');
            return;
        }
        setIsPlacingOrder(true);
        try {
            const response = await apiClient.post('/orders/create/', {pickup_point_id: selectedPickupPoint});
            toast.success('Заказ успешно создан!');
            // После создания заказа обновляем корзину (она должна стать пустой)
            fetchCart();
            // Перенаправляем на страницу успеха (создадим ее позже) или на страницу заказа
            navigate(`/profile/orders/${response.data.order_id}`);
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Не удалось создать заказ.');
        } finally {
            setIsPlacingOrder(false);
        }
    };

    if (cartItems.length === 0 && !useCartStore.getState().isLoading) {
        return <div className="text-center text-white">Ваша корзина пуста. Невозможно оформить заказ.</div>
    }

    return (
        <div className="mx-auto max-w-4xl text-white">
            <h1 className="mb-8 text-3xl font-bold">Оформление заказа</h1>
            <div className="grid grid-cols-1 gap-12 md:grid-cols-2">
                {/* Левая часть: Выбор доставки */}
                <div className="space-y-6">
                    <h2 className="text-2xl font-semibold">1. Выберите пункт выдачи</h2>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Город</label>
                        <select
                            onChange={(e) => setSelectedCity(Number(e.target.value))}
                            disabled={isLoadingCities}
                            className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                        >
                            <option>Выберите город...</option>
                            {cities?.map(city => <option key={city.id} value={city.id}>{city.name}</option>)}
                        </select>
                    </div>
                    {selectedCity && (
                        <div>
                            <label className="block text-sm font-medium text-slate-300">Пункт выдачи</label>
                            <select
                                onChange={(e) => setSelectedPickupPoint(Number(e.target.value))}
                                disabled={isLoadingPoints || !pickupPoints}
                                className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                            >
                                <option>Выберите пункт выдачи...</option>
                                {pickupPoints?.map(point => <option key={point.id}
                                                                    value={point.id}>{point.address}</option>)}
                            </select>
                        </div>
                    )}
                </div>

                {/* Правая часть: Состав и итог заказа */}
                <div className="space-y-4 rounded-lg bg-slate-800 p-6">
                    <h2 className="text-2xl font-semibold">2. Ваш заказ</h2>
                    {cartItems.map(item => (
                        <div key={item.product.id} className="flex justify-between text-sm">
                            <span>{item.product.title} x {item.quantity}</span>
                            <span
                                className="font-medium">{(item.product.price_with_discount * item.quantity).toFixed(2)} руб.</span>
                        </div>
                    ))}
                    <div className="flex justify-between border-t border-slate-600 pt-4 text-xl font-bold">
                        <span>Итого:</span>
                        <span>{totalPrice.toFixed(2)} руб.</span>
                    </div>
                    <button
                        onClick={handlePlaceOrder}
                        disabled={!selectedPickupPoint || isPlacingOrder}
                        className="w-full rounded-md bg-green-600 px-8 py-3 text-lg font-bold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-slate-600"
                    >
                        {isPlacingOrder ? 'Оформление...' : 'Подтвердить заказ'}
                    </button>
                </div>
            </div>
        </div>
    );
}