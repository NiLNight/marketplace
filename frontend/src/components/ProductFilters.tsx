import { useFilterStore } from '../stores/useFilterStore';

export function ProductFilters() {
  const {
    searchTerm, setSearchTerm,
    minPrice, setMinPrice,
    maxPrice, setMaxPrice,
    ordering, setOrdering
  } = useFilterStore();

  return (
    <div className="mb-6 grid grid-cols-1 gap-4 rounded-lg bg-slate-800 p-4 sm:grid-cols-2 md:grid-cols-4">
      <input
        type="text"
        placeholder="Поиск по названию..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="col-span-1 rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500 sm:col-span-2 md:col-span-1"
      />
      <input
        type="number"
        placeholder="Цена от"
        value={minPrice}
        onChange={(e) => setMinPrice(e.target.value)}
        className="rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
      <input
        type="number"
        placeholder="Цена до"
        value={maxPrice}
        onChange={(e) => setMaxPrice(e.target.value)}
        className="rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
      <select
        value={ordering}
        onChange={(e) => setOrdering(e.target.value)}
        className="rounded-md border-slate-600 bg-slate-700 p-2 text-white focus:border-cyan-500 focus:ring-cyan-500"
      >
        <option value="-popularity_score">По популярности</option>
        <option value="price">По возрастанию цены</option>
        <option value="-price">По убыванию цены</option>
        <option value="-rating_avg">По рейтингу</option>
      </select>
    </div>
  );
}