// src/components/CategorySidebar.tsx
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useFilterStore } from '../stores/filterStore';
import { List } from 'lucide-react'; // Иконка для "Всех товаров"

// 1. Описываем типы данных, которые приходят с бэкенда
type Category = {
  id: number;
  title: string;
  children: Category[];
};

// 2. Функция для загрузки данных
const fetchCategories = async (): Promise<Category[]> => {
  const { data } = await axios.get('http://localhost:8000/products/categories/');
  return data;
};

// 3. Рекурсивный компонент для отображения одного элемента списка (и его детей)
function CategoryListItem({ category, level }: { category: Category; level: number }) {
  const { activeCategoryId, setActiveCategoryId } = useFilterStore();
  const isActive = activeCategoryId === category.id;

  return (
    <li>
      <button
        onClick={() => setActiveCategoryId(category.id)}
        className={`w-full text-left rounded-md p-2 text-sm transition-colors ${
          isActive ? 'bg-cyan-500/20 font-semibold text-cyan-300' : 'text-slate-300 hover:bg-slate-700'
        }`}
        style={{ paddingLeft: `${1 + level * 1.25}rem` }}
      >
        {category.title}
      </button>
      {category.children?.length > 0 && (
        <ul className="mt-1">
          {category.children.map((child) => (
            <CategoryListItem key={child.id} category={child} level={level + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

// 4. Основной компонент сайдбара
export function CategorySidebar() {
  const { activeCategoryId, setActiveCategoryId } = useFilterStore();
  const { data: categories, isLoading, isError } = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories
  });

  if (isLoading) return <div className="p-4 text-slate-400">Загрузка категорий...</div>;
  if (isError) return <div className="p-4 text-red-500">Ошибка загрузки.</div>;

  return (
    <aside className="w-full rounded-lg bg-slate-800 p-4">
      <h2 className="mb-4 text-xl font-bold text-white">Категории</h2>
      <nav>
        <ul className="space-y-1">
          {/* Кнопка "Все товары" */}
          <li>
            <button
              onClick={() => setActiveCategoryId(null)}
              className={`flex w-full items-center rounded-md p-2 text-sm transition-colors ${
                !activeCategoryId ? 'bg-cyan-500/20 font-semibold text-cyan-300' : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              <List className="mr-3 h-4 w-4" />
              Все товары
            </button>
          </li>
          {/* Рендерим категории */}
          {categories?.map((category) => (
            <CategoryListItem key={category.id} category={category} level={0} />
          ))}
        </ul>
      </nav>
    </aside>
  );
}