// src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx'; // App теперь наш Layout
import './index.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ProductCatalogPage } from './pages/ProductCatalogPage.tsx'; // Импортируем страницу каталога
import { ProductDetailPage } from './pages/ProductDetailPage.tsx';

const queryClient = new QueryClient();

// Определяем маршруты. App - это родительский компонент для всех.
const router = createBrowserRouter([
  {
    path: "/",
    element: <App />, // App - это шаблон страницы
    children: [ // Вложенные маршруты, которые будут рендериться внутри <Outlet /> в App.tsx
      {
        index: true, // Это маршрут по умолчанию для родительского path: "/"
        element: <ProductCatalogPage />, // Показываем каталог на главной
      },
      {
        path: "products/:productId", // Путь относительно родителя
        element: <ProductDetailPage />, // Показываем детали
      },
      // Здесь можно добавлять другие страницы, например:
      // { path: "cart", element: <CartPage /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
);