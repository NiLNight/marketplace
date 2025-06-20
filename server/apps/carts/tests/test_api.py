from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.products.models import Product, Category
from apps.carts.models import OrderItem

User = get_user_model()


class CartViewsTests(TestCase):
    def setUp(self):
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
            user=self.user,
            is_active=True
        )

    def test_add_to_cart_authenticated(self):
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
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.session
        self.assertEqual(session.get('cart', {}).get(str(self.product.id)), 2)

    def test_update_cart_item(self):
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

    def test_remove_from_cart_authenticated(self):
        self.client.force_login(self.user)

        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.delete(
            reverse('carts:cart_item', args=[self.product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).exists()
        )

    def test_get_cart(self):
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product']['id'], self.product.id)
        self.assertEqual(response.data[0]['quantity'], 2)

    # Additional tests for views

    def test_add_to_cart_existing_item_authenticated(self):
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 2}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            OrderItem.objects.get(user=self.user, product=self.product).quantity,
            3
        )

    def test_add_to_cart_existing_item_unauthenticated(self):
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': self.product.id, 'quantity': 3}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.session
        self.assertEqual(session.get('cart', {}).get(str(self.product.id)), 5)

    def test_add_to_cart_invalid_product_id(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('carts:cart_add'),
            {'product_id': 999999, 'quantity': 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ProductNotAvailable', response.data['code'])

    def test_update_cart_item_invalid_quantity(self):
        self.client.force_login(self.user)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1, order__isnull=True)
        response = self.client.patch(
            reverse('carts:cart_item', args=[self.product.id]),
            {'quantity': 0}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Changed to 200 OK for updated item data
        self.assertFalse(OrderItem.objects.filter(user=self.user, product=self.product).exists())

    def test_update_cart_item_nonexistent_item(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse('carts:cart_item', args=[999999]),
            {'quantity': 1}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('cartitemnotfound', response.data['code'])

    def test_delete_cart_item_nonexistent_item(self):
        self.client.force_login(self.user)
        response = self.client.delete(
            reverse('carts:cart_item', args=[999999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('cartitemnotfound', response.data['code'])

    def test_get_empty_cart_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_empty_cart_unauthenticated(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
