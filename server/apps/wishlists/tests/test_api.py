from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.products.models import Product, Category
from apps.wishlists.models import WishlistItem
from django.core.cache import cache
import json

User = get_user_model()


class WishlistTests(TestCase):
    """Тесты для функциональности списков желаний.

    Проверяет создание, удаление и получение элементов списка желаний
    для авторизованных и неавторизованных пользователей.

    Attributes:
        client (APIClient): Тестовый клиент REST Framework.
        wishlist_url (str): URL для работы со списком желаний.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = APIClient()
        self.wishlist_url = reverse('wishlist-get')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product_active = Product.objects.create(
            title='Test Product Active',
            description='Test Description',
            price=Decimal('100.00'),
            category=self.category,
            stock=10,
            user=self.user,
            is_active=True
        )
        self.product_inactive = Product.objects.create(
            title='Test Product Inactive',
            description='Test Description',
            price=Decimal('50.00'),
            category=self.category,
            stock=5,
            user=self.user,
            is_active=False
        )
        cache.clear()

    def test_add_to_wishlist_authenticated(self):
        """Тест добавления товара в список желаний авторизованным пользователем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('wishlist-add'),
            data=json.dumps({'product_id': self.product_active.id}),
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}, data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            WishlistItem.objects.filter(user=self.user, product=self.product_active).exists()
        )

    def test_add_to_wishlist_invalid_product_id(self):
        """Тест добавления товара с некорректным product_id."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('wishlist-add'),
            data=json.dumps({'product_id': 'invalid'}),
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}, data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_add_to_wishlist_unauthenticated(self):
        """Тест добавления товара в список желаний неавторизованным пользователем."""
        response = self.client.post(
            reverse('wishlist-add'),
            data=json.dumps({'product_id': self.product_active.id}),
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}, data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.session
        self.assertIn(str(self.product_active.id), session.get('wishlist', []))

    def test_remove_from_wishlist(self):
        """Тест удаления товара из списка желаний."""
        self.client.force_authenticate(user=self.user)
        WishlistItem.objects.create(user=self.user, product=self.product_active)
        response = self.client.delete(
            reverse('wishlist-item-delete', args=[self.product_active.id])
        )
        print(f"Response status: {response.status_code}, data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            WishlistItem.objects.filter(user=self.user, product=self.product_active).exists()
        )

    def test_get_wishlist(self):
        """Тест получения списка желаний."""
        self.client.force_authenticate(user=self.user)
        WishlistItem.objects.create(user=self.user, product=self.product_active)
        response = self.client.get(self.wishlist_url)
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product']['id'], self.product_active.id)

    def test_add_inactive_product(self):
        """Тест добавления неактивного товара в список желаний."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('wishlist-add'),
            data=json.dumps({'product_id': self.product_inactive.id}),
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}, data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Товар недоступен для списка желаний")

    def test_remove_nonexistent_item(self):
        """Тест удаления несуществующего элемента из списка желаний."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse('wishlist-item-delete', args=[999999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
