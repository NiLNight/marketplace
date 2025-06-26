// src/pages/ProductCatalogPage.tsx
import { CategorySidebar } from '../components/CategorySidebar';
import { ProductFilters } from '../components/ProductFilters';
import { ProductList } from '../components/ProductList';

export function ProductCatalogPage() {
  return (
    <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
      <div className="md:col-span-1">
        <CategorySidebar />
      </div>
      <div className="md:col-span-3">
        <ProductFilters />
        <ProductList />
      </div>
    </div>
  );
}