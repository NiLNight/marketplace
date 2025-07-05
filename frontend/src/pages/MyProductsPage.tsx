// src/pages/MyProductsPage.tsx
import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import apiClient from "../api";
import {ProductRow} from "../components/ProductRow";
import toast from "react-hot-toast";

// Типы для товаров
export interface Product {
    id: number;
    title: string;
    price: string;
    stock: number;
    is_active: boolean;
    thumbnail: string | null;
    category: {
        title: string;
    };
}

const updateProductStatus = ({productId, isActive}: { productId: number, isActive: boolean }) => {
    return apiClient.patch(`/products/${productId}/update/`, {is_active: isActive});
};

// Функции для API
const fetchMyProducts = async (): Promise<Product[]> => {
    // Предполагаем, что бэкенд вернет список товаров текущего пользователя
    // Если такого эндпоинта нет, его нужно будет создать.
    // Пока будем использовать /products/list/ и фильтровать на клиенте (как временное решение)
    const {data} = await apiClient.get('/products/list/?my_products=true'); // нужен специальный параметр
    return data.results || [];
};

const deleteProduct = (productId: number) => {
    return apiClient.delete(`/products/${productId}/delete/`);
};

export function MyProductsPage() {
    const queryClient = useQueryClient();
    const updateStatusMutation = useMutation({
        mutationFn: updateProductStatus,
        onSuccess: () => {
            toast.success("Статус товара обновлен.");
            // Инвалидируем кэш, чтобы список перерисовался с новым статусом
            queryClient.invalidateQueries({queryKey: ['myProducts']});
        },
        onError: () => {
            toast.error("Не удалось обновить статус.");
        }
    });
    const {data: products, isLoading} = useQuery({
        queryKey: ['myProducts'],
        queryFn: fetchMyProducts,
    });

    const deleteMutation = useMutation({
        mutationFn: deleteProduct,
        onSuccess: () => {
            toast.success("Товар успешно удален.");
            queryClient.invalidateQueries({queryKey: ['myProducts']});
        },
        onError: () => {
            toast.error("Не удалось удалить товар.");
        }
    });

    const handleStatusToggle = (productId: number) => {
        // Мы можем только деактивировать, поэтому всегда отправляем is_active: false
        updateStatusMutation.mutate({productId, isActive: false});
    };

    const handleDelete = (id: number) => {
        if (window.confirm("Вы уверены, что хотите удалить этот товар? Это действие нельзя отменить.")) {
            deleteMutation.mutate(id);
        }
    };

    if (isLoading) {
        return <div className="text-white">Загрузка ваших товаров...</div>;
    }

    return (
        <div className="text-white">
            <h1 className="text-3xl font-bold mb-6">Мои товары</h1>
            <div className="overflow-hidden rounded-lg border border-slate-700">
                <table className="min-w-full">
                    <thead className="bg-slate-800 text-xs uppercase text-slate-400">
                    <tr>
                        <th className="p-4 text-left">Фото</th>
                        <th className="p-4 text-left">Название</th>
                        <th className="p-4 text-left">Категория</th>
                        <th className="p-4 text-left">Цена</th>
                        <th className="p-4 text-left">Запас</th>
                        <th className="p-4 text-left">Статус</th>
                        <th className="p-4 text-left">Действия</th>
                    </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                        {products?.map(product => (
                        <ProductRow
                            key={product.id}
                            product={product}
                            onStatusToggle={handleStatusToggle} // <-- Передаем новую функцию
                            onDelete={handleDelete}
                            isUpdatingStatus={updateStatusMutation.isPending && updateStatusMutation.variables?.productId === product.id}
                        />
                        ))}
                    </tbody>
                </table>
                {products?.length === 0 && (
                    <div className="p-8 text-center text-slate-400">
                        Вы еще не добавили ни одного товара.
                    </div>
                )}
            </div>
        </div>
    );
}