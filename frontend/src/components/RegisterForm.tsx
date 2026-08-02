// src/components/RegisterForm.tsx
import {useState} from 'react';
import {useAuthStore} from '../stores/authStore';

interface RegisterFormProps {
    onSuccess: () => void;
    setEmailForConfirmation: (email: string) => void;
}

// Клиентская валидация пароля — такие же правила, как на бэкенде
function validatePassword(password: string): string | null {
    if (password.length < 8) return 'Пароль должен содержать не менее 8 символов.';
    if (!/\d/.test(password)) return 'Пароль должен содержать хотя бы одну цифру.';
    if (!/[a-zA-Zа-яА-Я]/.test(password)) return 'Пароль должен содержать хотя бы одну букву.';
    return null;
}

export function RegisterForm({onSuccess, setEmailForConfirmation}: RegisterFormProps) {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const {register, error, isLoading} = useAuthStore();

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setPassword(val);
        // Показываем ошибку только если поле не пустое
        if (val) setPasswordError(validatePassword(val));
        else setPasswordError(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const pwError = validatePassword(password);
        if (pwError) {
            setPasswordError(pwError);
            return;
        }
        try {
            await register({username, email, password});
            setEmailForConfirmation(email);
            onSuccess();
        } catch (err) {
            console.error('Registration failed');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="rounded bg-red-900/50 p-3 text-center text-red-300">{error}</div>}

            <div>
                <label className="block text-sm font-medium text-slate-300">Имя пользователя</label>
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
                />
            </div>
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
                    onChange={handlePasswordChange}
                    required
                    className={`mt-1 block w-full rounded-md border bg-slate-700 p-2 text-white ${
                        passwordError ? 'border-red-500' : 'border-slate-600'
                    }`}
                />
                {passwordError && (
                    <p className="mt-1 text-sm text-red-400">{passwordError}</p>
                )}
                {!passwordError && password.length >= 8 && (
                    <p className="mt-1 text-sm text-green-400">Пароль подходит ✓</p>
                )}
                <p className="mt-1 text-xs text-slate-500">
                    Минимум 8 символов, должен содержать букву и цифру.
                </p>
            </div>
            <button
                type="submit"
                disabled={isLoading || !!passwordError}
                className="w-full rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-600"
            >
                {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
            </button>
        </form>
    );
}