"""Модуль тестов для сервисов приложения reviews."""

import logging
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from apps.reviews.models import Review
from apps.reviews.services.reviews_services import ReviewService
from apps.core.services.cache_services import CacheService
from apps.products.models import Product, Category
from apps.core.models import Like
from apps.reviews.exceptions import InvalidReviewData
from apps.reviews.serializers import ReviewSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewServiceTest(TestCase):
    """Тесты для сервиса Review.

    Проверяет бизнес-логику работы с отзывами.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, продукт и отзыв.
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
        self.review_data = {
            'product': self.product,
            'value': 5,
            'text': 'Отличный продукт!'
        }
        self.review = Review.objects.create(
            user=self.user,
            **self.review_data
        )
        cache.clear()

    def test_get_reviews(self):
        """Тест получения списка отзывов."""
        reviews = ReviewService.get_reviews(self.product.id)
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.first(), self.review)

    def test_create_review(self):
        """Тест создания отзыва."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        data = {
            'product': self.product,
            'value': 4,
            'text': 'Новый отзыв'
        }
        review = ReviewService.create_review(data, user2)
        
        self.assertEqual(review.value, 4)
        self.assertEqual(review.text, 'Новый отзыв')
        self.assertEqual(review.user, user2)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.likes.count(), 0)

    def test_create_duplicate_review(self):
        """Тест попытки создания повторного отзыва."""
        data = {
            'product': self.product,
            'value': 4,
            'text': 'Повторный отзыв'
        }
        with self.assertRaises(InvalidReviewData) as context:
            ReviewService.create_review(data, self.user)
        self.assertIn('Вы уже оставили отзыв на этот продукт', str(context.exception))

    def test_update_review(self):
        """Тест обновления отзыва."""
        data = {
            'value': 3,
            'text': 'Обновленный отзыв'
        }
        updated_review = ReviewService.update_review(self.review.id, data, self.user)
        
        self.assertEqual(updated_review.value, 3)
        self.assertEqual(updated_review.text, 'Обновленный отзыв')
        self.assertEqual(updated_review.user, self.user)

    def test_update_other_user_review(self):
        """Тест попытки обновления чужого отзыва."""
        other_user = User.objects.create_user('other', 'other@example.com', 'pass123')
        data = {
            'value': 3,
            'text': 'Попытка изменить чужой отзыв'
        }
        with self.assertRaises(PermissionDenied):
            ReviewService.update_review(self.review.id, data, other_user)

    def test_apply_ordering(self):
        """Тест применения сортировки к списку отзывов."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        Review.objects.create(
            user=user2,
            product=self.product,
            value=2,
            text='Плохой отзыв'
        )
        
        # Тест сортировки по оценке (по возрастанию)
        reviews = Review.objects.all()
        ordered_reviews = ReviewService.apply_ordering(reviews, 'value')
        self.assertEqual(ordered_reviews[0].value, 2)
        self.assertEqual(ordered_reviews[1].value, 5)
        
        # Тест сортировки по оценке (по убыванию)
        ordered_reviews = ReviewService.apply_ordering(reviews, '-value')
        self.assertEqual(ordered_reviews[0].value, 5)
        self.assertEqual(ordered_reviews[1].value, 2)

    def test_review_with_image(self):
        """Тест создания отзыва с изображением."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        image_data = b'fake-image-data'
        image = SimpleUploadedFile(
            'test_image.jpg',
            image_data,
            content_type='image/jpeg'
        )
        data = {
            'product': self.product,
            'value': 4,
            'text': 'Отзыв с картинкой',
            'image': image
        }
        review = ReviewService.create_review(data, user2)
        
        self.assertTrue(review.image)
        self.assertTrue(review.image.name.endswith('.jpg'))

    def test_review_cache(self):
        """Тест кэширования отзывов."""
        # Создаем DRF Request с параметрами
        wsgi_request = self.factory.get('/api/reviews/', {'page': 1, 'page_size': 10})
        request = Request(wsgi_request)
        
        # Проверяем, что кэш пуст
        cached_reviews = CacheService.cache_review_list(self.product.id, request)
        self.assertIsNone(cached_reviews)
        
        # Получаем отзывы и создаем response_data как в реальном приложении
        reviews = ReviewService.get_reviews(self.product.id)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(page, many=True, context={'request': request})
        response_data = paginator.get_paginated_response(serializer.data).data
        
        # Сохраняем в кэш
        cache_key = CacheService.build_cache_key(request, prefix=f"reviews:{self.product.id}")
        CacheService.set_cached_data(cache_key, response_data)
        
        # Проверяем, что данные в кэше
        cached_reviews = CacheService.cache_review_list(self.product.id, request)
        self.assertIsNotNone(cached_reviews)
        self.assertEqual(cached_reviews['count'], 1)
        
        # Создаем новый отзыв
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        data = {
            'product': self.product,
            'value': 4,
            'text': 'Новый отзыв'
        }
        ReviewService.create_review(data, user2)
        
        # Инвалидируем кэш с тем же ключом
        cache_key = CacheService.build_cache_key(request, prefix=f"reviews:{self.product.id}")
        cache.delete(cache_key)
        
        # Проверяем, что кэш инвалидирован
        cached_reviews = CacheService.cache_review_list(self.product.id, request)
        self.assertIsNone(cached_reviews)

    def test_review_validation(self):
        """Тест валидации данных отзыва."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        
        # Тест с некорректной оценкой
        data = {
            'product': self.product,
            'value': 6,
            'text': 'Тест'
        }
        with self.assertRaises(InvalidReviewData) as context:
            ReviewService.create_review(data, user2)
        self.assertEqual(str(context.exception), "Оценка должна быть числом от 1 до 5.")
        
        # Тест с пустым текстом (должен быть разрешен)
        data = {
            'product': self.product,
            'value': 4,
            'text': ''
        }
        review = ReviewService.create_review(data, user2)
        self.assertEqual(review.text, '')

    def test_review_likes(self):
        """Тест работы с лайками отзыва."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        user3 = User.objects.create_user('user3', 'user3@example.com', 'pass123')

        # Проверяем начальное количество лайков
        self.assertEqual(self.review.likes.count(), 0)

        # Добавляем лайки
        Like.objects.create(user=user2, content_object=self.review)
        self.assertEqual(self.review.likes.count(), 1)

        Like.objects.create(user=user3, content_object=self.review)
        self.assertEqual(self.review.likes.count(), 2)

        # Удаляем лайк
        Like.objects.filter(user=user2, content_type__model='review', object_id=self.review.id).delete()
        self.assertEqual(self.review.likes.count(), 1) 