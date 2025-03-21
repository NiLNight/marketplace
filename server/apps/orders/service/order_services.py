from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.carts.models import OrderItem
from apps.orders.models import Delivery, Order

User = get_user_model()


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user: User, delivery_id: int, requisite_id: int) -> Order:
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
            status='pending',
            total_price=total_price,
            delivery=delivery,
        )
        order.save()

        return order
