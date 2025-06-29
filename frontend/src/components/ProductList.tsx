// src/components/ProductList.tsx
import {useInfiniteQuery} from '@tanstack/react-query';
import {ImageIcon} from 'lucide-react';
import {Link} from 'react-router-dom';
import {useFilterStore, type FilterStore} from '../stores/useFilterStore';
import {useDebounce} from '../hooks/useDebounce';
import apiClient from '../api';
import {AddToWishlistButton} from './AddToWishlistButton'; // Убедитесь, что импорт есть

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
    next: string | null;
    results: Product[];
};

const fetchProducts = async ({pageParam = 1, filters}: {
    pageParam?: number,
    filters: FilterStore
}): Promise<ApiResponse> => {
    const params = new URLSearchParams();
    if (filters.category !== null) {
        params.append('category', String(filters.category));
    }
    if (filters.searchTerm) params.append('q', filters.searchTerm);
    if (filters.minPrice) params.append('price__gte', filters.minPrice);
    if (filters.maxPrice) params.append('price__lte', filters.maxPrice);
    if (filters.ordering) {
        params.append('ordering', filters.ordering);
    }
    params.append('page', String(pageParam));

    const {data} = await apiClient.get<ApiResponse>('/products/list/', {params});
    return data;
};

export function ProductList() {
    const filters = useFilterStore();
    const debouncedSearchTerm = useDebounce(filters.searchTerm, 500);
    const queryFilters = {...filters, searchTerm: debouncedSearchTerm};

    const {
        data,
        error,
        fetchNextPage,
        hasNextPage,
        isLoading,
        isFetchingNextPage,
        isError,
    } = useInfiniteQuery({
        queryKey: ['products', queryFilters],
        queryFn: ({pageParam}) => fetchProducts({pageParam, filters: queryFilters}),
        getNextPageParam: (lastPage) => {
            if (lastPage.next) {
                try {
                    const url = new URL(lastPage.next);
                    return Number(url.searchParams.get('page'));
                } catch {
                    return undefined;
                }
            }
            return undefined;
        },
        initialPageParam: 1,
    });

    if (isLoading) {
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

    const products = data?.pages.flatMap(page => page.results) ?? [];

    return (
        <div>
            <h2 className="mb-6 text-3xl font-bold text-white">Найдено товаров: {data?.pages[0]?.count ?? 0}</h2>
            {products.length === 0 && !isLoading && (
                <div className="text-center text-slate-400 p-10 bg-slate-800 rounded-lg">
                    <h3 className="text-xl font-semibold">Товары не найдены</h3>
                    <p className="mt-2">Попробуйте изменить параметры фильтра.</p>
                </div>
            )}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                {products.map((product: Product) => {
                    const baseUrl = import.meta.env.VITE_API_BASE_URL;
                    const imageUrl = product.thumbnail ? `${baseUrl}${product.thumbnail}` : null;
                    return (
                        <Link to={`/products/${product.id}`} key={product.id} className="group flex">
                            <div
                                className="flex w-full flex-col overflow-hidden rounded-lg bg-slate-800 shadow-lg transition-shadow duration-300 hover:shadow-cyan-500/30">

                                {/* --- НАЧАЛО ИСПРАВЛЕНИЙ --- */}
                                <div className="relative w-full aspect-[4/5] bg-slate-700">
                                    {imageUrl ? (
                                        <img src={imageUrl} alt={product.title}
                                             className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"/>
                                    ) : (
                                        <div className="flex h-full w-full items-center justify-center">
                                            <ImageIcon className="h-16 w-16 text-slate-500"/>
                                        </div>
                                    )}
                                    {/* Кнопка теперь ВНУТРИ этого блока */}
                                    <AddToWishlistButton productId={product.id}/>
                                </div>
                                {/* --- КОНЕЦ ИСПРАВЛЕНИЙ --- */}

                                <div className="flex flex-grow flex-col p-4">
                                    <h3 className="flex-grow font-semibold text-white"
                                        title={product.title}>{product.title}</h3>
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
            {hasNextPage && (
                <div className="mt-8 text-center">
                    <button
                        onClick={() => fetchNextPage()}
                        disabled={isFetchingNextPage}
                        className="rounded-md bg-slate-700 px-6 py-2 text-white transition hover:bg-slate-600 disabled:cursor-not-allowed"
                    >
                        {isFetchingNextPage ? 'Загрузка...' : 'Показать еще'}
                    </button>
                </div>
            )}
        </div>
    );
}