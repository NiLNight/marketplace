// src/pages/ProfilePage.tsx
import {useAuthStore} from '../stores/authStore';
import {useForm, type SubmitHandler} from 'react-hook-form'; // <-- Исправлен импорт
import {useEffect, useState} from 'react'; // <-- Убран неиспользуемый useRef
import toast from 'react-hot-toast';

// Типы для формы
interface ProfileFormInputs {
    username: string;
    first_name: string;
    last_name: string;
    profile: {
        phone: string | null;
        birth_date: string | null;
        avatar: FileList | null;
    };
}

export function ProfilePage() {
    const {user, updateProfile, isLoading} = useAuthStore();
    const {register, handleSubmit, reset, watch} = useForm<ProfileFormInputs>();
    // Инициализация с null, чтобы избежать проблем с первоначальным значением
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

    const avatarFile = watch('profile.avatar');

    // Эффект для локального превью при выборе нового файла
    useEffect(() => {
        if (avatarFile && avatarFile.length > 0) {
            const file = avatarFile[0];
            const reader = new FileReader();
            reader.onloadend = () => {
                setAvatarPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    }, [avatarFile]);

    // Эффект для заполнения формы и аватара из стора при загрузке
    useEffect(() => {
        if (user) {
            reset({
                username: user.username,
                first_name: user.first_name || '',
                last_name: user.last_name || '',
                profile: {
                    phone: user.profile?.phone || '',
                    birth_date: user.profile?.birth_date || '',
                    avatar: null
                }
            });

            if (user.profile?.avatar) {
                const baseUrl = import.meta.env.VITE_API_BASE_URL;
                // Проверяем, является ли аватар уже полным URL (на всякий случай)
                if (user.profile.avatar.startsWith('http')) {
                    setAvatarPreview(user.profile.avatar);
                } else {
                    setAvatarPreview(`${baseUrl}${user.profile.avatar}`);
                }
            } else {
                setAvatarPreview(null);
            }
        }
    }, [user, reset]);

    const onSubmit: SubmitHandler<ProfileFormInputs> = async (data) => {
        // Собираем данные для отправки, отфильтровывая пустые значения
        const profilePayload: { phone?: string; birth_date?: string; avatar?: File } = {};
        if (data.profile.phone) profilePayload.phone = data.profile.phone;
        if (data.profile.birth_date) profilePayload.birth_date = data.profile.birth_date;
        if (data.profile.avatar?.[0]) profilePayload.avatar = data.profile.avatar[0];

        const payload: {
            username?: string;
            first_name?: string;
            last_name?: string;
            profile?: typeof profilePayload
        } = {};
        if (data.username !== user?.username) payload.username = data.username;
        if (data.first_name !== user?.first_name) payload.first_name = data.first_name || '';
        if (data.last_name !== user?.last_name) payload.last_name = data.last_name || '';
        if (Object.keys(profilePayload).length > 0) payload.profile = profilePayload;

        // Не отправляем пустой запрос
        if (Object.keys(payload).length === 0) {
            toast('Вы не внесли никаких изменений.');
            return;
        }

        toast.promise(
            updateProfile(payload),
            {
                loading: 'Обновление профиля...',
                success: 'Профиль успешно обновлен!',
                error: (err) => err.message || 'Не удалось обновить профиль.',
            }
        );
    };

    if (!user) {
        return <div className="text-center text-white">Загрузка профиля...</div>;
    }

    return (
        <div>
            <h1 className="text-3xl font-bold text-white mb-6">Мой профиль</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
                <div className="flex items-center gap-6">
                    <img
                        src={avatarPreview || `https://ui-avatars.com/api/?name=${user.username}&background=random`}
                        alt="Аватар"
                        className="h-24 w-24 rounded-full object-cover bg-slate-700"
                    />
                    <div>
                        <label htmlFor="avatar-upload"
                               className="cursor-pointer rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-600">
                            Сменить аватар
                        </label>
                        <input id="avatar-upload" type="file" className="sr-only" {...register("profile.avatar")}
                               accept="image/*"/>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Имя пользователя</label>
                        <input {...register("username")}
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Телефон</label>
                        <input {...register("profile.phone")} type="tel"
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Имя</label>
                        <input {...register("first_name")}
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Фамилия</label>
                        <input {...register("last_name")}
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300">Дата рождения</label>
                        <input {...register("profile.birth_date")} type="date"
                               className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 p-2 text-white"/>
                    </div>
                </div>

                <button type="submit" disabled={isLoading}
                        className="rounded-md bg-cyan-600 px-6 py-2 text-white transition hover:bg-cyan-700 disabled:opacity-50">
                    {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
                </button>
            </form>
        </div>
    );
}