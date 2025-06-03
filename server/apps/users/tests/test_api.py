"""
Модуль тестов для API приложения users.

Содержит тесты для всех API endpoints, включая регистрацию, аутентификацию,
управление профилем и сброс пароля.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import EmailVerified
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from config import settings

User = get_user_model()


class UserRegistrationAPITests(TestCase):
    """Тесты для API регистрации пользователей."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()
        self.register_url = reverse('users:user_registration')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        cache.clear()

    def test_register_user_success(self):
        """Тест успешной регистрации пользователя."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_register_user_duplicate_email(self):
        """Тест регистрации с существующим email."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_weak_password(self):
        """Тест регистрации со слабым паролем."""
        self.user_data['password'] = '123'
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginAPITests(TestCase):
    """Тесты для API аутентификации."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()
        self.login_url = reverse('users:user_login')
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

    def test_login_success(self):
        """Тест успешной аутентификации."""
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем наличие токенов в cookies
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE'], response.cookies)
        self.assertIn(settings.SIMPLE_JWT['REFRESH_COOKIE'], response.cookies)
        # Проверяем данные в теле ответа
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_login_inactive_user(self):
        """Тест аутентификации неактивного пользователя."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_wrong_password(self):
        """Тест аутентификации с неверным паролем."""
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': 'WrongPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITests(TestCase):
    """Тесты для API профиля пользователя."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()
        self.profile_url = reverse('users:user_profile')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_active = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        cache.clear()

    def test_get_profile(self):
        """Тест получения профиля пользователя."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_update_profile(self):
        """Тест обновления профиля пользователя."""
        update_data = {
            "username": "testuser",
            "profile": {
                "phone": "+7 (999) 123-45-67",
                "birth_date": "1990-01-01"
            }
        }
        response = self.client.patch(
            self.profile_url,
            update_data,
            format='json'  # Указываем JSON вместо multipart
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone, update_data['profile']['phone'])
        self.assertEqual(str(self.user.profile.birth_date), update_data['profile']['birth_date'])

    def test_update_profile_with_avatar(self):
        """Тест обновления аватара профиля."""
        avatar = SimpleUploadedFile(
            "test_avatar.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        update_data = {
            'avatar': avatar
        }
        response = self.client.patch(
            self.profile_url,
            update_data,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar)

    def test_get_profile_unauthorized(self):
        """Тест получения профиля без аутентификации."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmailConfirmationAPITests(TestCase):
    """Тесты для API подтверждения email."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()
        self.confirm_url = reverse('users:confirm_code')
        self.resend_url = reverse('users:resend_code')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_active = False
        self.user.save()
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

    def test_confirm_email_success(self):
        """Тест успешного подтверждения email."""
        response = self.client.post(self.confirm_url, {
            'email': self.user_data['email'],
            'code': '123456'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_confirm_email_wrong_code(self):
        """Тест подтверждения с неверным кодом."""
        response = self.client.post(self.confirm_url, {
            'email': self.user_data['email'],
            'code': 'wrong_code'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_confirm_email_expired_code(self):
        """Тест подтверждения с просроченным кодом."""
        self.email_verified.code_created_at = timezone.now() - timedelta(hours=25)
        self.email_verified.save()
        response = self.client.post(self.confirm_url, {
            'email': self.user_data['email'],
            'code': '123456'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_resend_confirmation_code(self):
        """Тест повторной отправки кода подтверждения."""
        response = self.client.post(self.resend_url, {
            'email': self.user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.email_verified.refresh_from_db()
        self.assertNotEqual(self.email_verified.confirmation_code, '123456')


class PasswordResetAPITests(TestCase):
    """Тесты для API сброса пароля."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()
        self.reset_url = reverse('users:password_reset')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)

    def tearDown(self):
        """Очистка тестовых данных."""
        User.objects.all().delete()
        cache.clear()

    def test_request_password_reset(self):
        """Тест запроса на сброс пароля."""
        response = self.client.post(self.reset_url, {
            'email': self.user_data['email']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_invalid_email(self):
        """Тест запроса на сброс пароля с несуществующим email."""
        response = self.client.post(self.reset_url, {
            'email': 'nonexistent@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
