"""Модуль тестов для проверки интеграции между отзывами, рейтингами и кэшированием."""

import logging
from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Avg
from unittest.mock import patch

from apps.reviews.models import Review
from apps.products.models import Product, Category
from apps.core.services.cache_services import CacheService
from apps.products.services.query_services import ProductQueryService
from apps.products.utils import calculate_popularity_score
from apps.orders.models import Order
from apps.carts.models import OrderItem
from apps.delivery.models import PickupPoint, City
from apps.products.services.tasks import update_popularity_score

User = get_user_model()
logger = logging.getLogger(__name__)


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class ReviewIntegrationTests(TestCase):
    """Тесты интеграции между отзывами, рейтингами, популярностью и кэшированием."""

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
        self.city = City.objects.create(name='Москва')
        self.pickup_point = PickupPoint.objects.create(
            city=self.city,
            address='ул. Тестовая, д. 1',
            district='Тестовый район',
            is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def get_rating_avg(self, product_id):
        """Вычисляет средний рейтинг продукта."""
        return Review.objects.filter(product_id=product_id).aggregate(Avg('value'))['value__avg'] or 0.0

    def test_cache_invalidation_chain(self):
        """Тест цепочки инвалидации кэша при создании отзыва."""
        # Получаем начальные данные
        response = self.client.get(reverse('products:product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('review-list', args=[self.product.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Создаем отзыв
        data = {
            'product': self.product.id,
            'value': 5,
            'text': 'Отличный продукт!'
        }
        response = self.client.post(reverse('review-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Для тестов вызываем обновление популярности синхронно
        update_popularity_score(self.product.id)

        # Проверяем, что кэш инвалидирован
        self.assertIsNone(cache.get(f'product_detail:{self.product.id}'))
        self.assertIsNone(cache.get(f'product_list'))
        self.assertIsNone(cache.get(f'reviews:{self.product.id}'))

    def test_review_affects_product_rating(self):
        """Тест влияния отзыва на рейтинг продукта."""
        # Создаем первый отзыв
        data = {
            'product': self.product.id,
            'value': 5,
            'text': 'Отличный продукт!'
        }
        response = self.client.post(reverse('review-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем рейтинг
        rating_avg = self.get_rating_avg(self.product.id)
        self.assertEqual(rating_avg, 5.0)

        # Создаем второй отзыв от другого пользователя
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)
        data = {
            'product': self.product.id,
            'value': 3,
            'text': 'Нормальный продукт'
        }
        response = self.client.post(reverse('review-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем обновленный рейтинг
        rating_avg = self.get_rating_avg(self.product.id)
        self.assertEqual(rating_avg, 4.0)

    def test_review_affects_popularity_score(self):
        """Тест влияния отзыва на показатель популярности продукта."""
        initial_score = calculate_popularity_score(self.product)

        # Создаем отзыв
        data = {
            'product': self.product.id,
            'value': 5,
            'text': 'Отличный продукт!'
        }
        response = self.client.post(reverse('review-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что показатель популярности увеличился
        new_score = calculate_popularity_score(self.product)
        self.assertGreater(new_score, initial_score)

    def test_order_affects_popularity(self):
        """Тест влияния заказов на показатель популярности продукта."""
        initial_score = calculate_popularity_score(self.product)

        # Создаем заказ
        order = Order.objects.create(
            user=self.user,
            status='processing',
            total_price=Decimal('999.99'),
            pickup_point=self.pickup_point
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1
        )

        # Проверяем, что показатель популярности увеличился
        new_score = calculate_popularity_score(self.product)
        self.assertGreater(new_score, initial_score)

    def test_multiple_orders_and_reviews(self):
        """Тест совместного влияния нескольких заказов и отзывов на популярность."""
        initial_score = calculate_popularity_score(self.product)

        # Создаем заказы
        for _ in range(3):
            order = Order.objects.create(
                user=self.user,
                status='processing',
                total_price=Decimal('999.99'),
                pickup_point=self.pickup_point
            )
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=1
            )

        # Создаем отзывы
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            self.client.force_authenticate(user=user)
            data = {
                'product': self.product.id,
                'value': 4,
                'text': f'Отзыв от user{i}'
            }
            response = self.client.post(reverse('review-create'), data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что показатель популярности значительно увеличился
        new_score = calculate_popularity_score(self.product)
        self.assertGreater(new_score, initial_score * 2)

    def test_review_updates_elasticsearch(self):
        """Тест обновления данных в Elasticsearch при создании отзыва."""
        # Создаем отзыв
        data = {
            'product': self.product.id,
            'value': 5,
            'text': 'Отличный продукт!'
        }
        response = self.client.post(reverse('review-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем поиск в Elasticsearch
        response = self.client.get(reverse('products:product_list'), {'q': 'iphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.product.id)
        self.assertEqual(float(response.data['results'][0]['rating_avg']), 5.0)

    def test_review_delete_affects_metrics(self):
        """Тест влияния удаления отзыва на метрики продукта."""
        # Создаем отзыв
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            value=5,
            text='Отличный продукт!'
        )

        # Получаем метрики до удаления
        rating_before = self.get_rating_avg(self.product.id)
        popularity_before = calculate_popularity_score(self.product)

        # Удаляем отзыв
        review.delete()

        # Проверяем метрики после удаления
        rating_after = self.get_rating_avg(self.product.id)
        popularity_after = calculate_popularity_score(self.product)

        self.assertNotEqual(rating_before, rating_after)
        self.assertGreater(popularity_before, popularity_after)

    def test_review_update_affects_all_metrics(self):
        """Тест влияния обновления отзыва на все метрики продукта."""
        # Создаем отзыв
        review = Review.objects.create(
            user=self.user,
            product=self.product,
            value=3,
            text='Нормальный продукт'
        )

        # Получаем метрики до обновления
        rating_before = self.get_rating_avg(self.product.id)
        popularity_before = calculate_popularity_score(self.product)

        # Обновляем отзыв через PATCH
        data = {
            'value': 5,
            'text': 'Отличный продукт!'
        }
        response = self.client.patch(reverse('review-update', args=[review.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Для тестов вызываем обновление популярности синхронно
        update_popularity_score(self.product.id)

        # Проверяем метрики после обновления
        rating_after = self.get_rating_avg(self.product.id)
        popularity_after = calculate_popularity_score(self.product)

        self.assertGreater(rating_after, rating_before)
        self.assertGreater(popularity_after, popularity_before)

    def test_popularity_score_components(self):
        """Тест компонентов, влияющих на показатель популярности."""
        # Создаем заказ
        order = Order.objects.create(
            user=self.user,
            status='processing',
            total_price=Decimal('999.99'),
            pickup_point=self.pickup_point
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1
        )

        # Создаем отзыв
        Review.objects.create(
            user=self.user,
            product=self.product,
            value=5,
            text='Отличный продукт!'
        )

        # Проверяем компоненты показателя популярности
        product = Product.objects.get(id=self.product.id)
        popularity_score = calculate_popularity_score(product)

        # Проверяем, что все компоненты влияют на показатель
        self.assertGreater(popularity_score, 0)
        self.assertEqual(self.get_rating_avg(self.product.id), 5.0)
        self.assertEqual(product.order_items.count(), 1)
        self.assertEqual(product.reviews.count(), 1)
