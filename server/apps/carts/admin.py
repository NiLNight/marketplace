# carts/admin.py
from django.contrib import admin
from .models import OrderItem


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'quantity', 'order_status')
    list_filter = ('user', 'product')
    search_fields = ('product__title', 'user__email')
    raw_id_fields = ('product', 'user', 'order')

    def order_status(self, obj):
        return obj.order.status if obj.order else 'В корзине'

    order_status.short_description = 'Статус'
