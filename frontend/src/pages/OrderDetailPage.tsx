// src/pages/OrderDetailPage.tsx
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import apiClient from "../api";

// Типы
interface OrderDetail {
    id: number;
    status: string;
    total_price: string;
    created: string;
    pickup_point: { address: string, city: { name: string } };
    items: Array<{
        product: { title: string, price_with_discount: number, thumbnail: string | null };
        quantity: number;
    }>;
}

const fetchOrderDetail = async (orderId: string): Promise<OrderDetail> => {
    const { data } = await apiClient.get(`/orders/${orderId}/`);
    return data;
};

export function OrderDetailPage() {
    const { orderId } = useParams<{ orderId: string }>();
    const { data: order, isLoading } = useQuery({
        queryKey: ['order', orderId],
        queryFn: () => fetchOrderDetail(orderId!),
        enabled: !!orderId,
    });

    if (isLoading) {
        return <div className="text-center text-white">Загрузка деталей заказа...</div>;
    }

    if (!order) {
        return <div className="text-center text-white">Заказ не найден.</div>;
    }

    return (
        <div className="text-white">
            <h1 className="text-3xl font-bold">Детали заказа #{order.id}</h1>
            <div className="mt-4 space-y-2 text-slate-300">
                <p><b>Статус:</b> <span className="font-medium text-cyan-400">{order.status}</span></p>
                <p><b>Дата:</b> {new Date(order.created).toLocaleString()}</p>
                <p><b>Сумма:</b> <span className="font-bold">{order.total_price} руб.</span></p>
                <p><b>Пункт выдачи:</b> {order.pickup_point.city.name}, {order.pickup_point.address}</p>
            </div>

            <h2 className="mt-8 mb-4 text-2xl font-bold">Состав заказа</h2>
            <div className="space-y-4">
                {order.items.map((item, index) => (
                    <div key={index} className="flex items-center gap-4 rounded-lg bg-slate-800 p-4">
                         <img
                            src={item.product.thumbnail ? `${import.meta.env.VITE_API_BASE_URL}${item.product.thumbnail}` : ''}
                            alt={item.product.title}
                            className="h-20 w-20 rounded-md object-cover"
                        />
                        <div className="flex-grow">
                            <p className="font-semibold">{item.product.title}</p>
                            <p className="text-sm text-slate-400">{item.quantity} шт. x {item.product.price_with_discount.toFixed(2)} руб.</p>
                        </div>
                        <p className="font-bold">{(item.product.price_with_discount * item.quantity).toFixed(2)} руб.</p>
                    </div>
                ))}
            </div>
        </div>
    );
}