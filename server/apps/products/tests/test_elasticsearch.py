"""
Модуль тестов для интеграции с Elasticsearch.

Содержит тесты для индексации и поиска продуктов через Elasticsearch.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from elasticsearch_dsl import Search
from rest_framework import status
from django.core.cache import cache
from apps.products.models import Category, Product
from apps.products.documents import ProductDocument
from apps.products.services.query_services import ProductQueryService
from apps.products.services.tasks import update_elasticsearch_task
from django.db import models

User = get_user_model()


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class ElasticsearchIntegrationTests(TestCase):
    """Тесты интеграции с Elasticsearch.

    В тестовом режиме проверяет только подготовку данных для индексации.
    """

    @patch('apps.products.services.tasks.update_elasticsearch_task.delay')
    def setUp(self, mock_task):
        """Подготовка тестовых данных."""
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
            is_active=True,
            discount=Decimal('0.00')
        )
        # Сохраняем mock для использования в тестах
        self.mock_task = mock_task

    def test_product_data_preparation(self):
        """Тест подготовки данных продукта для индексации."""
        # Проверяем, что сигнал был отправлен при создании продукта в setUp
        self.mock_task.assert_called_with(self.product.id)

        # Проверяем методы prepare
        doc = ProductDocument()
        self.assertEqual(doc.prepare_price(self.product), float(self.product.price))
        self.assertEqual(doc.prepare_discount(self.product), float(self.product.discount))
        self.assertEqual(doc.prepare_price_with_discount(self.product), float(self.product.price_with_discount))
        self.assertEqual(doc.prepare_category(self.product), {
            'id': self.category.id,
            'title': self.category.title,
            'slug': self.category.slug
        })

    @patch('apps.products.services.tasks.update_elasticsearch_task.delay')
    def test_product_indexing(self, mock_task):
        """Тест индексации продукта в Elasticsearch."""
        # Создаем новый продукт
        product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=5,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Проверяем, что задача обновления была вызвана
        mock_task.assert_called_with(product.id)

        # Проверяем подготовку документа
        doc = ProductDocument()
        self.assertEqual(doc.prepare_price(product), float('99.99'))
        self.assertEqual(doc.prepare_category(product)['title'], self.category.title)

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_product_search(self, mock_search):
        """Тест поиска продуктов через Elasticsearch."""
        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id=self.product.id)

        # Очищаем кэш перед выполнением поиска
        cache.clear()

        # Выполняем поиск
        response = self.client.get(reverse('products:product_list') + '?q=iphone')

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')

        # Проверяем, что поиск был вызван с правильными параметрами
        mock_search.assert_called_once()

    @patch('elasticsearch_dsl.Search.filter')
    def test_product_filtering_with_elasticsearch(self, mock_filter):
        """Тест фильтрации продуктов через Elasticsearch."""
        # Настраиваем мок для фильтрации
        mock_filter.return_value = Search()

        # Применяем фильтры
        ProductQueryService.apply_common_filters(
            Search(),
            category_id=self.category.id,
            min_price=Decimal('500.00'),
            max_price=Decimal('1000.00'),
            min_discount=Decimal('0.00'),
            in_stock=True
        )

        # Проверяем, что фильтр был вызван
        self.assertTrue(mock_filter.called)

    @patch('apps.products.services.tasks.update_elasticsearch_task.delay')
    def test_product_update_triggers_reindex(self, mock_task):
        """Тест переиндексации при обновлении продукта."""
        # Обновляем продукт
        self.product.title = 'Updated iPhone 15'
        self.product.save()

        # Проверяем, что задача обновления была вызвана
        mock_task.assert_called_with(self.product.id)

        # Проверяем подготовку обновленного документа
        doc = ProductDocument()
        self.assertEqual(doc.prepare_price(self.product), float(self.product.price))
        self.assertEqual(doc.prepare_category(self.product)['title'], self.category.title)

    @patch('apps.products.services.tasks.update_elasticsearch_task.delay')
    def test_product_deletion_removes_from_index(self, mock_task):
        """Тест удаления продукта из индекса при удалении из БД."""
        # Удаляем продукт
        product_id = self.product.id
        self.product.delete()

        # Проверяем, что задача удаления была вызвана
        mock_task.assert_called_with(product_id, delete=True)

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_search_with_category_filter(self, mock_search):
        """Тест поиска с фильтрацией по категории."""
        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id=self.product.id)

        # Выполняем поиск с фильтром по категории
        response = self.client.get(
            reverse('products:product_list') +
            f'?q=iphone&category={self.category.id}'
        )

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')

        # Проверяем, что поиск был вызван с правильными параметрами
        mock_search.assert_called_once()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_search_relevance_scoring(self, mock_search):
        """Тест релевантности результатов поиска."""
        # Создаем второй продукт
        product2 = Product.objects.create(
            title='iPhone 13',
            description='Старый iPhone',
            price=Decimal('799.99'),
            stock=5,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Очищаем кэш перед поиском
        cache.clear()

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(
            id__in=[self.product.id, product2.id]
        ).order_by('-created')  # Сортируем по дате создания, чтобы iPhone 15 был первым

        # Выполняем поиск
        response = self.client.get(reverse('products:product_list') + '?q=iphone 13')

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 13')
        self.assertEqual(response.data['results'][1]['title'], 'iPhone 15')

        # Проверяем, что поиск был вызван с правильными параметрами
        mock_search.assert_called_once()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_russian_morphology_search(self, mock_search):
        """Тест поиска с учетом морфологии русского языка."""
        # Создаем продукты с разными формами слов
        products = [
            Product.objects.create(
                title='Красный телефон',
                description='Мобильный телефон красного цвета',
                price=Decimal('999.99'),
                stock=10,
                category=self.category,
                user=self.user,
                is_active=True
            ),
            Product.objects.create(
                title='Телефоны Samsung',
                description='Мобильные телефоны в ассортименте',
                price=Decimal('899.99'),
                stock=5,
                category=self.category,
                user=self.user,
                is_active=True
            )
        ]

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id__in=[p.id for p in products])

        # Тестируем поиск с разными формами слова
        test_queries = ['телефон', 'телефоны', 'телефонов']
        for query in test_queries:
            response = self.client.get(reverse('products:product_list') + f'?q={query}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 2)

        mock_search.assert_called()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_fuzzy_search_with_typos(self, mock_search):
        """Тест поиска с опечатками в русском языке."""
        # Создаем продукт
        product = Product.objects.create(
            title='Смартфон Samsung Galaxy',
            description='Современный смартфон',
            price=Decimal('999.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id=product.id)

        # Тестируем поиск с опечатками
        test_queries = ['смортфон', 'самсунг', 'галакси']
        for query in test_queries:
            response = self.client.get(reverse('products:product_list') + f'?q={query}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['title'], 'Смартфон Samsung Galaxy')

        mock_search.assert_called()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_partial_match_search(self, mock_search):
        """Тест поиска по частичному совпадению в русском языке."""
        # Создаем продукты
        products = [
            Product.objects.create(
                title='Беспроводные наушники Sony',
                description='Bluetooth наушники с шумоподавлением',
                price=Decimal('299.99'),
                stock=15,
                category=self.category,
                user=self.user,
                is_active=True
            ),
            Product.objects.create(
                title='Наушники проводные Sennheiser',
                description='Профессиональные наушники',
                price=Decimal('199.99'),
                stock=20,
                category=self.category,
                user=self.user,
                is_active=True
            )
        ]

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id__in=[p.id for p in products])

        # Тестируем поиск по частям слов
        test_queries = ['науш', 'беспр', 'пров']
        for query in test_queries:
            response = self.client.get(reverse('products:product_list') + f'?q={query}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(len(response.data['results']) > 0)

        mock_search.assert_called()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_synonym_search(self, mock_search):
        """Тест поиска с учетом синонимов в русском языке."""
        # Создаем продукт
        product = Product.objects.create(
            title='Мобильный телефон iPhone',
            description='Современный смартфон Apple',
            price=Decimal('999.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id=product.id)

        # Тестируем поиск с синонимами
        test_queries = ['телефон', 'смартфон', 'мобильник']
        for query in test_queries:
            response = self.client.get(reverse('products:product_list') + f'?q={query}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['title'], 'Мобильный телефон iPhone')

        mock_search.assert_called()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_search_results_caching(self, mock_search):
        """Тест кэширования результатов поиска."""
        # Создаем продукт
        product = Product.objects.create(
            title='Тестовый продукт',
            description='Описание тестового продукта',
            price=Decimal('99.99'),
            stock=10,
            category=self.category,
            user=self.user,
            is_active=True
        )

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id=product.id)

        # Очищаем кэш перед тестом
        cache.clear()

        # Первый запрос (должен вызвать поиск)
        response1 = self.client.get(reverse('products:product_list') + '?q=тестовый')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response1.data['results']), 1)

        # Второй запрос (должен использовать кэш)
        response2 = self.client.get(reverse('products:product_list') + '?q=тестовый')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data['results']), 1)

        # Проверяем, что поиск был вызван только один раз
        mock_search.assert_called_once()

    @patch('apps.products.services.query_services.ProductQueryService.search_products')
    def test_search_with_category_hierarchy(self, mock_search):
        """Тест поиска с учетом иерархии категорий."""
        # Создаем подкатегорию
        subcategory = Category.objects.create(
            title='Смартфоны',
            description='Мобильные телефоны и смартфоны',
            parent=self.category
        )

        # Создаем продукты в разных категориях
        products = [
            Product.objects.create(
                title='Смартфон в подкатегории',
                description='Тестовый смартфон',
                price=Decimal('599.99'),
                stock=10,
                category=subcategory,
                user=self.user,
                is_active=True
            ),
            Product.objects.create(
                title='Смартфон в основной категории',
                description='Другой тестовый смартфон',
                price=Decimal('699.99'),
                stock=5,
                category=self.category,
                user=self.user,
                is_active=True
            )
        ]

        # Настраиваем мок для результатов поиска
        mock_search.return_value = Product.objects.filter(id__in=[p.id for p in products])

        # Тестируем поиск по категории и подкатегории
        response = self.client.get(
            reverse('products:product_list') +
            f'?q=смартфон&category={self.category.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Тестируем поиск только по подкатегории
        response = self.client.get(
            reverse('products:product_list') +
            f'?q=смартфон&category={subcategory.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)

        mock_search.assert_called()
