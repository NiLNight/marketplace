from django.db import transaction
from apps.products.models import Product
from apps.wishlists.exceptions import (
    WishlistItemNotFound,
    ProductNotAvailable
)
from apps.wishlists.models import WishlistItem


class WishlistService:
    """Сервис для управления списками желаний зарегистрированных и незарегистрированных пользователей."""

    @staticmethod
    @transaction.atomic
    def add_to_wishlist(request, product_id: int) -> None:
        """Добавление товара в список желаний."""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise ProductNotAvailable("Товар не найден или недоступен")

        if request.user.is_authenticated:
            # Для зарегистрированных пользователей
            WishlistItem.objects.get_or_create(
                user=request.user,
                product=product
            )
        else:
            # Для незарегистрированных пользователей
            wishlist = request.session.get('wishlist', [])
            if str(product_id) not in wishlist:
                wishlist.append(str(product_id))
                request.session['wishlist'] = wishlist


    