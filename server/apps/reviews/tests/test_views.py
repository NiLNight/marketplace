"""Модуль тестов для представлений приложения reviews.

Тестирует API-эндпоинты для работы с отзывами: создание, обновление, лайки и получение списков.
"""

import json
import logging
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.reviews.models import Review
from apps.products.models import Product, Category
from apps.core.models import Like
from apps.core.services.cache_services import CacheService
import os

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewViewsTest(TestCase):
    """Тесты для представлений отзывов.

    Проверяет API-эндпоинты для работы с отзывами.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, категорию, продукт и отзыв.
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
            is_active=True  # Явно устанавливаем продукт как активный
        )
        # Создаем тестовый отзыв
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )
        # Создаем тестовый клиент
        self.client = APIClient()

        # Создаем директорию для тестовых изображений
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        if not os.path.exists(self.test_data_dir):
            os.makedirs(self.test_data_dir)

        # Создаем тестовое изображение
        self.test_image_path = os.path.join(self.test_data_dir, 'test_image.jpg')
        with open(self.test_image_path, 'wb') as f:
            # Минимальный валидный JPEG файл
            f.write(bytes([
                0xFF, 0xD8,                    # SOI
                0xFF, 0xE0, 0x00, 0x10,        # APP0
                0x4A, 0x46, 0x49, 0x46, 0x00,  # 'JFIF\0'
                0x01, 0x01,                    # версия 1.1
                0x00,                          # единицы измерения
                0x00, 0x01,                    # плотность по X
                0x00, 0x01,                    # плотность по Y
                0x00, 0x00,                    # миниатюра
                0xFF, 0xDB, 0x00, 0x43, 0x00,  # DQT
                *([0x01] * 64),                # таблица квантования
                0xFF, 0xC0, 0x00, 0x0B,        # SOF0 (baseline)
                0x08, 0x00, 0x01, 0x00, 0x01,  # параметры изображения
                0x01, 0x01, 0x11, 0x00,        # параметры компонента
                0xFF, 0xDA, 0x00, 0x08,        # SOS
                0x01, 0x01, 0x00, 0x00, 0x3F, 0x00  # параметры сканирования
            ]))

    def tearDown(self):
        """Очистка после тестов."""
        # Удаляем тестовое изображение и директорию
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        if os.path.exists(self.test_data_dir):
            os.rmdir(self.test_data_dir)

    def test_review_list_unauthorized(self):
        """Тест получения списка отзывов без авторизации."""
        url = reverse('review-list', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_review_list_with_cache(self):
        """Тест кэширования списка отзывов."""
        url = reverse('review-list', args=[self.product.id])

        # Первый запрос (кэш пуст)
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Второй запрос (данные из кэша)
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

        # Создаем новый отзыв (должен инвалидировать кэш)
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=user2)
        create_url = reverse('review-create')
        data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Новый отзыв'
        }
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Очищаем кэш перед третьим запросом
        cache.clear()

        # Третий запрос (кэш должен быть инвалидирован)
        response3 = self.client.get(url)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response1.data, response3.data)
        self.assertEqual(len(response3.data['results']), 2)  # Проверяем, что теперь два отзыва

    def test_review_list_ordering(self):
        """Тест сортировки списка отзывов."""
        # Создаем второй отзыв
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass'
        )
        Review.objects.create(
            product=self.product,
            user=user2,
            value=3,
            text='Хороший продукт'
        )

        url = reverse('review-list', args=[self.product.id])

        # Проверяем сортировку по дате создания (по убыванию)
        response = self.client.get(url + '?ordering=-created')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['value'], 3)

        # Проверяем сортировку по оценке (по возрастанию)
        response = self.client.get(url + '?ordering=value')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['value'], 3)

    def test_review_create_authorized(self):
        """Тест создания отзыва с авторизацией."""
        # Создаем второго пользователя
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=user2)

        # Создаем тестовое изображение
        with open(self.test_image_path, 'rb') as image_file:
            image = SimpleUploadedFile(
                name='test_image.jpg',
                content=image_file.read(),
                content_type='image/jpeg'
            )

        url = reverse('review-create')
        data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Новый отзыв',
            'image': image
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Новый отзыв')
        self.assertEqual(response.data['value'], 4)
        self.assertIsNotNone(response.data['image'])

    def test_review_create_unauthorized(self):
        """Тест создания отзыва без авторизации."""
        url = reverse('review-create')
        data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Новый отзыв'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_create_duplicate(self):
        """Тест попытки создания повторного отзыва."""
        self.client.force_authenticate(user=self.user)
        url = reverse('review-create')
        data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Повторный отзыв'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_update_authorized(self):
        """Тест обновления отзыва с авторизацией."""
        self.client.force_authenticate(user=self.user)
        url = reverse('review-update', args=[self.review.id])
        data = {
            'value': 3,
            'text': 'Обновленный отзыв'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Обновленный отзыв')
        self.assertEqual(response.data['value'], 3)

    def test_review_update_unauthorized(self):
        """Тест обновления отзыва без авторизации."""
        url = reverse('review-update', args=[self.review.id])
        data = {
            'value': 3,
            'text': 'Обновленный отзыв'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_update_other_user(self):
        """Тест попытки обновления чужого отзыва."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=other_user)
        url = reverse('review-update', args=[self.review.id])
        data = {
            'value': 3,
            'text': 'Попытка изменить чужой отзыв'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_like_authorized(self):
        """Тест лайка отзыва с авторизацией."""
        # Создаем второго пользователя для лайка
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass'
        )
        self.client.force_authenticate(user=user2)

        url = reverse('review-like', args=[self.review.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'liked')
        self.assertEqual(response.data['likes_count'], 1)

    def test_review_like_unauthorized(self):
        """Тест лайка отзыва без авторизации."""
        url = reverse('review-like', args=[self.review.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 