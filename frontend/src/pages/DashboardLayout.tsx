// src/pages/DashboardLayout.tsx
import {NavLink, Outlet} from "react-router-dom";
import {PlusCircle, Package, Store} from "lucide-react";

const activeLinkClass = "flex items-center gap-3 rounded-lg bg-slate-700 px-3 py-2 text-white";
const inactiveLinkClass = "flex items-center gap-3 rounded-lg px-3 py-2 text-slate-400 hover:text-white";

export function DashboardLayout() {
    return (
        <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
            <div className="hidden border-r border-slate-700 bg-slate-800/40 md:block">
                <div className="flex h-full max-h-screen flex-col gap-2">
                    <div className="flex h-14 items-center border-b border-slate-700 px-4 lg:h-[60px] lg:px-6">
                        <span className="flex items-center gap-2 font-semibold text-white">
                            <Store/>
                            <span>Мой магазин</span>
                        </span>
                    </div>
                    <div className="flex-1">
                        <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
                            <NavLink to="/dashboard/products" end
                                     className={({isActive}) => isActive ? activeLinkClass : inactiveLinkClass}>
                                <Package className="h-4 w-4"/>
                                Мои товары
                            </NavLink>
                            <NavLink to="/dashboard/products/create"
                                     className={({isActive}) => isActive ? activeLinkClass : inactiveLinkClass}>
                                <PlusCircle className="h-4 w-4"/>
                                Добавить товар
                            </NavLink>
                            {/* Ссылка на статистику (пока заглушка) */}
                        </nav>
                    </div>
                </div>
            </div>
            <div className="flex flex-col">
                <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                    <Outlet/>
                </main>
            </div>
        </div>
    );
}