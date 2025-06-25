from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from apps.orders.models import Order
from apps.delivery.models import PickupPoint, City
from apps.products.models import Product, Category
from apps.carts.models import OrderItem

User = get_user_model()


class OrderAPITest(TestCase):
    """
    Тесты для API заказов: список, детали, создание, отмена, ошибки, права.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123',
                                             is_active=True)
        self.client.force_authenticate(user=self.user)
        self.city = City.objects.create(name='Test City')
        self.pickup_point = PickupPoint.objects.create(city=self.city, address='Test address', is_active=True)
        self.category = Category.objects.create(title='TestCat')
        self.product = Product.objects.create(title='TestProd', description='desc', price=Decimal('10.00'),
                                              category=self.category, stock=5, user=self.user, is_active=True)
        self.order = Order.objects.create(user=self.user, total_price=20, pickup_point=self.pickup_point)

    def test_order_list(self):
        url = reverse('orders:order_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)

    def test_order_detail(self):
        url = reverse('orders:order_detail', args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)

    def test_order_create(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=2)
        url = reverse('orders:order_create')
        response = self.client.post(url, {'pickup_point_id': self.pickup_point.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_id', response.data)

    def test_order_create_empty_cart(self):
        url = reverse('orders:order_create')
        response = self.client.post(url, {'pickup_point_id': self.pickup_point.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_create_inactive_pickup_point(self):
        inactive_pickup = PickupPoint.objects.create(city=self.city, address='Inactive address', is_active=False)
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse('orders:order_create')
        response = self.client.post(url, {'pickup_point_id': inactive_pickup.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_cancel(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point,
                                     status='processing')
        url = reverse('orders:order_cancel', args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_order_cancel_invalid_status(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point, status='delivered')
        url = reverse('orders:order_cancel', args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_cancel_not_found(self):
        url = reverse('orders:order_cancel', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_detail_not_found(self):
        url = reverse('orders:order_detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('orders:order_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
