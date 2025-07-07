// src/pages/ProductCatalogPage.tsx
import {CategorySidebar} from '../components/CategorySidebar';
import {ProductFilters} from '../components/ProductFilters';
import {ProductList} from '../components/ProductList';

export function ProductCatalogPage() {
return (
    <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
      <div className="md:col-span-1">
        {/* Обертка для "липкости" теперь содержит оба компонента */}
        <div className="sticky top-8 space-y-8"> {/* Добавляем space-y-8 для отступа между блоками */}
            <CategorySidebar />
            <ProductFilters /> {/* <-- 1. Переносим фильтры сюда */}
        </div>
      </div>

      <div className="md:col-span-3">
        {/* 2. Убираем фильтры отсюда */}
        <ProductList />
      </div>
    </div>
  );
}