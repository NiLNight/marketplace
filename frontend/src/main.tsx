import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import {QueryClient, QueryClientProvider} from '@tanstack/react-query'
import {createBrowserRouter, RouterProvider} from 'react-router-dom'
import {ProductDetailPage} from './pages/ProductDetailPage.tsx' // Мы скоро создадим этот файл

// Создаем клиент для React Query
const queryClient = new QueryClient()

// Создаем наш роутер и определяем маршруты
const router = createBrowserRouter([
    {
        path: "/", // Главная страница
        element: <App/>, // Показывает наш компонент App с каталогом
    },
    {
        path: "/products/:productId", // Страница продукта с динамическим ID
        element: <ProductDetailPage/>, // Показывает страницу деталей
    },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            {/* Теперь мы используем RouterProvider вместо прямого рендера App */}
            <RouterProvider router={router}/>
        </QueryClientProvider>
    </React.StrictMode>,
)