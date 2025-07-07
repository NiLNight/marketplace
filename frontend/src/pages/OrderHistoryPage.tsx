// src/pages/OrderHistoryPage.tsx
import {useQuery} from "@tanstack/react-query";
import apiClient from "../api";
import {Link} from "react-router-dom";

// Типы на основе вашего API
interface OrderItem {
    product: {
        thumbnail: string | null;
    };
}

interface Order {
    id: number;
    status: string;
    total_price: string;
    created: string;
    pickup_point: { address: string };
    items?: OrderItem[]; // <-- Добавили поле с товарами
}

// Словарь для перевода статусов
const statusTranslations: { [key: string]: string } = {
    processing: "В обработке",
    shipped: "Отправлен",
    delivered: "Доставлен",
    cancelled: "Отменён"
};

const fetchOrders = async (): Promise<Order[]> => {
    const {data} = await apiClient.get('/orders/');
    return data.results || [];
};

export function OrderHistoryPage() {
    const {data: orders, isLoading} = useQuery({queryKey: ['orders'], queryFn: fetchOrders});
    const baseUrl = import.meta.env.VITE_API_BASE_URL;

    if (isLoading) {
        return <div className="text-center text-white">Загрузка истории заказов...</div>;
    }

    if (!orders || orders.length === 0) {
        return (
            <div>
                <h1 className="text-3xl font-bold text-white">Мои заказы</h1>
                <div className="mt-6 p-8 text-center bg-slate-800 rounded-lg text-slate-400">
                    У вас пока нет заказов.
                </div>
            </div>
        );
    }

    return (
        <div>
            <h1 className="text-3xl font-bold text-white">Мои заказы</h1>
            <div className="mt-6 space-y-4">
                {orders.map(order => (
                    <Link to={`/profile/orders/${order.id}`} key={order.id}
                          className="block rounded-lg bg-slate-800 p-6 transition hover:bg-slate-700/50">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-lg font-semibold text-white">Заказ #{order.id}</p>
                                <p className="text-sm text-slate-400">от {new Date(order.created).toLocaleDateString('ru-RU')}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-lg font-bold text-white">{parseFloat(order.total_price).toFixed(2)} руб.</p>
                                <p className={`text-sm font-semibold ${order.status === 'delivered' ? 'text-green-400' : 'text-cyan-400'}`}>
                                    {statusTranslations[order.status] || order.status}
                                </p>
                            </div>
                        </div>

                        <div className="mt-4 border-t border-slate-700 pt-4 flex items-center justify-between">
                            <div className="flex -space-x-4">
                                {order.items && order.items.length > 0 ? (
                                    <>
                                        {order.items.slice(0, 5).map((item, index) => (
                                            <img
                                                key={index}
                                                src={item.product.thumbnail ? `${baseUrl}${item.product.thumbnail}` : `https://ui-avatars.com/api/?name=?&background=random`}
                                                alt="Товар"
                                                className="h-10 w-10 rounded-full border-2 border-slate-800 object-cover"
                                                title={`Товар ${index + 1}`}
                                            />
                                        ))}
                                        {order.items.length > 5 && (
                                            <div
                                                className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-slate-800 bg-slate-700 text-xs font-semibold">
                                                +{order.items.length - 5}
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="h-10"></div> // Пустой div для сохранения высоты, если товаров нет
                                )}
                            </div>
                            <div className="text-sm text-slate-400 text-right">
                                <p>Пункт выдачи:</p>
                                <p className="text-slate-300">{order.pickup_point.address}</p>
                            </div>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
}