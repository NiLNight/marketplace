// src/components/Header.tsx
import {LogIn, UserPlus, ShoppingCart, UserCircle2, Store} from 'lucide-react';
import {useAuthStore} from '../stores/authStore';
import {useCartStore} from '../stores/useCartStore';
import {useState, useEffect, useRef} from 'react';
import {Link} from 'react-router-dom';
import {Modal} from './Modal';
import {LoginForm} from './LoginForm';
import {RegisterForm} from './RegisterForm';
import {ConfirmCodeForm} from './ConfirmCodeForm';
import {useWishlistStore} from '../stores/useWishlistStore';
import { ForgotPasswordForm } from './ForgotPasswordForm';

type ModalView = 'LOGIN' | 'REGISTER' | 'CONFIRM_CODE' | 'FORGOT_PASSWORD';

export function Header() {
    const {isLoggedIn, user, logout} = useAuthStore();
    const {total_items, fetchCart} = useCartStore();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalView, setModalView] = useState<ModalView>('LOGIN');
    const [emailForConfirmation, setEmailForConfirmation] = useState('');
    const {fetchWishlist} = useWishlistStore();


    useEffect(() => {
        console.log('Header mounted, fetching initial cart...');
        fetchCart();
        fetchWishlist();
    }, [fetchCart, fetchWishlist]);

    const prevIsLoggedIn = useRef(isLoggedIn);
    useEffect(() => {
        if (isLoggedIn && !prevIsLoggedIn.current) {
            console.log('User logged in, fetching merged cart...');
            fetchCart();
            fetchWishlist();
        }
        prevIsLoggedIn.current = isLoggedIn;
    }, [isLoggedIn, fetchCart, fetchWishlist]);


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
        FORGOT_PASSWORD: 'Сброс пароля',
    };

    return (
        <>
            <header className="mb-8 flex items-center justify-between rounded-lg bg-slate-800 p-4">
                <Link to="/" className="text-2xl font-bold text-white">
                    Marketplace
                </Link>
                <nav className="flex items-center gap-6">
                    <Link to="/cart" className="relative text-slate-300 transition hover:text-white">
                        <ShoppingCart size={24}/>
                        {total_items > 0 && (
                            <span
                                className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500 text-xs font-bold text-white">
                {total_items}
              </span>
                        )}
                    </Link>

                    <Link to="/dashboard" className="text-slate-300 transition hover:text-white" title="Кабинет продавца">
                            <Store size={24} />
                    </Link>

                    {isLoggedIn ? (
                        <div className="flex items-center gap-4">
                            <span className="text-white">Привет, {user?.username}!</span>
                            <Link to="/profile" className="text-slate-300 transition hover:text-white">
                                <UserCircle2 size={24}/>
                            </Link>

                            <button onClick={logout}
                                    className="rounded-md bg-red-500 px-4 py-2 text-white transition hover:bg-red-600">
                                Выйти
                            </button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-4">
                            <button onClick={() => openModal('LOGIN')}
                                    className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 text-slate-300 transition hover:bg-slate-700">
                                <LogIn size={18}/>
                                <span>Войти</span>
                            </button>
                            <button onClick={() => openModal('REGISTER')}
                                    className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700">
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
                        onForgotPassword={() => setModalView('FORGOT_PASSWORD')}
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
                {modalView === 'FORGOT_PASSWORD' && (
                    <ForgotPasswordForm onFormSubmit={closeModal} />
                )}
            </Modal>
        </>
    );
}