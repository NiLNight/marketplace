"""Модуль тестов для приложения carts.

Содержит тесты для проверки функциональности корзины,
её создания, обновления и других возможностей приложения carts.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.products.models import Product, Category
from apps.carts.models import OrderItem
from apps.carts.exceptions import ProductNotAvailable, InvalidQuantity, CartItemNotFound
from apps.carts.services.cart_services import CartService

User = get_user_model()


class CartTests(TestCase):
    """Тесты для функциональности корзины.

    Проверяет создание, удаление и получение элементов корзины
    для авторизованных и неавторизованных пользователей.

    Attributes:
        client (Client): Тестовый клиент Django.
        cart_url (str): URL для работы с корзиной.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.cart_url = reverse('carts:carts')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=100.00,
            category=self.category,
            stock=10,
            user=self.user
        )

    def test_add_to_cart_authenticated(self):
        """Тест добавления товара в корзину авторизованным пользователем."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            OrderItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_add_to_cart_unauthenticated(self):
        """Тест добавления товара в корзину неавторизованным пользователем."""
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.session
        self.assertEqual(session.get('cart', {}).get(str(self.product.id)), 2)

    def test_update_cart_item(self):
        """Тест обновления количества товара в корзине."""
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.patch(
            reverse('carts:cart_item', args=[self.product.id]),
            {'quantity': 3}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            OrderItem.objects.get(user=self.user, product=self.product).quantity,
            3
        )

    def test_remove_from_cart(self):
        """Тест удаления товара из корзины."""
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.delete(
            reverse('carts:cart_item', args=[self.product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OrderItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_get_cart(self):
        """Тест получения содержимого корзины."""
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product']['id'], self.product.id)
        self.assertEqual(response.data[0]['quantity'], 2)

    def test_add_invalid_quantity(self):
        """Тест добавления некорректного количества товара."""
        self.client.force_login(self.user)
        with self.assertRaises(InvalidQuantity):
            CartService.add_to_cart(
                request=type('Request', (), {'user': self.user}),
                product_id=self.product.id,
                quantity=0
            )

    def test_add_inactive_product(self):
        """Тест добавления неактивного товара."""
        self.client.force_login(self.user)
        self.product.is_active = False
        self.product.save()
        with self.assertRaises(ProductNotAvailable):
            CartService.add_to_cart(
                request=type('Request', (), {'user': self.user}),
                product_id=self.product.id
            )

    def test_remove_nonexistent_item(self):
        """Тест удаления несуществующего товара."""
        self.client.force_login(self.user)
        with self.assertRaises(CartItemNotFound):
            CartService.remove_from_cart(
                request=type('Request', (), {'user': self.user}),
                product_id=999999
            )
