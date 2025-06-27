// src/components/RegisterForm.tsx
import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';

interface RegisterFormProps {
  onSuccess: () => void; // Вызывается после успешной регистрации для перехода к шагу подтверждения
  setEmailForConfirmation: (email: string) => void; // Передаем email на следующий шаг
}

export function RegisterForm({ onSuccess, setEmailForConfirmation }: RegisterFormProps) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { register, error, isLoading } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register({ username, email, password });
      setEmailForConfirmation(email); // Сохраняем email для следующего шага
      onSuccess(); // Переключаем на форму подтверждения
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
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"
        />
      </div>
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-600"
      >
        {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}