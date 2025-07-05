// src/components/ProductRow.tsx
import {Link} from "react-router-dom";
import {Edit, Trash2} from "lucide-react";
import type {Product} from "../pages/MyProductsPage";

interface ProductRowProps {
    product: Product;
    onStatusToggle: (id: number) => void;
    onDelete: (id: number) => void;
    isUpdatingStatus: boolean;
}

export function ProductRow({product, onStatusToggle, onDelete, isUpdatingStatus}: ProductRowProps) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL;
    const imageUrl = product.thumbnail ? `${baseUrl}${product.thumbnail}` : `https://ui-avatars.com/api/?name=${product.title.charAt(0)}&background=random`;

    return (
        <tr className="border-b border-slate-700 hover:bg-slate-800/50">
            <td className="p-4 align-middle">
                <img src={imageUrl} alt={product.title} className="h-12 w-12 rounded-md object-cover"/>
            </td>
            <td className="p-4 align-middle font-medium text-white">{product.title}</td>
            <td className="p-4 align-middle text-slate-300">{product.category?.title || 'Без категории'}</td>
            <td className="p-4 align-middle text-slate-300">{product.price} руб.</td>
            <td className="p-4 align-middle text-slate-300">{product.stock} шт.</td>
            <td className="p-4 align-middle">
                {/* --- НАЧАЛО ИСПРАВЛЕНИЙ --- */}
                <button
                    onClick={() => onStatusToggle(product.id)}
                    disabled={!product.is_active || isUpdatingStatus}
                    className={`px-3 py-1 text-xs rounded-full transition-colors font-semibold ${
                        product.is_active
                            ? 'bg-green-500/10 text-green-400 border border-green-500/30 hover:bg-green-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                    } disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:opacity-50`}
                >
                    {isUpdatingStatus ? '...' : (product.is_active ? 'Активен' : 'Скрыт')}
                </button>
                {/* --- КОНЕЦ ИСПРАВЛЕНИЙ --- */}
            </td>
            <td className="p-4 align-middle">
                <div className="flex items-center gap-3">
                    <Link to={`/dashboard/products/edit/${product.id}`} className="text-slate-400 hover:text-cyan-400">
                        <Edit size={16}/>
                    </Link>
                    <button onClick={() => onDelete(product.id)} className="text-slate-400 hover:text-red-400">
                        <Trash2 size={16}/>
                    </button>
                </div>
            </td>
        </tr>
    );
}