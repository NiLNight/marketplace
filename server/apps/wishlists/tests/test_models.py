from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from apps.products.models import Product, Category
from decimal import Decimal
from apps.wishlists.models import WishlistItem

User = get_user_model()


class WishlistItemModelTest(TestCase):
    """
    Тесты для модели WishlistItem.

    Проверяют создание элементов списка желаний, ограничения уникальности
    для аутентифицированных пользователей, а также корректность связей
    с моделями User и Product.
    """

    def setUp(self):
        """
        Настройка тестовых данных.

        Создает пользователя, категорию и продукт для использования в тестах.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            title='Test Product',
            description='Description',
            price=Decimal('10.00'),
            category=self.category,
            stock=10,
            user=self.user
        )

    def test_wishlist_item_creation(self):
        """
        Тест создания элемента списка желаний.

        Проверяет, что элемент WishlistItem успешно создается с правильными
        связями с пользователем и продуктом, а также с установленными
        временными метками (created, updated).
        """
        wishlist_item = WishlistItem.objects.create(
            user=self.user,
            product=self.product
        )
        self.assertEqual(wishlist_item.user, self.user)
        self.assertEqual(wishlist_item.product, self.product)
        self.assertIsNotNone(wishlist_item.created)
        self.assertIsNotNone(wishlist_item.updated)

    def test_unique_wishlist_product_authenticated_user(self):
        """
        Тест ограничения уникальности для аутентифицированных пользователей.

        Проверяет, что модель WishlistItem имеет ограничение UniqueConstraint,
        которое предотвращает добавление одного и того же продукта в список
        желаний одним и тем же аутентифицированным пользователем более одного раза.

        Raises:
            IntegrityError: Ожидается при попытке создания дубликата.
        """
        WishlistItem.objects.create(user=self.user, product=self.product)
        with self.assertRaises(IntegrityError):
            # Попытка создать дубликат для того же пользователя и продукта
            WishlistItem.objects.create(user=self.user, product=self.product)

    def test_allow_duplicate_product_for_unauthenticated_users(self):
        """
        Тест, разрешающий дублирование для неаутентифицированных пользователей.

        Проверяет, что ограничение UniqueConstraint не применяется для
        элементов списка желаний, связанных с null=True пользователем (гостем).
        """
        # Создаем элементы для неаутентифицированных пользователей
        item1 = WishlistItem.objects.create(user=None, product=self.product)
        item2 = WishlistItem.objects.create(user=None, product=self.product)
        self.assertIsNotNone(item1.pk)
        self.assertIsNotNone(item2.pk)
        self.assertNotEqual(item1.pk, item2.pk) # Убеждаемся, что созданы разные объекты

    def test_foreign_key_relationships(self):
        """
        Тест связей внешнего ключа.

        Проверяет корректность связей элемента списка желаний с пользователем и продуктом.
        """
        wishlist_item = WishlistItem.objects.create(
            user=self.user,
            product=self.product
        )
        self.assertEqual(wishlist_item.user.username, 'testuser')
        self.assertEqual(wishlist_item.product.title, 'Test Product')

    def test_str_representation(self):
        """
        Тест строкового представления элемента списка желаний.

        Проверяет, что метод __str__ возвращает ожидаемое строковое представление.
        """
        wishlist_item = WishlistItem.objects.create(user=self.user, product=self.product)
        expected_str = f"{self.product.title} в списке желаний {self.user.username}"
        self.assertEqual(str(wishlist_item), expected_str)