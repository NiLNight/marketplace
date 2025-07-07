// src/pages/ResetPasswordPage.tsx
import {useLocation, useNavigate} from 'react-router-dom';
import {useForm, type SubmitHandler} from 'react-hook-form';
import {useMutation} from '@tanstack/react-query';
import apiClient from '../api';
import toast from 'react-hot-toast';

interface ResetPasswordInputs {
    new_password1: string;
    new_password2: string;
}

const confirmPasswordReset = (data: { new_password: string, uid: string, token: string }) => {
    return apiClient.post(`/user/password-reset-confirm/?uid=${data.uid}&token=${data.token}`, {new_password: data.new_password});
};

export function ResetPasswordPage() {
    const {register, handleSubmit, watch, formState: {errors}} = useForm<ResetPasswordInputs>();
    const navigate = useNavigate();
    const location = useLocation();

    const searchParams = new URLSearchParams(location.search);
    const uid = searchParams.get('uid');
    const token = searchParams.get('token');

    const mutation = useMutation({
        mutationFn: confirmPasswordReset,
        onSuccess: () => {
            toast.success('Пароль успешно изменен! Теперь вы можете войти.');
            navigate('/'); // Перенаправляем на главную, чтобы пользователь мог войти
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Ссылка недействительна или срок ее действия истек.');
        }
    });

    const onSubmit: SubmitHandler<ResetPasswordInputs> = data => {
        if (!uid || !token) {
            toast.error('Некорректная ссылка для сброса пароля.');
            return;
        }
        mutation.mutate({new_password: data.new_password1, uid, token});
    };

    return (
        <div className="mx-auto max-w-md text-white">
            <h1 className="text-2xl font-bold text-center">Установка нового пароля</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6">
                <div>
                    <label className="block text-sm font-medium text-slate-300">Новый пароль</label>
                    <input
                        type="password"
                        {...register('new_password1', {
                            required: 'Введите новый пароль',
                            minLength: {value: 8, message: 'Пароль должен быть не менее 8 символов'}
                        })}
                        className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                    />
                    {errors.new_password1 &&
                        <p className="text-red-400 text-sm mt-1">{errors.new_password1.message}</p>}
                </div>
                <div>
                    <label className="block text-sm font-medium text-slate-300">Повторите новый пароль</label>
                    <input
                        type="password"
                        {...register('new_password2', {
                            required: 'Повторите пароль',
                            validate: value => value === watch('new_password1') || 'Пароли не совпадают'
                        })}
                        className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                    />
                    {errors.new_password2 &&
                        <p className="text-red-400 text-sm mt-1">{errors.new_password2.message}</p>}
                </div>
                <button type="submit" disabled={mutation.isPending} className="w-full rounded-md bg-cyan-600 ...">
                    {mutation.isPending ? 'Сохранение...' : 'Сохранить новый пароль'}
                </button>
            </form>
        </div>
    );
}