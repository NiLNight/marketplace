"""
Модуль тестов для сервисов приложения products.

Содержит тесты для ProductServices и ProductQueryService.
"""

from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.products.models import Category, Product
from apps.products.services.product_services import ProductServices
from apps.products.services.query_services import ProductQueryService
from apps.products.exceptions import ProductNotFound, ProductServiceException

User = get_user_model()


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=False)
class ProductServicesTests(TestCase):
    """Тесты для ProductServices.

    Проверяет создание, обновление и удаление продуктов через сервисный слой.
    """

    @classmethod
    def setUpTestData(cls):
        """Подготовка тестовых данных."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Создаем тестовые категории через прямые запросы к БД
        cls.category = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )

    def setUp(self):
        """Подготовка данных для каждого теста."""
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/jpeg'
        )
        self.valid_data = {
            'title': 'iPhone 15',
            'description': 'Новый iPhone',
            'price': Decimal('999.99'),
            'stock': 10,
            'category': self.category,
            'thumbnail': self.image
        }

    def test_create_product(self):
        """Тест создания продукта через сервис."""
        product = ProductServices.create_product(self.valid_data, self.user)
        self.assertEqual(product.title, 'iPhone 15')
        self.assertEqual(product.price, Decimal('999.99'))
        self.assertEqual(product.user, self.user)
        self.assertFalse(product.is_active)

    def test_create_product_invalid_data(self):
        """Тест создания продукта с некорректными данными."""
        invalid_data = self.valid_data.copy()
        invalid_data['price'] = Decimal('-100.00')

        with self.assertRaises(ProductServiceException):
            ProductServices.create_product(invalid_data, self.user)

    def test_update_product(self):
        """Тест обновления продукта через сервис."""
        product = ProductServices.create_product(self.valid_data, self.user)
        update_data = {
            'title': 'iPhone 15 Pro',
            'price': Decimal('1099.99')
        }

        updated_product = ProductServices.update_product(product.id, update_data, self.user)
        self.assertEqual(updated_product.title, 'iPhone 15 Pro')
        self.assertEqual(updated_product.price, Decimal('1099.99'))

    def test_update_product_not_found(self):
        """Тест обновления несуществующего продукта."""
        with self.assertRaises(ProductNotFound):
            ProductServices.update_product(999, {'title': 'New Title'}, self.user)

    def test_update_product_wrong_user(self):
        """Тест обновления продукта другим пользователем."""
        product = ProductServices.create_product(self.valid_data, self.user)
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        with self.assertRaises(ProductServiceException):
            ProductServices.update_product(product.id, {'title': 'New Title'}, other_user)

    def test_delete_product(self):
        """Тест удаления продукта через сервис."""
        product = ProductServices.create_product(self.valid_data, self.user)
        ProductServices.delete_product(product.id, self.user)
        self.assertEqual(Product.objects.count(), 0)

    def test_delete_product_not_found(self):
        """Тест удаления несуществующего продукта."""
        with self.assertRaises(ProductNotFound):
            ProductServices.delete_product(999, self.user)

    def test_delete_product_wrong_user(self):
        """Тест удаления продукта другим пользователем."""
        product = ProductServices.create_product(self.valid_data, self.user)
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        with self.assertRaises(ProductServiceException):
            ProductServices.delete_product(product.id, other_user)


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=False)
class ProductQueryServiceTests(TestCase):
    """Тесты для ProductQueryService.

    Проверяет фильтрацию, сортировку и поиск продуктов.
    """

    @classmethod
    def setUpTestData(cls):
        """Подготовка тестовых данных."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Создаем тестовые категории через прямые запросы к БД
        cls.electronics = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        cls.phones = Category.objects.create(
            title='Смартфоны',
            description='Мобильные телефоны',
            parent=cls.electronics
        )

        # Создаем тестовые продукты
        cls.product1 = Product.objects.create(
            title='iPhone 15',
            description='Дорогой телефон',
            price=Decimal('999.99'),
            stock=10,
            category=cls.phones,
            user=cls.user,
            is_active=True
        )
        cls.product2 = Product.objects.create(
            title='Cheap Phone',
            description='Дешевый телефон',
            price=Decimal('99.99'),
            stock=20,
            category=cls.phones,
            user=cls.user,
            is_active=True,
            discount=Decimal('10.00')
        )
        cls.product3 = Product.objects.create(
            title='Out of Stock',
            description='Нет в наличии',
            price=Decimal('499.99'),
            stock=0,
            category=cls.phones,
            user=cls.user,
            is_active=True
        )

    def test_get_base_queryset(self):
        """Тест получения базового QuerySet."""
        # В тестовом режиме должны возвращаться все продукты
        queryset = ProductQueryService.get_base_queryset()
        self.assertEqual(queryset.count(), 3)  # Все продукты

        # Делаем один продукт неактивным
        self.product1.is_active = False
        self.product1.save()

        # В тестовом режиме все равно должны возвращаться все продукты
        queryset = ProductQueryService.get_base_queryset()
        self.assertEqual(queryset.count(), 3)  # Все продукты, включая неактивные

        # Проверяем, что в production режиме возвращаются только активные продукты
        with self.settings(TESTING=False):
            queryset = ProductQueryService.get_base_queryset()
            self.assertEqual(queryset.count(), 2)  # Только активные продукты

    def test_get_product_list(self):
        """Тест получения списка продуктов с аннотациями."""
        products = ProductQueryService.get_product_list()
        self.assertEqual(products.count(), 3)

        # Проверяем наличие аннотаций
        product = products.first()
        self.assertTrue(hasattr(product, 'rating_avg'))
        self.assertTrue(hasattr(product, 'purchase_count'))
        self.assertTrue(hasattr(product, 'review_count'))

    def test_get_single_product(self):
        """Тест получения одного продукта."""
        product = ProductQueryService.get_single_product(self.product1.id)
        self.assertEqual(product.id, self.product1.id)
        self.assertTrue(hasattr(product, 'rating_avg'))

    def test_get_single_product_not_found(self):
        """Тест получения несуществующего продукта."""
        with self.assertRaises(ProductNotFound):
            ProductQueryService.get_single_product(999)

    def test_apply_common_filters(self):
        """Тест применения фильтров."""
        # Фильтр по категории
        queryset = ProductQueryService.apply_common_filters(
            Product.objects.all(),
            category_id=self.phones.id
        )
        self.assertEqual(queryset.count(), 3)

        # Фильтр по цене
        queryset = ProductQueryService.apply_common_filters(
            Product.objects.all(),
            min_price=Decimal('500.00')
        )
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.product1)

        # Фильтр по наличию
        queryset = ProductQueryService.apply_common_filters(
            Product.objects.all(),
            in_stock=True
        )
        self.assertEqual(queryset.count(), 2)
        self.assertNotIn(self.product3, queryset)

        # Фильтр по скидке
        queryset = ProductQueryService.apply_common_filters(
            Product.objects.all(),
            min_discount=Decimal('5.00')
        )
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.product2)

    def test_apply_ordering(self):
        """Тест применения сортировки."""
        class MockRequest:
            def __init__(self, ordering):
                self.GET = {'ordering': ordering}

        # Сортировка по цене (по возрастанию)
        request = MockRequest('price')
        queryset = ProductQueryService.apply_ordering(Product.objects.all(), request)
        products = list(queryset)
        self.assertEqual(products[0], self.product2)  # Самый дешевый
        self.assertEqual(products[-1], self.product1)  # Самый дорогой

        # Сортировка по цене (по убыванию)
        request = MockRequest('-price')
        queryset = ProductQueryService.apply_ordering(Product.objects.all(), request)
        products = list(queryset)
        self.assertEqual(products[0], self.product1)  # Самый дорогой
        self.assertEqual(products[-1], self.product2)  # Самый дешевый

        # Некорректное поле сортировки
        request = MockRequest('invalid_field')
        queryset = ProductQueryService.apply_ordering(Product.objects.all(), request)
        self.assertTrue(queryset.ordered)  # Проверяем, что сортировка применена (по умолчанию) 