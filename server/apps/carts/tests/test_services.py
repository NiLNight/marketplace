from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from apps.products.models import Product, Category
from apps.carts.models import OrderItem
from decimal import Decimal
from apps.carts.exceptions import ProductNotAvailable, InvalidQuantity, CartItemNotFound, CartException
from apps.carts.services.cart_services import CartService
from django.http import HttpRequest

User = get_user_model()


class CartServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(title='Test Category')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=Decimal('100.00'),
            category=self.category,
            stock=20,  # Increased stock to accommodate quantity limit tests
            is_active=True,
            user=self.user
        )
        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=self.user.pk)
        self.request.session = {}

    # Tests for _validate_cart_item

    def test_validate_cart_item_valid(self):
        product = CartService._validate_cart_item(self.product.id, 5, self.user.id)
        self.assertEqual(product, self.product)

    def test_validate_cart_item_invalid_quantity_zero(self):
        with self.assertRaises(InvalidQuantity):
            CartService._validate_cart_item(self.product.id, 0, self.user.id)

    def test_validate_cart_item_invalid_quantity_negative(self):
        with self.assertRaises(InvalidQuantity):
            CartService._validate_cart_item(self.product.id, -1, self.user.id)

    def test_validate_cart_item_product_not_found(self):
        with self.assertRaises(ProductNotAvailable):
            CartService._validate_cart_item(999999, 1, self.user.id)

    def test_validate_cart_item_product_inactive(self):
        self.product.is_active = False
        self.product.save()
        with self.assertRaises(ProductNotAvailable):
            CartService._validate_cart_item(self.product.id, 1, self.user.id)

    def test_validate_cart_item_insufficient_stock(self):
        self.product.stock = 5
        self.product.save()

        # Должно пройти - 5 <= 5
        CartService._validate_cart_item(self.product.id, 5, self.user.id)

        # Должно вызвать исключение - 6 > 5
        with self.assertRaises(ProductNotAvailable):
            CartService._validate_cart_item(self.product.id, 6, self.user.id)

    def test_validate_cart_item_quantity_limit(self):
        # Устанавливаем достаточный запас для проверки ограничения корзины
        self.product.stock = 30  # Больше лимита корзины (20)
        self.product.save()

        # Проверяем, что запрос 21 единиц не вызывает исключение
        # (количество будет ограничено до 20)
        CartService._validate_cart_item(self.product.id, 21, self.user.id)

    def test_add_to_cart_respects_quantity_limit(self):
        # Добавляем 20 - должно пройти
        CartService.add_to_cart(self.request, self.product.id, 20)
        item = OrderItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, 20)

        # Пытаемся добавить ещё - должно остаться 20
        CartService.add_to_cart(self.request, self.product.id, 5)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 20)

    def test_update_cart_item_respects_quantity_limit(self):
        # Устанавливаем достаточный запас
        self.product.stock = 30
        self.product.save()

        CartService.add_to_cart(self.request, self.product.id, 10)
        # Пытаемся обновить до 25 - должно установиться 20
        CartService.update_cart_item(self.request, self.product.id, 25)
        item = OrderItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, 20)  # Проверяем ограничение

    # Tests for get_cart

    def test_get_cart_authenticated_empty(self):
        cart_items = CartService.get_cart(self.request)
        self.assertEqual(len(cart_items), 0)

    def test_get_cart_authenticated_with_items(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        cart_items = CartService.get_cart(self.request)
        self.assertEqual(len(cart_items), 1)
        self.assertEqual(cart_items[0].product, self.product)
        self.assertEqual(cart_items[0].quantity, 5)

    def test_get_cart_unauthenticated_empty(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {}
        cart_items = CartService.get_cart(request_unauthenticated)
        self.assertEqual(len(cart_items), 0)

    def test_get_cart_unauthenticated_with_items(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 3}}
        cart_items = CartService.get_cart(request_unauthenticated)
        self.assertEqual(len(cart_items), 1)
        self.assertEqual(cart_items[0]['product'], self.product)
        self.assertEqual(cart_items[0]['quantity'], 3)

    # Tests for add_to_cart

    def test_add_to_cart_authenticated_new_item(self):
        CartService.add_to_cart(self.request, self.product.id, 2)
        self.assertEqual(OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).count(), 1)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 2)

    def test_add_to_cart_authenticated_existing_item(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        CartService.add_to_cart(self.request, self.product.id, 2)
        self.assertEqual(OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).count(), 1)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 3)

    def test_add_to_cart_unauthenticated_new_item(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {}
        CartService.add_to_cart(request_unauthenticated, self.product.id, 2)
        self.assertEqual(request_unauthenticated.session.get('cart', {}).get(str(self.product.id)), 2)

    def test_add_to_cart_unauthenticated_existing_item(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 1}}
        CartService.add_to_cart(request_unauthenticated, self.product.id, 2)
        self.assertEqual(request_unauthenticated.session.get('cart', {}).get(str(self.product.id)), 3)

    def test_add_to_cart_quantity_limit_authenticated(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=18)
        CartService.add_to_cart(self.request, self.product.id, 3)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 20)

    def test_add_to_cart_quantity_limit_unauthenticated(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 18}}
        CartService.add_to_cart(request_unauthenticated, self.product.id, 3)
        self.assertEqual(request_unauthenticated.session.get('cart', {}).get(str(self.product.id)), 20)

    # Tests for update_cart_item

    def test_update_cart_item_authenticated(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        updated_item = CartService.update_cart_item(self.request, self.product.id, 3)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 3)
        self.assertEqual(updated_item['quantity'], 3)

    def test_update_cart_item_authenticated_remove(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=5, order=None)
        updated_item = CartService.update_cart_item(self.request, self.product.id, 0)
        self.assertFalse(OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).exists())
        self.assertIsNone(updated_item)

    def test_update_cart_item_authenticated_not_found(self):
        with self.assertRaises(ProductNotAvailable):
            CartService.update_cart_item(self.request, 999999, 1)

    def test_update_cart_item_unauthenticated(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 5}}
        updated_item = CartService.update_cart_item(request_unauthenticated, self.product.id, 3)
        self.assertEqual(request_unauthenticated.session.get('cart', {}).get(str(self.product.id)), 3)
        self.assertEqual(updated_item['quantity'], 3)

    def test_update_cart_item_unauthenticated_remove(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 5}}
        updated_item = CartService.update_cart_item(request_unauthenticated, self.product.id, 0)
        self.assertFalse(str(self.product.id) in request_unauthenticated.session.get('cart', {}))
        self.assertIsNone(updated_item)

    def test_update_cart_item_unauthenticated_not_found(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {}
        with self.assertRaises(ProductNotAvailable):
            CartService.update_cart_item(request_unauthenticated, 999999, 1)

    # Tests for remove_from_cart

    def test_remove_from_cart_authenticated(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=5)
        success = CartService.remove_from_cart(self.request, self.product.id)
        self.assertTrue(success)
        self.assertFalse(OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).exists())

    def test_remove_from_cart_authenticated_not_found(self):
        with self.assertRaises(CartItemNotFound):
            CartService.remove_from_cart(self.request, 999999)

    def test_remove_from_cart_unauthenticated(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {'cart': {str(self.product.id): 5}}
        success = CartService.remove_from_cart(request_unauthenticated, self.product.id)
        self.assertTrue(success)
        self.assertFalse(str(self.product.id) in request_unauthenticated.session.get('cart', {}))

    def test_remove_from_cart_unauthenticated_not_found(self):
        request_unauthenticated = HttpRequest()
        request_unauthenticated.user = AnonymousUser()
        request_unauthenticated.session = {}
        with self.assertRaises(CartItemNotFound):
            CartService.remove_from_cart(request_unauthenticated, 999999)

    # Tests for merge_cart_on_login

    def test_merge_cart_on_login_empty_session_cart(self):
        session_cart = {}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.filter(user=self.user, order__isnull=True).count(), 0)

    def test_merge_cart_on_login_new_items(self):
        product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=Decimal('200.00'),
            category=self.category,
            stock=5,
            is_active=True,
            user=self.user
        )
        session_cart = {str(self.product.id): 2, str(product2.id): 3}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.filter(user=self.user, order__isnull=True).count(), 2)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 2)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=product2, order__isnull=True).quantity, 3)

    def test_merge_cart_on_login_existing_items(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        session_cart = {str(self.product.id): 2}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.filter(user=self.user, product=self.product, order__isnull=True).count(), 1)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 3)

    def test_merge_cart_on_login_mix_new_and_existing(self):
        product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=Decimal('200.00'),
            category=self.category,
            stock=5,
            is_active=True,
            user=self.user
        )
        OrderItem.objects.create(user=self.user, product=self.product, quantity=1)
        session_cart = {str(self.product.id): 2, str(product2.id): 3}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.filter(user=self.user, order__isnull=True).count(), 2)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 3)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=product2, order__isnull=True).quantity, 3)

    def test_merge_cart_on_login_quantity_limit(self):
        OrderItem.objects.create(user=self.user, product=self.product, quantity=18)
        session_cart = {str(self.product.id): 5}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 20)

    def test_merge_cart_on_login_insufficient_stock(self):
        product2 = Product.objects.create(
            title='Test Product 2',
            description='Desc 2',
            price=Decimal('200.00'),
            category=self.category,
            stock=1,
            user=self.user
        )
        session_cart = {str(product2.id): 3}
        with self.assertRaises(ProductNotAvailable):
            CartService.merge_cart_on_login(self.user, session_cart)
        self.assertFalse(OrderItem.objects.filter(user=self.user, product=product2, order__isnull=True).exists())

    def test_merge_cart_on_login_invalid_product_id_in_session(self):
        session_cart = {str(self.product.id): 2, 'invalid_id': 3}
        CartService.merge_cart_on_login(self.user, session_cart)
        self.assertEqual(OrderItem.objects.filter(user=self.user, order__isnull=True).count(), 1)
        self.assertEqual(OrderItem.objects.get(user=self.user, product=self.product, order__isnull=True).quantity, 2)
