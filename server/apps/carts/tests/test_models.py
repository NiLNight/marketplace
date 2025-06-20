from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.carts.models import OrderItem
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

User = get_user_model()


class CartModelsTests(TestCase):
    def setUp(self):
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
        self.product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=200.00,
            category=self.category,
            stock=5,
            user=self.user
        )

    def test_order_item_creation(self):
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.assertEqual(order_item.user, self.user)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 1)
        self.assertIsNone(order_item.order)

    def test_order_item_unique_cart_constraint(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(user=self.user, product=self.product, quantity=1)

    def test_order_item_unique_order_constraint(self):
        OrderItem.objects.create(product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(product=self.product, quantity=1)

    def test_order_item_clean_no_user_or_order(self):
        order_item = OrderItem(user=None, order=None, product=self.product, quantity=1)
        with self.assertRaises(ValidationError):
            order_item.clean()

    def test_order_item_str_representation(self):
        order_item = OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        self.assertEqual(str(order_item), f"5 x {self.product.title}")
