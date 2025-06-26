import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { ImageIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

// Тип для одного товара, основанный на вашей схеме ProductList
type Product = {
  id: number;
  title: string;
  price: string;
  price_with_discount: number;
  thumbnail: string | null;
  rating_avg: number;
};

// Тип для ответа от API (стандартная пагинация DRF)
type ApiResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
};

// Асинхронная функция для получения данных
const fetchProducts = async (): Promise<ApiResponse> => {
  const { data } = await axios.get('http://localhost:8000/products/list/');
  return data;
};

export function ProductList() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
  });

  if (isLoading) {
    return <div className="text-xl text-center text-white">Загрузка товаров...</div>;
  }

  if (isError) {
    return (
      <div className="rounded-lg bg-red-900/20 p-6 text-center text-red-400">
        <h2 className="text-2xl font-bold">Ошибка при загрузке данных</h2>
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
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data?.results.map(product => {
          const baseUrl = import.meta.env.VITE_API_BASE_URL;
          const imageUrl = product.thumbnail
            ? `${baseUrl}${product.thumbnail}`
            : null;

          return (
            <Link to={`/products/${product.id}`} key={product.id} className="group flex">
              <div className="flex w-full flex-col overflow-hidden rounded-lg bg-slate-800 shadow-lg transition-shadow duration-300 hover:shadow-cyan-500/30">
                {/* --- ИЗМЕНЕНИЕ ИМЕННО ЗДЕСЬ --- */}
                {/* Вместо h-56 мы используем aspect-[4/5] для вертикальной ориентации */}
                <div className="relative w-full aspect-[4/5] bg-slate-700">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={product.title}
                      className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <ImageIcon className="h-16 w-16 text-slate-500" />
                    </div>
                  )}
                </div>
                <div className="flex flex-grow flex-col p-4">
                  <h3 className="flex-grow font-semibold text-white" title={product.title}>
                    {product.title}
                  </h3>
                  <div className="mt-4 flex items-baseline justify-between">
                    <p className="text-xl font-bold text-green-400">{product.price_with_discount} руб.</p>
                    {product.price !== product.price_with_discount.toString() && (
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