"""Модуль тестов для моделей приложения comments."""

import logging
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.comments.models import Comment
from apps.reviews.models import Review
from apps.products.models import Product, Category
from apps.core.models import Like

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentModelTest(TestCase):
    """Тесты для модели Comment.

    Проверяет создание, валидацию и методы модели Comment.
    """

    def setUp(self):
        """Инициализация данных для тестов.

        Создает тестового пользователя, продукт, отзыв и комментарий.
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
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            value=5,
            text='Отличный продукт!'
        )
        self.comment_data = {
            'review': self.review,
            'user': self.user,
            'text': 'Тестовый комментарий'
        }
        self.comment = Comment.objects.create(**self.comment_data)

    def test_comment_creation(self):
        """Тест создания комментария."""
        self.assertEqual(self.comment.text, 'Тестовый комментарий')
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.review, self.review)
        self.assertIsNone(self.comment.parent)
        self.assertEqual(str(self.comment), f"{self.product.title}: {self.comment.text[:50]}...")

    def test_comment_with_parent(self):
        """Тест создания вложенного комментария."""
        child_comment = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Ответ на комментарий',
            parent=self.comment
        )
        self.assertEqual(child_comment.parent, self.comment)
        self.assertEqual(list(self.comment.children.all()), [child_comment])

    def test_comment_likes(self):
        """Тест лайков комментария."""
        # Создаем второго пользователя
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Добавляем лайки
        Like.objects.create(user=self.user, content_object=self.comment)
        Like.objects.create(user=user2, content_object=self.comment)
        
        self.assertEqual(self.comment.likes.count(), 2)

    def test_comment_empty_text(self):
        """Тест валидации пустого текста комментария."""
        with self.assertRaises(ValidationError):
            comment = Comment(
                review=self.review,
                user=self.user,
                text=''
            )
            comment.full_clean()

    def test_comment_deletion_cascade(self):
        """Тест каскадного удаления комментариев."""
        # Создаем дочерние комментарии
        child1 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 1',
            parent=self.comment
        )
        child2 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 2',
            parent=child1
        )

        # Удаляем родительский комментарий
        self.comment.delete()

        # Проверяем, что все дочерние комментарии также удалены
        self.assertEqual(Comment.objects.filter(id=child1.id).count(), 0)
        self.assertEqual(Comment.objects.filter(id=child2.id).count(), 0)

    def test_comment_ordering(self):
        """Тест порядка комментариев."""
        # Создаем несколько комментариев
        comment2 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Второй комментарий'
        )
        comment3 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Третий комментарий'
        )

        # Проверяем порядок по дате создания
        comments = Comment.objects.filter(review=self.review)
        self.assertEqual(list(comments), [self.comment, comment2, comment3])

    def test_cached_children(self):
        """Тест кэширования дочерних комментариев."""
        # Создаем дочерние комментарии
        child1 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 1',
            parent=self.comment
        )
        child2 = Comment.objects.create(
            review=self.review,
            user=self.user,
            text='Дочерний комментарий 2',
            parent=self.comment
        )

        # Проверяем кэширование через свойство cached_children
        cached_children = self.comment.cached_children
        self.assertEqual(list(cached_children), [child1, child2]) 