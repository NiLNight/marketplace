from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.carts.models import OrderItem
from apps.orders.models import Order, PickupPoint
from apps.delivery.models import City
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from decimal import Decimal

User = get_user_model()


class CartModelsTests(TestCase):
    def setUp(self):
        """Инициализация данных для тестов."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=Decimal('100.00'),
            category=self.category,
            stock=10,
            user=self.user
        )
        self.product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=Decimal('200.00'),
            category=self.category,
            stock=5,
            user=self.user
        )
        # Создаем City для PickupPoint
        self.city = City.objects.create(name='Test City')
        # Создаем PickupPoint для Order
        self.pickup_point = PickupPoint.objects.create(
            city=self.city,
            address='123 Test Street',
            is_active=True
        )
        self.order = Order.objects.create(
            user=self.user,
            status='processing',
            pickup_point=self.pickup_point,
            total_price=Decimal('0.00')  # Указываем total_price, так как поле обязательное
        )

    def test_order_item_creation(self):
        """Проверка создания элемента корзины."""
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.assertEqual(order_item.user, self.user)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 1)
        self.assertIsNone(order_item.order)

    def test_order_item_unique_cart_constraint(self):
        """Проверка ограничения уникальности товара в корзине пользователя."""
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(user=self.user, product=self.product, quantity=1)

    def test_order_item_unique_order_constraint(self):
        """Проверка ограничения уникальности товара в заказе."""
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def test_order_item_clean_no_user_or_order(self):
        """Проверка валидации при отсутствии пользователя и заказа."""
        order_item = OrderItem(user=None, order=None, product=self.product, quantity=1)
        with self.assertRaises(ValidationError) as cm:
            order_item.clean()
        self.assertEqual(
            str(cm.exception),
            "['Элемент должен быть привязан либо к пользователю, либо к заказу.']"
        )

    def test_order_item_clean_both_user_and_order(self):
        """Проверка валидации при наличии одновременно пользователя и заказа."""
        order_item = OrderItem(
            user=self.user,
            order=self.order,
            product=self.product,
            quantity=1
        )
        with self.assertRaises(ValidationError) as cm:
            order_item.clean()
        self.assertEqual(
            str(cm.exception),
            "['Элемент не может одновременно принадлежать пользователю (корзина) и заказу.']"
        )

    def test_order_item_str_representation(self):
        """Проверка строкового представления элемента корзины."""
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        self.assertEqual(str(order_item), f"5 x {self.product.title}")
