// src/components/ForgotPasswordForm.tsx
import { useForm, type SubmitHandler } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';

interface ForgotPasswordInputs {
    email: string;
}

const requestPasswordReset = (data: ForgotPasswordInputs) => {
    return apiClient.post('/user/password-reset/', data);
};

export function ForgotPasswordForm({ onFormSubmit }: { onFormSubmit: () => void }) {
    const { register, handleSubmit, formState: { errors } } = useForm<ForgotPasswordInputs>();

    const mutation = useMutation({
        mutationFn: requestPasswordReset,
        onSuccess: () => {
            toast.success('Если email верный, мы отправили на него ссылку.');
            onFormSubmit(); // Закрываем модальное окно после успеха
        },
        onError: (error: any) => {
            // Мы не показываем ошибку, если пользователь не найден, для безопасности
            if (error.response?.data?.code === 'not_found') {
                toast.success('Если email верный, мы отправили на него ссылку.');
                onFormSubmit();
            } else {
                toast.error(error.response?.data?.error || 'Произошла ошибка.');
            }
        }
    });

    const onSubmit: SubmitHandler<ForgotPasswordInputs> = data => {
        mutation.mutate(data);
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <p className="text-sm text-slate-300">
                Введите ваш email, и мы отправим ссылку для восстановления пароля.
            </p>
            <div>
                <label htmlFor="forgot-email" className="sr-only">Email</label>
                <input
                    id="forgot-email"
                    type="email"
                    placeholder="Email"
                    {...register('email', { required: 'Email обязателен' })}
                    className="w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                />
                {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>}
            </div>
            <button
                type="submit"
                disabled={mutation.isPending}
                className="w-full rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:opacity-50"
            >
                {mutation.isPending ? 'Отправка...' : 'Отправить'}
            </button>
        </form>
    );
}