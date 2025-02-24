from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from apps.users.models import EmailVerified
from apps.services.user.tasks import send_confirmation_email, send_password_reset_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import random

User = get_user_model()


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


def login_user(email, password):
    """Аутентификация пользователя."""
    user = User.objects.filter(email=email).first()
    if not user:
        raise ValueError("Неверные учетные данные")
    if not user.is_active:
        raise ValueError("Аккаунт не активирован")
    if not user.check_password(password):
        raise ValueError("Неверные учетные данные")
    user = authenticate(username=user.username, password=password)
    if not user:
        raise ValueError("Ошибка аутентификации")
    return user


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
    return User


def request_password_reset(email):
    """Запрос на сброс пароля."""
    user = User.objects.get(email=email)
    token = PasswordResetTokenGenerator().make_token(user)
    reset_url = f"http://localhost:8000/reset-password/?token={token}&uid={user.id}"
    print(reset_url)
    send_password_reset_email.delay(email, reset_url)
    return True


def confirm_password_reset(uid, token, new_password):
    """Подтверждение сброса пароля."""
    user = User.objects.get(id=uid)
    if not PasswordResetTokenGenerator().check_token(user, token):
        raise ValueError("Неверный или просроченный токен")
    user.set_password(new_password)
    user.save()
    return user
