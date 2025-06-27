// src/components/Header.tsx
import { LogIn, UserPlus } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useState } from 'react';
import { Modal } from './Modal';
import { LoginForm } from './LoginForm';

export function Header() {
  const { isLoggedIn, user, logout } = useAuthStore();
  const [isLoginModalOpen, setLoginModalOpen] = useState(false);
  // В будущем добавим состояние и для модального окна регистрации
  // const [isRegisterModalOpen, setRegisterModalOpen] = useState(false);

  return (
    <>
      <header className="mb-8 flex items-center justify-between rounded-lg bg-slate-800 p-4">
        <a href="/" className="text-2xl font-bold text-white">
          Marketplace
        </a>
        <nav className="flex items-center gap-4">
          {isLoggedIn ? (
            <div className="flex items-center gap-4">
              <span className="text-white">Привет, {user?.username}!</span>
              <button
                onClick={logout}
                className="rounded-md bg-red-500 px-4 py-2 text-white transition hover:bg-red-600"
              >
                Выйти
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <button
                onClick={() => setLoginModalOpen(true)} // <-- Открываем модальное окно
                className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 text-slate-300 transition hover:bg-slate-700"
              >
                <LogIn size={18} />
                <span>Войти</span>
              </button>
              <button className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700">
                <UserPlus size={18} />
                <span>Регистрация</span>
              </button>
            </div>
          )}
        </nav>
      </header>

      {/* Наше модальное окно для входа */}
      <Modal
        isOpen={isLoginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        title="Вход в аккаунт"
      >
        <LoginForm onSuccess={() => setLoginModalOpen(false)} />
      </Modal>
    </>
  );
}