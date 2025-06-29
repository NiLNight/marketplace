// src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {createBrowserRouter, RouterProvider, Navigate} from 'react-router-dom';
import {ProductCatalogPage} from './pages/ProductCatalogPage.tsx';
import {ProductDetailPage} from './pages/ProductDetailPage.tsx';
import {AppInitializer} from './components/AppInitializer.tsx'; // <-- Импортируем
import {CartPage} from './pages/CartPage.tsx';
import {Toaster} from 'react-hot-toast';
import {CheckoutPage} from './pages/CheckoutPage.tsx';
import {ProfileLayout} from './pages/ProfileLayout.tsx';
import {OrderHistoryPage} from './pages/OrderHistoryPage.tsx';
import {OrderDetailPage} from './pages/OrderDetailPage.tsx';
import {ProfilePage} from "./pages/ProfilePage.tsx";
import {WishlistPage} from "./pages/WishlistPage.tsx";

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
            {
                path: "cart",
                element: <CartPage/>,
            },
            {
                path: "checkout",
                element: <CheckoutPage/>
            },
            {
                path: "profile",
                element: <ProfileLayout/>,
                children: [
                    // Перенаправление с /profile на /profile/orders
                    {index: true, element: <Navigate to="/profile/details" replace/>},
                    {
                        path: "details", // <-- Новый маршрут
                        element: <ProfilePage/>,
                    },
                    {
                        path: "orders",
                        element: <OrderHistoryPage/>,
                    },
                    {
                        path: "orders/:orderId",
                        element: <OrderDetailPage/>,
                    },
                    {
                        path: "wishlist",
                        element: <WishlistPage/>
                    },
                ]
            }
        ],
    },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        {/* Оборачиваем все приложение в AppInitializer */}
        <AppInitializer>
            <QueryClientProvider client={queryClient}>
                <Toaster
                    position="top-center"
                    toastOptions={{
                        style: {
                            background: '#334155', // slate-700
                            color: '#fff',
                        },
                    }}
                />
                <RouterProvider router={router}/>
            </QueryClientProvider>
        </AppInitializer>
    </React.StrictMode>
);