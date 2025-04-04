from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import EmailVerified, UserProfile
from apps.users.services.tasks import send_confirmation_email, send_password_reset_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import random

User = get_user_model()


class UserService:
    @staticmethod
    def register_user(username, email, password):
        """Регистрация пользователя."""
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )
        code = str(random.randint(100000, 999999))
        EmailVerified.objects.create(
            user=user,
            confirmation_code=code,
            code_created_at=timezone.now()
        )
        send_confirmation_email.delay(email, code)
        return user

    @staticmethod
    def login_user(email, password):
        """Аутентификация пользователя."""
        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed("Неверные учетные данные")
        if not user.is_active:
            raise AuthenticationFailed("Аккаунт не активирован")
        if not user.check_password(password):
            raise AuthenticationFailed("Неверные учетные данные")
        user = authenticate(username=user.username, password=password)
        if not user:
            raise AuthenticationFailed("Ошибка аутентификации")
        return user

    @staticmethod
    def logout_user(refresh_token):
        """Добавление refresh-токена в чёрный список"""
        if not refresh_token:
            raise ValueError("Требуется refresh токен")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            raise ValueError("Неправильный токен")

    @staticmethod
    def update_user_and_profile(user, validated_data):
        profile_data = validated_data.pop('profile', None)
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save()

        # Если данные профиля переданы, обновляем или создаем профиль
        if profile_data:
            if hasattr(user, 'profile') and user.profile is not None:
                from apps.users.serializers import UserProfileSerializer
                profile_serializer = UserProfileSerializer(
                    instance=user.profile,
                    data=profile_data,
                    partial=True
                )
                profile_serializer.is_valid(raise_exception=True)
                profile_serializer.save()
            else:
                UserProfile.objects.create(user=user, **profile_data)

        return user


class ConfirmCodeService:
    @staticmethod
    def resend_confirmation_code(email):
        """Повторная отправка кода подтверждения."""
        user = User.objects.get(email=email, is_active=False)
        code = str(random.randint(100000, 999999))
        EmailVerified.objects.update_or_create(
            user=user,
            defaults={
                'confirmation_code': code,
                'code_created_at': timezone.now()
            }
        )
        send_confirmation_email.delay(email, code)
        return True

    @staticmethod
    def confirm_account(email, code):
        """Подтверждение аккаунта."""
        user = User.objects.get(email=email)
        email_verified = EmailVerified.objects.filter(user=user, confirmation_code=code).first()
        if not email_verified:
            raise ValueError("Неверный код")
        time_diff = (timezone.now() - email_verified.code_created_at).total_seconds()
        if time_diff > 86400:  # 24 часа
            raise ValueError("Срок действия кода истек")
        user.is_active = True
        user.save()
        email_verified.confirmation_code = None
        email_verified.save()
        return True


class ConfirmPasswordService:
    @staticmethod
    def request_password_reset(email):
        """Запрос на сброс пароля."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Пользователь с таким email не найден.")
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id))
        reset_url = f"http://localhost:8000/reset-password/?token={token}&uid={uid}"
        send_password_reset_email.delay(email, reset_url)
        return True

    @staticmethod
    def confirm_password_reset(uid, token, new_password):
        """Подтверждение сброса пароля."""
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(id=user_id)
        if not PasswordResetTokenGenerator().check_token(user, token):
            raise ValueError("Неверный или просроченный токен")
        user.set_password(new_password)
        user.save()
        return user
