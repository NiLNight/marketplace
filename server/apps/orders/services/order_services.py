import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, F, Q, Case, Value, IntegerField, When
from rest_framework.exceptions import ValidationError, APIException
from django.utils.translation import gettext_lazy as _
from apps.carts.models import OrderItem
from apps.orders.models import Order
from apps.products.models import Product
from apps.delivery.services.delivery_services import DeliveryService

User = get_user_model()
logger = logging.getLogger(__name__)


class OrderService:
    """
    Сервис для управления заказами пользователей.

    Предоставляет методы для создания, получения, отмены заказов и обработки связанных данных.

    Attributes:
        logger: Логгер для записи событий сервиса.
    """

    @staticmethod
    def get_user_orders(user: User, request) -> list:
        """
        Получает список заказов пользователя с сортировкой.

        Активные заказы (processing, shipped) отображаются первыми, затем завершенные (delivered)
        и отмененные (cancelled) по дате создания.

        Args:
            user (User): Аутентифицированный пользователь.
            request: HTTP-запрос, содержащий параметры фильтрации и сортировки.

        Returns:
            list: Список объектов заказов.

        Raises:
            APIException: Если пользователь неактивен.
        """
        logger.debug(f"Starting retrieval of orders for user={user.id}")
        if not user.is_active:
            logger.warning(f"Inactive user={user.id} attempted to access orders, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise APIException(_("Аккаунт не активирован"), code="account_not_activated")

        logger.info(f"Retrieving orders for user={user.id}, "
                    f"path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        status = request.GET.get('status')
        queryset = Order.objects.filter(user=user)
        status_filters = {
            'processing': Q(status__in=['processing', 'shipped']),
            'delivered': Q(status='delivered'),
            'cancelled': Q(status='cancelled'),
        }

        if status in status_filters:
            queryset = queryset.filter(status_filters[status]).order_by('-created')
        else:
            # Приоритет сортировки: активные заказы первые, затем delivered, затем cancelled
            order_priority = Case(
                When(status__in=['processing', 'shipped'], then=Value(1)),
                When(status='delivered', then=Value(2)),
                When(status='cancelled', then=Value(3)),
                output_field=IntegerField(),
            )
            sort_by = request.GET.get('ordering')
            order_by = ['order_priority', '-created'] if sort_by != 'd' else ['-order_priority', '-created']
            queryset = queryset.annotate(order_priority=order_priority).order_by(*order_by)

        logger.info(f"Retrieved {queryset.count()} orders for user={user.id},"
                    f" IP={request.META.get('REMOTE_ADDR')}")
        return queryset

    @staticmethod
    def get_order_details(order_id: int, user: User, request) -> Order:
        """
        Получает детальную информацию о заказе.

        Args:
            order_id (int): Идентификатор заказа.
            user (User): Аутентифицированный пользователь.
            request: HTTP-запрос для логирования IP.

        Returns:
            Order: Объект заказа с деталями.

        Raises:
            ValidationError: Если order_id некорректен или заказ не найден.
            APIException: Если пользователь неактивен.
        """
        logger.debug(f"Starting retrieval of order={order_id} for user={user.id}")
        if not user.is_active:
            logger.warning(f"Inactive user={user.id} attempted to access order={order_id}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise APIException(_("Аккаунт не активирован"), code="account_not_activated")
        if not isinstance(order_id, int) or order_id <= 0:
            logger.warning(f"Invalid order_id={order_id} for user={user.id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(_("Идентификатор заказа должен быть положительным целым числом"))

        logger.info(f"Retrieving details for order={order_id}, user={user.id}, "
                    f"IP={request.META.get('REMOTE_ADDR')}")
        try:
            order = Order.objects.prefetch_related(
                Prefetch(
                    'order_items',
                    queryset=OrderItem.objects.select_related('product__category').prefetch_related(
                        'product__category__children',
                    )
                )
            ).get(pk=order_id, user=user)
            logger.info(f"Order {order_id} details retrieved for user={user.id}, "
                        f"IP={request.META.get('REMOTE_ADDR')}")
            return order
        except Order.DoesNotExist:
            logger.warning(f"Order {order_id} not found for user={user.id}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError({"detail": _("Заказ не найден"), "code": "not_found"})

    @staticmethod
    @transaction.atomic
    def create_order(user: User, delivery_id: int = None, pickup_point_id: int = None, request=None) -> Order:
        """
        Создает заказ из корзины пользователя.

        Позволяет выбрать либо адрес доставки, либо пункт выдачи.

        Args:
            user (User): Аутентифицированный пользователь.
            delivery_id (int, optional): Идентификатор адреса доставки.
            pickup_point_id (int, optional): Идентификатор пункта выдачи.
            request: HTTP-запрос для логирования IP.

        Returns:
            Order: Созданный объект заказа.

        Raises:
            ValidationError: Если входные данные некорректны, корзина пуста или недостаточно товара.
            APIException: Если пользователь неактивен.
        """
        logger.debug(f"Starting order creation for user={user.id}")
        if not user.is_active:
            logger.warning(f"Inactive user={user.id} attempted to create order, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise APIException(_("Аккаунт не активирован"), code="account_not_activated")
        if delivery_id and not (isinstance(delivery_id, int) and delivery_id > 0):
            logger.warning(f"Invalid delivery_id={delivery_id} for user={user.id}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(_("Идентификатор доставки должен быть положительным целым числом"))
        if pickup_point_id and not (isinstance(pickup_point_id, int) and pickup_point_id > 0):
            logger.warning(f"Invalid pickup_point_id={pickup_point_id} for user={user.id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(_("Идентификатор пункта выдачи должен быть положительным целым числом"))

        logger.info(f"Attempting to create order for user={user.id}, "
                    f"delivery_id={delivery_id}, pickup_point_id={pickup_point_id}, "
                    f"IP={request.META.get('REMOTE_ADDR')}")
        if delivery_id and pickup_point_id:
            logger.warning(f"Both delivery_id and pickup_point_id provided for user={user.id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(
                {"detail": _("Нельзя указать и доставку, и пункт выдачи одновременно"), "code": "invalid_input"}
            )
        if not delivery_id and not pickup_point_id:
            logger.warning(f"Neither delivery_id nor pickup_point_id provided for user={user.id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(
                {"detail": _("Необходимо указать либо доставку, либо пункт выдачи"), "code": "missing_input"}
            )

        cart_items = OrderItem.objects.filter(user=user, order__isnull=True)
        if not cart_items.exists():
            logger.warning(f"Cart is empty for user={user.id}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError({"detail": _("Корзина пуста"), "code": "empty_cart"})

        delivery = None
        pickup_point = None
        total_price = sum(item.product.price_with_discount * item.quantity for item in cart_items)

        if delivery_id:
            delivery = DeliveryService.get_user_delivery(request, user, delivery_id)
            total_price += delivery.cost
        else:
            pickup_point = DeliveryService.get_pickup_point(request, pickup_point_id)

        order = Order.objects.create(
            user=user,
            status='processing',
            total_price=total_price,
            delivery=delivery,
            pickup_point=pickup_point,
        )

        products = {item.product.id: item.quantity for item in cart_items}
        for product in Product.objects.filter(id__in=products.keys()).select_for_update():
            if product.stock < products[product.id]:
                logger.warning(f"Insufficient stock for product {product.id}, "
                               f"user={user.id}, IP={request.META.get('REMOTE_ADDR')}")
                raise ValidationError(
                    {"detail": _("Недостаточно товара {product.title} на складе"), "code": "insufficient_stock"}
                )
            product.stock = F('stock') - products[product.id]
            product.save()

        for item in cart_items:
            item.order = order
            item.user = None
            item.save()

        OrderItem.objects.filter(user=user, order__isnull=True).delete()
        logger.info(f"Order {order.id} successfully created for user={user.id},"
                    f" IP={request.META.get('REMOTE_ADDR')}")
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int, user: User, request) -> None:
        """
        Отменяет заказ пользователя.

        Args:
            order_id (int): Идентификатор заказа.
            user (User): Аутентифицированный пользователь.
            request: HTTP-запрос для логирования IP.

        Raises:
            ValidationError: Если order_id некорректен, заказ не найден или его нельзя отменить.
            APIException: Если пользователь неактивен.
        """
        logger.debug(f"Starting cancellation of order={order_id} for user={user.id}")
        if not user.is_active:
            logger.warning(f"Inactive user={user.id} attempted to cancel order={order_id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise APIException(_("Аккаунт не активирован"), code="account_not_activated")
        if not isinstance(order_id, int) or order_id <= 0:
            logger.warning(f"Invalid order_id={order_id} for user={user.id}, "
                           f"IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError(_("Идентификатор заказа должен быть положительным числом"))

        logger.info(f"Attempting to cancel order={order_id} for user={user.id},"
                    f" IP={request.META.get('REMOTE_ADDR')}")
        try:
            order = Order.objects.get(id=order_id, user=user)
            if order.status in ['processing']:
                order.status = 'cancelled'
                order.save()
                logger.info(f"Order {order_id} successfully cancelled for user={user.id},"
                            f" IP={request.META.get('REMOTE_ADDR')}")
            else:
                logger.warning(f"Cannot cancel order {order_id} with status={order.status} for user={user.id},"
                               f" IP={request.META.get('REMOTE_ADDR')}")
                raise ValidationError(
                    {"detail": _("Нельзя отменить заказ, который уже отправлен или доставлен"),
                     "code": "invalid_status"}
                )
        except Order.DoesNotExist:
            logger.warning(f"Order {order_id} not found for user={user.id},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError({"detail": _("Заказ не найден"), "code": "not_found"})
