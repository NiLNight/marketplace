// src/components/AppInitializer.tsx
import {useEffect, useState} from 'react';
import {useAuthStore} from '../stores/authStore';

export function AppInitializer({children}: { children: React.ReactNode }) {
    const checkAuth = useAuthStore((state) => state.checkAuth);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        const initialize = async () => {
            await checkAuth();
            setIsInitialized(true);
        };
        initialize();
    }, [checkAuth]);

    if (!isInitialized) {
        return <div className="flex h-screen items-center justify-center bg-slate-900 text-white">Загрузка
            приложения...</div>;
    }

    return <>{children}</>;
}