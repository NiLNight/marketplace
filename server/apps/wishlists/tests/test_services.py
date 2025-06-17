from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from apps.products.models import Product, Category
from apps.wishlists.models import WishlistItem
from apps.wishlists.exceptions import ProductNotAvailable, WishlistItemNotFound
from apps.wishlists.services.wishlist_services import WishlistService

User = get_user_model()


class WishlistServiceTests(TestCase):
    """
    Тесты для WishlistService.

    Покрывают функциональность добавления, удаления и получения элементов списка желаний,
    а также слияния списка желаний при входе пользователя.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        Создает пользователя, категорию и два тестовых товара (активный и неактивный).
        """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product1 = Product.objects.create(
            title='Test Product 1',
            description='Description 1',
            price=Decimal('100.00'),
            category=self.category,
            stock=10,
            user=self.user,
            is_active=True
        )
        self.product2 = Product.objects.create(
            title='Test Product 2',
            description='Description 2',
            price=Decimal('200.00'),
            category=self.category,
            stock=0,  # Не в наличии
            user=self.user,
            is_active=False  # Неактивен
        )

    def tearDown(self):
        """
        Очистка тестовых данных после каждого теста.
        Удаляет все созданные тестовые объекты.
        """
        User.objects.all().delete()
        Category.objects.all().delete()
        Product.objects.all().delete()
        WishlistItem.objects.all().delete()

    def test_add_to_wishlist_authenticated_success(self):
        """
        Тест успешного добавления товара в список желаний авторизованным пользователем.

        Проверяет, что после вызова сервиса создается новый объект WishlistItem
        для указанного пользователя и товара.
        """
        request = self.factory.post('/')
        request.user = self.user
        WishlistService.add_to_wishlist(request, self.product1.id)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )

    def test_add_to_wishlist_authenticated_duplicate(self):
        """
        Тест добавления существующего товара авторизованным пользователем.

        Проверяет, что при попытке добавить товар, который уже есть в списке желаний
        авторизованного пользователя, новый объект не создается, и их количество остается равным 1.
        """
        request = self.factory.post('/')
        request.user = self.user
        WishlistItem.objects.create(user=self.user, product=self.product1)
        WishlistService.add_to_wishlist(request, self.product1.id)
        self.assertEqual(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).count(), 1
        )

    def test_add_to_wishlist_unauthenticated_success(self):
        """
        Тест успешного добавления товара в список желаний неавторизованным пользователем.

        Проверяет, что ID товара добавляется в список 'wishlist' в сессии пользователя.
        Используется тестовая сессия клиента.
        """
        request = self.factory.post('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session  # Используем тестовую сессию
        WishlistService.add_to_wishlist(request, self.product1.id)
        self.assertIn(
            str(self.product1.id),
            request.session.get('wishlist', [])
        )

    def test_add_to_wishlist_unauthenticated_duplicate(self):
        """
        Тест добавления существующего товара неавторизованным пользователем.

        Проверяет, что при попытке добавить товар, который уже есть в списке 'wishlist'
        в сессии неавторизованного пользователя, дубликат не добавляется.
        """
        request = self.factory.post('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session
        request.session['wishlist'] = [str(self.product1.id)]
        WishlistService.add_to_wishlist(request, self.product1.id)
        self.assertEqual(
            request.session.get('wishlist', []).count(str(self.product1.id)),
            1
        )

    def test_add_to_wishlist_product_not_available(self):
        """
        Тест добавления неактивного товара.

        Проверяет, что при попытке добавить неактивный товар вызывается исключение ProductNotAvailable.
        """
        request = self.factory.post('/')
        request.user = self.user
        with self.assertRaises(ProductNotAvailable):
            WishlistService.add_to_wishlist(request, self.product2.id)

    def test_add_to_wishlist_nonexistent_product(self):
        """
        Тест добавления несуществующего товара.

        Проверяет, что при попытке добавить товар с несуществующим ID вызывается исключение ProductNotAvailable.
        """
        request = self.factory.post('/')
        request.user = self.user
        with self.assertRaises(ProductNotAvailable):
            WishlistService.add_to_wishlist(request, 999999)

    # Tests for remove_from_wishlist
    def test_remove_from_wishlist_authenticated_success(self):
        """
        Тест успешного удаления товара из списка желаний авторизованным пользователем.

        Проверяет, что после вызова сервиса соответствующий объект WishlistItem удаляется.
        """
        request = self.factory.delete('/')
        request.user = self.user
        WishlistItem.objects.create(user=self.user, product=self.product1)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )
        WishlistService.remove_from_wishlist(request, self.product1.id)
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )

    def test_remove_from_wishlist_authenticated_not_found(self):
        """
        Тест удаления несуществующего товара из списка желаний авторизованным пользователем.

        Проверяет, что при попытке удалить товар, которого нет в списке желаний, вызывается исключение WishlistItemNotFound.
        """
        request = self.factory.delete('/')
        request.user = self.user
        with self.assertRaises(WishlistItemNotFound):
            WishlistService.remove_from_wishlist(request, self.product1.id)

    def test_remove_from_wishlist_unauthenticated_success(self):
        """
        Тест успешного удаления товара из списка желаний неавторизованным пользователем.

        Проверяет, что ID товара удаляется из списка 'wishlist' в сессии пользователя,
        если он там присутствует.
        """
        request = self.factory.delete('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session
        request.session['wishlist'] = [str(self.product1.id), str(self.product2.id)]
        WishlistService.remove_from_wishlist(request, self.product1.id)
        self.assertNotIn(
            str(self.product1.id),
            request.session.get('wishlist', [])
        )
        self.assertIn(
            str(self.product2.id),
            request.session.get('wishlist', [])
        )

    def test_remove_from_wishlist_unauthenticated_not_found(self):
        """
        Тест удаления несуществующего товара из списка желаний неавторизованным пользователем.

        Проверяет, что при попытке удалить товар, которого нет в списке 'wishlist'
        в сессии неавторизованного пользователя, вызывается исключение WishlistItemNotFound.
        """
        request = self.factory.delete('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session
        request.session['wishlist'] = [str(self.product2.id)]
        with self.assertRaises(WishlistItemNotFound):
            WishlistService.remove_from_wishlist(request, self.product1.id)

    # Tests for get_wishlist
    def test_get_wishlist_authenticated(self):
        """
        Тест получения списка желаний авторизованным пользователем.

        Проверяет, что сервис возвращает QuerySet с элементами WishlistItem,
        связанными с текущим пользователем.
        """
        request = self.factory.get('/')
        request.user = self.user
        WishlistItem.objects.create(user=self.user, product=self.product1)
        WishlistItem.objects.create(user=self.user, product=self.product2)
        wishlist_items = WishlistService.get_wishlist(request)
        self.assertEqual(wishlist_items.count(), 2)
        self.assertIn(self.product1, [item.product for item in wishlist_items])
        self.assertIn(self.product2, [item.product for item in wishlist_items])

    def test_get_wishlist_unauthenticated(self):
        """
        Тест получения списка желаний неавторизованным пользователем.

        Проверяет, что сервис возвращает список объектов Product,
        соответствующих ID в сессии, исключая неактивные и несуществующие товары.
        """
        request = self.factory.get('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session
        request.session['wishlist'] = [str(self.product1.id), str(self.product2.id), 'invalid_id']
        wishlist_items = WishlistService.get_wishlist(request)
        # Возвращаются только активные и существующие продукты из сессии
        self.assertEqual(wishlist_items.count(), 1)
        self.assertIn(self.product1, wishlist_items)
        self.assertNotIn(self.product2, wishlist_items)  # product2 неактивен
        # Несуществующий и не цифровой ID игнорируются

    def test_get_wishlist_empty_authenticated(self):
        """
        Тест получения пустого списка желаний авторизованным пользователем.

        Проверяет, что для пользователя без элементов в списке желаний возвращается пустой QuerySet.
        """
        request = self.factory.get('/')
        request.user = self.user
        wishlist_items = WishlistService.get_wishlist(request)
        self.assertEqual(wishlist_items.count(), 0)

    def test_get_wishlist_empty_unauthenticated(self):
        """
        Тест получения пустого списка желаний неавторизованным пользователем.

        Проверяет, что для сессии без сохраненных ID товаров возвращается пустой QuerySet продуктов.
        """
        request = self.factory.get('/')
        request.user = MagicMock(is_authenticated=False)
        request.session = self.client.session
        request.session['wishlist'] = []
        wishlist_items = WishlistService.get_wishlist(request)
        self.assertEqual(wishlist_items.count(), 0)

    @patch('apps.wishlists.services.wishlist_services.logger')
    def test_merge_wishlist_on_login_success(self, mock_logger):
        """
        Тест успешного слияния списка желаний при входе.

        Проверяет, что активные товары из списка в сессии
        добавляются в список желаний аутентифицированного пользователя,
        а неактивные игнорируются. Также проверяет соответствующее логирование.
        """
        # session_wishlist содержит ID активного и неактивного продукта
        session_wishlist = [str(self.product1.id), str(self.product2.id)]  # product2 неактивен
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        # Ожидаем, что добавится только product1
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product2
            ).exists()
        )
        # Проверяем логирование
        mock_logger.info.assert_any_call(
            f"Product {self.product1.id} merged into wishlist for user={self.user.id}"
        )
        mock_logger.debug.assert_called_once_with(
            f"Product with ID {self.product2.id} not found or inactive during wishlist merge for user={self.user.id}"
        )

    @patch('apps.wishlists.services.wishlist_services.logger')
    def test_merge_wishlist_on_login_with_duplicates(self, mock_logger):
        """
        Тест слияния списка желаний при наличии дубликатов.

        Проверяет, что при слиянии товаров, которые уже есть в списке желаний пользователя,
        дубликаты не создаются благодаря использованию get_or_create.
        """
        WishlistItem.objects.create(user=self.user, product=self.product1)
        session_wishlist = [str(self.product1.id)]
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )
        # Проверяем, что get_or_create не вызвал ошибку
        mock_logger.info.assert_any_call(
            f"Product {self.product1.id} merged into wishlist for user={self.user.id}"
        )

    @patch('apps.wishlists.services.wishlist_services.logger')
    def test_merge_wishlist_on_login_product_not_available(self, mock_logger):
        """
        Тест слияния списка желаний с неактивным товаром из сессии.

        Проверяет, что неактивный товар игнорируется и логируется как debug.
        """
        session_wishlist = [str(self.product2.id)]
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 0)
        mock_logger.debug.assert_called_once_with(
            f"Product with ID {self.product2.id} not found or inactive during wishlist merge for user={self.user.id}"
        )

    @patch('apps.wishlists.services.wishlist_services.logger')
    def test_merge_wishlist_on_login_nonexistent_product(self, mock_logger):
        """
        Тест слияния списка желаний с несуществующим товаром из сессии.

        Проверяет, что несуществующий товар игнорируется и логируется как debug.
        """
        non_existent_product_id = 999999
        session_wishlist = [str(non_existent_product_id)]
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 0)
        mock_logger.debug.assert_called_once_with(
            f"Product with ID {non_existent_product_id} not found or inactive during wishlist merge for user={self.user.id}"
        )

    @patch('apps.wishlists.services.wishlist_services.logger')
    def test_merge_wishlist_on_login_invalid_id_in_session(self, mock_logger):
        """
        Тест слияния списка желаний с некорректным ID в сессии.

        Проверяет, что некорректный ID игнорируется и логируется как debug.
        """
        session_wishlist = ['invalid_id']
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 0)
        mock_logger.debug.assert_called_once_with(
            f"Invalid product ID 'invalid_id' in session wishlist for user={self.user.id}"
        )

    def test_merge_wishlist_on_login_empty_session(self):
        """
        Тест слияния пустого списка желаний из сессии.

        Проверяет, что при слиянии пустого списка из сессии никаких изменений не происходит.
        """
        session_wishlist = []
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 0)

    def test_merge_wishlist_on_login_existing_wishlist_items(self):
        """
        Тест слияния списка желаний при наличии уже существующих элементов у пользователя.

        Проверяет, что при слиянии товаров, один из которых уже есть у пользователя, дубликат не создается.
        """
        WishlistItem.objects.create(user=self.user, product=self.product1)
        session_wishlist = [str(self.product1.id), str(self.product2.id)]  # product2 неактивен
        WishlistService.merge_wishlist_on_login(self.user, session_wishlist)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product1
            ).exists()
        )
