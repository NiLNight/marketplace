"""
Модуль тестов для моделей приложения users.

Содержит тесты для моделей UserProfile и EmailVerified.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from apps.users.models import UserProfile, EmailVerified

User = get_user_model()


class UserProfileModelTests(TestCase):
    """Тесты для модели UserProfile."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.profile = self.user.profile  # Профиль создается автоматически через сигнал

    def test_profile_creation(self):
        """Тест автоматического создания профиля."""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)

    def test_public_id_generation(self):
        """Тест генерации публичного идентификатора."""
        self.assertIsNotNone(self.profile.public_id)
        self.assertTrue(self.profile.public_id.startswith('testuser-'))

    def test_valid_phone_number(self):
        """Тест валидации корректного номера телефона."""
        # Тест формата +999999999
        self.profile.phone = '+123456789'
        try:
            self.profile.full_clean()
        except ValidationError as e:
            self.fail(f"Валидация не прошла для номера {self.profile.phone}: {str(e)}")

        # Тест формата +9 (999) 999-99-99
        self.profile.phone = '+7 (999) 123-45-67'
        try:
            self.profile.full_clean()
        except ValidationError as e:
            self.fail(f"Валидация не прошла для номера {self.profile.phone}: {str(e)}")

    def test_invalid_phone_number(self):
        """Тест валидации некорректного номера телефона."""
        invalid_phones = [
            '123456789',  # Без +
            '+12345',  # Слишком короткий
            '+1234567890',  # Слишком длинный
            '+7(999)1234567',  # Неверный формат скобок
            '+7 999 123-45-67',  # Неверный формат пробелов
        ]
        for phone in invalid_phones:
            self.profile.phone = phone
            with self.assertRaises(ValidationError):
                self.profile.full_clean()

    def test_avatar_upload(self):
        """Тест загрузки аватара."""
        avatar = SimpleUploadedFile(
            "test_avatar.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        self.profile.avatar = avatar
        self.profile.save()
        self.assertTrue(self.profile.avatar)
        self.assertNotEqual(self.profile.avatar.name, 'images/avatars/default.png')

    def test_str_representation(self):
        """Тест строкового представления профиля."""
        expected = f"Профиль {self.user.username}"
        self.assertEqual(str(self.profile), expected)


class EmailVerifiedModelTests(TestCase):
    """Тесты для модели EmailVerified."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.email_verified = EmailVerified.objects.create(
            user=self.user,
            confirmation_code='123456',
            code_created_at=timezone.now()
        )

    def test_email_verified_creation(self):
        """Тест создания объекта подтверждения email."""
        self.assertIsNotNone(self.email_verified)
        self.assertEqual(self.email_verified.user, self.user)
        self.assertEqual(self.email_verified.confirmation_code, '123456')

    def test_code_created_at_auto_set(self):
        """Тест автоматической установки времени создания кода."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='NewPass123!'
        )
        new_verified = EmailVerified.objects.create(
            user=new_user,
            confirmation_code='654321'
        )
        self.assertIsNotNone(new_verified.code_created_at)

    def test_str_representation(self):
        """Тест строкового представления объекта подтверждения email."""
        expected = f'{self.user.email}-{self.email_verified.code_created_at}'
        self.assertEqual(str(self.email_verified), expected)

    def test_unique_user_constraint(self):
        """Тест ограничения уникальности пользователя."""
        with self.assertRaises(Exception):
            EmailVerified.objects.create(
                user=self.user,
                confirmation_code='987654'
            ) 