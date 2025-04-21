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

    @staticmethod
    @transaction.atomic
    def remove_from_wishlist(request, product_id: int) -> bool:
        """Удаление товара из списка желаний."""
        if request.user.is_authenticated:
            try:
                wishlist_item = WishlistItem.objects.get(
                    user=request.user,
                    product_id=product_id
                )
                wishlist_item.delete()
                return True
            except WishlistItem.DoesNotExist:
                raise WishlistItemNotFound()
        else:
            wishlist = request.session.get('wishlist', [])
            product_id_str = str(product_id)
            if product_id_str in wishlist:
                wishlist.remove(product_id_str)
                request.session['wishlist'] = wishlist
                return True
            raise WishlistItemNotFound()

    @staticmethod
    def get_wishlist(request):
        """Получение содержимого списка желаний."""
        if request.user.is_authenticated:
            return WishlistItem.objects.filter(
                user=request.user
            ).select_related('product', 'product__category').prefetch_related(
                'product__category__children'
            )
        else:
            wishlist = request.session.get('wishlist', [])
            product_ids = [int(pid) for pid in wishlist if pid.isdigit()]
            return Product.objects.filter(
                id__in=product_ids,
                is_active=True
            ).select_related('category').prefetch_related('category__children')