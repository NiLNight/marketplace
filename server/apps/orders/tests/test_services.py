from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, APIException
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from decimal import Decimal
from apps.orders.models import Order
from apps.orders.services.order_services import OrderService
from apps.orders.services.notification_services import NotificationService
from apps.delivery.models import PickupPoint, City
from apps.products.models import Product, Category
from apps.carts.models import OrderItem
from unittest.mock import patch, MagicMock

User = get_user_model()


class OrderServiceTest(TestCase):
    """
    Тесты для OrderService: создание, получение, отмена заказа, ошибки.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123',
                                             is_active=True)
        self.city = City.objects.create(name='Test City')
        self.pickup_point = PickupPoint.objects.create(city=self.city, address='Test address', is_active=True)
        self.category = Category.objects.create(title='TestCat')
        self.product = Product.objects.create(title='TestProd', description='desc', price=Decimal('10.00'),
                                              category=self.category, stock=5, user=self.user, is_active=True)
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user
        self.request.META['REMOTE_ADDR'] = '127.0.0.1'
        self.request.path = '/orders/'

    def test_get_user_orders_active(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point)
        orders = OrderService.get_user_orders(self.user, self.request)
        self.assertIn(order, list(orders))

    def test_get_user_orders_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(APIException):
            OrderService.get_user_orders(self.user, self.request)

    def test_get_order_details_success(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point)
        result = OrderService.get_order_details(order.id, self.user, self.request)
        self.assertEqual(result, order)

    def test_get_order_details_not_found(self):
        with self.assertRaises(ValidationError):
            OrderService.get_order_details(9999, self.user, self.request)

    def test_create_order_success(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=2)
        order = OrderService.create_order(self.user, self.pickup_point.id, self.request)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.pickup_point, self.pickup_point)
        self.assertEqual(order.total_price, self.product.price * 2)

    def test_create_order_empty_cart(self):
        with self.assertRaises(ValidationError):
            OrderService.create_order(self.user, self.pickup_point.id, self.request)

    def test_create_order_inactive_pickup_point(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        inactive_pickup = PickupPoint.objects.create(city=self.city, address='Inactive address', is_active=False)
        with self.assertRaises(ValidationError):
            OrderService.create_order(self.user, inactive_pickup.id, self.request)

    def test_create_order_insufficient_stock(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=10)
        with self.assertRaises(ValidationError):
            OrderService.create_order(self.user, self.pickup_point.id, self.request)

    def test_create_order_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(APIException):
            OrderService.create_order(self.user, self.pickup_point.id, self.request)

    def test_cancel_order_success(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point,
                                     status='processing')
        OrderService.cancel_order(order.id, self.user, self.request)
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_cancel_order_invalid_status(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point, status='delivered')
        with self.assertRaises(ValidationError):
            OrderService.cancel_order(order.id, self.user, self.request)

    def test_cancel_order_not_found(self):
        with self.assertRaises(ValidationError):
            OrderService.cancel_order(9999, self.user, self.request)

    def test_cancel_order_inactive_user(self):
        order = Order.objects.create(user=self.user, total_price=10, pickup_point=self.pickup_point,
                                     status='processing')
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(APIException):
            OrderService.cancel_order(order.id, self.user, self.request)


class NotificationServiceTest(TestCase):
    """
    Тесты для NotificationService: отправка email, ошибки, валидация.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

    @patch('apps.orders.services.notification_services.NotificationService.send_notification_async.delay')
    def test_send_notification_success(self, mock_delay):
        NotificationService.send_notification(self.user, 'Test message')
        mock_delay.assert_called_once_with(self.user.email, 'Test message', user_id=self.user.id)

    def test_send_notification_no_email(self):
        self.user.email = ''
        with self.assertRaises(DjangoValidationError):
            NotificationService.send_notification(self.user, 'Test message')

    def test_send_notification_empty_message(self):
        with self.assertRaises(DjangoValidationError):
            NotificationService.send_notification(self.user, '')
