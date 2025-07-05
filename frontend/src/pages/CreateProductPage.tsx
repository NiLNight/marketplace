// src/pages/CreateProductPage.tsx
import { useForm, type SubmitHandler } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

// Типы
interface Category {
    id: number;
    title: string;
}
interface ProductFormInputs {
    title: string;
    description: string;
    price: number;
    discount?: number;
    stock: number;
    category: number;
    thumbnail: FileList;
}

// Функции для API
const createProduct = (data: FormData) => apiClient.post('/products/create/', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
});
const fetchCategories = async (): Promise<Category[]> => {
    const { data } = await apiClient.get('/products/categories/');
    const flattenCategories = (categories: any[], level = 0): Category[] => {
        let result: Category[] = [];
        for (const cat of categories) {
            result.push({ id: cat.id, title: `${'— '.repeat(level)}${cat.title}` });
            if (cat.children && cat.children.length > 0) {
                result = result.concat(flattenCategories(cat.children, level + 1));
            }
        }
        return result;
    };
    return flattenCategories(data);
};

export function CreateProductPage() {
    const { register, handleSubmit, formState: { errors } } = useForm<ProductFormInputs>();
    const navigate = useNavigate();

    const { data: categories, isLoading: isLoadingCategories } = useQuery({
        queryKey: ['flatCategories'],
        queryFn: fetchCategories
    });

    const mutation = useMutation({
        mutationFn: createProduct,
        onSuccess: () => {
            toast.success('Товар успешно создан!');
            navigate('/dashboard/products');
        },
        onError: (error: any) => {
            const errorMessages = Object.values(error.response?.data).flat();
            toast.error((errorMessages[0] as string) || 'Не удалось создать товар.');
        }
    });

    const onSubmit: SubmitHandler<ProductFormInputs> = data => {
        const formData = new FormData();
        formData.append('title', data.title);
        formData.append('description', data.description);
        formData.append('price', String(data.price));
        if (data.discount) formData.append('discount', String(data.discount));
        formData.append('stock', String(data.stock));
        formData.append('category', String(data.category));
        if (data.thumbnail?.[0]) {
            formData.append('thumbnail', data.thumbnail[0]);
        }
        mutation.mutate(formData);
    };

    return (
        <div className="text-white">
            <h1 className="text-3xl font-bold mb-6">Добавление нового товара</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
                {/* Название */}
                <div>
                    <label htmlFor="title" className="block text-sm font-medium text-slate-300">Название</label>
                    <input id="title" {...register('title', { required: 'Название обязательно' })} className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"/>
                    {errors.title && <p className="text-red-400 text-sm mt-1">{errors.title.message}</p>}
                </div>

                {/* Описание */}
                <div>
                    <label htmlFor="description" className="block text-sm font-medium text-slate-300">Описание</label>
                    <textarea id="description" {...register('description', { required: 'Описание обязательно' })} rows={5} className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"/>
                    {errors.description && <p className="text-red-400 text-sm mt-1">{errors.description.message}</p>}
                </div>

                {/* Категория */}
                <div>
                    <label htmlFor="category" className="block text-sm font-medium text-slate-300">Категория</label>
                    <select id="category" {...register('category', { required: 'Выберите категорию', valueAsNumber: true })} disabled={isLoadingCategories} className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white focus:border-cyan-500 focus:ring-cyan-500 disabled:opacity-50">
                        <option value="">Выберите...</option>
                        {categories?.map(cat => <option key={cat.id} value={cat.id}>{cat.title}</option>)}
                    </select>
                    {errors.category && <p className="text-red-400 text-sm mt-1">{errors.category.message}</p>}
                </div>

                {/* Цена, Скидка, Запас */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    <div>
                        <label htmlFor="price" className="block text-sm font-medium text-slate-300">Цена (руб.)</label>
                        <input id="price" {...register('price', { required: 'Укажите цену', valueAsNumber: true, min: { value: 0.01, message: 'Цена должна быть больше 0'} })} type="number" step="0.01" className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"/>
                        {errors.price && <p className="text-red-400 text-sm mt-1">{errors.price.message}</p>}
                    </div>
                    <div>
                        <label htmlFor="discount" className="block text-sm font-medium text-slate-300">Скидка (%)</label>
                        <input id="discount" {...register('discount', { valueAsNumber: true, min: 0, max: 100 })} type="number" placeholder="0-100" className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"/>
                    </div>
                     <div>
                        <label htmlFor="stock" className="block text-sm font-medium text-slate-300">Запас (шт.)</label>
                        <input id="stock" {...register('stock', { required: 'Укажите остаток', valueAsNumber: true, min: { value: 0, message: 'Остаток не может быть отрицательным'} })} type="number" className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"/>
                         {errors.stock && <p className="text-red-400 text-sm mt-1">{errors.stock.message}</p>}
                    </div>
                </div>

                {/* Изображение */}
                <div>
                    <label htmlFor="thumbnail" className="block text-sm font-medium text-slate-300">Изображение</label>
                    <input id="thumbnail" type="file" {...register('thumbnail', { required: 'Загрузите изображение' })} className="mt-1 block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-cyan-400 hover:file:bg-slate-600"/>
                    {errors.thumbnail && <p className="text-red-400 text-sm mt-1">{errors.thumbnail.message}</p>}
                </div>

                <button type="submit" disabled={mutation.isPending} className="rounded-md bg-cyan-600 px-6 py-2 text-white transition hover:bg-cyan-700 disabled:opacity-50">
                    {mutation.isPending ? 'Создание...' : 'Создать товар'}
                </button>
            </form>
        </div>
    );
}