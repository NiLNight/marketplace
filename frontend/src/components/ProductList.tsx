import {useQuery} from '@tanstack/react-query';
import axios from 'axios';

// ... Типы Product и ApiResponse остаются без изменений ...
type Product = {
    id: number;
    title: string;
    price: string;
    price_with_discount: number;
    thumbnail: string | null; // ВАЖНО: Картинка может отсутствовать (быть null)
    rating_avg: number;
};

type ApiResponse = {
    count: number;
    results: Product[];
};

const fetchProducts = async (): Promise<ApiResponse> => {
    const {data} = await axios.get('http://localhost:8000/products/list/');
    return data;
};

export function ProductList() {
    const {data, isLoading, isError, error} = useQuery({
        queryKey: ['products'],
        queryFn: fetchProducts,
    });

    if (isLoading) { /* ... без изменений ... */
    }
    if (isError) {
        return (
            <div className="rounded-lg bg-red-900/20 p-6 text-center text-red-400">
                <h2 className="text-2xl font-bold">Ошибка при загрузке данных</h2>
                {/* Вот здесь мы используем переменную 'error' */}
                <p className="mt-2 font-mono bg-slate-800 p-2 rounded">{error.message}</p>
                <p className="mt-4 text-slate-300">
                    Убедитесь, что ваш бэкенд-сервер запущен на http://localhost:8000 и доступен.
                </p>
            </div>
        );
    }

    return (
        <div>
            <h2 className="mb-6 text-3xl font-bold text-white">Каталог товаров ({data?.count})</h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {data?.results.map(product => {
                    // Строим полный URL для изображения
                    const imageUrl = product.thumbnail
                        ? `${import.meta.env.VITE_API_BASE_URL}${product.thumbnail}`
                        : null;

                    return (
                        <div key={product.id}
                             className="overflow-hidden rounded-lg bg-slate-800 shadow-lg transition-transform hover:scale-105">
                            {/* Условие для отображения картинки или плейсхолдера */}
                            {imageUrl ? (
                                <img src={imageUrl} alt={product.title} className="aspect-square w-full object-cover"/>) : (
                                <div className="flex h-56 w-full items-center justify-center bg-slate-700">
                                    <span className="text-slate-500">Нет изображения</span>
                                </div>
                            )}
                            <div className="p-4">
                                <h3 className="truncate font-semibold text-white"
                                    title={product.title}>{product.title}</h3>
                                <div className="mt-4 flex items-baseline justify-between">
                                    <p className="text-xl font-bold text-green-400">{product.price_with_discount} руб.</p>
                                    <p className="text-sm text-slate-400 line-through">{product.price} руб.</p>
                                </div>
                                <p className="mt-2 text-xs text-slate-500">Рейтинг: {product.rating_avg.toFixed(1)} ★</p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}