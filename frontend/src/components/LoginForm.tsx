// src/components/LoginForm.tsx
import {useState} from 'react';
import {useAuthStore} from '../stores/authStore';
import apiClient from '../api';

interface LoginFormProps {
    onSuccess: () => void;
    onActivateAccount: (email: string) => void;
    onForgotPassword: () => void;
}

export function LoginForm({onSuccess, onActivateAccount, onForgotPassword}: LoginFormProps) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isActivationRequired, setActivationRequired] = useState(false);
    const [localError, setLocalError] = useState<string | null>(null);

    const {login, isLoading} = useAuthStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);
        setActivationRequired(false);

        try {
            await login({email, password});
            onSuccess();
        } catch (err: any) {
            const code = err.response?.data?.code;
            const message = err.response?.data?.error || 'Произошла ошибка входа';

            if (code === 'account_not_activated') {
                setActivationRequired(true);
            }
            setLocalError(message);
            console.error('Login failed');
        }
    };

    const handleActivate = async () => {
        try {
            await apiClient.post('/user/resend-code/', {email});
            onActivateAccount(email);
        } catch (err: any) {
            setLocalError(err.response?.data?.error || 'Не удалось отправить код.');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {localError && (
                <div
                    className={isActivationRequired ? "rounded border border-yellow-500/50 bg-yellow-900/30 p-4 text-center" : "rounded bg-red-900/50 p-3 text-center text-red-300"}>
                    <p className={isActivationRequired ? "text-yellow-300" : ""}>{localError}</p>
                    {isActivationRequired && (
                        <button
                            type="button"
                            onClick={handleActivate}
                            className="mt-2 rounded bg-yellow-500 px-3 py-1 text-sm text-black transition hover:bg-yellow-400"
                        >
                            Активировать
                        </button>
                    )}
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-slate-300">Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-slate-300">Пароль</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                />
            </div>
            <div className="text-right">
                <button
                    type="button"
                    onClick={onForgotPassword}
                    className="text-sm text-cyan-400 hover:underline"
                >
                    Забыли пароль?
                </button>
            </div>
            <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-600"
            >
                {isLoading ? 'Вход...' : 'Войти'}
            </button>
        </form>
    );
}