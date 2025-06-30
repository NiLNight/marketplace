// src/components/SortDropdown.tsx
import { useReviewFilterStore } from '../stores/useReviewFilterStore';

export function SortDropdown() {
    const { ordering, setOrdering } = useReviewFilterStore();

    return (
        <div className="flex justify-end mb-4">
            <select
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
                className="rounded-md border-slate-600 bg-slate-700 p-2 text-sm text-white focus:border-cyan-500 focus:ring-cyan-500"
            >
                <option value="-created">Сначала новые</option>
                <option value="created">Сначала старые</option>
                <option value="-likes">По полезности</option>
                <option value="-value">Сначала с высокой оценкой</option>
                <option value="value">Сначала с низкой оценкой</option>
            </select>
        </div>
    );
}