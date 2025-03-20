from django.db import transaction
from django.core.exceptions import ValidationError

from apps.carts.models import OrderItem
from apps.products.models import Product


class CartService:
    """Сервис для управления корзиной авторизованных пользователей."""

    @staticmethod
    def add_to_cart(request, product_id: int, quantity: int = 1):
        """Добавление товара в корзину."""
        if quantity < 1:
            raise ValidationError("Количество должно быть положительным.")

        product = Product.objects.get(id=product_id)
        if quantity > product.stock:
            raise ValueError('Товар не в наличии')

        if request.user.is_authenticated:
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
    def update_cart_item(request, product_id: int, quantity: int) -> dict | None:
        """Обновление количества товара в корзине."""
        product = Product.objects.get(id=product_id)
        if quantity > product.stock:
            raise ValueError('Товар не в наличии')
        if request.user.is_authenticated:
            try:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                    return {'id': cart_item.id, 'product_id': cart_item.product_id, 'quantity': cart_item.quantity}
                else:
                    cart_item.delete()
                    return None
            except OrderItem.DoesNotExist:
                return None
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            if quantity > 0:
                cart[product_id_str] = quantity
                request.session['cart'] = cart
                return {'product_id': product_id, 'quantity': quantity}
            else:
                if product_id_str in cart:
                    del cart[product_id_str]
                    request.session['cart'] = cart
                return None

    @staticmethod
    def remove_from_cart(request, product_id: int) -> bool:
        """Удаление товара из корзины."""
        if request.user.is_authenticated:
            try:
                cart_item = OrderItem.objects.get(user=request.user, product_id=product_id, order__isnull=True)
                cart_item.delete()
                return True
            except OrderItem.DoesNotExist:
                return False
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            if product_id_str in cart:
                del cart[product_id_str]
                request.session['cart'] = cart
                return True
            return False

    @staticmethod
    def get_cart(request):
        """Получение содержимого корзины."""
        if request.user.is_authenticated:
            return OrderItem.objects.filter(user=request.user, order__isnull=True).select_related('product')
        else:
            cart = request.session.get('cart', {})
            print(cart)
            product_ids = cart.keys()
            products = Product.objects.filter(id__in=product_ids)
            return [{'product': p, 'quantity': cart[str(p.id)]} for p in products]

    @staticmethod
    @transaction.atomic
    def merge_cart_on_login(user, session_cart: dict):
        if session_cart:
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
