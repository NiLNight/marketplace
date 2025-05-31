"""Модуль тестов для приложения users.

Содержит тесты для проверки функциональности регистрации, аутентификации,
управления профилем и других возможностей приложения users.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from apps.users.models import UserProfile, EmailVerified
from apps.users.services.users_services import UserService, ConfirmCodeService
from apps.users.exceptions import UserNotFound, InvalidUserData, AuthenticationFailed, AccountNotActivated

User = get_user_model()

# Отключаем троттлинг для всех тестов
@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
        'celery': None,
    }
})
class UserRegistrationTests(TestCase):
    """Тесты для процесса регистрации пользователей.

    Проверяет создание пользователя, отправку кода подтверждения и активацию аккаунта.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.register_url = reverse('users:user_registration')
        self.confirm_url = reverse('users:confirm_code')
        self.resend_code_url = reverse('users:resend_code')
        self.valid_payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_valid_registration(self):
        """Тест успешной регистрации пользователя."""
        response = self.client.post(
            self.register_url,
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.valid_payload['email']).exists())
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertFalse(user.is_active)
        self.assertTrue(hasattr(user, 'email_verified'))

    def test_invalid_registration_duplicate_email(self):
        """Тест регистрации с уже существующим email."""
        User.objects.create_user(
            username='existing',
            email=self.valid_payload['email'],
            password='existing123'
        )
        response = self.client.post(
            self.register_url,
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_registration_weak_password(self):
        """Тест регистрации со слабым паролем."""
        data = self.valid_payload.copy()
        data['password'] = '123'  # Слишком короткий пароль
        response = self.client.post(
            self.register_url,
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error'])

    def test_confirm_email(self):
        """Тест подтверждения email."""
        # Регистрируем пользователя
        response = self.client.post(
            self.register_url,
            data=self.valid_payload,
            format='json'
        )
        user = User.objects.get(email=self.valid_payload['email'])
        code = user.email_verified.confirmation_code

        # Подтверждаем email
        response = self.client.post(
            self.confirm_url,
            data={'email': self.valid_payload['email'], 'code': code},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_resend_confirmation_code(self):
        """Тест повторной отправки кода подтверждения."""
        # Регистрируем пользователя
        self.client.post(
            self.register_url,
            data=self.valid_payload,
            format='json'
        )
        
        # Запрашиваем новый код
        response = self.client.post(
            self.resend_code_url,
            data={'email': self.valid_payload['email']},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertTrue(user.email_verified.confirmation_code)


@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
        'celery': None,
    }
})
class UserAuthenticationTests(TestCase):
    """Тесты для процесса аутентификации пользователей.

    Проверяет вход, выход и обработку ошибок аутентификации.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.login_url = reverse('users:user_login')
        self.logout_url = reverse('users:user_logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )

    def test_valid_login(self):
        """Тест успешного входа пользователя."""
        response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'testpass123'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_invalid_login_wrong_password(self):
        """Тест входа с неверным паролем."""
        response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'wrongpass'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Тест входа неактивного пользователя."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'testpass123'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout(self):
        """Тест выхода пользователя."""
        # Сначала входим
        login_response = self.client.post(
            self.login_url,
            data={
                'email': 'test@example.com',
                'password': 'testpass123'
            },
            format='json'
        )
        # Сохраняем cookies после входа
        self.client.cookies = login_response.cookies
        
        # Затем выходим
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что значения cookies пустые или отсутствуют
        self.assertTrue(
            'access_token' not in response.cookies or 
            not response.cookies['access_token'].value
        )
        self.assertTrue(
            'refresh_token' not in response.cookies or 
            not response.cookies['refresh_token'].value
        )


@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
        'celery': None,
    }
})
class UserProfileTests(TestCase):
    """Тесты для управления профилем пользователя.

    Проверяет создание, обновление и получение данных профиля.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.profile_url = reverse('users:user_profile')
        self.password_reset_url = reverse('users:password_reset')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Тест получения данных профиля."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertTrue('profile' in response.data)

    def test_update_profile(self):
        """Тест обновления профиля."""
        update_data = {
            'username': 'newusername',
            'profile': {
                'phone': '+7 (912) 345-67-89',  # Формат телефона согласно регулярному выражению
                'birth_date': '1990-01-01'
            }
        }
        response = self.client.patch(
            self.profile_url,
            data=update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
        self.assertEqual(self.user.profile.phone, '+7 (912) 345-67-89')

    def test_update_profile_invalid_phone(self):
        """Тест обновления профиля с неверным форматом телефона."""
        update_data = {
            'profile': {
                'phone': '123'  # Неверный формат
            }
        }
        response = self.client.patch(
            self.profile_url,
            data=update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_password_reset(self):
        """Тест запроса сброса пароля."""
        response = self.client.post(
            self.password_reset_url,
            data={'email': self.user.email},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_invalid_email(self):
        """Тест запроса сброса пароля с несуществующим email."""
        response = self.client.post(
            self.password_reset_url,
            data={'email': 'nonexistent@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserServiceTests(TestCase):
    """Тесты для сервисного слоя пользователей.

    Проверяет бизнес-логику работы с пользователями.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_register_user(self):
        """Тест регистрации пользователя через сервис."""
        user = UserService.register_user(**self.user_data)
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertFalse(user.is_active)
        self.assertTrue(hasattr(user, 'email_verified'))
        self.assertTrue(user.email_verified.confirmation_code)

    def test_login_user_success(self):
        """Тест успешного входа через сервис."""
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True
        )
        logged_in_user = UserService.login_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(user, logged_in_user)

    def test_login_user_inactive(self):
        """Тест входа неактивного пользователя через сервис."""
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=False
        )
        with self.assertRaises(AccountNotActivated):
            UserService.login_user(
                email=self.user_data['email'],
                password=self.user_data['password']
            )

    def test_login_user_wrong_password(self):
        """Тест входа с неверным паролем через сервис."""
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True
        )
        with self.assertRaises(AuthenticationFailed):
            UserService.login_user(
                email=self.user_data['email'],
                password='wrongpass'
            )
