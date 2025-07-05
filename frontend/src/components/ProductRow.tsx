// src/components/ProductRow.tsx
import { Link } from "react-router-dom";
import { Edit, Trash2 } from "lucide-react";
import type { Product } from "../pages/MyProductsPage"; // Импортируем тип

interface ProductRowProps {
    product: Product;
    onDelete: (id: number) => void;
}

export function ProductRow({ product, onDelete }: ProductRowProps) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL;
    const imageUrl = product.thumbnail ? `${baseUrl}${product.thumbnail}` : `https://ui-avatars.com/api/?name=${product.title.charAt(0)}&background=random`;

    return (
        <tr className="border-b border-slate-700 hover:bg-slate-800/50">
            <td className="p-4 align-middle">
                <img src={imageUrl} alt={product.title} className="h-12 w-12 rounded-md object-cover" />
            </td>
            <td className="p-4 align-middle font-medium text-white">{product.title}</td>
            <td className="p-4 align-middle text-slate-300">{product.category.title}</td>
            <td className="p-4 align-middle text-slate-300">{product.price} руб.</td>
            <td className="p-4 align-middle text-slate-300">{product.stock} шт.</td>
            <td className="p-4 align-middle">
                <span className={`px-2 py-1 text-xs rounded-full ${product.is_active ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                    {product.is_active ? 'Активен' : 'Скрыт'}
                </span>
            </td>
            <td className="p-4 align-middle">
                <div className="flex items-center gap-3">
                    <Link to={`/dashboard/products/edit/${product.id}`} className="text-slate-400 hover:text-cyan-400">
                        <Edit size={16} />
                    </Link>
                    <button onClick={() => onDelete(product.id)} className="text-slate-400 hover:text-red-400">
                        <Trash2 size={16} />
                    </button>
                </div>
            </td>
        </tr>
    );
}