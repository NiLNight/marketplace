"""Модуль тестов для приложения products.

Содержит тесты для проверки функциональности продуктов и категорий,
их создания, обновления и других возможностей приложения products.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.products.models import Category, Product
from apps.products.exceptions import ProductNotFound

User = get_user_model()


class CategoryTests(TestCase):
    """Тесты для модели Category.

    Проверяет создание, валидацию и обновление категорий.

    Attributes:
        client (Client): Тестовый клиент Django.
        categories_url (str): URL для работы с категориями.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.categories_url = reverse('products:category_list')
        self.parent_category = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        self.child_category = Category.objects.create(
            title='Смартфоны',
            description='Мобильные телефоны',
            parent=self.parent_category
        )

    def test_category_creation(self):
        """Тест создания категории."""
        category = Category.objects.create(
            title='Ноутбуки',
            description='Портативные компьютеры'
        )
        self.assertEqual(category.title, 'Ноутбуки')
        self.assertTrue(category.slug)

    def test_category_str(self):
        """Тест строкового представления категории."""
        self.assertEqual(str(self.parent_category), 'Электроника')

    def test_category_hierarchy(self):
        """Тест иерархии категорий."""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertIn(self.child_category, self.parent_category.children.all())


class ProductTests(TestCase):
    """Тесты для модели Product.

    Проверяет создание, валидацию и обновление продуктов.

    Attributes:
        client (Client): Тестовый клиент Django.
        products_url (str): URL для работы с продуктами.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.products_url = reverse('products:product_list')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        self.product = Product.objects.create(
            title='iPhone 15',
            description='Новый iPhone',
            price=Decimal('999.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )

    def test_product_creation(self):
        """Тест создания продукта."""
        product = Product.objects.create(
            title='MacBook Pro',
            description='Новый MacBook',
            price=Decimal('1999.99'),
            stock=5,
            category=self.category,
            user=self.user
        )
        self.assertEqual(product.title, 'MacBook Pro')
        self.assertEqual(product.price, Decimal('1999.99'))
        self.assertEqual(product.stock, 5)
        self.assertFalse(product.is_active)

    def test_product_str(self):
        """Тест строкового представления продукта."""
        expected = self.product.title
        self.assertEqual(str(self.product), expected)

    def test_product_price_with_discount(self):
        """Тест расчета цены со скидкой."""
        self.product.discount = Decimal('10.00')
        self.product.save()
        expected_price = Decimal('899.99')
        self.assertEqual(self.product.price_with_discount.quantize(Decimal('0.01')), expected_price)

    def test_product_in_stock(self):
        """Тест проверки наличия на складе."""
        self.assertTrue(self.product.in_stock)
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.in_stock)

    def test_product_validation(self):
        """Тест валидации продукта."""
        # Проверка отрицательной цены
        with self.assertRaises(ValidationError):
            Product.objects.create(
                title='Test Product',
                price=Decimal('-10.00'),
                stock=1,
                category=self.category,
                user=self.user
            )

        # Проверка отрицательного остатка
        with self.assertRaises(ValidationError):
            Product.objects.create(
                title='Test Product',
                price=Decimal('10.00'),
                stock=-1,
                category=self.category,
                user=self.user
            )
