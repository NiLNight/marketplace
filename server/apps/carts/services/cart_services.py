from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from apps.carts.models import OrderItem
from apps.products.models import Product
from apps.users.models import User


class CartService:
    """Сервис для управления корзиной авторизованных пользователей."""

    @staticmethod
    @transaction.atomic
    def add_to_cart(user: User, product_id: int, quantity: int = 1) -> OrderItem:
        """Добавление товара в корзину."""
        if quantity < 1:
            raise ValidationError("Количество должно быть положительным.")

        product = Product.objects.get(id=product_id)
        cart_item, created = OrderItem.objects.get_or_create(
            user=user,
            product=product,
            order__isnull=True,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item

    @staticmethod
    @transaction.atomic
    def update_cart_item(user: User, product_id: int, quantity: int) -> OrderItem | None:
        """Обновление количества товара в корзине."""
        try:
            cart_item = OrderItem.objects.get(user=user, product_id=product_id, order__isnull=True)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
                return None
            return cart_item
        except OrderItem.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def remove_from_cart(user: User, product_id: int) -> bool:
        """Удаление товара из корзины."""
        try:
            cart_item = OrderItem.objects.get(user=user, product_id=product_id, order__isnull=True)
            cart_item.delete()
            return True
        except OrderItem.DoesNotExist:
            return False

    @staticmethod
    def get_cart_items(user: User) -> 'QuerySet[OrderItem]':
        """Получение всех элементов корзины пользователя."""
        return OrderItem.objects.filter(user=user, order__isnull=True).select_related('product')