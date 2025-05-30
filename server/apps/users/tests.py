"""Модуль тестов для приложения users.

Содержит тесты для проверки функциональности регистрации, аутентификации,
управления профилем и других возможностей приложения users.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from apps.users.models import UserProfile, EmailVerified
from apps.users.services.users_services import UserService, ConfirmCodeService
from apps.users.exceptions import UserNotFound, InvalidUserData, AuthenticationFailed

User = get_user_model()


class UserRegistrationTests(TestCase):
    """Тесты для процесса регистрации пользователей.

    Проверяет создание пользователя, отправку кода подтверждения и активацию аккаунта.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.register_url = reverse('users:user_registration')
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


class UserProfileTests(TestCase):
    """Тесты для управления профилем пользователя.

    Проверяет создание, обновление и получение данных профиля.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.profile_url = reverse('users:user_profile')
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
