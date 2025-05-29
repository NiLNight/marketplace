"""Модуль администрирования для приложения carts.

Регистрирует модель OrderItem в административном интерфейсе Django с кастомизацией отображения.
"""

from django.contrib import admin
from .models import OrderItem


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админ-класс для модели OrderItem.

    Attributes:
        list_display: Поля для отображения в списке (id, product, user, quantity, order_status).
        list_filter: Фильтры для списка (user, product).
        search_fields: Поля для поиска (product__title, user__email).
        raw_id_fields: Поля с выбором по ID (product, user, order).
    """
    list_display = ('id', 'product', 'user', 'quantity', 'order_status')
    list_filter = ('user', 'product')
    search_fields = ('product__title', 'user__email')
    raw_id_fields = ('product', 'user', 'order')

    def order_status(self, obj):
        """Возвращает статус заказа или указание на корзину.

        Args:
            obj (OrderItem): Объект элемента заказа/корзины.

        Returns:
            str: Статус заказа или 'В корзине', если заказ отсутствует.
        """
        return obj.order.status if obj.order else 'В корзине'

    order_status.short_description = 'Статус'
