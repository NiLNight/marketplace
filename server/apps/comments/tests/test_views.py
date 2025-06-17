"""Модуль тестов для представлений приложения comments.

Тестирует API-эндпоинты для работы с комментариями: создание, обновление, лайки и получение списков.
"""

import json
import logging
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.comments.models import Comment
from apps.products.models import Product, Category
from apps.reviews.models import Review

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentViewsTest(TestCase):
    """Тесты для представлений комментариев.

    Проверяет API-эндпоинты для работы с комментариями.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, категорию, продукт, отзыв и комментарий.
        """
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        # Создаем тестовую категорию
        self.category = Category.objects.create(title='Электроника')
        # Создаем тестовый продукт
        self.product = Product.objects.create(
            title='iPhone 15',
            category=self.category,
            price=Decimal('999.99'),
            stock=10,
            user=self.user,
            is_active=True
        )
        # Создаем тестовый отзыв
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )
        # Создаем тестовый комментарий
        self.comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Тестовый комментарий'
        )
        # Создаем тестовый клиент
        self.client = APIClient()
        cache.clear()

    def test_comment_list(self):
        """Тест получения списка комментариев."""
        url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['text'], 'Тестовый комментарий')

    def test_comment_create_authenticated(self):
        """Тест создания комментария аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.user)
        url = reverse('comment-create')
        data = {
            'review': self.review.id,
            'text': 'Новый комментарий'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Новый комментарий')
        self.assertEqual(Comment.objects.count(), 2)

    def test_comment_create_unauthenticated(self):
        """Тест попытки создания комментария неаутентифицированным пользователем."""
        url = reverse('comment-create')
        data = {
            'review': self.review.id,
            'text': 'Новый комментарий'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comment_update_owner(self):
        """Тест обновления комментария его автором."""
        self.client.force_authenticate(user=self.user)
        url = reverse('comment-update', args=[self.comment.id])
        data = {
            'text': 'Обновленный комментарий'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Обновленный комментарий')

    def test_comment_update_other_user(self):
        """Тест попытки обновления комментария другим пользователем."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=other_user)
        url = reverse('comment-update', args=[self.comment.id])
        data = {
            'text': 'Попытка изменить чужой комментарий'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_delete_owner(self):
        """Тест удаления комментария его автором."""
        self.client.force_authenticate(user=self.user)
        url = reverse('comment-delete', args=[self.comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_delete_other_user(self):
        """Тест попытки удаления комментария другим пользователем."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=other_user)
        url = reverse('comment-delete', args=[self.comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_like(self):
        """Тест лайка комментария."""
        self.client.force_authenticate(user=self.user)
        url = reverse('comment-like', args=[self.comment.id])

        # Добавляем лайк
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'liked')
        self.assertEqual(self.comment.likes.count(), 1)

        # Убираем лайк
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'unliked')
        self.assertEqual(self.comment.likes.count(), 0)

    def test_comment_list_ordering(self):
        """Тест сортировки списка комментариев."""
        # Создаем второй комментарий
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass'
        )
        Comment.objects.create(
            review=self.review,
            user=user2,
            text='Второй комментарий'
        )

        url = reverse('comment-list', args=[self.review.id])

        # Проверяем сортировку по дате создания (по убыванию)
        response = self.client.get(url + '?ordering=-created')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['text'], 'Второй комментарий')

    def test_comment_list_pagination(self):
        """Тест пагинации списка комментариев."""
        # Очищаем кэш перед тестом
        cache.clear()

        # У нас уже есть один комментарий из setUp
        # Создаем еще 11 комментариев, чтобы получить 2 на второй странице
        for i in range(11):
            Comment.objects.create(
                review=self.review,
                user=self.user,
                text=f'Комментарий {i}',
                parent=None  # Явно указываем, что это корневые комментарии
            )

        # Проверяем общее количество комментариев
        total_comments = Comment.objects.filter(review=self.review, parent=None).count()
        logger.info(f"Total root comments created: {total_comments}")

        url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Проверяем, что на первой странице 10 результатов
        self.assertIsNotNone(response.data['next'])  # Проверяем, что есть следующая страница
        self.assertIsNone(response.data['previous'])  # Проверяем, что нет предыдущей страницы

        # Проверяем вторую страницу
        response = self.client.get(response.data['next'])
        logger.info(f"Second page results: {len(response.data['results'])} comments")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # На второй странице должно быть 2 комментария
        self.assertIsNone(response.data['next'])  # Проверяем, что нет следующей страницы
        self.assertIsNotNone(response.data['previous'])  # Проверяем, что есть предыдущая страница

    def test_comment_create_with_parent(self):
        """Тест создания вложенного комментария."""
        self.client.force_authenticate(user=self.user)
        url = reverse('comment-create')
        data = {
            'review': self.review.id,
            'text': 'Ответ на комментарий',
            'parent': self.comment.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], self.comment.id)
        self.assertEqual(response.data['text'], 'Ответ на комментарий')