// src/components/EditReviewForm.tsx
import {useForm, Controller, type SubmitHandler} from 'react-hook-form';
import {useMutation, useQueryClient} from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';
import {Star} from 'lucide-react';
import type {Review} from './ReviewCard';

interface ReviewFormInputs {
    value: number;
    text: string;
}

interface EditReviewFormProps {
    review: Review;
    productId: number;
    onCancel: () => void;
}

const updateReview = ({id, data}: { id: number; data: FormData }) => {
    return apiClient.patch(`/reviews/update/${id}/`, data, {
        headers: {'Content-Type': 'multipart/form-data'},
    });
};

export function EditReviewForm({review, productId, onCancel}: EditReviewFormProps) {
    const {handleSubmit, control} = useForm<ReviewFormInputs>({
        defaultValues: {value: review.value, text: review.text}
    });
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: updateReview,
        onSuccess: () => {
            toast.success('Отзыв успешно обновлен!');
            queryClient.invalidateQueries({queryKey: ['reviews', productId]});
            queryClient.invalidateQueries({queryKey: ['product', String(productId)]});
            onCancel();
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Не удалось обновить отзыв.');
        }
    });

    const onSubmit: SubmitHandler<ReviewFormInputs> = (data) => {
        const formData = new FormData();
        formData.append('value', String(data.value));
        formData.append('text', data.text);

        mutation.mutate({id: review.id, data: formData});
    };

    return (
        <div className="p-4 my-2 bg-slate-700/50 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">Редактирование отзыва</h4>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Ваша оценка</label>
                    <Controller
                        name="value"
                        control={control}
                        render={({field}) => (
                            <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map(star => (
                                    <button type="button" key={star} onClick={() => field.onChange(star)}>
                                        <Star
                                            size={24}
                                            className={`transition-colors ${field.value >= star ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600 hover:text-slate-500'}`}
                                        />
                                    </button>
                                ))}
                            </div>
                        )}
                    />
                </div>
                <div>
                    <label htmlFor="review-text-edit" className="block text-sm font-medium text-slate-300">Текст
                        отзыва</label>
                    <textarea
                        id="review-text-edit"
                        {...control.register('text')}
                        rows={4}
                        placeholder="Поделитесь вашими впечатлениями..."
                        className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
                    />
                </div>
                <div className="flex items-center gap-4">
                    <button
                        type="submit"
                        disabled={mutation.isPending}
                        className="rounded-md bg-cyan-600 px-4 py-2 text-sm text-white transition hover:bg-cyan-700 disabled:opacity-50"
                    >
                        {mutation.isPending ? 'Сохранение...' : 'Сохранить'}
                    </button>
                    <button type="button" onClick={onCancel}
                            className="rounded-md bg-slate-600 px-4 py-2 text-sm text-white transition hover:bg-slate-500">
                        Отмена
                    </button>
                </div>
            </form>
        </div>
    );
}