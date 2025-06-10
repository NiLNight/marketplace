"""Модуль тестов для сервисов приложения comments."""

import logging
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from apps.comments.models import Comment
from apps.comments.services.comment_services import CommentService
from apps.core.services.cache_services import CacheService
from apps.products.models import Product, Category
from apps.reviews.models import Review
from apps.comments.exceptions import CommentNotFound, InvalidCommentData
from apps.comments.serializers import CommentSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentServiceTest(TestCase):
    """Тесты для сервиса Comment.

    Проверяет бизнес-логику работы с комментариями.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, продукт, отзыв и комментарий.
        """
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        self.product = Product.objects.create(
            title='iPhone 15',
            description='Новый iPhone',
            price=Decimal('999.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )
        self.comment_data = {
            'review': self.review,
            'text': 'Тестовый комментарий'
        }
        self.comment = Comment.objects.create(
            user=self.user,
            **self.comment_data
        )
        cache.clear()

    def test_get_comments(self):
        """Тест получения списка комментариев."""
        comments = CommentService.get_comments(self.review.id, request=self.factory.get('/'))
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0], self.comment)

    def test_create_comment(self):
        """Тест создания комментария."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        data = {
            'review': self.review,
            'text': 'Новый комментарий'
        }
        comment = CommentService.create_comment(data, user2)

        self.assertEqual(comment.text, 'Новый комментарий')
        self.assertEqual(comment.user, user2)
        self.assertEqual(comment.review, self.review)

    def test_create_comment_with_parent(self):
        """Тест создания вложенного комментария."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        data = {
            'review': self.review,
            'text': 'Ответ на комментарий',
            'parent': self.comment
        }
        comment = CommentService.create_comment(data, user2)

        self.assertEqual(comment.text, 'Ответ на комментарий')
        self.assertEqual(comment.parent, self.comment)
        self.assertEqual(comment.review, self.review)

    def test_create_comment_empty_text(self):
        """Тест попытки создания комментария с пустым текстом."""
        data = {
            'review': self.review,
            'text': ''
        }
        with self.assertRaises(InvalidCommentData) as context:
            CommentService.create_comment(data, self.user)
        self.assertIn('Текст комментария не может быть пустым', str(context.exception))

    def test_update_comment(self):
        """Тест обновления комментария."""
        data = {
            'text': 'Обновленный комментарий'
        }
        updated_comment = CommentService.update_comment(self.comment.id, data, self.user)

        self.assertEqual(updated_comment.text, 'Обновленный комментарий')
        self.assertEqual(updated_comment.user, self.user)

    def test_update_other_user_comment(self):
        """Тест попытки обновления чужого комментария."""
        other_user = User.objects.create_user('other', 'other@example.com', 'pass123')
        data = {
            'text': 'Попытка изменить чужой комментарий'
        }
        with self.assertRaises(PermissionDenied):
            CommentService.update_comment(self.comment.id, data, other_user)

    def test_delete_comment(self):
        """Тест удаления комментария."""
        CommentService.delete_comment(self.comment.id, self.user)
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(pk=self.comment.id)

    def test_delete_other_user_comment(self):
        """Тест попытки удаления чужого комментария."""
        other_user = User.objects.create_user('other', 'other@example.com', 'pass123')
        with self.assertRaises(PermissionDenied):
            CommentService.delete_comment(self.comment.id, other_user)

    def test_get_nonexistent_comment(self):
        """Тест получения несуществующего комментария."""
        with self.assertRaises(CommentNotFound):
            CommentService.get_comments(999, self.factory.get('/'))

    def test_create_comment_invalid_review(self):
        """Тест создания комментария с несуществующим отзывом."""
        data = {
            'review': 999,
            'text': 'Тестовый комментарий'
        }
        with self.assertRaises(InvalidCommentData):
            CommentService.create_comment(data, self.user)

    def test_create_comment_invalid_parent(self):
        """Тест создания комментария с неверным родительским комментарием."""
        # Создаем другой продукт
        other_product = Product.objects.create(
            title='Samsung Galaxy',
            description='Другой продукт',
            price=Decimal('799.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )
        # Создаем отзыв для другого продукта
        other_review = Review.objects.create(
            product=other_product,
            user=self.user,
            value=4,
            text='Другой отзыв'
        )
        other_comment = Comment.objects.create(
            review=other_review,
            user=self.user,
            text='Комментарий к другому отзыву'
        )

        data = {
            'review': self.review.id,  # Передаем ID отзыва
            'text': 'Тестовый комментарий',
            'parent': other_comment.id  # Передаем ID родительского комментария
        }
        with self.assertRaises(InvalidCommentData) as context:
            CommentService.create_comment(data, self.user)
        self.assertIn('Родительский комментарий должен относиться к тому же отзыву', str(context.exception))
