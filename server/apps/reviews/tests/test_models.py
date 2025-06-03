"""Модуль тестов для моделей приложения reviews."""

import logging
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.reviews.models import Review
from apps.products.models import Product, Category
from apps.core.models import Like

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewModelTest(TestCase):
    """Тесты для модели Review.

    Проверяет создание, валидацию и методы модели Review.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя и продукт для тестирования отзывов.
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
            user=self.user
        )
        self.review_data = {
            'product': self.product,
            'user': self.user,
            'value': 5,
            'text': 'Отличный продукт!'
        }

    def test_review_creation(self):
        """Тест создания отзыва с валидными данными."""
        review = Review.objects.create(**self.review_data)
        self.assertEqual(review.value, 5)
        self.assertEqual(review.text, 'Отличный продукт!')
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.likes.count(), 0)

    def test_review_str_representation(self):
        """Тест строкового представления отзыва."""
        review = Review.objects.create(**self.review_data)
        expected = f"{self.product.title}: 5 ({self.user.username})"
        self.assertEqual(str(review), expected)

    def test_review_invalid_rating(self):
        """Тест валидации некорректной оценки."""
        invalid_ratings = [-1, 0, 6, 10]
        for rating in invalid_ratings:
            with self.assertRaises(ValidationError):
                review = Review(
                    product=self.product,
                    user=self.user,
                    value=rating,
                    text='Test'
                )
                review.full_clean()

    def test_review_duplicate_user_product(self):
        """Тест создания дублирующего отзыва для одного продукта и пользователя."""
        Review.objects.create(**self.review_data)
        with self.assertRaises(ValidationError):
            duplicate_review = Review(
                product=self.product,
                user=self.user,
                value=4,
                text='Другой отзыв'
            )
            duplicate_review.full_clean()

    def test_review_image_upload(self):
        """Тест загрузки изображения для отзыва."""
        image_data = b'fake-image-data'
        image = SimpleUploadedFile(
            'test_image.jpg',
            image_data,
            content_type='image/jpeg'
        )
        review = Review.objects.create(
            **self.review_data,
            image=image
        )
        self.assertTrue(review.image.name.startswith('images/reviews/'))
        self.assertTrue(review.image.name.endswith('.jpg'))

    def test_review_image_invalid_extension(self):
        """Тест загрузки изображения с недопустимым расширением."""
        image_data = b'fake-image-data'
        image = SimpleUploadedFile(
            'test_image.txt',
            image_data,
            content_type='text/plain'
        )
        with self.assertRaises(ValidationError):
            review = Review(
                **self.review_data,
                image=image
            )
            review.full_clean()

    def test_review_ordering(self):
        """Тест сортировки отзывов по дате создания."""
        review1 = Review.objects.create(**self.review_data)
        review2 = Review.objects.create(
            product=self.product,
            user=User.objects.create_user('user2', 'user2@example.com', 'pass123'),
            value=4,
            text='Второй отзыв'
        )
        reviews = Review.objects.all()
        self.assertEqual(reviews[0], review2)
        self.assertEqual(reviews[1], review1)

    def test_review_likes_relation(self):
        """Тест связи отзыва с лайками."""
        review = Review.objects.create(**self.review_data)
        self.assertTrue(hasattr(review, 'likes'))
        self.assertEqual(review.likes.count(), 0)

        # Создаем лайк для отзыва
        user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
        Like.objects.create(
            user=user2,
            content_object=review
        )
        self.assertEqual(review.likes.count(), 1) 