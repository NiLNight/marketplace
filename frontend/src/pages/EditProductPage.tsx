// src/pages/EditProductPage.tsx
import {useForm, type SubmitHandler} from 'react-hook-form';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';
import {useNavigate, useParams} from 'react-router-dom';
import {useEffect} from 'react';

// Типы
interface Category {
    id: number;
    title: string;
}

interface ProductData { // Для получения данных
    id: number;
    title: string;
    description: string;
    price: string;
    discount: string;
    stock: number;
    category: { id: number; };
    thumbnail: string | null;
}

interface ProductFormInputs { // Для формы
    title: string;
    description: string;
    price: number;
    discount?: number;
    stock: number;
    category: number;
    thumbnail?: FileList;
}

// --- Функции для API ---
const fetchProduct = async (id: string): Promise<ProductData> => {
    const {data} = await apiClient.get(`/products/${id}/`);
    return data;
};

const updateProduct = ({id, data}: { id: string; data: FormData }) => {
    return apiClient.patch(`/products/${id}/update/`, data, {
        headers: {'Content-Type': 'multipart/form-data'}
    });
};

const fetchCategories = async (): Promise<Category[]> => {
    const {data} = await apiClient.get('/products/categories/');
    const flattenCategories = (categories: any[], level = 0): Category[] => {
        let result: Category[] = [];
        for (const cat of categories) {
            result.push({id: cat.id, title: `${'— '.repeat(level)}${cat.title}`});
            if (cat.children) {
                result = result.concat(flattenCategories(cat.children, level + 1));
            }
        }
        return result;
    };
    return flattenCategories(data);
};

export function EditProductPage() {
    const {productId} = useParams<{ productId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const {register, handleSubmit, formState: {errors}, reset} = useForm<ProductFormInputs>();

    // 1. Загружаем данные редактируемого товара
    const {data: productData, isLoading: isLoadingProduct} = useQuery({
        queryKey: ['product', productId],
        queryFn: () => fetchProduct(productId!),
        enabled: !!productId,
    });

    // 2. Загружаем категории
    const {data: categories, isLoading: isLoadingCategories} = useQuery({
        queryKey: ['flatCategories'],
        queryFn: fetchCategories
    });

    // 3. Заполняем форму, когда данные о товаре загрузятся
    useEffect(() => {
        if (productData) {
            reset({
                title: productData.title,
                description: productData.description,
                price: parseFloat(productData.price),
                discount: parseFloat(productData.discount) || undefined,
                stock: productData.stock,
                category: productData.category.id,
            });
        }
    }, [productData, reset]);

    // 4. Мутация для отправки обновлений
    const mutation = useMutation({
        mutationFn: updateProduct,
        onSuccess: () => {
            toast.success('Товар успешно обновлен!');
            queryClient.invalidateQueries({queryKey: ['myProducts']});
            queryClient.invalidateQueries({queryKey: ['product', productId]});
            navigate('/dashboard/products');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Не удалось обновить товар.');
        }
    });

    const onSubmit: SubmitHandler<ProductFormInputs> = data => {
        const formData = new FormData();

        // Добавляем в FormData только измененные поля
        if (data.title !== productData?.title) formData.append('title', data.title);
        if (data.description !== productData?.description) formData.append('description', data.description);
        if (data.price !== parseFloat(productData?.price || '0')) formData.append('price', String(data.price));
        if (data.discount !== parseFloat(productData?.discount || '0')) formData.append('discount', String(data.discount || 0));
        if (data.stock !== productData?.stock) formData.append('stock', String(data.stock));
        if (data.category !== productData?.category.id) formData.append('category', String(data.category));
        if (data.thumbnail?.[0]) {
            formData.append('thumbnail', data.thumbnail[0]);
        }

        // Если изменений нет, не отправляем запрос
        if (Array.from(formData.keys()).length === 0) {
            toast.custom('Вы не внесли никаких изменений.');
            return;
        }

        mutation.mutate({id: productId!, data: formData});
    };

    if (isLoadingProduct) {
        return <div className="text-white">Загрузка данных товара...</div>;
    }

    return (
        <div className="text-white">
            <h1 className="text-3xl font-bold mb-6">Редактирование товара</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-2xl">
                {/* Форма полностью аналогична CreateProductPage, поэтому я сокращу код */}
                <div>
                    <label>Название</label>
                    <input {...register('title', {required: 'Название обязательно'})}
                           className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>}
                </div>
                <div>
                    <label>Описание</label>
                    <textarea {...register('description', {required: 'Описание обязательно'})} rows={5}
                              className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>}
                </div>
                <div>
                    <label>Категория</label>
                    <select {...register('category', {required: 'Выберите категорию'})} disabled={isLoadingCategories}
                            className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white">
                        {categories?.map(cat => <option key={cat.id} value={cat.id}>{cat.title}</option>)}
                    </select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <label>Цена (руб.)</label>
                        <input {...register('price', {required: true, valueAsNumber: true, min: 0})} type="number"
                               step="0.01"
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label>Скидка (%)</label>
                        <input {...register('discount', {valueAsNumber: true, min: 0, max: 100})} type="number"
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label>Запас (шт.)</label>
                        <input {...register('stock', {required: true, valueAsNumber: true, min: 0})} type="number"
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                </div>
                <div>
                    <label>Новое изображение (оставьте пустым, чтобы не менять)</label>
                    <input type="file" {...register('thumbnail')}
                           className="mt-1 block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-cyan-400 hover:file:bg-slate-600"/>
                </div>

                <button type="submit" disabled={mutation.isPending}
                        className="rounded-md bg-cyan-600 px-6 py-2 text-white transition hover:bg-cyan-700 disabled:opacity-50">
                    {mutation.isPending ? 'Сохранение...' : 'Сохранить изменения'}
                </button>
            </form>
        </div>
    );
}