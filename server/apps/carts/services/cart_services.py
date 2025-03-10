from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from apps.orders.models import OrderItem
from apps.products.models import Product
from apps.carts.exceptions import *


class CartService:
    MAX_ITEMS = 40
    MAX_QUANTITY = 20

    @classmethod
    def get_cart_queryset(cls, request):
        """Получение QuerySet для корзины"""
        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key

        if user:
            return OrderItem.objects.filter(user=user, order=None)
        elif session_key:
            return OrderItem.objects.filter(session_key=session_key, order=None)
        return OrderItem.objects.none()

    @classmethod
    def _validate_product(cls, product):
        if not product.is_available or product.stock < 1:
            raise ProductNotAvailable()

    @classmethod
    def _validate_quantity(cls, quantity):
        if not (1 <= quantity <= cls.MAX_QUANTITY):
            raise InvalidQuantity(f"Количество должно быть от 1 до {cls.MAX_QUANTITY}")

    @classmethod
    def _get_identifier(cls, request):
        if request.user.is_authenticated:
            return {'user': request.user}
        return {'session_key': request.session.session_key}

    @classmethod
    @transaction.atomic
    def add_to_cart(cls, request, product_id, quantity=1):
        try:
            product = Product.objects.select_for_update().get(pk=product_id)
            cls._validate_product(product)
            cls._validate_quantity(quantity)

            identifier = cls._get_identifier(request)
            price = product.price * (100 - product.discount) / 100

            item, created = OrderItem.objects.update_or_create(
                **identifier,
                product=product,
                order=None,
                defaults={'quantity': quantity, 'price': price}
            )

            return item
        except ObjectDoesNotExist:
            raise ProductNotAvailable("Товар не найден")
