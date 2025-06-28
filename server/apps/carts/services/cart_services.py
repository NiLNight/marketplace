import logging
from django.db import transaction
from apps.carts.models import OrderItem
from apps.products.models import Product
from apps.carts.exceptions import ProductNotAvailable, InvalidQuantity, CartItemNotFound

logger = logging.getLogger(__name__)


class CartService:
    """Сервис для управления корзиной авторизованных и неавторизованных пользователей.

    Attributes:
        None: Класс не содержит статических атрибутов, только методы.
    """

    @staticmethod
    def _validate_cart_item(product_id: int, quantity: int, user_id: str) -> Product:
        """Проверка корректности данных для добавления или обновления товара в корзине.

        Args:
            product_id (int): ID товара.
            quantity (int): Количество товара.
            user_id (str): ID пользователя или 'anonymous'.

        Returns:
            Product: Объект товара, если проверки пройдены.

        Raises:
            InvalidQuantity: Если количество меньше 1.
            ProductNotAvailable: Если товар не существует, неактивен или недостаточно на складе.
        """
        product = Product.objects.filter(id=product_id, is_active=True).first()
        if not product:
            raise ProductNotAvailable("Товар не найден или неактивен")
        if quantity <= 0:
            raise InvalidQuantity("Количество должно быть больше 0")
        if quantity > product.stock:
            raise ProductNotAvailable("Недостаточно товара на складе")
        if quantity > 20:
            quantity = 20  # Ограничиваем до 20 для лимита корзины
            logger.info(f"Quantity {quantity} for product {product_id} exceeds limit, setting to 20, user={user_id}")
        return product

    @staticmethod
    def get_cart(request):
        """Получение содержимого корзины.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            QuerySet или список: Содержимое корзины для авторизованных или неавторизованных пользователей.

        Raises:
            Exception: Если произошла ошибка при получении данных корзины из-за проблем с базой данных.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            cart_items = OrderItem.objects.filter(
                user=request.user, order__isnull=True
            ).select_related('product', 'product__category').prefetch_related(
                'product__category__children'
            )
            logger.info(f"Retrieved cart, user={user_id}, items={cart_items.count()}")
            return cart_items
        else:
            cart = request.session.get('cart', {})
            product_ids = [int(pid) for pid in cart.keys() if pid.isdigit()]
            products = Product.objects.filter(
                id__in=product_ids, is_active=True
            ).select_related('category').prefetch_related('category__children')
            logger.info(f"Retrieved session cart, user={user_id}, items={products.count()}")
            return [{'product': p, 'quantity': cart[str(p.id)]} for p in products]

    @staticmethod
    @transaction.atomic
    def add_to_cart(request, product_id: int, quantity: int = 1) -> None:
        """Добавление товара в корзину.

        Args:
            request (HttpRequest): Объект запроса, содержащий информацию о пользователе и сессии.
            product_id (int): ID товара для добавления.
            quantity (int): Количество товара (по умолчанию 1).

        Raises:
            InvalidQuantity: Если количество меньше 1.
            ProductNotAvailable: Если товар не существует, неактивен или недостаточно на складе.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        product = CartService._validate_cart_item(product_id, quantity, user_id)

        if request.user.is_authenticated:
            cart_item, created = OrderItem.objects.get_or_create(
                user=request.user,
                product=product,
                order__isnull=True,
                defaults={'quantity': 0}
            )
            new_quantity = min(cart_item.quantity + quantity, 20)  # Ограничиваем до 20
            cart_item.quantity = new_quantity
            cart_item.save()
            logger.info(f"Added product {product_id} to cart, user={user_id}, quantity={new_quantity}")
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            current_quantity = cart.get(product_id_str, 0)
            new_quantity = min(current_quantity + quantity, 20)  # Ограничиваем до 20
            cart[product_id_str] = new_quantity
            request.session['cart'] = cart
            logger.info(f"Added product {product_id} to session cart, user={user_id}, quantity={new_quantity}")

    @staticmethod
    @transaction.atomic
    def update_cart_item(request, product_id: int, quantity: int) -> dict | None:
        """Обновление количества товара в корзине.

        Args:
            request (HttpRequest): Объект запроса.
            product_id (int): ID товара.
            quantity (int): Новое количество товара.

        Returns:
            dict | None: Данные элемента корзины или None, если элемент удален.

        Raises:
            ProductNotAvailable: Если товар не существует, неактивен или недостаточно на складе.
            CartItemNotFound: Если элемент корзины не найден и quantity > 0.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if quantity > 0:
            product = CartService._validate_cart_item(product_id, quantity, user_id)
        else:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                logger.warning(f"Product {product_id} not found or inactive, user={user_id}")
                raise ProductNotAvailable()

        if request.user.is_authenticated:
            try:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                if quantity > 0:
                    cart_item.quantity = min(quantity, 20)  # Ограничиваем до 20
                    cart_item.save()
                    logger.info(f"Updated cart item {product_id}, quantity={cart_item.quantity}, user={user_id}")
                    return {'id': cart_item.id, 'product_id': cart_item.product_id, 'quantity': cart_item.quantity}
                else:
                    cart_item.delete()
                    logger.info(f"Removed cart item {product_id}, user={user_id}")
                    return None
            except OrderItem.DoesNotExist:
                logger.warning(f"Cart item {product_id} not found, user={user_id}")
                if quantity > 0:
                    raise CartItemNotFound()
                return None  # Для quantity=0 возвращаем None
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            if product_id_str not in cart:
                logger.warning(f"Cart item {product_id} not found, user={user_id}")
                if quantity > 0:
                    raise CartItemNotFound()
                return None  # Для quantity=0 возвращаем None
            if quantity > 0:
                cart[product_id_str] = min(quantity, 20)  # Ограничиваем до 20
                request.session['cart'] = cart
                logger.info(f"Updated session cart item {product_id}, quantity={cart[product_id_str]}, user={user_id}")
                return {'product_id': product_id, 'quantity': cart[product_id_str]}
            else:
                del cart[product_id_str]
                request.session['cart'] = cart
                logger.info(f"Removed session cart item {product_id}, user={user_id}")
                return None

    @staticmethod
    @transaction.atomic
    def remove_from_cart(request, product_id: int) -> bool:
        """Удаление товара из корзины.

        Args:
            request (HttpRequest): Объект запроса.
            product_id (int): ID товара для удаления.

        Returns:
            bool: True, если товар удален, False, если не найден.

        Raises:
            CartItemNotFound: Если товар не найден в корзине.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            try:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                cart_item.delete()
                logger.info(f"Removed product {product_id} from cart, user={user_id}")
                return True
            except OrderItem.DoesNotExist:
                logger.warning(f"Product {product_id} not found in cart, user={user_id}")
                raise CartItemNotFound()
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            if product_id_str in cart:
                del cart[product_id_str]
                request.session['cart'] = cart
                logger.info(f"Removed product {product_id} from session cart, user={user_id}")
                return True
            logger.warning(f"Product {product_id} not found in session cart, user={user_id}")
            raise CartItemNotFound()

    @staticmethod
    @transaction.atomic
    def merge_cart_on_login(user, session_cart: dict) -> None:
        """Слияние корзины из сессии с данными пользователя при входе.

        Args:
            user (User): Аутентифицированный пользователь.
            session_cart (dict): Корзина из сессии (id товара: количество).

        Raises:
            ProductNotAvailable: Если товар не существует или неактивен.
        """
        user_id = user.id
        if session_cart:
            for product_id_str, quantity in session_cart.items():
                try:
                    product_id = int(product_id_str)
                    product = CartService._validate_cart_item(product_id, quantity, user_id)
                    cart_item, created = OrderItem.objects.get_or_create(
                        user=user,
                        product=product,
                        order__isnull=True,
                        defaults={'quantity': min(quantity, 20)}
                    )
                    if not created:
                        new_quantity = min(cart_item.quantity + quantity, 20)
                        if new_quantity > product.stock:
                            raise ProductNotAvailable("Недостаточно товара на складе.")
                        cart_item.quantity = new_quantity
                        cart_item.save()
                    logger.info(f"Merged product {product_id} to cart, user={user_id}")
                except Product.DoesNotExist:
                    logger.warning(f"Product {product_id_str} not found or inactive, user={user_id}")
                    raise ProductNotAvailable(f"Товар с ID {product_id_str} не найден или неактивен")
                except ValueError:
                    logger.warning(f"Invalid product ID {product_id_str}, user={user_id}")
                    continue
