// src/pages/ProductDetailPage.tsx
import {useQuery} from '@tanstack/react-query';
import {useParams} from 'react-router-dom';
import apiClient from '../api';
import {AddToCartButton} from '../components/AddToCartButton';
import {AddToWishlistButton} from '../components/AddToWishlistButton';
import {ReviewList} from '../components/ReviewList';
import { AddReviewForm } from '../components/AddReviewForm';
import { useAuthStore } from '../stores/authStore';
import { SortDropdown } from '../components/SortDropdown';
import { getImageUrl } from '../utils/url';

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
    has_user_reviewed: boolean;
};

const fetchProductById = async (productId: string): Promise<ProductDetail> => {
    const {data} = await apiClient.get(`/products/${productId}/`);
    return data;
};

export function ProductDetailPage() {
    const {productId} = useParams<{ productId: string }>();
    const { isLoggedIn } = useAuthStore();
    const numericProductId = Number(productId);

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

    const imageUrl = getImageUrl(product?.thumbnail);

    const hasReviewed = product.has_user_reviewed;

    return (
        <div className="min-h-screen bg-slate-900 p-8 text-white">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-4">{product.title}</h1>
                <p className="text-lg text-slate-400 mb-6">Категория: {product.category.title}</p>
                <div className="grid md:grid-cols-2 gap-8">
                    <div className="relative">
                        {imageUrl ? (
                            <img src={imageUrl} alt={product.title} className="w-full rounded-lg shadow-lg"/>
                        ) : (
                            <div
                                className="w-full h-96 bg-slate-800 rounded-lg flex items-center justify-center text-slate-500">Нет
                                изображения</div>
                        )}
                        <AddToWishlistButton productId={product.id}/>
                    </div>
                    <div className="flex flex-col">
                        <div className="mb-6">
                            <span
                                className="text-4xl font-bold text-green-400">{product.price_with_discount} руб.</span>
                            {parseFloat(product.discount) > 0 &&
                                <span className="ml-4 text-xl text-slate-500 line-through">{product.price} руб.</span>}
                        </div>
                        <p className="text-slate-300 flex-grow">{product.description}</p>
                        <div className="mt-6 pt-6 border-t border-slate-700 space-y-2">
                            <p>В наличии: <span
                                className="font-semibold">{product.stock > 0 ? `${product.stock} шт.` : 'Нет в наличии'}</span>
                            </p>
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

                <div className="mt-16"> {/* Большой отступ сверху */}
                    <h2 className="text-3xl font-bold mb-8 text-center text-white">Отзывы о товаре</h2>
                    <SortDropdown />
                    {isLoggedIn && !hasReviewed && (
                        <AddReviewForm productId={numericProductId} />
                    )}
                    {isLoggedIn && hasReviewed && (
                        <div className="p-4 mb-8 bg-green-900/50 text-green-300 rounded-lg text-center">
                            Вы уже оставили отзыв на этот товар. Спасибо!
                        </div>
                    )}
                    <ReviewList productId={product.id}/>
                </div>
            </div>
        </div>
    );
}