import logging
from django.db import transaction
from apps.products.models import Product
from apps.wishlists.exceptions import ProductNotAvailable, WishlistItemNotFound
from apps.wishlists.models import WishlistItem

logger = logging.getLogger(__name__)


class WishlistService:
    """Сервис для управления списками желаний зарегистрированных и незарегистрированных пользователей.

    Attributes:
        None: Класс не содержит статических атрибутов, только методы.
    """

    @staticmethod
    @transaction.atomic
    def add_to_wishlist(request, product_id: int) -> None:
        """Добавление товара в список желаний.

        Args:
            request (HttpRequest): Объект запроса, содержащий информацию о пользователе и сессии.
            product_id (int): ID товара для добавления.

        Raises:
            ProductNotAvailable: Если товар не существует или неактивен.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise ProductNotAvailable()
        if request.user.is_authenticated:
            WishlistItem.objects.get_or_create(user=request.user, product=product)
            logger.info(f"Product {product_id} added to wishlist for user={user_id}")
        else:
            wishlist = request.session.get('wishlist', [])
            if str(product_id) not in wishlist:
                wishlist.append(str(product_id))
                request.session['wishlist'] = wishlist
                logger.info(f"Product {product_id} added to session wishlist for user={user_id}")

    @staticmethod
    @transaction.atomic
    def remove_from_wishlist(request, product_id: int) -> None:
        """Удаление товара из списка желаний.

        Args:
            request (HttpRequest): Объект запроса.
            product_id (int): ID товара для удаления.

        Raises:
            WishlistItemNotFound: Если товар не найден в списке желаний.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            try:
                wishlist_item = WishlistItem.objects.get(user=request.user, product_id=product_id)
                wishlist_item.delete()
                logger.info(f"Product {product_id} removed from wishlist for user={user_id}")
            except WishlistItem.DoesNotExist:
                raise WishlistItemNotFound()
        else:
            wishlist = request.session.get('wishlist', [])
            product_id_str = str(product_id)
            if product_id_str in wishlist:
                wishlist.remove(product_id_str)
                request.session['wishlist'] = wishlist
                logger.info(f"Product {product_id} removed from session wishlist for user={user_id}")
            else:
                raise WishlistItemNotFound()

    @staticmethod
    def get_wishlist(request):
        """Получение содержимого списка желаний.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            QuerySet или список: Список элементов желаний для авторизованных или неавторизованных пользователей.

        Raises:
            Exception: Если произошла ошибка при получении данных списка желаний из-за проблем с базой данных.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if request.user.is_authenticated:
            items = WishlistItem.objects.filter(
                user=request.user
            ).select_related('product', 'product__category').prefetch_related(
                'product__category__children'
            )
            logger.info(f"Wishlist retrieved for user={user_id}, items_count={items.count()}")
            return items
        else:
            wishlist = request.session.get('wishlist', [])
            product_ids = [int(pid) for pid in wishlist if pid.isdigit()]
            items = Product.objects.filter(
                id__in=product_ids,
                is_active=True
            ).select_related('category').prefetch_related('category__children')
            logger.info(f"Session wishlist retrieved for user={user_id}, items_count={items.count()}")
            return items

    @staticmethod
    @transaction.atomic
    def merge_wishlist_on_login(user, session_wishlist: list) -> None:
        """Слияние списка желаний из сессии с данными пользователя при входе.

        Args:
            user (User): Аутентифицированный пользователь.
            session_wishlist (list): Список ID товаров из сессии.

        Raises:
            ProductNotAvailable: Если товар из сессии не существует или неактивен.
        """
        user_id = user.id
        for product_id_str in session_wishlist:
            try:
                product = Product.objects.get(id=int(product_id_str), is_active=True)
            except Product.DoesNotExist:
                logger.debug(
                    f"Product with ID {product_id_str} not found or inactive during wishlist merge for user={user_id}"
                )
                continue
            except ValueError:
                logger.debug(f"Invalid product ID '{product_id_str}' in session wishlist for user={user_id}")
                continue

            WishlistItem.objects.get_or_create(user=user, product=product)
            logger.info(f"Product {product_id_str} merged into wishlist for user={user_id}")

