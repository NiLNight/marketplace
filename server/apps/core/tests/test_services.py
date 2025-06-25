from django.db import IntegrityError
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch
from apps.core.services.cache_services import CacheService
from apps.core.services.like_services import LikeService
from apps.core.models import Like
from apps.products.models import Product, Category
from apps.reviews.exceptions import InvalidReviewData, ReviewNotFound
from apps.reviews.models import Review

User = get_user_model()

class CacheServiceTest(TestCase):
    """
    Тесты для CacheService: генерация ключей, set/get/invalidate, edge-cases, ошибки.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/api/products', {'page': 2, 'q': 'test'})

    def test_build_cache_key(self):
        key = CacheService.build_cache_key(self.request, 'product_list')
        self.assertTrue(key.startswith('product_list:'))
        self.assertEqual(len(key.split(':')[1]), 32)  # md5 hash

    def test_set_and_get_cached_data(self):
        key = 'test_key'
        data = {'foo': 'bar'}
        CacheService.set_cached_data(key, data)
        cached = CacheService.get_cached_data(key)
        self.assertEqual(cached, data)

    def test_invalidate_cache(self):
        key = 'test_invalidate:123'
        CacheService.set_cached_data(key, 42)
        CacheService.invalidate_cache('test_invalidate', pk=123)
        self.assertIsNone(CacheService.get_cached_data(key))

    @patch('django.core.cache.cache.delete_pattern')
    def test_invalidate_cache_prefix(self, mock_delete_pattern):
        CacheService.invalidate_cache('prefix')
        mock_delete_pattern.assert_called_once_with('prefix:*')

    @patch('django.core.cache.cache.get', side_effect=Exception('fail'))
    def test_get_cached_data_error(self, mock_get):
        self.assertIsNone(CacheService.get_cached_data('err_key'))

    @patch('django.core.cache.cache.set', side_effect=Exception('fail'))
    def test_set_cached_data_error(self, mock_set):
        # Не должно выбрасывать исключение
        CacheService.set_cached_data('err_key', 1)

class LikeServiceTest(TestCase):
    """
    Тесты для LikeService: переключение лайка, ошибки, подсчёт, edge-cases.
    """
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.category = Category.objects.create(
            title='Test Category',
            description='Test description'
        )
        self.product = Product.objects.create(
            title="Test Product",
            user=self.user,
            price=100.00,
            category_id=self.category.id
        )
        # Создаем объект Review
        self.review = Review.objects.create(
            user=self.user,
            product_id=self.product.id,
            value=5,
            text="Test review"
        )
        self.content_type = ContentType.objects.get_for_model(Review)
        self.object_id = self.review.id
        # Создаем лайк для self.user
        Like.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.object_id
        )
        # Очищаем лишние лайки, сохраняя лайк для self.user
        Like.objects.filter(content_type=self.content_type, object_id=self.object_id).exclude(
            user=self.user
        ).delete()

    def test_toggle_like_create_and_remove(self):
        # Создаем другого пользователя
        another_user = User.objects.create_user('anotheruser', 'another@example.com', 'password')
        # Проверяем добавление лайка
        result = LikeService.toggle_like(self.content_type, self.object_id, another_user)
        self.assertEqual(result['action'], 'liked')
        self.assertEqual(result['likes_count'], 2)  # Один лайк от self.user, второй от another_user
        # Проверяем удаление лайка
        result2 = LikeService.toggle_like(self.content_type, self.object_id, another_user)
        self.assertEqual(result2['action'], 'unliked')
        self.assertEqual(result2['likes_count'], 1)  # Остается только лайк от self.user

    def test_toggle_like_object_not_found(self):
        fake_ct = ContentType.objects.get_for_model(User)
        with self.assertRaises(ReviewNotFound):
            LikeService.toggle_like(fake_ct, 999999, self.user)

    @patch('apps.core.models.Like.objects.get_or_create', side_effect=IntegrityError('db error'))
    def test_toggle_like_integrity_error(self, mock_get_or_create):
        with self.assertRaises(InvalidReviewData):
            LikeService.toggle_like(self.content_type, self.object_id, self.user)