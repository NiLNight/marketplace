from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from apps.core.models import Like

User = get_user_model()


class TimeStampedModelTest(TestCase):
    """
    Тесты для абстрактной модели TimeStampedModel.
    Проверяет автоматическое создание временных меток.
    """

    def test_timestamps(self):
        like = Like.objects.create(
            user=User.objects.create_user('testuser', 'test@example.com', 'password'),
            content_type=ContentType.objects.first(),
            object_id=1
        )
        self.assertIsNotNone(like.created)
        self.assertIsNotNone(like.updated)


class LikeModelTest(TestCase):
    """
    Тесты для модели Like: создание, валидация, уникальность, __str__.
    """

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.content_type = ContentType.objects.first()

    def test_like_creation(self):
        like = Like.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=1
        )
        self.assertEqual(str(like), f"Лайк от {self.user.username} для {self.content_type.model}:1")

    def test_like_validation(self):
        like = Like(
            user=self.user,
            content_type=self.content_type,
            object_id=999999  # Несуществующий объект
        )
        with self.assertRaises(ValidationError):
            like.full_clean()

    def test_like_uniqueness(self):
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
