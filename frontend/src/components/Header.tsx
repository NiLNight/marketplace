// src/components/Header.tsx
import {LogIn, UserPlus, ShoppingCart} from 'lucide-react';
import {useAuthStore} from '../stores/authStore';
import {useCartStore} from '../stores/useCartStore';
import {useState, useEffect} from 'react';
import {Link} from 'react-router-dom';
import {Modal} from './Modal';
import {LoginForm} from './LoginForm';
import {RegisterForm} from './RegisterForm';
import {ConfirmCodeForm} from './ConfirmCodeForm';

type ModalView = 'LOGIN' | 'REGISTER' | 'CONFIRM_CODE';

export function Header() {
    const {isLoggedIn, user, logout} = useAuthStore();
    const {total_items, fetchCart} = useCartStore();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalView, setModalView] = useState<ModalView>('LOGIN');
    const [emailForConfirmation, setEmailForConfirmation] = useState('');


    useEffect(() => {
        if (isLoggedIn) {
            fetchCart();
        }
    }, [isLoggedIn, fetchCart]);

    const openModal = (view: ModalView) => {
        setModalView(view);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
    };

    const switchToConfirmView = (email: string) => {
        setEmailForConfirmation(email);
        setModalView('CONFIRM_CODE');
    };

    const titles: Record<ModalView, string> = {
        LOGIN: 'Вход в аккаунт',
        REGISTER: 'Создание аккаунта',
        CONFIRM_CODE: 'Подтверждение Email',
    };

    return (
        <>
            <header className="mb-8 flex items-center justify-between rounded-lg bg-slate-800 p-4">
                <a href="/" className="text-2xl font-bold text-white">
                    Marketplace
                </a>
                <nav className="flex items-center gap-6">
                    <Link to="/cart" className="relative text-slate-300 transition hover:text-white">
                        <ShoppingCart size={24}/>
                        {isLoggedIn && total_items > 0 && (
                            <span
                                className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500 text-xs font-bold text-white">
                {total_items}
              </span>
                        )}
                    </Link>
                    {isLoggedIn ? (
                        <div className="flex items-center gap-6">
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
                                onClick={() => openModal('LOGIN')}
                                className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 text-slate-300 transition hover:bg-slate-700"
                            >
                                <LogIn size={18}/>
                                <span>Войти</span>
                            </button>
                            <button
                                onClick={() => openModal('REGISTER')}
                                className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700"
                            >
                                <UserPlus size={18}/>
                                <span>Регистрация</span>
                            </button>
                        </div>
                    )}
                </nav>
            </header>

            <Modal
                isOpen={isModalOpen}
                onClose={closeModal}
                title={titles[modalView]}
            >
                {modalView === 'LOGIN' && (
                    <LoginForm
                        onSuccess={closeModal}
                        onActivateAccount={switchToConfirmView}
                    />
                )}
                {modalView === 'REGISTER' && (
                    <RegisterForm
                        setEmailForConfirmation={setEmailForConfirmation}
                        onSuccess={() => setModalView('CONFIRM_CODE')}
                    />
                )}
                {modalView === 'CONFIRM_CODE' && (
                    <ConfirmCodeForm
                        email={emailForConfirmation}
                        onSuccess={closeModal}
                    />
                )}
            </Modal>
        </>
    );
}