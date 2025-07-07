// src/pages/CheckoutPage.tsx
import {useState, useEffect} from 'react';
import {useCartStore} from '../stores/useCartStore';
import {useQuery} from '@tanstack/react-query';
import apiClient from '../api';
import {useNavigate} from 'react-router-dom';
import toast from 'react-hot-toast';
import {useDebounce} from '../hooks/useDebounce';

// Типы
interface City {
    id: number;
    name: string;
}

interface PickupPoint {
    id: number;
    address: string;
    city: City;
}

// Обновляем функцию, добавляем searchQuery и page_size
const fetchPickupPoints = async (cityId: number | null, searchQuery: string): Promise<PickupPoint[]> => {
    if (!cityId) return [];

    const params = new URLSearchParams();
    params.append('city_id', String(cityId));
    params.append('page_size', '100'); // <-- 1. Запрашиваем до 100 пунктов сразу
    if (searchQuery) {
        params.append('q', searchQuery);
    }

    const {data} = await apiClient.get('/delivery/pickup_points/', {params});
    return data.results || [];
};

const fetchCities = async (): Promise<City[]> => {
    const {data} = await apiClient.get('/delivery/city_list/');
    return data.results || [];
};

export function CheckoutPage() {
    const {items: cartItems, fetchCart} = useCartStore();
    const navigate = useNavigate();

    const [selectedCity, setSelectedCity] = useState<number | null>(null);
    const [selectedPickupPoint, setSelectedPickupPoint] = useState<number | null>(null);
    const [isPlacingOrder, setIsPlacingOrder] = useState(false);

    const [searchQuery, setSearchQuery] = useState('');
    const debouncedSearchQuery = useDebounce(searchQuery, 300);

    useEffect(() => {
        if (cartItems.length === 0) {
            fetchCart();
        }
    }, [cartItems, fetchCart]);

    const {data: cities, isLoading: isLoadingCities} = useQuery({queryKey: ['cities'], queryFn: fetchCities});

    const {data: pickupPoints, isLoading: isLoadingPoints} = useQuery({
        queryKey: ['pickupPoints', selectedCity, debouncedSearchQuery],
        queryFn: () => fetchPickupPoints(selectedCity, debouncedSearchQuery),
        enabled: !!selectedCity,
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
                <div className="space-y-6">
                    <h2 className="text-2xl font-semibold">1. Выберите пункт выдачи</h2>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Город</label>
                        <select
                            onChange={(e) => {
                                const cityId = e.target.value ? Number(e.target.value) : null;
                                setSelectedCity(cityId);
                                setSearchQuery('');
                                setSelectedPickupPoint(null);
                            }}
                            disabled={isLoadingCities}
                            className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                        >
                            <option value="">Выберите город...</option>
                            {cities?.map(city => <option key={city.id} value={city.id}>{city.name}</option>)}
                        </select>
                    </div>
                    {selectedCity && (
                        <div className="space-y-4 rounded-lg bg-slate-800 p-4">
                            <div>
                                <label htmlFor="pickup-search" className="block text-sm font-medium text-slate-300">Поиск
                                    по адресу</label>
                                <input id="pickup-search" type="text" placeholder="Введите улицу, метро..."
                                       value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                                       className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                            </div>

                            {isLoadingPoints ? (
                                <div className="text-slate-400">Загрузка пунктов...</div>
                            ) : (
                                // 2. Добавляем div с прокруткой
                                <div className="max-h-60 space-y-2 overflow-y-auto pr-2">
                                    {pickupPoints && pickupPoints.length > 0 ? (
                                        pickupPoints.map(point => (
                                            // --- 3. НАЧАЛО ИЗМЕНЕНИЙ В СТИЛЯХ ---
                                            <label key={point.id} htmlFor={`point-${point.id}`}
                                                   className={`flex cursor-pointer items-start gap-3 rounded-md p-3 border-2 transition-colors ${selectedPickupPoint === point.id ? 'border-cyan-500 bg-cyan-900/50' : 'border-transparent bg-slate-700 hover:bg-slate-600/50'}`}>
                                                <div
                                                    className="mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border-2 border-slate-500">
                                                    {selectedPickupPoint === point.id && (
                                                        <div className="h-2.5 w-2.5 rounded-full bg-cyan-400"></div>
                                                    )}
                                                </div>
                                                <span className="flex-grow text-sm">{point.address}</span>
                                                <input type="radio" id={`point-${point.id}`} name="pickupPoint"
                                                       value={point.id} checked={selectedPickupPoint === point.id}
                                                       onChange={() => setSelectedPickupPoint(point.id)}
                                                       className="sr-only"/>
                                            </label>
                                            // --- КОНЕЦ ИЗМЕНЕНИЙ В СТИЛЯХ ---
                                        ))
                                    ) : (
                                        <p className="p-3 text-center text-sm text-slate-400">Пункты выдачи не
                                            найдены.</p>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Правая часть (без изменений) */}
                <div className="space-y-4 rounded-lg bg-slate-800 p-6 self-start">
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