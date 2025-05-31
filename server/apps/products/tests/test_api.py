"""
Модуль тестов для API приложения products.

Содержит тесты для всех API endpoints.
"""

from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from apps.products.models import Category, Product

from django.core.management import call_command

User = get_user_model()


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=False)
class CategoryAPITests(TestCase):
    """Тесты для API категорий.

    Проверяет операции чтения категорий через API.
    """

    def setUp(self):
        """Подготовка тестовых данных для каждого теста."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Создаем тестовые категории
        self.electronics = Category.objects.create(
            title='Электроника',
            description='Электронные устройства'
        )
        self.phones = Category.objects.create(
            title='Смартфоны',
            description='Мобильные телефоны',
            parent=self.electronics
        )

    def tearDown(self):
        """Очистка тестовых данных после каждого теста."""
        Category.objects.all().delete()
        User.objects.all().delete()

    def test_category_list(self):
        """Тест получения списка категорий."""
        response = self.client.get(reverse('products:category_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только корневая категория
        self.assertEqual(response.data[0]['title'], 'Электроника')

    def test_category_detail(self):
        """Тест получения деталей категории."""
        response = self.client.get(
            reverse('products:category_detail', kwargs={'pk': self.electronics.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Электроника')
        self.assertTrue('children' in response.data)
        self.assertEqual(len(response.data['children']), 1)


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)  # Включаем синхронизацию с Elasticsearch
class ProductAPITests(TestCase):
    """Тесты для API продуктов.

    Проверяет CRUD операции с продуктами через API.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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
            is_active=True,
            discount=Decimal('0.00')
        )

        # Добавляем valid_payload
        self.valid_payload = {
            'title': 'New Product',
            'description': 'A new test product',
            'price': '499.99',
            'stock': 20,
            'category': self.category.pk,
            'thumbnail': self.image,
            'discount': '0.00'
        }

        from django.core.cache import cache
        cache.clear()  # Очистка кэша перед тестами

        # Переиндексируем Elasticsearch
        call_command('search_index', '--rebuild', '-f')

    def tearDown(self):
        """Очистка тестовых данных после каждого теста."""
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        from django.core.cache import cache
        cache.clear()  # Очистка кэша после тестов

    def test_product_list(self):
        """Тест получения списка продуктов."""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')

    def test_product_detail(self):
        """Тест получения деталей продукта."""
        response = self.client.get(
            reverse('products:product_detail', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'iPhone 15')

    def test_product_create(self):
        """Тест создания продукта."""
        response = self.client.post(
            reverse('products:product_create'),
            self.valid_payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New Product')

    def test_product_create_invalid(self):
        """Тест создания продукта с некорректными данными."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['price'] = '-100.00'

        response = self.client.post(
            reverse('products:product_create'),
            invalid_payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.count(), 1)

    def test_product_update(self):
        """Тест обновления продукта."""
        update_data = {
            'title': 'Updated Product',
            'price': '299.99'
        }
        response = self.client.patch(
            reverse('products:product_update', kwargs={'pk': self.product.pk}),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, 'Updated Product')
        self.assertEqual(self.product.price, Decimal('299.99'))

    def test_product_delete(self):
        """Тест удаления продукта."""
        response = self.client.delete(
            reverse('products:product_delete', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_product_list_filtering(self):
        """Тест фильтрации списка продуктов."""
        # Создаем дополнительный продукт для тестирования фильтров
        Product.objects.create(
            title='Cheap Product',
            description='Дешевый товар',
            price=Decimal('9.99'),
            stock=100,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Фильтр по минимальной цене
        response = self.client.get(reverse('products:product_list'), {'min_price': '500'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')

        # Фильтр по наличию
        response = self.client.get(reverse('products:product_list'), {'in_stock': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_product_list_ordering(self):
        """Тест сортировки списка продуктов."""
        # Создаем дополнительный продукт для тестирования сортировки
        Product.objects.create(
            title='Cheap Product',
            description='Дешевый товар',
            price=Decimal('9.99'),
            stock=100,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Сортировка по цене (по возрастанию)
        response = self.client.get(reverse('products:product_list'), {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], 'Cheap Product')
        self.assertEqual(response.data['results'][1]['title'], 'iPhone 15')

        # Сортировка по цене (по убыванию)
        response = self.client.get(reverse('products:product_list'), {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')
        self.assertEqual(response.data['results'][1]['title'], 'Cheap Product')

    def test_product_search(self):
        """Тест поиска продуктов."""
        # Создаем продукты для поиска
        iphone_14 = Product.objects.create(
            title='iPhone 14',
            description='Новый iPhone 14',
            price=Decimal('999.99'),
            stock=15,
            category=self.category,
            user=self.user,
            is_active=True
        )
        samsung = Product.objects.create(
            title='Samsung Galaxy',
            description='Android смартфон',
            price=Decimal('799.99'),
            stock=15,
            category=self.category,
            user=self.user,
            is_active=True
        )
        xiaomi = Product.objects.create(
            title='Xiaomi Phone',
            description='iPhone killer с отличной камерой',
            price=Decimal('399.99'),
            stock=15,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Переиндексируем Elasticsearch
        from django.core.management import call_command
        call_command('search_index', '--rebuild', '-f')

        # Базовый поиск по слову 'iphone'
        response = self.client.get(reverse('products:product_list'), {'q': 'iphone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # iPhone 14
        
        # Проверяем, что iPhone 14 и iPhone 15 в начале результатов (выше ранжированы)
        iphone_titles = [product['title'] for product in response.data['results'][:2]]
        self.assertTrue(all('iPhone' in title for title in iphone_titles))

        # Поиск с опечаткой
        response = self.client.get(reverse('products:product_list'), {'q': 'ifone'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)  # Должен найти iPhone

        # Поиск по описанию
        response = self.client.get(reverse('products:product_list'), {'q': 'killer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Xiaomi Phone')

        # Поиск по части слова
        response = self.client.get(reverse('products:product_list'), {'q': 'sam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Samsung Galaxy')

        # Поиск по нескольким словам
        response = self.client.get(reverse('products:product_list'), {'q': 'phone android'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 1)  # Должен найти телефоны с Android

        # Точный поиск по модели
        response = self.client.get(reverse('products:product_list'), {'q': '"iPhone 14"'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 14')

    def test_unauthorized_access(self):
        """Тест доступа без авторизации."""
        self.client.logout()

        # Проверка доступа к списку продуктов (должен быть разрешен)
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка создания продукта (должно быть запрещено)
        response = self.client.post(
            reverse('products:product_create'),
            self.valid_payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wrong_user_access(self):
        """Тест доступа другого пользователя."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=other_user)

        # Попытка обновления чужого продукта
        response = self.client.patch(
            reverse('products:product_update', kwargs={'pk': self.product.pk}),
            {'title': 'Hacked Product'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'permission_denied')
        self.assertEqual(response.data['error'], 'У вас недостаточно прав для выполнения данного действия.')

        # Попытка удаления чужого продукта
        response = self.client.delete(
            reverse('products:product_delete', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'permission_denied')
        self.assertEqual(response.data['error'], 'У вас недостаточно прав для выполнения данного действия.')
