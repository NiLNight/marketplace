// src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {createBrowserRouter, RouterProvider} from 'react-router-dom';
import {ProductCatalogPage} from './pages/ProductCatalogPage.tsx';
import {ProductDetailPage} from './pages/ProductDetailPage.tsx';
import {AppInitializer} from './components/AppInitializer.tsx'; // <-- Импортируем

const queryClient = new QueryClient();

const router = createBrowserRouter([
    {
        path: "/",
        element: <App/>,
        children: [
            {
                index: true,
                element: <ProductCatalogPage/>,
            },
            {
                path: "products/:productId",
                element: <ProductDetailPage/>,
            },
        ],
    },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        {/* Оборачиваем все приложение в AppInitializer */}
        <AppInitializer>
            <QueryClientProvider client={queryClient}>
                <RouterProvider router={router}/>
            </QueryClientProvider>
        </AppInitializer>
    </React.StrictMode>
);