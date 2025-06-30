// src/components/AddCommentForm.tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, type SubmitHandler } from 'react-hook-form';
import apiClient from '../api';
import toast from 'react-hot-toast';

interface AddCommentFormInputs {
    text: string;
}

interface AddCommentFormProps {
    reviewId: number;
    parentId?: number | null; // Для ответа на комментарий
    onSuccess: () => void; // Колбэк для закрытия формы после успеха
}

const createComment = (data: { review: number; text: string; parent?: number | null }) => {
    return apiClient.post('/comments/create/', data);
};

export function AddCommentForm({ reviewId, parentId = null, onSuccess }: AddCommentFormProps) {
    const { register, handleSubmit, reset } = useForm<AddCommentFormInputs>();
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: createComment,
        onSuccess: () => {
            // Инвалидируем кэш комментариев для этого отзыва, чтобы список обновился
            queryClient.invalidateQueries({ queryKey: ['comments', reviewId] });
            toast.success('Комментарий добавлен!');
            reset(); // Очищаем форму
            onSuccess(); // Вызываем колбэк (например, для скрытия формы)
        },
        onError: () => {
            toast.error('Не удалось добавить комментарий.');
        },
    });

    const onSubmit: SubmitHandler<AddCommentFormInputs> = (data) => {
        mutation.mutate({
            review: reviewId,
            text: data.text,
            parent: parentId,
        });
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="flex items-start gap-3">
            <textarea
                {...register('text', { required: true })}
                placeholder={parentId ? 'Ваш ответ...' : 'Ваш комментарий...'}
                rows={2}
                className="flex-grow rounded-md border-slate-600 bg-slate-700 p-2 text-sm text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
            />
            <button
                type="submit"
                disabled={mutation.isPending}
                className="h-full rounded-md bg-cyan-600 px-4 py-2 text-sm text-white transition hover:bg-cyan-700 disabled:opacity-50"
            >
                {mutation.isPending ? '...' : 'Отправить'}
            </button>
        </form>
    );
}