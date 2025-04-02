from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError

from apps.carts.models import OrderItem
from apps.orders.models import Delivery, Order

User = get_user_model()


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user: User, delivery_id: int) -> Order:
        """Создание заказа из корзины."""
        # Получение товаров корзины
        cart_items = OrderItem.objects.filter(user=user, order__isnull=True)
        if not cart_items.exists():
            raise ValidationError("Корзина пуста")

        try:
            delivery = Delivery.objects.get(pk=delivery_id, user=user)
        except Delivery.DoesNotExist:
            raise ValidationError("Указанная доставка не найдена")

        total_price = sum(
            item.product.price_with_discount * item.quantity for item in cart_items
        ) + delivery.cost

        order = Order.objects.create(
            user=user,
            status='processing',
            total_price=total_price,
            delivery=delivery,
        )
        for item in cart_items:
            product = item.product
            if product.stock < item.quantity:
                raise ValidationError(f"Недостаточно товара {product.title} на складе.")
            product.stock -= item.quantity
            product.save()

        for item in cart_items:
            item.order = order
            item.user = None
            item.save()

        order.save()
        OrderItem.objects.filter(user=user, order__isnull=True).delete()
        return order

    @staticmethod
    def get_user_orders(user: User):
        """Получение заказов пользователя: активные первыми, затем архивные по дате."""
        active_statuses = ['processing', 'shipped']
        archived_statuses = ['delivered', 'cancelled']

        active_orders = Order.objects.filter(user=user, status__in=active_statuses).order_by('-created')
        archived_orders = Order.objects.filter(user=user, status__in=archived_statuses).order_by('-created')

        return list(active_orders) + list(archived_orders)

    @staticmethod
    def get_order_details(order_id: int, user: User):
        """Получение деталей заказа."""
        try:
            order = Order.objects.prefetch_related(
                Prefetch(
                    'order_items',
                    queryset=OrderItem.objects.select_related('product__category').prefetch_related(
                        'product__category__children',
                    )
                )
            ).get(pk=order_id, user=user)
            return order
        except Order.DoesNotExist:
            raise ValidationError('Заказ не найден')

    @staticmethod
    def cancel_order(order_id: int, user: User):
        order = Order.objects.get(id=order_id, user=user)
        if order.status in ['processing']:
            order.status = 'cancelled'
            order.save()
        else:
            raise ValidationError("Нельзя отменить заказ, который уже отправлен или доставлен.")