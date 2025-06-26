// src/components/ProductList.tsx
import {useQuery} from '@tanstack/react-query';
import axios from 'axios';
import {ImageIcon} from 'lucide-react';
import {Link} from 'react-router-dom';
import {useFilterStore, type FilterStore} from '../stores/useFilterStore';
import {useDebounce} from '../hooks/useDebounce';

type Product = {
    id: number;
    title: string;
    price: string;
    price_with_discount: number;
    thumbnail: string | null;
    rating_avg: number;
};

type ApiResponse = {
    count: number;
    results: Product[];
};

const fetchProducts = async (filters: FilterStore): Promise<ApiResponse> => {
    const params = new URLSearchParams();
    if (filters.category !== null && filters.category !== undefined && !isNaN(filters.category)) {
        params.append('category', String(filters.category));
    }
    if (filters.searchTerm) params.append('q', filters.searchTerm);
    if (filters.minPrice) params.append('price__gte', filters.minPrice);
    if (filters.maxPrice) params.append('price__lte', filters.maxPrice);
    if (filters.ordering) params.append('ordering', filters.ordering);

    console.log('Request URL:', `http://localhost:8000/products/list/?${params.toString()}`);
    const {data} = await axios.get(`http://localhost:8000/products/list/`, {params});
    return data;
};

export function ProductList() {
    const filters = useFilterStore();
    console.log('Filters in ProductList:', filters);
    const debouncedSearchTerm = useDebounce(filters.searchTerm, 500);
    const queryFilters = {...filters, searchTerm: debouncedSearchTerm};

    const {data, isLoading, isError, error, isPlaceholderData} = useQuery({
        queryKey: ['products', queryFilters],
        queryFn: () => fetchProducts(queryFilters),
        placeholderData: (previousData) => previousData,
    });

    if (isLoading && !isPlaceholderData) {
        return <div className="text-xl text-center text-white p-10">Загрузка товаров...</div>;
    }

    if (isError) {
        return (
            <div className="rounded-lg bg-red-900/20 p-6 text-center text-red-400">
                <h2 className="text-2xl font-bold">Ошибка при загрузке данных</h2>
                <p className="mt-2 font-mono bg-slate-800 p-2 rounded">{error.message}</p>
                <p className="mt-4 text-slate-300">Убедитесь, что ваш бэкенд-сервер запущен.</p>
            </div>
        );
    }

    if (!data) {
        return <div className="text-center text-slate-400 p-10">Нет данных для отображения.</div>;
    }

    return (
        <div style={{opacity: isPlaceholderData ? 0.6 : 1, transition: 'opacity 0.2s ease-in-out'}}>
            <h2 className="mb-6 text-3xl font-bold text-white">Найдено товаров: {data.count}</h2>
            {data.results.length === 0 && !isLoading && (
                <div className="text-center text-slate-400 p-10 bg-slate-800 rounded-lg">
                    <h3 className="text-xl font-semibold">Товары не найдены</h3>
                    <p className="mt-2">Попробуйте изменить параметры фильтра.</p>
                </div>
            )}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                {data.results.map((product: Product) => {
                    const baseUrl = import.meta.env.VITE_API_BASE_URL;
                    const imageUrl = product.thumbnail ? `${baseUrl}${product.thumbnail}` : null;

                    return (
                        <Link to={`/products/${product.id}`} key={product.id} className="group flex">
                            <div
                                className="flex w-full flex-col overflow-hidden rounded-lg bg-slate-800 shadow-lg transition-shadow duration-300 hover:shadow-cyan-500/30"
                            >
                                <div className="relative w-full aspect-[4/5] bg-slate-700">
                                    {imageUrl ? (
                                        <img
                                            src={imageUrl}
                                            alt={product.title}
                                            className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="flex h-full w-full items-center justify-center">
                                            <ImageIcon className="h-16 w-16 text-slate-500"/>
                                        </div>
                                    )}
                                </div>
                                <div className="flex flex-grow flex-col p-4">
                                    <h3 className="flex-grow font-semibold text-white" title={product.title}>
                                        {product.title}
                                    </h3>
                                    <div className="mt-4 flex items-baseline justify-between">
                                        <p className="text-xl font-bold text-green-400">{product.price_with_discount} руб.</p>
                                        {parseFloat(product.price) !== product.price_with_discount && (
                                            <p className="text-sm text-slate-400 line-through">{product.price} руб.</p>
                                        )}
                                    </div>
                                    <p className="mt-2 text-xs text-slate-500">Рейтинг: {product.rating_avg.toFixed(1)} ★</p>
                                </div>
                            </div>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}