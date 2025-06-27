// src/components/LoginForm.tsx
import {useState} from 'react';
import {useAuthStore} from '../stores/authStore';

export function LoginForm({onSuccess}: { onSuccess: () => void }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const {login, error, isLoading} = useAuthStore();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await login({email, password});
            // Если логин успешен, вызываем колбэк для закрытия модального окна
            onSuccess();
        } catch (err) {
            // Ошибка уже обработана в сторе, здесь ничего делать не нужно
            console.error('Login failed');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* Поле для отображения ошибок */}
            {error && <div className="rounded bg-red-900/50 p-3 text-center text-red-300">{error}</div>}

            <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300">Email</label>
                <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
                />
            </div>
            <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300">Пароль</label>
                <input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
                />
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