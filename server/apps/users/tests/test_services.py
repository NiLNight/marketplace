"""
Модуль тестов для сервисов приложения users.

Содержит тесты для всех сервисных классов, включая UserService,
ConfirmPasswordService и ConfirmCodeService.
"""
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.users.models import EmailVerified
from apps.users.services.users_services import UserService, ConfirmPasswordService, ConfirmCodeService
from apps.users.exceptions import (
    InvalidUserData,
    AccountNotActivated,
    AuthenticationFailed,
    UserNotFound
)

User = get_user_model()


class UserServiceTests(TestCase):
    """Тесты для UserService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_active = True
        self.user.save()

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        cache.clear()

    def test_register_user_success(self):
        """Тест успешной регистрации пользователя."""
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'NewPass123!'
        }
        user = UserService.register_user(**new_user_data)
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, new_user_data['email'])
        self.assertFalse(user.is_active)  # Пользователь не активен до подтверждения email

    def test_register_user_duplicate_email(self):
        """Тест регистрации с уже существующим email."""
        with self.assertRaises(InvalidUserData):
            UserService.register_user(**self.user_data)

    def test_login_user_success(self):
        """Тест успешной аутентификации."""
        user = UserService.login_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(user, self.user)

    def test_login_user_wrong_password(self):
        """Тест аутентификации с неверным паролем."""
        with self.assertRaises(AuthenticationFailed):
            UserService.login_user(
                email=self.user_data['email'],
                password='WrongPass123!'
            )

    def test_login_user_inactive(self):
        """Тест аутентификации неактивного пользователя."""
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(AccountNotActivated):
            UserService.login_user(
                email=self.user_data['email'],
                password=self.user_data['password']
            )


class ConfirmCodeServiceTests(TestCase):
    """Тесты для ConfirmCodeService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=False
        )
        self.email_verified = EmailVerified.objects.create(
            user=self.user,
            confirmation_code='123456',
            code_created_at=timezone.now()
        )

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        EmailVerified.objects.all().delete()
        cache.clear()

    def test_confirm_account_success(self):
        """Тест успешного подтверждения email."""
        ConfirmCodeService.confirm_account(
            email='test@example.com',
            code='123456'
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_confirm_account_wrong_code(self):
        """Тест подтверждения с неверным кодом."""
        with self.assertRaises(InvalidUserData):
            ConfirmCodeService.confirm_account(
                email='test@example.com',
                code='wrong_code'
            )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_confirm_account_expired_code(self):
        """Тест подтверждения с просроченным кодом."""
        self.email_verified.code_created_at = timezone.now() - timedelta(hours=25)
        self.email_verified.save()
        with self.assertRaises(InvalidUserData):
            ConfirmCodeService.confirm_account(
                email='test@example.com',
                code='123456'
            )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_resend_confirmation_code(self):
        """Тест повторной отправки кода подтверждения."""
        ConfirmCodeService.resend_confirmation_code('test@example.com')
        self.email_verified.refresh_from_db()
        self.assertNotEqual(self.email_verified.confirmation_code, '123456')


class ConfirmPasswordServiceTests(TestCase):
    """Тесты для ConfirmPasswordService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        cache.clear()

    def test_request_password_reset(self):
        """Тест запроса на сброс пароля."""
        ConfirmPasswordService.request_password_reset('test@example.com')
        # Проверяем, что письмо отправлено (в реальности проверяем через mock)

    def test_request_password_reset_invalid_email(self):
        """Тест запроса на сброс пароля с несуществующим email."""
        with self.assertRaises(UserNotFound):
            ConfirmPasswordService.request_password_reset('nonexistent@example.com')

    def test_confirm_password_reset(self):
        """Тест подтверждения сброса пароля."""
        # Запрашиваем сброс пароля
        ConfirmPasswordService.request_password_reset('test@example.com')
        
        # Получаем uid и token
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        # Подтверждаем сброс пароля
        user = ConfirmPasswordService.confirm_password_reset(
            uid=uid,
            token=token,
            new_password='NewPass123!'
        )
        self.assertTrue(user.check_password('NewPass123!'))

    def test_confirm_password_reset_invalid_code(self):
        """Тест подтверждения сброса пароля с неверным кодом."""
        # Запрашиваем сброс пароля
        ConfirmPasswordService.request_password_reset('test@example.com')
        
        # Получаем uid в правильном формате
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        with self.assertRaises(InvalidUserData):
            ConfirmPasswordService.confirm_password_reset(
                uid=uid,
                token='invalid-token',
                new_password='NewPass123!'
            )
