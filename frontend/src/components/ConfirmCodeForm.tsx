// src/components/ConfirmCodeForm.tsx
import {useState, useEffect} from 'react';
import apiClient from '../api';
import toast from 'react-hot-toast';

interface ConfirmCodeFormProps {
    email: string;
    onSuccess: () => void;
}

const RESEND_TIMEOUT = 60;

export function ConfirmCodeForm({email, onSuccess}: ConfirmCodeFormProps) {
    const [code, setCode] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);

    useEffect(() => {
        if (resendCooldown > 0) {
            const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCooldown]);

    const handleConfirmSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            await apiClient.post('/user/confirm-code/', {email, code});
            toast('Аккаунт успешно активирован! Теперь вы можете войти.');
            onSuccess();
        } catch (err: any) {
            setError(err.response?.data?.error || 'Неверный код или произошла ошибка.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleResendCode = async () => {
        if (resendCooldown > 0) return;

        setIsLoading(true);
        setError(null);
        try {
            await apiClient.post('/user/resend-code/', {email});
            setResendCooldown(RESEND_TIMEOUT);
            toast('Новый код отправлен на ваш email.');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Не удалось отправить код.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="text-white">
            <p className="mb-4 text-center text-slate-300">
                Мы отправили код подтверждения на ваш email: <strong>{email}</strong>.
            </p>
            <form onSubmit={handleConfirmSubmit} className="space-y-4">
                {error && <div className="rounded bg-red-900/50 p-3 text-center text-red-300">{error}</div>}
                <div>
                    <label className="block text-sm font-medium text-slate-300">Код подтверждения</label>
                    <input
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        required
                        maxLength={6}
                        className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-center text-lg tracking-[.5em] text-white"
                    />
                </div>
                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-600"
                >
                    {isLoading ? 'Проверка...' : 'Подтвердить'}
                </button>
            </form>
            <div className="mt-4 text-center">
                <button
                    onClick={handleResendCode}
                    disabled={resendCooldown > 0 || isLoading}
                    className="text-sm text-cyan-400 hover:text-cyan-300 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                    {resendCooldown > 0 ? `Отправить снова через ${resendCooldown}с` : 'Отправить код повторно'}
                </button>
            </div>
        </div>
    );
}