from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal

from apps.carts.models import OrderItem
from apps.products.models import Product, Category
from apps.orders.models import Order, PickupPoint
from apps.delivery.models import City

User = get_user_model()


class CartModelsTests(TestCase):
    """Тестирование модели OrderItem (элемент корзины/заказа)."""

    @classmethod
    def setUpTestData(cls):
        """
        Создает начальные данные для всех тестов в этом классе.
        Метод выполняется один раз перед запуском тестов.
        """
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cls.category = Category.objects.create(title='Test Category')
        cls.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=Decimal('100.00'),
            category=cls.category,
            stock=10,
            user=cls.user
        )
        cls.product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=Decimal('200.00'),
            category=cls.category,
            stock=5,
            user=cls.user
        )
        # Создаем City для PickupPoint, так как это требуется для Order
        city = City.objects.create(name='Test City')
        # Создаем PickupPoint для Order
        pickup_point = PickupPoint.objects.create(
            city=city,
            address='123 Test Street',
            is_active=True
        )
        # Создаем Order для тестов, где OrderItem связан с заказом
        cls.order = Order.objects.create(
            user=cls.user,
            status='processing',
            pickup_point=pickup_point,
            total_price=Decimal('0.00')
        )

    def test_order_item_creation(self):
        """Тестирует успешное создание элемента корзины."""
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.assertEqual(order_item.user, self.user)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 1)
        # По умолчанию элемент не связан с заказом
        self.assertIsNone(order_item.order)

    def test_order_item_unique_cart_constraint(self):
        """
        Тестирует ограничение уникальности: один и тот же товар
        не может быть добавлен в корзину пользователя дважды.
        """
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        # Попытка создать дубликат должна вызывать IntegrityError
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(user=self.user, product=self.product, quantity=1)

    def test_order_item_unique_order_constraint(self):
        """
        Тестирует ограничение уникальности: один и тот же товар
        не может дважды встречаться в одном заказе.
        """
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        # Попытка создать дубликат должна вызывать IntegrityError
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def test_order_item_clean_no_user_or_order(self):
        """
        Тестирует валидацию: элемент должен быть привязан
        либо к корзине (пользователю), либо к заказу.
        """
        order_item = OrderItem(user=None, order=None, product=self.product, quantity=1)
        with self.assertRaises(ValidationError) as cm:
            order_item.clean()
        self.assertIn(
            "Элемент должен быть привязан либо к пользователю, либо к заказу.",
            str(cm.exception)
        )

    def test_order_item_clean_both_user_and_order(self):
        """
        Тестирует валидацию: элемент не может одновременно
        принадлежать и корзине, и заказу.
        """
        order_item = OrderItem(
            user=self.user,
            order=self.order,
            product=self.product,
            quantity=1
        )
        with self.assertRaises(ValidationError) as cm:
            order_item.clean()
        self.assertIn(
            "Элемент не может одновременно принадлежать пользователю (корзина) и заказу.",
            str(cm.exception)
        )

    def test_order_item_str_representation(self):
        """Тестирует строковое представление элемента корзины."""
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        expected_str = f"{order_item.quantity} x {order_item.product.title}"
        self.assertEqual(str(order_item), expected_str)
