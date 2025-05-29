"""Модуль тестов для приложения reviews.

Содержит тесты для проверки функциональности отзывов и комментариев,
их создания, обновления, модерации и других возможностей приложения reviews.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.reviews.models import Review, Comment
from apps.reviews.exceptions import ReviewNotFound, CommentNotFound

User = get_user_model()


class ReviewTests(TestCase):
    """Тесты для модели Review.

    Проверяет создание, валидацию и обновление отзывов.

    Attributes:
        client (Client): Тестовый клиент Django.
        reviews_url (str): URL для работы с отзывами.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.reviews_url = reverse('reviews:review_list')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.review = Review.objects.create(
            user=self.user,
            text='Тестовый отзыв',
            rating=5
        )

    def test_review_creation(self):
        """Тест создания отзыва."""
        review = Review.objects.create(
            user=self.user,
            text='Новый отзыв',
            rating=4
        )
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.text, 'Новый отзыв')
        self.assertTrue(review.is_active)

    def test_review_str(self):
        """Тест строкового представления отзыва."""
        expected = f"Отзыв #{self.review.id} от {self.user.username}"
        self.assertEqual(str(self.review), expected)

    def test_review_validation(self):
        """Тест валидации отзыва."""
        # Проверка некорректного рейтинга
        with self.assertRaises(ValidationError):
            Review.objects.create(
                user=self.user,
                text='Тест',
                rating=6
            )

        # Проверка пустого текста
        with self.assertRaises(ValidationError):
            Review.objects.create(
                user=self.user,
                text='',
                rating=5
            )


class CommentTests(TestCase):
    """Тесты для модели Comment.

    Проверяет создание, валидацию и обновление комментариев.

    Attributes:
        client (Client): Тестовый клиент Django.
        comments_url (str): URL для работы с комментариями.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.review = Review.objects.create(
            user=self.user,
            text='Тестовый отзыв',
            rating=5
        )
        self.comment = Comment.objects.create(
            user=self.user,
            review=self.review,
            text='Тестовый комментарий'
        )

    def test_comment_creation(self):
        """Тест создания комментария."""
        comment = Comment.objects.create(
            user=self.user,
            review=self.review,
            text='Новый комментарий'
        )
        self.assertEqual(comment.text, 'Новый комментарий')
        self.assertTrue(comment.is_active)

    def test_comment_str(self):
        """Тест строкового представления комментария."""
        expected = f"Комментарий #{self.comment.id} от {self.user.username}"
        self.assertEqual(str(self.comment), expected)

    def test_comment_validation(self):
        """Тест валидации комментария."""
        # Проверка пустого текста
        with self.assertRaises(ValidationError):
            Comment.objects.create(
                user=self.user,
                review=self.review,
                text=''
            )

        # Проверка комментария к неактивному отзыву
        self.review.is_active = False
        self.review.save()
        with self.assertRaises(ValidationError):
            Comment.objects.create(
                user=self.user,
                review=self.review,
                text='Тест'
            )
