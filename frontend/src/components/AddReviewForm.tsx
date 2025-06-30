// src/components/AddReviewForm.tsx
import { useForm, Controller, type SubmitHandler } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';
import { Star } from 'lucide-react';

interface ReviewFormInputs {
    value: number;
    text: string;
    image: FileList | null;
}

interface AddReviewFormProps {
    productId: number;
}

const createReview = (data: FormData) => {
    return apiClient.post('/reviews/create/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};

export function AddReviewForm({ productId }: AddReviewFormProps) {
    const { register, handleSubmit, control, reset } = useForm<ReviewFormInputs>({
        defaultValues: { value: 0, text: '' }
    });
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: createReview,
        onSuccess: () => {
            toast.success('Спасибо за ваш отзыв!');
            // Инвалидируем кэш отзывов и самого продукта (чтобы обновить средний рейтинг)
            queryClient.invalidateQueries({ queryKey: ['reviews', productId] });
            queryClient.invalidateQueries({ queryKey: ['product', String(productId)] });
            reset();
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Не удалось отправить отзыв.');
        }
    });

    const onSubmit: SubmitHandler<ReviewFormInputs> = (data) => {
        if (data.value === 0) {
            toast.error('Пожалуйста, поставьте оценку.');
            return;
        }

        const formData = new FormData();
        formData.append('product', String(productId));
        formData.append('value', String(data.value));
        formData.append('text', data.text);
        if (data.image && data.image.length > 0) {
            formData.append('image', data.image[0]);
        }

        mutation.mutate(formData);
    };

    return (
        <div className="p-6 mb-8 bg-slate-800 rounded-lg">
            <h3 className="text-xl font-semibold text-white mb-4">Оставить отзыв</h3>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Ваша оценка</label>
                    <Controller
                        name="value"
                        control={control}
                        render={({ field }) => (
                            <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map(star => (
                                    <button type="button" key={star} onClick={() => field.onChange(star)}>
                                        <Star
                                            size={24}
                                            className={`transition-colors ${field.value >= star ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'}`}
                                        />
                                    </button>
                                ))}
                            </div>
                        )}
                    />
                </div>
                <div>
                    <label htmlFor="review-text" className="block text-sm font-medium text-slate-300">Текст отзыва</label>
                    <textarea
                        id="review-text"
                        {...register('text')}
                        rows={4}
                        placeholder="Поделитесь вашими впечатлениями..."
                        className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
                    />
                </div>
                <div>
                    <label htmlFor="review-image" className="block text-sm font-medium text-slate-300">Прикрепить фото</label>
                    <input
                        id="review-image"
                        type="file"
                        {...register('image')}
                        accept="image/png, image/jpeg"
                        className="mt-1 block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-cyan-400 hover:file:bg-slate-600"
                    />
                </div>
                <button
                    type="submit"
                    disabled={mutation.isPending}
                    className="rounded-md bg-cyan-600 px-6 py-2 text-white transition hover:bg-cyan-700 disabled:opacity-50"
                >
                    {mutation.isPending ? 'Отправка...' : 'Отправить отзыв'}
                </button>
            </form>
        </div>
    );
}