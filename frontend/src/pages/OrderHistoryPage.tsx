// src/pages/OrderHistoryPage.tsx
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api";
import { Link } from "react-router-dom";

// Типы на основе вашего API
interface Order {
    id: number;
    status: string;
    total_price: string;
    created: string;
    pickup_point: { address: string };
}

const fetchOrders = async (): Promise<Order[]> => {
    const { data } = await apiClient.get('/orders/');
    // API возвращает объект с пагинацией
    return data.results || [];
};

export function OrderHistoryPage() {
    const { data: orders, isLoading } = useQuery({ queryKey: ['orders'], queryFn: fetchOrders });

    if (isLoading) {
        return <div className="text-center text-white">Загрузка истории заказов...</div>;
    }

    return (
        <div>
            <h1 className="text-3xl font-bold text-white">Мои заказы</h1>
            <div className="mt-6 space-y-4">
                {orders?.map(order => (
                    <Link to={`/profile/orders/${order.id}`} key={order.id} className="block rounded-lg bg-slate-800 p-4 transition hover:bg-slate-700">
                        <div className="flex justify-between">
                            <span className="font-semibold">Заказ #{order.id}</span>
                            <span className="text-sm text-slate-400">{new Date(order.created).toLocaleDateString()}</span>
                        </div>
                        <div className="mt-2 text-sm">Статус: <span className="font-medium text-cyan-400">{order.status}</span></div>
                        <div className="mt-1 text-sm">Сумма: <span className="font-bold">{order.total_price} руб.</span></div>
                        <div className="mt-1 text-sm">Пункт выдачи: <span className="text-slate-300">{order.pickup_point.address}</span></div>
                    </Link>
                ))}
            </div>
        </div>
    );
}