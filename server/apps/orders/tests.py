"""Модуль тестов для приложения orders.

Содержит тесты для проверки функциональности заказов,
их создания, обновления и других возможностей приложения orders.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from decimal import Decimal
from apps.delivery.models import City, PickupPoint
from apps.orders.models import Order

User = get_user_model()


class OrderTests(TestCase):
    """Тесты для модели Order.

    Проверяет создание, валидацию и обновление заказов.

    Attributes:
        client (Client): Тестовый клиент Django.
        orders_url (str): URL для работы с заказами.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.orders_url = reverse('orders:order_list')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.city = City.objects.create(name='Москва')
        self.pickup_point = PickupPoint.objects.create(
            city=self.city,
            address='ул. Пушкина, д. 1',
            district='Центральный'
        )
        self.order = Order.objects.create(
            user=self.user,
            pickup_point=self.pickup_point,
            total_price=Decimal('100.00')
        )

    def test_order_creation(self):
        """Тест создания заказа."""
        order = Order.objects.create(
            user=self.user,
            pickup_point=self.pickup_point,
            total_price=Decimal('150.00')
        )
        self.assertEqual(order.total_price, Decimal('150.00'))
        self.assertEqual(order.status, 'processing')

    def test_order_str(self):
        """Тест строкового представления заказа."""
        expected = f"Заказ #{self.order.id} - {self.user.username}"
        self.assertEqual(str(self.order), expected)

    def test_order_validation(self):
        """Тест валидации заказа."""
        # Проверка отрицательной стоимости
        with self.assertRaises(ValidationError):
            Order.objects.create(
                user=self.user,
                pickup_point=self.pickup_point,
                total_price=Decimal('-50.00')
            )

        # Проверка неактивного пункта выдачи
        self.pickup_point.is_active = False
        self.pickup_point.save()
        with self.assertRaises(ValidationError):
            Order.objects.create(
                user=self.user,
                pickup_point=self.pickup_point,
                total_price=Decimal('100.00')
            )

    def test_order_status_update(self):
        """Тест обновления статуса заказа."""
        self.order.status = 'shipped'
        self.order.save()
        self.assertEqual(self.order.status, 'shipped')

        self.order.status = 'delivered'
        self.order.save()
        self.assertEqual(self.order.status, 'delivered')
