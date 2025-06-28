// src/components/ProductDetailPage.tsx
import {useQuery} from '@tanstack/react-query';
import {useParams} from 'react-router-dom';
import apiClient from '../api'; // <-- Используем apiClient
import { AddToCartButton } from '../components/AddToCartButton';

// Тип на основе схемы ProductDetail из вашего OpenAPI
type ProductDetail = {
    id: number;
    title: string;
    description: string;
    price: string;
    price_with_discount: number;
    stock: number;
    discount: string;
    thumbnail: string | null;
    rating_avg: number;
    owner: string;
    category: {
        id: number;
        title: string;
        slug: string;
    };
};

const fetchProductById = async (productId: string): Promise<ProductDetail> => {
    const {data} = await apiClient.get(`/products/${productId}/`); // <-- Используем apiClient
    return data;
};

export function ProductDetailPage() {
    const {productId} = useParams<{ productId: string }>();

    const {data: product, isLoading, isError, error} = useQuery({
        queryKey: ['product', productId],
        queryFn: () => fetchProductById(productId!),
        enabled: !!productId,
    });

    if (isLoading) {
        return <div className="text-white text-center p-10">Загрузка данных о товаре...</div>;
    }

    if (isError) {
        return <div className="text-red-500 text-center p-10">Ошибка: {error.message}</div>;
    }

    if (!product) {
        return <div className="text-white text-center p-10">Товар не найден.</div>;
    }

    const imageUrl = product.thumbnail
        ? `${import.meta.env.VITE_API_BASE_URL}${product.thumbnail}`
        : null;

    return (
        <div className="min-h-screen bg-slate-900 p-8 text-white">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-4">{product.title}</h1>
                <p className="text-lg text-slate-400 mb-6">Категория: {product.category.title}</p>
                <div className="grid md:grid-cols-2 gap-8">
                    <div>
                        {imageUrl ? (
                            <img src={imageUrl} alt={product.title} className="w-full rounded-lg shadow-lg"/>
                        ) : (
                            <div
                                className="w-full h-96 bg-slate-800 rounded-lg flex items-center justify-center text-slate-500">Нет
                                изображения</div>
                        )}
                    </div>
                    <div className="flex flex-col">
                        <div className="mb-6">
                            <span
                                className="text-4xl font-bold text-green-400">{product.price_with_discount} руб.</span>
                            <span className="ml-4 text-xl text-slate-500 line-through">{product.price} руб.</span>
                        </div>
                        <p className="text-slate-300 flex-grow">{product.description}</p>
                        <div className="mt-6 pt-6 border-t border-slate-700">
                            <p>В наличии: <span className="font-semibold">{product.stock} шт.</span></p>
                            <p>Рейтинг: <span className="font-semibold">{product.rating_avg.toFixed(1)} ★</span></p>
                            <p>Продавец: <span className="font-semibold">{product.owner}</span></p>
                        </div>
                        <div className="mt-auto pt-6">
                            {product.stock > 0 ? (
                                <AddToCartButton productId={product.id}/>
                            ) : (
                                <button disabled
                                        className="w-full rounded-md bg-slate-700 px-4 py-2 text-slate-400 cursor-not-allowed">Нет
                                    в наличии</button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}