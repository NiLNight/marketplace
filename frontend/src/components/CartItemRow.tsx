// src/components/CartItemRow.tsx
import {Link} from "react-router-dom";
import {Trash2, Plus, Minus} from "lucide-react";
import {useCartStore, type CartItem} from "../stores/useCartStore";
import {useDebounce} from "../hooks/useDebounce";
import {useEffect, useState} from "react";

interface CartItemRowProps {
    item: CartItem;
}

export function CartItemRow({item}: CartItemRowProps) {
    const {updateItemQuantity, removeFromCart} = useCartStore();
    const [quantity, setQuantity] = useState(item.quantity);

    // Используем debounce, чтобы не отправлять запрос на каждое нажатие "+"/"-"
    const debouncedQuantity = useDebounce(quantity, 500);

    useEffect(() => {
        // Если реальное кол-во в пропсах и локальное debounced-значение отличаются, отправляем запрос
        if (debouncedQuantity !== item.quantity) {
            updateItemQuantity(item.product.id, debouncedQuantity);
        }
    }, [debouncedQuantity, item.product.id, item.quantity, updateItemQuantity]);

    const handleIncrement = () => {
        if (quantity < 20) {
            setQuantity(q => q + 1);
        }
    };

    const handleDecrement = () => {
        if (quantity > 1) {
            setQuantity(q => q - 1);
        }
    };

    return (
        <div className="flex items-center gap-4 rounded-lg bg-slate-800 p-4">
            <img
                src={item.product.thumbnail ? `${import.meta.env.VITE_API_BASE_URL}${item.product.thumbnail}` : ''}
                alt={item.product.title}
                className="h-24 w-24 rounded-md object-cover"
            />
            <div className="flex-grow">
                <Link to={`/products/${item.product.id}`} className="font-semibold hover:underline">
                    {item.product.title}
                </Link>
            </div>

            {/* Блок управления количеством */}
            <div className="flex items-center gap-2 rounded-md border border-slate-700 p-1">
                <button onClick={handleDecrement} className="p-1 text-slate-400 hover:text-white"><Minus size={16}/>
                </button>
                <span className="w-8 text-center font-bold">{quantity}</span>
                <button onClick={handleIncrement} className="p-1 text-slate-400 hover:text-white"><Plus size={16}/>
                </button>
            </div>

            <div className="w-32 text-right">
                <p className="font-bold">{(item.product.price_with_discount * quantity).toFixed(2)} руб.</p>
                <p className="text-sm text-slate-500">{quantity} x {item.product.price_with_discount} руб.</p>
            </div>

            <button onClick={() => removeFromCart(item.product.id)}
                    className="text-slate-500 transition hover:text-red-500">
                <Trash2 size={20}/>
            </button>
        </div>
    );
}