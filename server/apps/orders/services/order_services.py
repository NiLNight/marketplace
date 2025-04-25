import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError
from apps.carts.models import OrderItem
from apps.orders.models import Delivery, Order

User = get_user_model()
logger = logging.getLogger(__name__)


class OrderService:
    """Сервис для управления заказами пользователей.

    Предоставляет методы для создания, получения и отмены заказов, а также обработки связанных данных.
    """

    @staticmethod
    def get_user_orders(user: User, request) -> list:
        """Получение списка заказов пользователя с сортировкой.

        Активные заказы отображаются первыми, затем завершенные и отмененные по дате создания.

        Args:
            user (User): Аутентифицированный пользователь.
            request: HTTP-запрос, содержащий параметры фильтрации и сортировки.

        Returns:
            list: Список объектов заказов.
        """
        logger.info(f"Retrieving orders for user={user.id}")
        active_statuses = ['processing', 'shipped']
        status = request.GET.get('status')

        # Фильтрация по статусу, если указан
        if status in active_statuses:
            orders = Order.objects.filter(user=user, status__in=active_statuses).order_by('-created')
        elif status == 'delivered':
            orders = Order.objects.filter(user=user, status='delivered').order_by('-created')
        elif status == 'cancelled':
            orders = Order.objects.filter(user=user, status='cancelled').order_by('-created')
        else:
            # По умолчанию: активные, затем доставленные, затем отмененные
            active_orders = Order.objects.filter(user=user, status__in=active_statuses).order_by('-created')
            delivered_orders = Order.objects.filter(user=user, status='delivered').order_by('-created')
            cancelled_orders = Order.objects.filter(user=user, status='cancelled').order_by('-created')
            sort_by = request.GET.get('ordering')
            if sort_by == 'd':
                orders = list(cancelled_orders) + list(delivered_orders) + list(active_orders)
            else:
                orders = list(active_orders) + list(delivered_orders) + list(cancelled_orders)

        logger.info(f"Retrieved {len(orders)} orders for user={user.id}")
        return orders

    @staticmethod
    def get_order_details(order_id: int, user: User) -> Order:
        """Получение детальной информации о заказе.

        Args:
            order_id (int): Идентификатор заказа.
            user (User): Аутентифицированный пользователь.

        Returns:
            Order: Объект заказа с деталями.

        Raises:
            ValidationError: Если заказ не найден или не принадлежит пользователю.
        """
        logger.info(f"Retrieving details for order={order_id}, user={user.id}")
        try:
            order = Order.objects.prefetch_related(
                Prefetch(
                    'order_items',
                    queryset=OrderItem.objects.select_related('product__category').prefetch_related(
                        'product__category__children',
                    )
                )
            ).get(pk=order_id, user=user)
            logger.info(f"Order {order_id} details retrieved for user={user.id}")
            return order
        except Order.DoesNotExist:
            logger.warning(f"Order {order_id} not found for user={user.id}")
            raise ValidationError("Заказ не найден")

    @staticmethod
    @transaction.atomic
    def create_order(user: User, delivery_id: int) -> Order:
        """Создание заказа из корзины пользователя.

        Args:
            user (User): Аутентифицированный пользователь, для которого создается заказ.
            delivery_id (int): Идентификатор адреса доставки.

        Returns:
            Order: Созданный объект заказа.

        Raises:
            ValidationError: Если корзина пуста, доставка не найдена или недостаточно товара на складе.
        """
        logger.info(f"Attempting to create order for user={user.id}")
        # Получение товаров из корзины, еще не привязанных к заказу
        cart_items = OrderItem.objects.filter(user=user, order__isnull=True)
        if not cart_items.exists():
            logger.warning(f"Cart is empty for user={user.id}")
            raise ValidationError("Корзина пуста")

        # Проверка существования адреса доставки
        try:
            delivery = Delivery.objects.get(pk=delivery_id, user=user)
        except Delivery.DoesNotExist:
            logger.warning(f"Delivery {delivery_id} not found for user={user.id}")
            raise ValidationError("Указанная доставка не найдена")

        # Расчет общей стоимости заказа с учетом скидок и доставки
        total_price = sum(
            item.product.price_with_discount * item.quantity for item in cart_items
        ) + delivery.cost

        # Создание заказа
        order = Order.objects.create(
            user=user,
            status='processing',
            total_price=total_price,
            delivery=delivery,
        )

        # Проверка и обновление запасов товаров
        for item in cart_items:
            product = item.product
            if product.stock < item.quantity:
                logger.warning(f"Insufficient stock for product {product.id}, user={user.id}")
                raise ValidationError(f"Недостаточно товара {product.title} на складе.")
            product.stock -= item.quantity
            product.save()

        # Привязка элементов корзины к заказу и очистка связи с пользователем
        for item in cart_items:
            item.order = order
            item.user = None
            item.save()

        # Удаление оставшихся элементов корзины, не привязанных к заказу
        OrderItem.objects.filter(user=user, order__isnull=True).delete()
        logger.info(f"Order {order.id} successfully created for user={user.id}")
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int, user: User) -> None:
        """Отмена заказа пользователем.

        Args:
            order_id (int): Идентификатор заказа.
            user (User): Аутентифицированный пользователь.

        Raises:
            ValidationError: Если заказ не найден или его нельзя отменить.
        """
        logger.info(f"Attempting to cancel order={order_id} for user={user.id}")
        try:
            order = Order.objects.get(id=order_id, user=user)
            if order.status in ['processing']:
                order.status = 'cancelled'
                order.save()
                logger.info(f"Order {order_id} successfully cancelled for user={user.id}")
            else:
                logger.warning(f"Cannot cancel order {order_id} with status={order.status} for user={user.id}")
                raise ValidationError("Нельзя отменить заказ, который уже отправлен или доставлен.")
        except Order.DoesNotExist:
            logger.warning(f"Order {order_id} not found for user={user.id}")
            raise ValidationError("Заказ не найден")
