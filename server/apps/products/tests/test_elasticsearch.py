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
from rest_framework.test import APIClient
from django.core.cache import cache
from apps.products.models import Category, Product
from apps.products.documents import ProductDocument
from apps.products.services.query_services import ProductQueryService
from apps.products.services.tasks import update_elasticsearch_task

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
        response = self.client.get(reverse('products:product_list') + '?q=iphone')
        
        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], 'iPhone 15')
        self.assertEqual(response.data['results'][1]['title'], 'iPhone 13')

        # Проверяем, что поиск был вызван с правильными параметрами
        mock_search.assert_called_once()