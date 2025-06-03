"""Модуль тестов для сериализаторов приложения reviews."""

import logging
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer, ReviewCreateSerializer
from apps.products.models import Product, Category
from apps.core.models import Like

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewSerializerTest(TestCase):
    """Тесты для сериализатора Review.

    Проверяет сериализацию и десериализацию данных отзывов.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, продукт и отзыв.
        """
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
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )

    def test_review_serialization(self):
        """Тест сериализации отзыва."""
        serializer = ReviewSerializer(self.review)
        data = serializer.data
        
        self.assertEqual(data['value'], 5)
        self.assertEqual(data['text'], 'Отличный продукт!')
        self.assertEqual(data['user'], str(self.user))
        self.assertEqual(data['product'], str(self.product))
        self.assertIn('created', data)
        self.assertIn('updated', data)
        self.assertEqual(data['likes_count'], 0)

        # Добавляем лайк и проверяем обновление счетчика
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        Like.objects.create(
            user=user2,
            content_object=self.review
        )
        serializer = ReviewSerializer(self.review)
        self.assertEqual(serializer.data['likes_count'], 1)

    def test_review_create_serializer_validation(self):
        """Тест валидации данных при создании отзыва."""
        # Тест с валидными данными
        valid_data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Хороший продукт'
        }
        serializer = ReviewCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Тест с некорректной оценкой
        invalid_data = valid_data.copy()
        invalid_data['value'] = 6
        serializer = ReviewCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('value', serializer.errors)

        # Тест с несуществующим продуктом
        invalid_data = valid_data.copy()
        invalid_data['product'] = 999
        serializer = ReviewCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product', serializer.errors)

    def test_review_update_serializer(self):
        """Тест обновления отзыва через сериализатор."""
        update_data = {
            'value': 3,
            'text': 'Обновленный текст отзыва'
        }
        serializer = ReviewCreateSerializer(self.review, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_review = serializer.save()
        
        self.assertEqual(updated_review.value, 3)
        self.assertEqual(updated_review.text, 'Обновленный текст отзыва')
        self.assertEqual(updated_review.product, self.product)
        self.assertEqual(updated_review.user, self.user)

    def test_review_image_serialization(self):
        """Тест сериализации отзыва с изображением."""
        image_data = b'fake-image-data'
        image = SimpleUploadedFile(
            'test_image.jpg',
            image_data,
            content_type='image/jpeg'
        )
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        review_with_image = Review.objects.create(
            product=self.product,
            user=user2,
            value=5,
            text='Отзыв с картинкой',
            image=image
        )
        
        serializer = ReviewSerializer(review_with_image)
        self.assertIn('image', serializer.data)
        self.assertTrue(serializer.data['image'].endswith('.jpg'))

    def test_review_likes_serialization(self):
        """Тест сериализации лайков отзыва."""
        serializer = ReviewSerializer(self.review)
        self.assertIn('likes_count', serializer.data)
        self.assertEqual(serializer.data['likes_count'], 0)

        # Добавляем лайки и проверяем обновление счетчика
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        user3 = User.objects.create_user('user3', 'user3@example.com', 'pass123')
        
        Like.objects.create(user=user2, content_object=self.review)
        serializer = ReviewSerializer(self.review)
        self.assertEqual(serializer.data['likes_count'], 1)
        
        Like.objects.create(user=user3, content_object=self.review)
        serializer = ReviewSerializer(self.review)
        self.assertEqual(serializer.data['likes_count'], 2)

    def test_review_create_with_empty_text(self):
        """Тест создания отзыва с пустым текстом."""
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        data = {
            'product': self.product.id,
            'value': 4
        }
        serializer = ReviewCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        review = serializer.save(user=user2)
        self.assertEqual(review.text, '')

    def test_review_create_with_invalid_image(self):
        """Тест создания отзыва с некорректным изображением."""
        image_data = b'fake-image-data'
        image = SimpleUploadedFile(
            'test_image.txt',
            image_data,
            content_type='text/plain'
        )
        data = {
            'product': self.product.id,
            'value': 4,
            'text': 'Тест',
            'image': image
        }
        serializer = ReviewCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors) 