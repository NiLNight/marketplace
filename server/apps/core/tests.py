"""Модуль тестов для приложения core.

Содержит тесты для проверки функциональности базовых моделей и утилит.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from apps.core.models import Like
from apps.core.utils import unique_slugify

User = get_user_model()


class TimeStampedModelTest(TestCase):
    """Тесты для абстрактной модели TimeStampedModel.

    Проверяет автоматическое создание временных меток.
    """

    def test_timestamps(self):
        """Тест автоматического создания временных меток."""
        like = Like.objects.create(
            user=User.objects.create_user('testuser', 'test@example.com', 'password'),
            content_type=ContentType.objects.first(),
            object_id=1
        )
        self.assertIsNotNone(like.created)
        self.assertIsNotNone(like.updated)


class LikeModelTest(TestCase):
    """Тесты для модели Like.

    Проверяет создание, валидацию и уникальность лайков.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.content_type = ContentType.objects.first()

    def test_like_creation(self):
        """Тест создания лайка."""
        like = Like.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=1
        )
        self.assertEqual(str(like), f"Лайк от {self.user.username} для {self.content_type.model}:1")

    def test_like_validation(self):
        """Тест валидации лайка."""
        like = Like(
            user=self.user,
            content_type=self.content_type,
            object_id=999999  # Несуществующий объект
        )
        with self.assertRaises(ValidationError):
            like.full_clean()

    def test_like_uniqueness(self):
        """Тест уникальности лайка."""
        Like.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=1
        )
        with self.assertRaises(Exception):
            Like.objects.create(
                user=self.user,
                content_type=self.content_type,
                object_id=1
            )


class UniqueSlugifyTest(TestCase):
    """Тесты для функции unique_slugify.

    Проверяет генерацию уникальных слагов.
    """

    def test_slugify_basic(self):
        """Тест базовой функциональности генерации слага."""
        slug = unique_slugify("Test Title")
        self.assertTrue(slug.startswith("test-title-"))
        self.assertEqual(len(slug.split("-")[-1]), 8)  # UUID часть

    def test_slugify_cyrillic(self):
        """Тест генерации слага для кириллицы."""
        slug = unique_slugify("Тестовый Заголовок")
        self.assertTrue(slug.startswith("testovyj-zagolovok-"))
        self.assertEqual(len(slug.split("-")[-1]), 8)

    def test_slugify_invalid_input(self):
        """Тест обработки некорректного ввода."""
        with self.assertRaises(TypeError):
            unique_slugify(123)  # Не строка
