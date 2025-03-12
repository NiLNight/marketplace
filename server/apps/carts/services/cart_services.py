from django.db import transaction
from django.core.exceptions import ValidationError
from apps.carts.models import OrderItem
from apps.products.models import Product
from apps.users.models import User


class CartService:
    @staticmethod
    @transaction.atomic
    def add_to_cart(user: User, product_id: int, quantity: int = 1) -> OrderItem:
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
