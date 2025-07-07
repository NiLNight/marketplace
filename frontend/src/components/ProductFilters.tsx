// src/components/ProductFilters.tsx
import {useFilterStore} from '../stores/useFilterStore';

export function ProductFilters() {
    const {
        searchTerm, setSearchTerm,
        minPrice, setMinPrice,
        maxPrice, setMaxPrice,
        ordering, setOrdering
    } = useFilterStore();

    const inputStyles = "w-full rounded-md border-transparent bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500";

    return (
        <div className="flex flex-col gap-4">
            <input
                type="text"
                placeholder="Поиск по названию..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={inputStyles}
            />

            {/* --- НАЧАЛО ИЗМЕНЕНИЙ --- */}
            <div>
                {/* 1. Добавляем заголовок "Цена" */}
                <label className="block text-sm font-medium text-slate-300 mb-1">
                    Цена
                </label>
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        placeholder="от" // 2. Меняем плейсхолдер
                        value={minPrice}
                        onChange={(e) => setMinPrice(e.target.value)}
                        className={`${inputStyles} flex-1`}
                    />
                    <span className="text-slate-500">-</span>
                    <input
                        type="number"
                        placeholder="до" // 3. Меняем плейсхолдер
                        value={maxPrice}
                        onChange={(e) => setMaxPrice(e.target.value)}
                        className={`${inputStyles} flex-1`}
                    />
                </div>
            </div>
            {/* --- КОНЕЦ ИЗМЕНЕНИЙ --- */}

            <select
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
                className={inputStyles}
            >
                <option value="-popularity_score">По популярности</option>
                <option value="price">По возрастанию цены</option>
                <option value="-price">По убыванию цены</option>
                <option value="-rating_avg">По рейтингу</option>
                {searchTerm.trim() && <option value="">По релевантности</option>}
            </select>
        </div>
    );
}