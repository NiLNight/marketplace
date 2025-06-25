from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.orders.models import Order
from apps.delivery.models import PickupPoint, City

User = get_user_model()

class OrderModelTest(TestCase):
    """
    Тесты для модели Order: валидация, save, __str__ и edge-cases.
    """
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        cls.city = City.objects.create(name='Test City')
        cls.pickup_point = PickupPoint.objects.create(city=cls.city, address='Test address', is_active=True)

    def test_order_str(self):
        order = Order.objects.create(user=self.user, total_price=100, pickup_point=self.pickup_point)
        self.assertIn(str(order.id), str(order))
        self.assertIn(self.user.username, str(order))

    def test_order_negative_total_price(self):
        order = Order(user=self.user, total_price=-10, pickup_point=self.pickup_point)
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_order_inactive_pickup_point(self):
        inactive_pickup = PickupPoint.objects.create(city=self.city, address='Inactive address', is_active=False)
        order = Order(user=self.user, total_price=10, pickup_point=inactive_pickup)
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_order_save_calls_full_clean(self):
        order = Order(user=self.user, total_price=10, pickup_point=self.pickup_point)
        order.save()  # Should not raise
        order.total_price = -1
        with self.assertRaises(ValidationError):
            order.save() 