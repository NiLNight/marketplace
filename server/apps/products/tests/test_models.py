"""
Модуль тестов для моделей приложения products.

Содержит тесты для моделей Category и Product.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.products.models import Category, Product

User = get_user_model()


class CategoryModelTests(TestCase):
    """Тесты для модели Category.

    Проверяет чтение и иерархию категорий.
    """

    @classmethod
    def setUpTestData(cls):
        """Подготовка тестовых данных."""
        # Создаем тестовые категории через прямые запросы к БД для тестирования
        cls.electronics = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        cls.phones = Category.objects.create(
            title='Смартфоны',
            description='Мобильные телефоны',
            parent=cls.electronics
        )
        cls.laptops = Category.objects.create(
            title='Ноутбуки',
            description='Портативные компьютеры',
            parent=cls.electronics
        )

    def test_category_str_representation(self):
        """Тест строкового представления категории."""
        self.assertEqual(str(self.electronics), 'Электроника')
        self.assertEqual(str(self.phones), 'Смартфоны')

    def test_category_hierarchy(self):
        """Тест иерархии категорий."""
        # Проверка родительских связей
        self.assertEqual(self.phones.parent, self.electronics)
        self.assertEqual(self.laptops.parent, self.electronics)

        # Проверка дочерних связей
        children = self.electronics.children.all()
        self.assertEqual(len(children), 2)
        self.assertIn(self.phones, children)
        self.assertIn(self.laptops, children)

        # Проверка уровней
        self.assertEqual(self.electronics.level, 0)
        self.assertEqual(self.phones.level, 1)

    def test_category_cached_children(self):
        """Тест получения кэшированных дочерних категорий."""
        children = self.electronics.cached_children
        self.assertEqual(len(children), 2)
        self.assertIn(self.phones, children)
        self.assertIn(self.laptops, children)


class ProductModelTests(TestCase):
    """Тесты для модели Product.

    Проверяет создание, валидацию и методы модели Product.
    """

    def setUp(self):
        """Подготовка данных для тестов."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/jpeg'
        )
        self.product = Product.objects.create(
            title='iPhone 15',
            description='Новый iPhone',
            price=Decimal('999.99'),
            stock=10,
            category=self.category,
            user=self.user,
            thumbnail=self.image
        )

    def test_product_creation(self):
        """Тест создания продукта с проверкой всех полей."""
        self.assertEqual(self.product.title, 'iPhone 15')
        self.assertTrue(self.product.slug)
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.user, self.user)
        self.assertFalse(self.product.is_active)
        self.assertEqual(self.product.discount, Decimal('0.00'))

    def test_product_str_representation(self):
        """Тест строкового представления продукта."""
        self.assertEqual(str(self.product), 'iPhone 15')

    def test_product_price_validation(self):
        """Тест валидации цены продукта."""
        # Тест отрицательной цены
        product = Product(
            title='Test Product',
            price=Decimal('-100.00'),
            category=self.category,
            user=self.user
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

        # Тест нулевой цены
        product = Product(
                title='Test Product',
                price=Decimal('0.00'),
                category=self.category,
                user=self.user
            )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_discount_validation(self):
        """Тест валидации скидки продукта."""
        # Тест отрицательной скидки
        self.product.discount = Decimal('-10.00')
        with self.assertRaises(ValidationError):
            self.product.full_clean()

        # Тест скидки больше 100%
        self.product.discount = Decimal('110.00')
        with self.assertRaises(ValidationError):
            self.product.full_clean()

        # Тест корректной скидки
        self.product.discount = Decimal('50.00')
        self.product.full_clean()  # Не должно вызывать исключение

    def test_product_price_with_discount(self):
        """Тест расчета цены со скидкой."""
        # Установка скидки 50%
        self.product.discount = Decimal('50.00')
        self.product.save()

        # Проверка расчета цены со скидкой
        expected_price = Decimal('499.995')  # 999.99 * 0.5
        self.assertEqual(self.product.price_with_discount, expected_price)

    def test_product_stock_validation(self):
        """Тест валидации количества товара на складе."""
        # Тест отрицательного количества
        with self.assertRaises(ValidationError):
            self.product.stock = -1
            self.product.full_clean()

    def test_product_in_stock_property(self):
        """Тест свойства in_stock."""
        # Товар в наличии
        self.product.stock = 1
        self.assertTrue(self.product.in_stock)

        # Товар не в наличии
        self.product.stock = 0
        self.assertFalse(self.product.in_stock)

    def test_product_unique_slug(self):
        """Тест уникальности slug продукта."""
        # Создаем продукт с таким же названием
        product2 = Product.objects.create(
            title='iPhone 15',
            price=Decimal('999.99'),
            category=self.category,
            user=self.user
        )
        self.assertNotEqual(product2.slug, self.product.slug)

    def test_product_search_vector_update(self):
        """Тест обновления поискового вектора."""
        self.product.title = 'New Title'
        self.product.save()
        self.assertIsNotNone(self.product.search_vector)

    def test_product_transaction_rollback(self):
        """Тест отката транзакции при ошибке сохранения."""
        initial_count = Product.objects.count()

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                product = Product(
                    title='Test Product',
                    price=Decimal('-100.00'),
                    category=self.category,
                    user=self.user
                )
                product.full_clean()
                product.save()

        # Проверяем, что количество продуктов не изменилось
        self.assertEqual(Product.objects.count(), initial_count)

    def test_product_thumbnail_validation(self):
        """Тест валидации изображения продукта."""
        # Тест некорректного формата файла
        invalid_image = SimpleUploadedFile(
            name='test.txt',
            content=b'Invalid image content',
            content_type='text/plain'
        )
        product = Product(
            title='Test Product',
            price=Decimal('100.00'),
            category=self.category,
            user=self.user,
            thumbnail=invalid_image
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
