// src/components/CategorySidebar.tsx

import {useQuery} from '@tanstack/react-query';
import axios from 'axios';
import {useFilterStore} from '../stores/useFilterStore';
import {List, ChevronRight, ChevronDown} from 'lucide-react';
import {useState, useCallback, useMemo} from 'react';

// 1. Обновляем тип, добавляем id
type Category = {
    id: number; // <-- Добавили!
    slug: string;
    title: string;
    description?: string;
    parent: number | null;
    children: Category[];
};

const fetchCategories = async (): Promise<Category[]> => {
    // Давайте сразу перенесем URL в переменную окружения
    const apiUrl = `${import.meta.env.VITE_API_BASE_URL}/products/categories/`;
    try {
        const {data} = await axios.get(apiUrl);
        if (!Array.isArray(data)) {
            console.error('Expected an array, got:', data);
            return [];
        }
        return data;
    } catch (error) {
        console.error('Error fetching categories:', error);
        throw error;
    }
};

// 3. Упрощаем функцию поиска пути, теперь она работает с id
function findCategoryPath(categories: Category[], selectedId: number | null): number[] {
    if (selectedId === null) return [];
    const path: number[] = [];

    function dfs(nodes: Category[], currentPath: number[]): boolean {
        for (const node of nodes) {
            if (node.id === selectedId) {
                path.push(...currentPath, node.id);
                return true;
            }
            if (node.children && node.children.length > 0) {
                if (dfs(node.children, [...currentPath, node.id])) {
                    return true;
                }
            }
        }
        return false;
    }

    dfs(categories, []);
    return path;
}


function CategoryListItem({
                              category,
                              level,
                              expanded,
                              toggleExpand,
                              selectedCategory,
                              pathToSelected,
                          }: {
    category: Category;
    level: number;
    expanded: Record<number, boolean>; // Используем id в качестве ключа
    toggleExpand: (id: number) => void;
    selectedCategory: number | null;
    pathToSelected: number[];
}) {
    const {setCategory} = useFilterStore();
    const isActive = selectedCategory === category.id;
    const isInPath = pathToSelected.includes(category.id);
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expanded[category.id] || isInPath; // Категория раскрыта, если она в пути к выбранной

    return (
        <li key={category.id}>
            <div className="flex items-center">
                {hasChildren && (
                    <button
                        type="button"
                        aria-label={isExpanded ? 'Свернуть' : 'Раскрыть'}
                        onClick={() => toggleExpand(category.id)}
                        className="mr-1 text-slate-400 hover:text-cyan-400 focus:outline-none"
                        style={{marginLeft: `${level * 1.25}rem`}}
                    >
                        {isExpanded ? <ChevronDown size={16}/> : <ChevronRight size={16}/>}
                    </button>
                )}
                {!hasChildren && <span style={{marginLeft: `${level * 1.25 + 1.25}rem`}}/>}
                <button
                    onClick={() => setCategory(category.id)} // <--- Передаем сразу id
                    className={`flex-1 text-left rounded-md p-2 text-sm transition-colors ${
                        isActive
                            ? 'bg-cyan-500/20 font-semibold text-cyan-300'
                            : 'text-slate-300 hover:bg-slate-700'
                    }`}
                >
                    {category.title}
                </button>
            </div>
            {hasChildren && isExpanded && (
                <ul className="mt-1">
                    {category.children.map((child) => (
                        <CategoryListItem
                            key={child.id}
                            category={child}
                            level={level + 1}
                            expanded={expanded}
                            toggleExpand={toggleExpand}
                            selectedCategory={selectedCategory}
                            pathToSelected={pathToSelected}
                        />
                    ))}
                </ul>
            )}
        </li>
    );
}

export function CategorySidebar() {
    const {category: selectedCategory, setCategory} = useFilterStore();
    const {data: categories, isLoading, isError} = useQuery({
        queryKey: ['categories'],
        queryFn: fetchCategories,
    });

    const [expanded, setExpanded] = useState<Record<number, boolean>>({});

    const pathToSelected = useMemo(
        () => (categories ? findCategoryPath(categories, selectedCategory) : []),
        [categories, selectedCategory]
    );

    const toggleExpand = useCallback((id: number) => {
        setExpanded((prev) => ({...prev, [id]: !prev[id]}));
    }, []);


    if (isLoading) return <div className="p-4 text-slate-400">Загрузка категорий...</div>;
    if (isError) return <div className="p-4 text-red-500">Ошибка загрузки.</div>;

    return (
        <aside className="w-full rounded-lg bg-slate-800 p-4">
            <h2 className="mb-4 text-xl font-bold text-white">Категории</h2>
            <nav>
                <ul className="space-y-1">
                    <li>
                        <button
                            onClick={() => setCategory(null)}
                            className={`flex w-full items-center rounded-md p-2 text-sm transition-colors ${
                                selectedCategory === null
                                    ? 'bg-cyan-500/20 font-semibold text-cyan-300'
                                    : 'text-slate-300 hover:bg-slate-700'
                            }`}
                        >
                            <List className="mr-3 h-4 w-4"/>
                            Все товары
                        </button>
                    </li>
                    {categories?.map((category) => (
                        <CategoryListItem
                            key={category.id}
                            category={category}
                            level={0}
                            expanded={expanded}
                            toggleExpand={toggleExpand}
                            selectedCategory={selectedCategory}
                            pathToSelected={pathToSelected}
                        />
                    ))}
                </ul>
            </nav>
        </aside>
    );
}