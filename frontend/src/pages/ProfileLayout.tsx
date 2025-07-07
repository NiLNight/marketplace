// src/pages/ProfileLayout.tsx
import {NavLink, Outlet} from "react-router-dom";
import {List, User, Heart} from "lucide-react";

const activeLinkClass = "flex items-center gap-3 rounded-lg bg-slate-700 px-3 py-2 text-white";
const inactiveLinkClass = "flex items-center gap-3 rounded-lg px-3 py-2 text-slate-400 hover:text-white";

export function ProfileLayout() {
    return (
        // 1. Возвращаем простую grid-структуру
        <div className="grid w-full gap-8 md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">

            {/* 2. Левая колонка */}
            <div className="hidden md:block">
                {/* 3. Обертка с position: sticky, как в каталоге */}
                <div className="sticky top-8 space-y-4">
                    <div className="flex items-center gap-2 font-semibold text-white px-2 lg:px-4">
                        <User/>
                        <span>Личный кабинет</span>
                    </div>
                    <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
                        <NavLink to="/profile/details"
                                 className={({isActive}) => isActive ? activeLinkClass : inactiveLinkClass}>
                            <User className="h-4 w-4"/>
                            Мой профиль
                        </NavLink>
                        <NavLink to="/profile/orders"
                                 className={({isActive}) => isActive ? activeLinkClass : inactiveLinkClass}>
                            <List className="h-4 w-4"/>
                            Мои заказы
                        </NavLink>
                        <NavLink to="/profile/wishlist"
                                 className={({isActive}) => isActive ? activeLinkClass : inactiveLinkClass}>
                            <Heart className="h-4 w-4"/>
                            Список желаний
                        </NavLink>
                    </nav>
                </div>
            </div>

            {/* 4. Правая колонка с основным контентом */}
            <main className="p-4 lg:p-6">
                <Outlet/>
            </main>
        </div>
    );
}