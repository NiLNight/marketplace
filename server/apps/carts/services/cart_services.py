from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from apps.carts.models import OrderItem
from apps.products.models import Product
from apps.users.models import User


class CartService:
    """Сервис для управления корзиной авторизованных пользователей."""

    @staticmethod
    def add_to_cart(request, product_id: int, quantity: int = 1):
        """Добавление товара в корзину."""
        if quantity < 1:
            raise ValidationError("Количество должно быть положительным.")

        if request.user.is_authenticated:
            product = Product.objects.get(id=product_id)
            cart_item, created = OrderItem.objects.get_or_create(
                user=request.user,
                product=product,
                order__isnull=True,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            cart[product_id_str] = cart.get(product_id_str, 0) + quantity
            request.session['cart'] = cart

    @staticmethod
    @transaction.atomic
    def update_cart_item(request, product_id: int, quantity: int) -> OrderItem | None | dict:
        """Обновление количества товара в корзине."""
        try:
            if request.user.is_authenticated:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                else:
                    cart_item.delete()
                    return None
                return cart_item
            else:
                cart = request.session.get('cart', {})
                if quantity > 0:
                    cart[str(product_id)] = quantity
                else:
                    if str(product_id) in cart:
                        del cart[str(product_id)]
                    return None
                return {'product_id': product_id, 'quantity': quantity}
        except OrderItem.DoesNotExist:
            return None

    @staticmethod
    def remove_from_cart(request, product_id: int) -> bool:
        """Удаление товара из корзины."""
        try:
            if request.user.is_authenticated:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                cart_item.delete()
                return True
            else:
                cart = request.session.get('cart', {})
                product_id_str = str(product_id)
                if product_id_str in cart:
                    del cart[product_id_str]
                    request.session['cart'] = cart
                    return True
        except OrderItem.DoesNotExist:
            return False

    @staticmethod
    def get_cart(request):
        """Получение содержимого корзины."""
        if request.user.is_authenticated:
            return OrderItem.objects.filter(user=request.user, order__isnull=True).select_related('product')
        else:
            cart = request.session.get('cart', {})
            product_ids = cart.keys()
            products = Product.objects.filter(id__in=product_ids)
            return [{'product': p, 'quantity': cart[str(p.id)]} for p in products]

    @staticmethod
    @transaction.atomic
    def merge_cart_on_login(user: User, session_cart: dict):
        for product_id_str, quantity in session_cart.items():
            try:
                product_id = int(product_id_str)
                product = Product.objects.get(id=product_id)
                cart_item, created = OrderItem.objects.get_or_create(
                    user=user,
                    product=product,
                    order__isnull=True,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity  # Складываем количества при дубликатах
                    cart_item.save()
            except (ValueError, Product.DoesNotExist):
                continue  # Пропускаем некорректные товары
