"""Модуль тестов для проверки интеграции между комментариями, отзывами и кэшированием."""

import logging
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Count
from unittest.mock import patch

from apps.comments.models import Comment
from apps.reviews.models import Review
from apps.products.models import Product, Category
from apps.core.services.cache_services import CacheService
from apps.core.models import Like

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentIntegrationTests(TestCase):
    """Тесты интеграции между комментариями, отзывами и кэшированием."""

    def setUp(self):
        """Подготовка данных для тестов."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Электроника')
        self.product = Product.objects.create(
            title='iPhone 15',
            description='Тестовый продукт',
            price=Decimal('999.99'),
            category=self.category,
            user=self.user,
            stock=10,
            is_active=True
        )
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def test_cache_invalidation_chain(self):
        """Тест цепочки инвалидации кэша при создании комментария."""
        # Получаем список комментариев и проверяем, что он кэшируется
        url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные в кэше
        cached_data = CacheService.cache_comment_list(self.review.id, response.wsgi_request)
        self.assertIsNotNone(cached_data)

        # Создаем новый комментарий
        create_url = reverse('comment-create')
        data = {
            'review': self.review.id,
            'text': 'Новый комментарий'
        }
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что кэш инвалидирован
        cached_data = CacheService.cache_comment_list(self.review.id, response.wsgi_request)
        self.assertIsNone(cached_data)

    def test_comment_tree_structure(self):
        """Тест древовидной структуры комментариев."""
        # Создаем корневой комментарий
        root_comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Корневой комментарий'
        )

        # Создаем дочерние комментарии
        child1 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 1',
            parent=root_comment
        )
        child2 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 2',
            parent=root_comment
        )
        grandchild = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Комментарий третьего уровня',
            parent=child1
        )

        # Получаем список комментариев
        url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру дерева в ответе
        root = next(c for c in response.data['results'] if c['id'] == root_comment.id)
        self.assertEqual(len(root['children']), 2)
        child1_data = next(c for c in root['children'] if c['id'] == child1.id)
        self.assertEqual(len(child1_data['children']), 1)
        self.assertEqual(child1_data['children'][0]['id'], grandchild.id)

    def test_comment_likes_integration(self):
        """Тест интеграции комментариев с системой лайков."""
        # Создаем комментарий
        comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Комментарий для лайков'
        )

        # Создаем второго пользователя
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)

        # Добавляем лайк
        url = reverse('comment-like', args=[comment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'liked')

        # Проверяем, что лайк отображается в списке комментариев
        list_url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(list_url)
        comment_data = next(c for c in response.data['results'] if c['id'] == comment.id)
        self.assertEqual(comment_data['likes_count'], 1)

    def test_comment_deletion_cascade(self):
        """Тест каскадного удаления комментариев и связанных данных."""
        # Создаем корневой комментарий
        root_comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Корневой комментарий'
        )

        # Создаем дочерние комментарии и лайки
        child = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий',
            parent=root_comment
        )
        Like.objects.create(user=self.user, content_object=root_comment)
        Like.objects.create(user=self.user, content_object=child)

        # Удаляем корневой комментарий
        url = reverse('comment-delete', args=[root_comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что все связанные данные удалены
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(Like.objects.count(), 0)

    def test_review_comment_count(self):
        """Тест подсчета комментариев к отзыву."""
        # Создаем комментарии
        Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Комментарий 1'
        )
        root = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Комментарий 2'
        )
        Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Ответ на комментарий 2',
            parent=root
        )

        # Проверяем количество комментариев
        review_with_count = Review.objects.annotate(
            comment_count=Count('comments')
        ).get(id=self.review.id)
        self.assertEqual(review_with_count.comment_count, 3)

    def test_comment_cache_invalidation_on_like(self):
        """Тест инвалидации кэша комментариев при добавлении/удалении лайков."""
        # Создаем комментарий
        comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Комментарий для лайков'
        )

        # Получаем список комментариев и проверяем кэширование
        url = reverse('comment-list', args=[self.review.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные в кэше
        cached_data = CacheService.cache_comment_list(self.review.id, response.wsgi_request)
        self.assertIsNotNone(cached_data)

        # Добавляем лайк
        like_url = reverse('comment-like', args=[comment.id])
        response = self.client.post(like_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что кэш инвалидирован
        cached_data = CacheService.cache_comment_list(self.review.id, response.wsgi_request)
        self.assertIsNone(cached_data)
