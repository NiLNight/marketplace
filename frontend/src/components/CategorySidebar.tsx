// src/components/CategorySidebar.tsx
import {useQuery} from '@tanstack/react-query';
import axios from 'axios';
import {useFilterStore} from '../stores/useFilterStore';
import {List, ChevronRight, ChevronDown} from 'lucide-react';
import {useState, useCallback, useMemo, useEffect} from 'react';

type Category = {
    slug: string;
    title: string;
    description?: string;
    parent: number | null;
    children: Category[];
};

// Маппинг slug → id на основе структуры категорий
const slugToIdMap: Record<string, number> = {
    'produkty': 1,
    'ovoshi': 2,
    'fructi': 3,
    'yagody': 4,
    'molochnye-produkty': 5,
    'myasnye-produkty': 6,
    'hlebobulochnye-izdeliya': 7,
    'napitki': 8,
    'sladosti': 9,
    'zamorozhennye-produkty': 10,
    'morozhenoe': 11
};

const fetchCategories = async (): Promise<Category[]> => {
    try {
        const {data} = await axios.get('http://localhost:8000/products/categories/');
        console.log('Fetched categories:', data);
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

function findCategoryPath(Categories: Category[], selectedId: number | null): number[] {
    if (selectedId === null) return [];
    const path: number[] = [];

    function dfs(nodes: Category[], currentPath: number[]): boolean {
        for (const node of nodes) {
            const nodeId = slugToIdMap[node.slug];
            if (nodeId === selectedId) {
                path.push(...currentPath, nodeId);
                return true;
            }
            if (node.children && node.children.length > 0) {
                if (dfs(node.children, [...currentPath, nodeId])) return true;
            }
        }
        return false;
    }

    dfs(Categories, []);
    return path;
}

function CategoryListItem({
                              category,
                              level,
                              expanded,
                              toggleExpand,
                              selectedCategory,
                              pathToSelected
                          }: {
    category: Category;
    level: number;
    expanded: Record<string, boolean>;
    toggleExpand: (slug: string) => void;
    selectedCategory: number | null;
    pathToSelected: number[];
}) {
    const {setCategory} = useFilterStore();
    console.log('CategoryListItem received category:', category);
    const categoryId = slugToIdMap[category.slug];
    const isActive = selectedCategory === categoryId;
    const isInPath = pathToSelected.includes(categoryId);
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expanded[category.slug] || false;

    return (
        <li key={category.slug}>
            <div className="flex items-center">
                {hasChildren && (
                    <button
                        type="button"
                        aria-label={isExpanded ? 'Свернуть' : 'Раскрыть'}
                        onClick={() => toggleExpand(category.slug)}
                        className="mr-1 text-slate-400 hover:text-cyan-400 focus:outline-none"
                        style={{marginLeft: `${level * 1.25}rem`}}
                    >
                        {isExpanded ? <ChevronDown size={16}/> : <ChevronRight size={16}/>}
                    </button>
                )}
                {!hasChildren && <span style={{marginLeft: `${level * 1.25 + 1.25}rem`}}/>}
                <button
                    onClick={() => {
                        if (category.slug === undefined) {
                            console.error('Category slug is undefined:', category);
                            return;
                        }
                        console.log('Category clicked:', category.slug, 'Mapped ID:', categoryId);
                        setCategory(categoryId);
                    }}
                    className={`flex-1 text-left rounded-md p-2 text-sm transition-colors ${
                        isActive
                            ? 'bg-cyan-500/20 font-semibold text-cyan-300'
                            : isInPath
                                ? 'bg-cyan-900/10 text-cyan-200'
                                : 'text-slate-300 hover:bg-slate-700'
                    }`}
                >
                    {category.title}
                </button>
            </div>
            {hasChildren && isExpanded && (
                <ul className="mt-1">
                    {category.children.map((child) => (
                        <li key={child.slug}>
                            <CategoryListItem
                                category={child}
                                level={level + 1}
                                expanded={expanded}
                                toggleExpand={toggleExpand}
                                selectedCategory={selectedCategory}
                                pathToSelected={pathToSelected}
                            />
                        </li>
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
        queryFn: fetchCategories
    });

    useEffect(() => {
        console.log('Current selected category:', selectedCategory);
    }, [selectedCategory]);

    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    const pathToSelected = useMemo(() =>
            categories ? findCategoryPath(categories, selectedCategory) : [],
        [categories, selectedCategory]
    );

    useMemo(() => {
        if (!categories || !selectedCategory) return;
        const path = findCategoryPath(categories, selectedCategory);
        if (path.length > 0) {
            setExpanded((prev) => {
                const next = {...prev};
                path.forEach((id) => {
                    next[id] = true;
                });
                return next;
            });
        }
    }, [categories, selectedCategory]);

    const toggleExpand = useCallback((slug: string) => {
        setExpanded((prev) => ({...prev, [slug]: !prev[slug]}));
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
                            onClick={() => {
                                console.log('All products clicked');
                                setCategory(null);
                            }}
                            className={`flex w-full items-center rounded-md p-2 text-sm transition-colors ${
                                selectedCategory === null ? 'bg-cyan-500/20 font-semibold text-cyan-300' : 'text-slate-300 hover:bg-slate-700'
                            }`}
                        >
                            <List className="mr-3 h-4 w-4"/>
                            Все товары
                        </button>
                    </li>
                    {categories?.map((category) => (
                        <li key={category.slug}>
                            <CategoryListItem
                                category={category}
                                level={0}
                                expanded={expanded}
                                toggleExpand={toggleExpand}
                                selectedCategory={selectedCategory}
                                pathToSelected={pathToSelected}
                            />
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    );
}