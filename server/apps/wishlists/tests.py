"""Модуль тестов для приложения wishlists.

Содержит тесты для проверки функциональности списков желаний,
их создания, обновления и других возможностей приложения wishlists.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.products.models import Product, Category
from apps.wishlists.models import WishlistItem
from apps.wishlists.exceptions import ProductNotAvailable, WishlistItemNotFound
from apps.wishlists.services.wishlist_services import WishlistService

User = get_user_model()


class WishlistTests(TestCase):
    """Тесты для функциональности списков желаний.

    Проверяет создание, удаление и получение элементов списка желаний
    для авторизованных и неавторизованных пользователей.

    Attributes:
        client (Client): Тестовый клиент Django.
        wishlist_url (str): URL для работы со списком желаний.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.wishlist_url = reverse('wishlist-get')
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

    def test_add_to_wishlist_authenticated(self):
        """Тест добавления товара в список желаний авторизованным пользователем."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('wishlist-add'),
            {'product_id': self.product.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            WishlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_add_to_wishlist_unauthenticated(self):
        """Тест добавления товара в список желаний неавторизованным пользователем."""
        response = self.client.post(
            reverse('wishlist-add'),
            {'product_id': self.product.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.session
        self.assertIn(str(self.product.id), session.get('wishlist', []))

    def test_remove_from_wishlist(self):
        """Тест удаления товара из списка желаний."""
        self.client.force_login(self.user)
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.delete(
            reverse('wishlist-item-delete', args=[self.product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            WishlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_get_wishlist(self):
        """Тест получения списка желаний."""
        self.client.force_login(self.user)
        WishlistItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product']['id'], self.product.id)

    def test_add_inactive_product(self):
        """Тест добавления неактивного товара в список желаний."""
        self.client.force_login(self.user)
        self.product.is_active = False
        self.product.save()
        with self.assertRaises(ProductNotAvailable):
            WishlistService.add_to_wishlist(
                request=type('Request', (), {'user': self.user}),
                product_id=self.product.id
            )

    def test_remove_nonexistent_item(self):
        """Тест удаления несуществующего элемента из списка желаний."""
        self.client.force_login(self.user)
        with self.assertRaises(WishlistItemNotFound):
            WishlistService.remove_from_wishlist(
                request=type('Request', (), {'user': self.user}),
                product_id=999999
            )
