// src/pages/DashboardLayout.tsx
import {NavLink, Outlet} from "react-router-dom";
import {PlusCircle, Package, Store} from "lucide-react";

const activeLinkClass = "flex items-center gap-3 rounded-lg bg-slate-700 px-3 py-2 text-white";
const inactiveLinkClass = "flex items-center gap-3 rounded-lg px-3 py-2 text-slate-400 hover:text-white";

export function DashboardLayout() {
    return (
        <div className="grid w-full gap-8 md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">

            <div className="hidden md:block">
                <div className="sticky top-8 space-y-4">
                    <div className="flex items-center gap-2 font-semibold text-white px-2 lg:px-4">
                        <Store/>
                        <span>Мой магазин</span>
                    </div>
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
                    </nav>
                </div>
            </div>

            <main>
                <Outlet/>
            </main>
        </div>
    );
}