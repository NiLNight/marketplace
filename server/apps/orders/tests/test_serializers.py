from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer, OrderDetailSerializer
from apps.delivery.models import PickupPoint, City
from apps.products.models import Product, Category
from apps.carts.models import OrderItem

User = get_user_model()

class OrderSerializerTest(TestCase):
    """
    Тесты для OrderSerializer и OrderDetailSerializer: валидация, сериализация, edge-cases.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.city = City.objects.create(name='Test City')
        self.pickup_point = PickupPoint.objects.create(city=self.city, address='Test address', is_active=True)
        self.category = Category.objects.create(title='TestCat')
        self.product = Product.objects.create(title='TestProd', description='desc', price=Decimal('10.00'), category=self.category, stock=5, user=self.user, is_active=True)
        self.order = Order.objects.create(user=self.user, total_price=20, pickup_point=self.pickup_point)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, quantity=2)

    def test_order_serializer_valid(self):
        serializer = OrderSerializer(instance=self.order)
        self.assertEqual(serializer.data['id'], self.order.id)
        self.assertEqual(serializer.data['total_price'], format(self.order.total_price, '.2f'))

    def test_order_serializer_invalid_status(self):
        self.order.status = 'invalid_status'
        serializer = OrderSerializer(instance=self.order)
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_order_detail_serializer_valid(self):
        serializer = OrderDetailSerializer(instance=self.order)
        self.assertEqual(serializer.data['id'], self.order.id)
        self.assertEqual(serializer.data['items'][0]['product']['id'], self.product.id)

    def test_order_detail_serializer_inactive_pickup_point(self):
        inactive_pickup = PickupPoint.objects.create(city=self.city, address='Inactive address', is_active=False)
        self.order.pickup_point = inactive_pickup
        self.order.save()
        serializer = OrderDetailSerializer(instance=self.order)
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_order_detail_serializer_inactive_product(self):
        self.product.is_active = False
        self.product.save()
        self.order.refresh_from_db()
        serializer = OrderDetailSerializer(instance=self.order)
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True) 